"""
PingMonitor Pro v2.0 - Portable Package Creator
Creates a portable ZIP package for easy distribution
Alternative to Inno Setup installer
"""

import zipfile
import os
import shutil
from pathlib import Path
from datetime import datetime

def create_portable_package():
    """Create portable ZIP package"""

    print("=" * 80)
    print("  PingMonitor Pro v2.0 - Portable Package Creator")
    print("  Creating portable ZIP for easy distribution")
    print("=" * 80)
    print()

    base_dir = Path(__file__).parent
    dist_dir = base_dir / "dist"
    dist_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_filename = f"PingMonitorPro_v2_Portable_{timestamp}.zip"
    zip_path = dist_dir / zip_filename

    print(f"[1/5] Creating ZIP file: {zip_filename}")

    files_to_include = [
        # Main files
        "PingMonitorPro.pyw",
        "START.bat",
        "icon.ico",
        "icon.png",
        "README.md",
        "LICENSE.txt",
        "GUIDA_RAPIDA_NUOVE_FEATURES.txt",
        "NUOVE_FEATURES_IMPLEMENTATE.txt",

        # Folders
        "src",
        "config",
    ]

    total_files = 0

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as zipf:

        print("[2/5] Adding main files...")
        for item in files_to_include:
            item_path = base_dir / item

            if item_path.is_file():
                arcname = f"PingMonitorPro_v2/{item}"
                zipf.write(item_path, arcname)
                print(f"     Added: {item}")
                total_files += 1

            elif item_path.is_dir():
                print(f"[3/5] Adding folder: {item}/")
                for root, dirs, files in os.walk(item_path):
                    # Skip __pycache__ and .pyc files
                    dirs[:] = [d for d in dirs if d != '__pycache__']

                    for file in files:
                        if file.endswith('.pyc'):
                            continue

                        file_path = Path(root) / file
                        arcname = f"PingMonitorPro_v2/{file_path.relative_to(base_dir)}"
                        zipf.write(file_path, arcname)
                        total_files += 1
                print(f"     Added: {item}/ ({total_files} files total)")

        # Add installer README
        print("[4/5] Creating installation instructions...")
        readme_content = """
================================================================================
    PingMonitor Pro v2.0 - Portable Installation
    by Fabrizio Cerchia
================================================================================

SYSTEM REQUIREMENTS:
--------------------
- Windows 7 or later (Windows 10/11 recommended)
- Python 3.8 or later (https://www.python.org/downloads/)
- 100 MB free disk space
- Internet connection for initial setup

INSTALLATION STEPS:
-------------------

1. INSTALL PYTHON (if not already installed):
   - Download Python from: https://www.python.org/downloads/
   - IMPORTANT: Check "Add Python to PATH" during installation!
   - Recommended version: Python 3.10 or later

2. EXTRACT THIS ZIP:
   - Extract all files to a folder of your choice
   - Example: C:\\PingMonitorPro_v2\\

3. INSTALL DEPENDENCIES:
   - Open Command Prompt (CMD) as Administrator
   - Navigate to the extracted folder
   - Run: python -m pip install --upgrade pip
   - Run: python -m pip install PyQt6 requests paramiko cryptography SQLAlchemy loguru rich Pillow icmplib

4. LAUNCH THE APPLICATION:
   - Double-click: START.bat
   - Or double-click: PingMonitorPro.pyw

FIRST TIME SETUP:
-----------------
1. On first launch, the app will auto-import devices from config/config.json
2. Click "▶ Start Monitoring" to begin
3. Use "📧 Email Test" tab to verify email alerts work
4. Right-click any device for quick actions

FEATURES:
---------
✅ Real-time network monitoring (Ping, HTTP, HTTPS, SSH, DNS)
✅ Intelligent email alerts (only when manual intervention needed)
✅ Auto-recovery via SSH (automatic reboot on failures)
✅ Integrated SSH terminal
✅ Email alert testing
✅ Context menu on devices (right-click)
✅ Professional logging and statistics
✅ Secure credential storage (AES-256)

TROUBLESHOOTING:
----------------
Q: Console window appears behind the app?
A: Make sure to use START.bat or PingMonitorPro.pyw (not main.py)

Q: Email alerts not working?
A: Use the "📧 Email Test" tab to verify your configuration

Q: CMD windows keep appearing?
A: Fixed in v2.0! Make sure you're using the latest version

Q: Can't import devices?
A: Check that config/config.json exists and is valid JSON

DOCUMENTATION:
--------------
- Quick Guide: GUIDA_RAPIDA_NUOVE_FEATURES.txt
- Technical Details: NUOVE_FEATURES_IMPLEMENTATE.txt
- Full README: README.md

SUPPORT:
--------
For issues or questions, check the documentation files included.

================================================================================
Enjoy monitoring your network! 🚀
================================================================================
"""
        zipf.writestr("PingMonitorPro_v2/INSTALLATION.txt", readme_content)
        print("     Created: INSTALLATION.txt")

    print("[5/5] Package creation complete!")
    print()
    print("=" * 80)
    print("  SUCCESS! Portable package created")
    print("=" * 80)
    print()
    print(f"  📦 Package: {zip_path}")
    print(f"  📊 Total files: {total_files}")
    print(f"  💾 Size: {zip_path.stat().st_size / 1024 / 1024:.2f} MB")
    print()
    print("  This portable package can be distributed and extracted on any")
    print("  Windows computer with Python 3.8+ installed.")
    print()
    print("=" * 80)
    print()

    # Offer to open folder
    import webbrowser
    choice = input("Open dist folder? (y/n): ")
    if choice.lower() == 'y':
        webbrowser.open(str(dist_dir))

if __name__ == '__main__':
    try:
        create_portable_package()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

    input("\nPress Enter to exit...")
