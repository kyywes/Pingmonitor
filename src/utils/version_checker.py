"""
Version Checker - Auto-patching System
Controlla modifiche al codice sorgente e applica patch automaticamente
"""

import hashlib
import json
import os
from pathlib import Path
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class VersionChecker:
    """
    Sistema di versioning che controlla modifiche ai file sorgente
    """

    def __init__(self, src_dir=None):
        """
        Inizializza il version checker

        Args:
            src_dir: Directory sorgente da monitorare (default: src/)
        """
        if src_dir is None:
            # Ottieni la directory src/
            self.src_dir = Path(__file__).parent.parent
        else:
            self.src_dir = Path(src_dir)

        # File dove salvare gli hash
        self.version_file = Path.home() / ".pingmonitor" / "version.json"
        self.version_file.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Version checker initialized for: {self.src_dir}")

    def calculate_file_hash(self, file_path: Path) -> str:
        """
        Calcola hash MD5 di un file

        Args:
            file_path: Path al file

        Returns:
            Hash MD5 del file
        """
        md5_hash = hashlib.md5()

        try:
            with open(file_path, "rb") as f:
                # Leggi file a blocchi per efficienza
                for chunk in iter(lambda: f.read(4096), b""):
                    md5_hash.update(chunk)
            return md5_hash.hexdigest()
        except Exception as e:
            logger.error(f"Error calculating hash for {file_path}: {e}")
            return ""

    def scan_source_files(self) -> dict:
        """
        Scansiona tutti i file .py nella directory src/ e calcola gli hash

        Returns:
            Dictionary con {file_path_relativo: hash_md5}
        """
        file_hashes = {}

        # Scansiona ricorsivamente tutti i file .py
        for py_file in self.src_dir.rglob("*.py"):
            # Ignora __pycache__ e file temporanei
            if "__pycache__" in str(py_file) or py_file.name.startswith("."):
                continue

            # Path relativo alla src/
            relative_path = py_file.relative_to(self.src_dir)

            # Calcola hash
            file_hash = self.calculate_file_hash(py_file)

            if file_hash:
                file_hashes[str(relative_path)] = file_hash

        logger.info(f"Scanned {len(file_hashes)} Python files")
        return file_hashes

    def load_saved_version(self) -> dict:
        """
        Carica la versione salvata dal file version.json

        Returns:
            Dictionary con info versione precedente
        """
        if not self.version_file.exists():
            logger.info("No saved version found (first run)")
            return {}

        try:
            with open(self.version_file, "r") as f:
                data = json.load(f)
            logger.info(f"Loaded saved version from {data.get('timestamp', 'unknown')}")
            return data
        except Exception as e:
            logger.error(f"Error loading saved version: {e}")
            return {}

    def save_current_version(self, file_hashes: dict):
        """
        Salva la versione corrente nel file version.json

        Args:
            file_hashes: Dictionary degli hash dei file
        """
        version_data = {
            "timestamp": datetime.now().isoformat(),
            "file_count": len(file_hashes),
            "file_hashes": file_hashes
        }

        try:
            with open(self.version_file, "w") as f:
                json.dump(version_data, f, indent=2)
            logger.info(f"Saved version snapshot: {len(file_hashes)} files")
        except Exception as e:
            logger.error(f"Error saving version: {e}")

    def check_for_updates(self) -> tuple:
        """
        Controlla se ci sono modifiche rispetto alla versione salvata

        Returns:
            (has_updates: bool, modified_files: list, details: dict)
        """
        logger.info("=" * 70)
        logger.info("AUTO-PATCH: Checking for source code updates...")
        logger.info("=" * 70)

        # Scansiona file correnti
        current_hashes = self.scan_source_files()

        # Carica versione salvata
        saved_version = self.load_saved_version()
        saved_hashes = saved_version.get("file_hashes", {})

        if not saved_hashes:
            # Prima esecuzione - salva versione corrente
            logger.info("First run - saving current version as baseline")
            self.save_current_version(current_hashes)
            return False, [], {"message": "First run - baseline created"}

        # Confronta hash
        modified_files = []
        new_files = []
        deleted_files = []

        # File modificati o nuovi
        for file_path, current_hash in current_hashes.items():
            saved_hash = saved_hashes.get(file_path)

            if saved_hash is None:
                new_files.append(file_path)
                logger.info(f"  [NEW] {file_path}")
            elif saved_hash != current_hash:
                modified_files.append(file_path)
                logger.info(f"  [MODIFIED] {file_path}")

        # File eliminati
        for file_path in saved_hashes.keys():
            if file_path not in current_hashes:
                deleted_files.append(file_path)
                logger.info(f"  [DELETED] {file_path}")

        has_updates = bool(modified_files or new_files or deleted_files)

        details = {
            "modified": modified_files,
            "new": new_files,
            "deleted": deleted_files,
            "total_changes": len(modified_files) + len(new_files) + len(deleted_files)
        }

        if has_updates:
            logger.warning(f"Found {details['total_changes']} changes in source code!")
            logger.warning(f"  - Modified: {len(modified_files)}")
            logger.warning(f"  - New: {len(new_files)}")
            logger.warning(f"  - Deleted: {len(deleted_files)}")

            # Salva nuova versione
            self.save_current_version(current_hashes)
        else:
            logger.info("No source code changes detected")

        logger.info("=" * 70)

        return has_updates, modified_files + new_files, details

    def get_version_info(self) -> dict:
        """
        Ottieni informazioni sulla versione corrente

        Returns:
            Dictionary con info versione
        """
        saved_version = self.load_saved_version()

        return {
            "last_update": saved_version.get("timestamp", "Never"),
            "file_count": saved_version.get("file_count", 0),
            "src_directory": str(self.src_dir)
        }


def check_and_notify_updates() -> bool:
    """
    Funzione helper per controllare aggiornamenti e notificare utente

    Returns:
        True se ci sono aggiornamenti, False altrimenti
    """
    try:
        checker = VersionChecker()
        has_updates, modified_files, details = checker.check_for_updates()

        if has_updates:
            logger.warning("🔄 AUTO-PATCH DETECTED!")
            logger.warning(f"🔄 {details['total_changes']} files have been modified")
            logger.warning("🔄 Changes will be applied automatically")
            return True

        return False

    except Exception as e:
        logger.error(f"Error checking for updates: {e}")
        return False
