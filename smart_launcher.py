"""
Smart Launcher - Auto-Patching System
Launcher intelligente che rileva modifiche e applica patch automaticamente
"""

import sys
import os
from pathlib import Path
import subprocess
import logging

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


def is_frozen():
    """
    Controlla se l'applicazione è eseguita da un .exe compilato

    Returns:
        True se frozen (exe), False se codice sorgente
    """
    return getattr(sys, 'frozen', False)


def get_base_dir():
    """
    Ottieni la directory base dell'applicazione

    Returns:
        Path alla directory base
    """
    if is_frozen():
        # Se frozen, usa la directory dell'exe
        return Path(sys.executable).parent
    else:
        # Se non frozen, usa la directory dello script
        return Path(__file__).parent


def check_source_exists():
    """
    Controlla se esiste il codice sorgente nella directory src/

    Returns:
        True se src/ esiste, False altrimenti
    """
    base_dir = get_base_dir()
    src_dir = base_dir / "src"

    if src_dir.exists() and (src_dir / "main.py").exists():
        logger.info(f"✓ Source code found at: {src_dir}")
        return True
    else:
        logger.warning(f"✗ Source code not found at: {src_dir}")
        return False


def check_for_updates():
    """
    Controlla se ci sono modifiche al codice sorgente

    Returns:
        True se ci sono modifiche, False altrimenti
    """
    try:
        # Importa il version checker
        sys.path.insert(0, str(get_base_dir() / "src"))
        from utils.version_checker import check_and_notify_updates

        has_updates = check_and_notify_updates()
        return has_updates

    except Exception as e:
        logger.error(f"Error checking for updates: {e}")
        return False


def launch_from_source():
    """
    Lancia l'applicazione dal codice sorgente Python
    """
    logger.info("=" * 70)
    logger.info("🔄 LAUNCHING FROM SOURCE CODE (AUTO-PATCH MODE)")
    logger.info("=" * 70)

    base_dir = get_base_dir()
    main_py = base_dir / "src" / "main.py"

    # Trova Python
    python_exe = None

    # Prova venv locale
    venv_python = base_dir / "venv" / "Scripts" / "python.exe"
    if venv_python.exists():
        python_exe = venv_python
        logger.info(f"Using venv Python: {python_exe}")
    else:
        # Usa Python di sistema
        python_exe = sys.executable
        logger.info(f"Using system Python: {python_exe}")

    # Lancia l'applicazione
    try:
        logger.info(f"Launching: {python_exe} {main_py}")
        subprocess.run([str(python_exe), str(main_py)], check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to launch application: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Application closed by user")
        sys.exit(0)


def launch_from_exe():
    """
    Lancia l'applicazione dall'exe compilato
    """
    logger.info("=" * 70)
    logger.info("🚀 LAUNCHING FROM COMPILED EXE")
    logger.info("=" * 70)

    base_dir = get_base_dir()
    exe_path = base_dir / "PingMonitorPro.exe"

    if not exe_path.exists():
        logger.error(f"Exe not found: {exe_path}")
        logger.error("Falling back to source code...")
        launch_from_source()
        return

    try:
        logger.info(f"Launching: {exe_path}")
        subprocess.run([str(exe_path)], check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to launch exe: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Application closed by user")
        sys.exit(0)


def main():
    """
    Main launcher logic
    """
    print("=" * 70)
    print("PingMonitor Pro v2.3 - Smart Launcher with Auto-Patching")
    print("=" * 70)
    print()

    # Controlla se siamo già in modalità codice sorgente
    if not is_frozen():
        logger.info("Already running from source code")
        # Importa e esegui main direttamente
        sys.path.insert(0, str(get_base_dir() / "src"))
        from main import main as app_main
        app_main()
        return

    # Se frozen (exe), controlla aggiornamenti
    logger.info("Running from compiled exe - checking for updates...")

    # Controlla se esiste il codice sorgente
    if not check_source_exists():
        logger.warning("Source code not found - using compiled exe")
        launch_from_exe()
        return

    # Controlla aggiornamenti
    has_updates = check_for_updates()

    if has_updates:
        logger.warning("=" * 70)
        logger.warning("📦 UPDATES DETECTED - APPLYING PATCH")
        logger.warning("=" * 70)
        logger.warning("")
        logger.warning("Il codice sorgente è stato modificato.")
        logger.warning("Avvio in modalità AUTO-PATCH dal codice Python...")
        logger.warning("")
        logger.warning("Questo garantisce che le modifiche vengano applicate immediatamente.")
        logger.warning("")
        input("Premi INVIO per continuare...")
        launch_from_source()
    else:
        logger.info("No updates found - using compiled exe for better performance")
        launch_from_exe()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nApplication closed by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Critical error in launcher: {e}", exc_info=True)
        input("\nPress ENTER to exit...")
        sys.exit(1)
