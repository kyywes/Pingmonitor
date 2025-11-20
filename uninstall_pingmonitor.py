"""
PingMonitor Pro - Uninstaller Script
Safely removes PingMonitor Pro installation and user data
"""

import os
import sys
import shutil
from pathlib import Path
import ctypes


def is_admin():
    """Check if script is running with admin privileges"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def banner(text):
    """Print banner"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def get_installation_paths():
    """Get all installation paths"""
    paths = {
        'user_data': Path.home() / ".pingmonitor",
        'desktop_setup': Path.home() / "Desktop" / "PingMonitorPro_Setup.exe",
        'desktop_shortcut': Path.home() / "Desktop" / "PingMonitor Pro.lnk",
    }

    return paths


def check_running_process():
    """Check if PingMonitor is currently running"""
    try:
        import psutil

        for proc in psutil.process_iter(['name']):
            if 'pingmonitor' in proc.info['name'].lower():
                return True, proc.info['name']

        return False, None

    except ImportError:
        print("  [WARN] psutil not available, cannot check running processes")
        print("  [INFO] Please manually ensure PingMonitor is not running")
        return False, None
    except Exception as e:
        print(f"  [WARN] Error checking processes: {e}")
        return False, None


def remove_path(path, path_type="file"):
    """Remove file or directory"""
    try:
        if not path.exists():
            print(f"  [SKIP] {path_type} not found: {path}")
            return True

        if path.is_file():
            path.unlink()
            print(f"  [OK] Removed {path_type}: {path}")
        elif path.is_dir():
            shutil.rmtree(path)
            print(f"  [OK] Removed {path_type}: {path}")

        return True

    except PermissionError:
        print(f"  [ERROR] Permission denied: {path}")
        print(f"  [HINT] Close PingMonitor and try again as administrator")
        return False
    except Exception as e:
        print(f"  [ERROR] Failed to remove {path}: {e}")
        return False


def backup_user_data(data_dir):
    """Backup user data before removal"""
    try:
        if not data_dir.exists():
            print("  [SKIP] No user data to backup")
            return True

        backup_dir = data_dir.parent / f"pingmonitor_backup_{Path(data_dir).name}"
        counter = 1

        while backup_dir.exists():
            backup_dir = data_dir.parent / f"pingmonitor_backup_{counter}"
            counter += 1

        shutil.copytree(data_dir, backup_dir)
        print(f"  [OK] Backup created: {backup_dir}")
        return True

    except Exception as e:
        print(f"  [ERROR] Backup failed: {e}")
        return False


def main():
    """Main uninstaller"""
    banner("PingMonitor Pro - Uninstaller")

    # Check if running as admin
    if not is_admin():
        print("\n[WARN] Not running as administrator")
        print("[INFO] Some files may not be removable without admin privileges")
        input("\nPress Enter to continue anyway, or Ctrl+C to cancel...")

    # Check if PingMonitor is running
    print("\n[1/6] Checking if PingMonitor is running...")
    is_running, process_name = check_running_process()

    if is_running:
        print(f"  [ERROR] PingMonitor is currently running ({process_name})")
        print(f"  [HINT] Please close PingMonitor and try again")
        input("\nPress Enter to exit...")
        return 1

    print("  [OK] PingMonitor is not running")

    # Get installation paths
    print("\n[2/6] Detecting installation paths...")
    paths = get_installation_paths()

    for name, path in paths.items():
        if path.exists():
            print(f"  [FOUND] {name}: {path}")
        else:
            print(f"  [NOT FOUND] {name}: {path}")

    # Ask user for confirmation
    print("\n" + "=" * 70)
    print("  UNINSTALLATION OPTIONS")
    print("=" * 70)
    print("\n1. Complete Removal (removes all data, settings, and databases)")
    print("2. Remove Application Only (keeps user data and settings)")
    print("3. Backup and Remove (creates backup before removal)")
    print("4. Cancel")

    choice = input("\nEnter your choice (1-4): ").strip()

    if choice == "4":
        print("\n[INFO] Uninstallation cancelled")
        return 0

    # Perform uninstallation
    if choice == "3":
        print("\n[3/6] Creating backup...")
        if not backup_user_data(paths['user_data']):
            print("\n[ERROR] Backup failed, uninstallation aborted")
            input("Press Enter to exit...")
            return 1

    if choice in ["1", "3"]:
        # Complete removal
        print("\n[4/6] Removing user data...")
        remove_path(paths['user_data'], "User data directory")

    elif choice == "2":
        # Remove application only (keep user data)
        print("\n[4/6] Keeping user data (application-only removal)")
        print("  [SKIP] User data preserved: " + str(paths['user_data']))

    else:
        print("\n[ERROR] Invalid choice")
        input("Press Enter to exit...")
        return 1

    # Remove desktop items
    print("\n[5/6] Removing desktop items...")
    remove_path(paths['desktop_setup'], "Setup executable")
    remove_path(paths['desktop_shortcut'], "Desktop shortcut")

    # Final cleanup
    print("\n[6/6] Final cleanup...")
    print("  [OK] Uninstallation completed")

    # Summary
    banner("UNINSTALLATION COMPLETE")

    if choice == "3":
        print("\nBackup Location:")
        print(f"  {paths['user_data'].parent / 'pingmonitor_backup_*'}")

    print("\nRemoved Items:")
    if choice in ["1", "3"]:
        print("  - User data and settings")
        print("  - Database and logs")
        print("  - Encrypted credentials")

    print("  - Desktop setup executable")
    print("  - Desktop shortcuts")

    print("\n" + "=" * 70)
    print("\nThank you for using PingMonitor Pro!")
    print("\n" + "=" * 70)

    input("\nPress Enter to exit...")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n[INFO] Uninstallation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Uninstaller failed: {e}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to exit...")
        sys.exit(1)
