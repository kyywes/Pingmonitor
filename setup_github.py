"""
Setup GitHub Auto-Update
Script per configurare il repository GitHub per auto-update
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from utils.github_updater import GitHubUpdater
import logging

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)


def main():
    """Setup GitHub configuration"""
    print("=" * 70)
    print("PingMonitor Pro - GitHub Auto-Update Setup")
    print("=" * 70)
    print()

    print("Questo script configura l'auto-update da GitHub.")
    print("L'app controllerà automaticamente il tuo repository ad ogni avvio.")
    print()

    # Input repository URL
    print("1. Inserisci l'URL del repository GitHub")
    print("   Esempio: https://github.com/tuousername/PingMonitorPro.git")
    print()
    repo_url = input("Repository URL: ").strip()

    if not repo_url:
        print("\n[ERROR] Repository URL è obbligatorio!")
        sys.exit(1)

    # Input branch
    print()
    print("2. Inserisci il branch da monitorare (default: main)")
    branch = input("Branch [main]: ").strip() or "main"

    # Input token (opzionale)
    print()
    print("3. Personal Access Token (opzionale - solo per repository privati)")
    print("   Lascia vuoto se il repository è pubblico")
    print("   Per generare token: https://github.com/settings/tokens")
    print("   Permessi richiesti: repo (Full control of private repositories)")
    print()
    token = input("Token (opzionale): ").strip()

    # Conferma
    print()
    print("=" * 70)
    print("Configurazione:")
    print(f"  Repository: {repo_url}")
    print(f"  Branch:     {branch}")
    print(f"  Token:      {'***' + token[-4:] if token else 'Non configurato (repo pubblico)'}")
    print("=" * 70)
    print()

    confirm = input("Confermi configurazione? [s/N]: ").strip().lower()

    if confirm != 's':
        print("\n[CANCELLED] Configurazione annullata")
        sys.exit(0)

    # Configura updater
    print()
    print("Configurazione in corso...")

    try:
        updater = GitHubUpdater()
        updater.configure(repo_url=repo_url, branch=branch, token=token if token else None)

        print()
        print("=" * 70)
        print("✅ CONFIGURAZIONE COMPLETATA!")
        print("=" * 70)
        print()
        print("Il sistema GitHub Auto-Update è ora attivo.")
        print()
        print("Cosa succede ora:")
        print("  1. Ad ogni avvio, PingMonitor controlla il repository")
        print("  2. Se trova nuovi commit, scarica le modifiche")
        print("  3. Chiede conferma prima di applicare gli update")
        print("  4. Crea backup automatici prima di ogni update")
        print("  5. Permette rollback in caso di problemi")
        print()
        print("File di configurazione:")
        print(f"  {updater.config_file}")
        print()
        print("Per disabilitare, elimina il file di configurazione.")
        print("=" * 70)

        # Test connessione
        print()
        test = input("Vuoi testare la connessione al repository? [s/N]: ").strip().lower()

        if test == 's':
            print()
            print("Testing connessione...")
            has_updates, message, details = updater.check_for_updates(silent=False)

            print()
            if has_updates:
                print(f"✅ Connessione OK! Trovati aggiornamenti: {message}")
            else:
                print(f"✅ Connessione OK! {message}")

    except Exception as e:
        print()
        print(f"[ERROR] Configurazione fallita: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[CANCELLED] Configurazione interrotta dall'utente")
        sys.exit(1)
