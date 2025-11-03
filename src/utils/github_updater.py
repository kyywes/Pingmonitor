"""
GitHub Auto-Updater
Sistema di aggiornamento automatico da repository GitHub
Controlla patch remote e applica automaticamente
"""

import os
import subprocess
import json
import shutil
from pathlib import Path
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class GitHubUpdater:
    """
    Sistema di auto-update da GitHub repository
    """

    def __init__(self, repo_url=None, branch="main", config_file=None):
        """
        Inizializza GitHub Updater

        Args:
            repo_url: URL del repository GitHub
            branch: Branch da monitorare (default: main)
            config_file: File configurazione custom
        """
        self.branch = branch

        # Directory base dell'applicazione
        self.app_dir = Path(__file__).parent.parent.parent
        self.src_dir = self.app_dir / "src"

        # Directory per configurazione GitHub
        self.config_dir = Path.home() / ".pingmonitor"
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # File configurazione GitHub
        if config_file:
            self.config_file = Path(config_file)
        else:
            self.config_file = self.config_dir / "github_config.json"

        # Carica configurazione
        self.config = self._load_config()

        # URL repository (da config o parametro)
        if repo_url:
            self.repo_url = repo_url
        else:
            self.repo_url = self.config.get("repo_url", "")

        # Directory temporanea per clone
        self.temp_dir = self.config_dir / "github_temp"

        # File stato ultimo update
        self.state_file = self.config_dir / "github_state.json"

        # Directory backup
        self.backup_dir = self.config_dir / "backups"
        self.backup_dir.mkdir(exist_ok=True)

        logger.info(f"GitHub Updater initialized")
        logger.info(f"Repository: {self.repo_url}")
        logger.info(f"Branch: {self.branch}")

    def _load_config(self) -> dict:
        """Carica configurazione GitHub"""
        if not self.config_file.exists():
            return {}

        try:
            with open(self.config_file, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading GitHub config: {e}")
            return {}

    def _save_config(self, config: dict):
        """Salva configurazione GitHub"""
        try:
            with open(self.config_file, "w") as f:
                json.dump(config, f, indent=2)
            logger.info("GitHub config saved")
        except Exception as e:
            logger.error(f"Error saving GitHub config: {e}")

    def is_configured(self) -> bool:
        """Controlla se GitHub è configurato"""
        return bool(self.repo_url and self.repo_url.strip())

    def configure(self, repo_url: str, branch: str = "main", token: str = None):
        """
        Configura GitHub updater

        Args:
            repo_url: URL repository (es: https://github.com/user/repo.git)
            branch: Branch da monitorare
            token: Personal Access Token (opzionale per repo privati)
        """
        self.repo_url = repo_url
        self.branch = branch

        config = {
            "repo_url": repo_url,
            "branch": branch,
            "configured_at": datetime.now().isoformat()
        }

        # Salva token in modo sicuro se fornito
        if token:
            config["token"] = token  # In produzione, criptare!

        self._save_config(config)
        logger.info(f"GitHub configured: {repo_url} (branch: {branch})")

    def _run_git_command(self, args: list, cwd=None, check=True) -> tuple:
        """
        Esegue comando git

        Args:
            args: Lista argomenti comando git
            cwd: Working directory
            check: Se True, solleva eccezione su errore

        Returns:
            (success: bool, output: str, error: str)
        """
        try:
            # Prepara ambiente
            env = os.environ.copy()

            # Aggiungi token se presente (per repo privati)
            token = self.config.get("token")
            if token and self.repo_url:
                # Inserisci token nell'URL
                if "https://" in self.repo_url:
                    url_with_token = self.repo_url.replace(
                        "https://",
                        f"https://{token}@"
                    )
                    env["GIT_URL"] = url_with_token

            # Esegui comando
            result = subprocess.run(
                ["git"] + args,
                cwd=cwd,
                capture_output=True,
                text=True,
                env=env,
                check=check
            )

            return True, result.stdout, result.stderr

        except subprocess.CalledProcessError as e:
            logger.error(f"Git command failed: {e}")
            return False, e.stdout if hasattr(e, 'stdout') else "", e.stderr if hasattr(e, 'stderr') else str(e)
        except FileNotFoundError:
            logger.error("Git not found - please install Git")
            return False, "", "Git not installed"
        except Exception as e:
            logger.error(f"Error running git command: {e}")
            return False, "", str(e)

    def check_for_updates(self, silent=True) -> tuple:
        """
        Controlla se ci sono aggiornamenti disponibili su GitHub

        Args:
            silent: Se True, non mostra errori (solo log)

        Returns:
            (has_updates: bool, message: str, details: dict)
        """
        if not self.is_configured():
            msg = "GitHub not configured"
            if not silent:
                logger.warning(msg)
            return False, msg, {}

        try:
            logger.info("=" * 70)
            logger.info("🔍 GITHUB AUTO-UPDATE: Checking for updates...")
            logger.info("=" * 70)

            # Pulisci directory temporanea se esiste
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)

            # Crea directory temporanea
            self.temp_dir.mkdir(parents=True, exist_ok=True)

            # Clone repository (shallow per velocità)
            logger.info(f"Cloning {self.repo_url}...")
            success, stdout, stderr = self._run_git_command([
                "clone",
                "--depth", "1",
                "--branch", self.branch,
                self.repo_url,
                str(self.temp_dir)
            ])

            if not success:
                msg = f"Failed to clone repository: {stderr}"
                logger.error(msg)
                return False, msg, {}

            logger.info("✓ Repository cloned successfully")

            # Ottieni hash ultimo commit remoto
            success, remote_hash, stderr = self._run_git_command(
                ["rev-parse", "HEAD"],
                cwd=self.temp_dir
            )

            if not success:
                msg = f"Failed to get remote commit: {stderr}"
                logger.error(msg)
                return False, msg, {}

            remote_hash = remote_hash.strip()

            # Carica stato precedente
            last_state = self._load_state()
            last_hash = last_state.get("last_commit_hash", "")

            # Confronta hash
            if remote_hash == last_hash:
                logger.info("✓ No updates available (same commit hash)")
                logger.info("=" * 70)
                return False, "No updates available", {
                    "remote_hash": remote_hash,
                    "last_hash": last_hash
                }

            # Ci sono aggiornamenti!
            logger.warning("🆕 NEW UPDATES AVAILABLE!")
            logger.warning(f"   Remote commit: {remote_hash[:8]}")
            logger.warning(f"   Local commit:  {last_hash[:8] if last_hash else 'None'}")

            # Ottieni info commit
            success, commit_msg, stderr = self._run_git_command(
                ["log", "-1", "--pretty=format:%s"],
                cwd=self.temp_dir
            )

            commit_message = commit_msg.strip() if success else "Unknown"

            # Ottieni lista file modificati (se c'è stato precedente)
            modified_files = []
            if last_hash:
                # Qui non possiamo fare diff perché non abbiamo il vecchio repo
                # Ma possiamo contare i file in src/
                src_temp = self.temp_dir / "src"
                if src_temp.exists():
                    modified_files = [str(f.relative_to(src_temp)) for f in src_temp.rglob("*.py")]

            logger.info("=" * 70)

            return True, f"Updates available: {commit_message}", {
                "remote_hash": remote_hash,
                "last_hash": last_hash,
                "commit_message": commit_message,
                "modified_files": modified_files,
                "temp_dir": str(self.temp_dir)
            }

        except Exception as e:
            msg = f"Error checking for updates: {e}"
            logger.error(msg, exc_info=True)
            return False, msg, {}

    def apply_updates(self, details: dict) -> tuple:
        """
        Applica gli aggiornamenti scaricati

        Args:
            details: Dettagli da check_for_updates

        Returns:
            (success: bool, message: str)
        """
        try:
            logger.info("=" * 70)
            logger.info("📦 APPLYING GITHUB UPDATES...")
            logger.info("=" * 70)

            temp_dir = Path(details.get("temp_dir", self.temp_dir))

            if not temp_dir.exists():
                return False, "Temp directory not found"

            # 1. Crea backup della directory src/ corrente
            logger.info("Creating backup...")
            backup_path = self._create_backup()
            if not backup_path:
                return False, "Failed to create backup"

            logger.info(f"✓ Backup created: {backup_path}")

            # 2. Copia nuovi file da temp_dir/src/ a src/
            src_temp = temp_dir / "src"

            if not src_temp.exists():
                return False, "No src/ directory in repository"

            logger.info(f"Copying files from {src_temp} to {self.src_dir}...")

            # Copia ricorsivamente
            copied_files = 0
            for item in src_temp.rglob("*"):
                if item.is_file():
                    # Path relativo
                    rel_path = item.relative_to(src_temp)
                    dest_path = self.src_dir / rel_path

                    # Crea directory se non esiste
                    dest_path.parent.mkdir(parents=True, exist_ok=True)

                    # Copia file
                    shutil.copy2(item, dest_path)
                    copied_files += 1
                    logger.debug(f"  Copied: {rel_path}")

            logger.info(f"✓ Copied {copied_files} files")

            # 3. Salva nuovo stato
            remote_hash = details.get("remote_hash", "")
            self._save_state({
                "last_commit_hash": remote_hash,
                "last_update": datetime.now().isoformat(),
                "backup_path": str(backup_path),
                "copied_files": copied_files
            })

            logger.info("✓ State saved")

            # 4. Pulisci temp directory
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
                logger.info("✓ Temp directory cleaned")

            logger.info("=" * 70)
            logger.info("✅ UPDATES APPLIED SUCCESSFULLY!")
            logger.info("=" * 70)

            return True, f"Successfully applied {copied_files} file updates"

        except Exception as e:
            msg = f"Error applying updates: {e}"
            logger.error(msg, exc_info=True)

            # Tenta rollback
            logger.warning("Attempting rollback...")
            rollback_success = self.rollback()
            if rollback_success:
                return False, f"{msg} (rolled back successfully)"
            else:
                return False, f"{msg} (rollback failed - manual intervention needed)"

    def _create_backup(self) -> Path:
        """
        Crea backup della directory src/

        Returns:
            Path al backup creato, None se errore
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.backup_dir / f"backup_{timestamp}"

            # Copia src/ nel backup
            shutil.copytree(self.src_dir, backup_path)

            # Mantieni solo ultimi 5 backup
            self._cleanup_old_backups(keep=5)

            return backup_path

        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return None

    def _cleanup_old_backups(self, keep=5):
        """Elimina vecchi backup mantenendo solo gli ultimi N"""
        try:
            backups = sorted(
                [b for b in self.backup_dir.iterdir() if b.is_dir()],
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )

            # Elimina vecchi backup
            for old_backup in backups[keep:]:
                shutil.rmtree(old_backup)
                logger.debug(f"Removed old backup: {old_backup.name}")

        except Exception as e:
            logger.error(f"Error cleaning old backups: {e}")

    def rollback(self) -> bool:
        """
        Rollback all'ultimo backup

        Returns:
            True se successo, False altrimenti
        """
        try:
            logger.warning("=" * 70)
            logger.warning("🔄 ROLLING BACK TO LAST BACKUP...")
            logger.warning("=" * 70)

            # Trova ultimo backup
            state = self._load_state()
            last_backup = state.get("backup_path")

            if not last_backup or not Path(last_backup).exists():
                # Cerca ultimo backup disponibile
                backups = sorted(
                    [b for b in self.backup_dir.iterdir() if b.is_dir()],
                    key=lambda x: x.stat().st_mtime,
                    reverse=True
                )

                if not backups:
                    logger.error("No backups found for rollback")
                    return False

                last_backup = backups[0]

            logger.info(f"Rolling back from: {last_backup}")

            # Elimina src/ corrente
            if self.src_dir.exists():
                shutil.rmtree(self.src_dir)

            # Ripristina backup
            shutil.copytree(last_backup, self.src_dir)

            logger.info("✓ Rollback completed successfully")
            logger.warning("=" * 70)

            return True

        except Exception as e:
            logger.error(f"Rollback failed: {e}", exc_info=True)
            return False

    def _load_state(self) -> dict:
        """Carica stato ultimo update"""
        if not self.state_file.exists():
            return {}

        try:
            with open(self.state_file, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading state: {e}")
            return {}

    def _save_state(self, state: dict):
        """Salva stato update"""
        try:
            with open(self.state_file, "w") as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving state: {e}")

    def get_update_info(self) -> dict:
        """
        Ottieni informazioni sull'ultimo update

        Returns:
            Dictionary con info ultimo update
        """
        state = self._load_state()
        config = self._load_config()

        return {
            "configured": self.is_configured(),
            "repo_url": self.repo_url,
            "branch": self.branch,
            "last_update": state.get("last_update", "Never"),
            "last_commit": state.get("last_commit_hash", "Unknown")[:8],
            "configured_at": config.get("configured_at", "Unknown")
        }


def check_github_updates_silent() -> tuple:
    """
    Funzione helper per controllo silenzioso GitHub all'avvio

    Returns:
        (has_updates: bool, updater: GitHubUpdater, details: dict)
    """
    try:
        updater = GitHubUpdater()

        if not updater.is_configured():
            logger.debug("GitHub updater not configured - skipping check")
            return False, updater, {}

        has_updates, message, details = updater.check_for_updates(silent=True)

        return has_updates, updater, details

    except Exception as e:
        logger.error(f"Error in GitHub update check: {e}")
        return False, None, {}
