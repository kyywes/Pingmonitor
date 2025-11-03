"""
Setup GitHub Automatico
Script completo che configura GitHub usando credenziali GitHub Desktop
"""

import sys
import subprocess
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from utils.github_updater import GitHubUpdater
import logging

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)


def run_command(cmd, cwd=None, check=True):
    """Esegue comando e ritorna output"""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=check,
            shell=True
        )
        return True, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return False, e.stdout if hasattr(e, 'stdout') else "", e.stderr if hasattr(e, 'stderr') else str(e)
    except Exception as e:
        return False, "", str(e)


def check_git_installed():
    """Verifica se Git è installato"""
    success, stdout, stderr = run_command("git --version", check=False)
    return success


def is_git_repo():
    """Verifica se la directory corrente è già un repo git"""
    return Path(".git").exists()


def create_gitignore():
    """Crea file .gitignore ottimale"""
    gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
ENV/
env/

# PyInstaller
*.manifest
*.spec

# Installer logs
pip-log.txt
pip-delete-this-directory.txt

# Unit test / coverage
htmlcov/
.tox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db
desktop.ini

# PingMonitor specific
*.db
*.sqlite
*.sqlite3
logs/
data/
temp/
*.log

# Secrets
secrets.enc
.key
*.pem
*.p12

# Config locale (ma tieni template)
config/config.json

# Backup
backups/
*.bak

# Temp GitHub
github_temp/
"""

    gitignore_path = Path(".gitignore")

    if gitignore_path.exists():
        print("[INFO] .gitignore già esistente, lo aggiorno...")

    with open(gitignore_path, "w") as f:
        f.write(gitignore_content)

    print("[OK] .gitignore creato/aggiornato")


def main():
    """Setup automatico completo"""
    print("=" * 70)
    print("PingMonitor Pro - Setup GitHub Automatico")
    print("=" * 70)
    print()

    # Verifica Git installato
    if not check_git_installed():
        print("[ERROR] Git non installato!")
        print()
        print("Installa GitHub Desktop da: https://desktop.github.com/")
        print("Oppure Git da: https://git-scm.com/download/win")
        return 1

    print("[OK] Git installato")
    print()

    # Input repository URL
    print("Hai già creato il repository su GitHub?")
    print()
    print("Se NO:")
    print("  1. Vai su https://github.com/new")
    print("  2. Nome: PingMonitorPro")
    print("  3. Pubblico o Privato")
    print("  4. Click 'Create repository'")
    print("  5. Copia l'URL che ti mostra")
    print()
    print("Se SÌ:")
    print("  Inserisci l'URL del repository")
    print()

    repo_url = input("Repository URL: ").strip()

    if not repo_url:
        print("[ERROR] URL obbligatorio!")
        return 1

    # Estrai username e repo name dall'URL
    try:
        # https://github.com/username/repo.git
        parts = repo_url.replace(".git", "").split("/")
        username = parts[-2]
        repo_name = parts[-1]
        print(f"[OK] Repository: {username}/{repo_name}")
    except:
        print("[WARNING] Non riesco a estrarre username/repo dall'URL")

    print()
    print("=" * 70)
    print("Configurazione:")
    print(f"  Repository: {repo_url}")
    print(f"  Branch:     main")
    print("=" * 70)
    print()

    confirm = input("Procedo con il setup automatico? [s/N]: ").strip().lower()

    if confirm != 's':
        print("[CANCELLED] Setup annullato")
        return 0

    print()
    print("=" * 70)
    print("SETUP IN CORSO...")
    print("=" * 70)
    print()

    # Step 1: Crea .gitignore
    print("[1/8] Creazione .gitignore...")
    try:
        create_gitignore()
    except Exception as e:
        print(f"[ERROR] Fallito: {e}")
        return 1

    # Step 2: Inizializza git (se non già fatto)
    print("[2/8] Inizializzazione repository Git...")
    if is_git_repo():
        print("[INFO] Repository Git già inizializzato")
    else:
        success, stdout, stderr = run_command("git init")
        if not success:
            print(f"[ERROR] git init fallito: {stderr}")
            return 1
        print("[OK] git init completato")

    # Step 3: Configura branch main
    print("[3/8] Configurazione branch main...")
    run_command("git branch -M main", check=False)
    print("[OK] Branch configurato")

    # Step 4: Aggiungi remote (se non esiste)
    print("[4/8] Configurazione remote GitHub...")
    success, stdout, stderr = run_command("git remote get-url origin", check=False)

    if success:
        print("[INFO] Remote 'origin' già configurato")
        # Aggiorna URL se diverso
        run_command(f'git remote set-url origin "{repo_url}"')
        print("[OK] URL remote aggiornato")
    else:
        success, stdout, stderr = run_command(f'git remote add origin "{repo_url}"')
        if not success:
            print(f"[ERROR] Aggiunta remote fallita: {stderr}")
            return 1
        print("[OK] Remote aggiunto")

    # Step 5: Aggiungi file
    print("[5/8] Aggiunta file al repository...")

    # Aggiungi file specifici
    files_to_add = [
        "src/",
        "requirements.txt",
        "README.md",
        ".gitignore",
        "icon.ico",
        "icon.png",
        "setup_github.py",
        "setup_github_auto.py",
        "SETUP_GITHUB.bat",
        "SETUP_GITHUB_AUTO.bat",
        "START_PINGMONITOR.bat",
        "START_DIRECT.bat",
        "smart_launcher.py",
        "GITHUB_AUTO_UPDATE_README.md",
        "QUICK_START_GITHUB.md",
        "AUTO_PATCH_README.md"
    ]

    for file in files_to_add:
        if Path(file).exists():
            success, stdout, stderr = run_command(f'git add "{file}"', check=False)
            if success:
                print(f"  [OK] Aggiunto: {file}")
            else:
                print(f"  [SKIP] Non trovato: {file}")

    print("[OK] File aggiunti")

    # Step 6: Commit
    print("[6/8] Creazione commit iniziale...")

    # Verifica se ci sono cambiamenti da committare
    success, stdout, stderr = run_command("git status --porcelain")

    if stdout.strip():
        commit_message = "Initial commit - PingMonitor Pro v2.3 with GitHub Auto-Update"
        success, stdout, stderr = run_command(f'git commit -m "{commit_message}"')

        if not success:
            print(f"[ERROR] Commit fallito: {stderr}")
            return 1

        print("[OK] Commit creato")
    else:
        print("[INFO] Nessun cambiamento da committare")

    # Step 7: Push
    print("[7/8] Push su GitHub...")
    print("[INFO] Questo userà le credenziali di GitHub Desktop")
    print()

    success, stdout, stderr = run_command("git push -u origin main")

    if not success:
        print(f"[ERROR] Push fallito: {stderr}")
        print()
        print("Possibili cause:")
        print("  1. GitHub Desktop non è loggato")
        print("  2. Repository non esiste su GitHub")
        print("  3. Non hai permessi sul repository")
        print()
        print("Soluzioni:")
        print("  1. Apri GitHub Desktop e fai login")
        print("  2. Crea il repository su https://github.com/new")
        print("  3. Verifica i permessi")
        return 1

    print("[OK] Push completato!")
    print()

    # Step 8: Configura auto-update
    print("[8/8] Configurazione auto-update...")

    try:
        updater = GitHubUpdater()
        updater.configure(repo_url=repo_url, branch="main", token=None)
        print("[OK] Auto-update configurato")
    except Exception as e:
        print(f"[ERROR] Configurazione auto-update fallita: {e}")
        return 1

    print()
    print("=" * 70)
    print("✅ SETUP COMPLETATO CON SUCCESSO!")
    print("=" * 70)
    print()
    print("Cosa è stato fatto:")
    print("  ✓ Repository Git inizializzato")
    print("  ✓ .gitignore creato")
    print("  ✓ File aggiunti al repository")
    print("  ✓ Commit iniziale creato")
    print(f"  ✓ Push su {repo_url}")
    print("  ✓ Auto-update configurato")
    print()
    print("Il tuo codice è ora su GitHub!")
    print(f"  URL: {repo_url.replace('.git', '')}")
    print()
    print("Prossimi passi:")
    print("  1. Quando modifichi il codice:")
    print("     git add src/")
    print('     git commit -m "Descrizione modifiche"')
    print("     git push")
    print()
    print("  2. Su altri PC:")
    print("     - Installa PingMonitor")
    print("     - Esegui SETUP_GITHUB.bat")
    print("     - Inserisci stesso repository URL")
    print("     - L'app si aggiornerà automaticamente!")
    print()
    print("=" * 70)

    # Test connessione
    print()
    test = input("Vuoi testare che il sistema funzioni? [s/N]: ").strip().lower()

    if test == 's':
        print()
        print("Test connessione GitHub...")

        try:
            has_updates, message, details = updater.check_for_updates(silent=False)
            print()
            print(f"[OK] Connessione funzionante!")
            print(f"[INFO] {message}")
        except Exception as e:
            print(f"[ERROR] Test fallito: {e}")
            return 1

    return 0


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n[CANCELLED] Setup interrotto")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Errore critico: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
