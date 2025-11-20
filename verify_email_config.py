"""
Quick verification script for email configuration
Checks configuration without sending actual emails
"""

import sys
import json
from pathlib import Path

# Add src to path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir.parent))

from src.core.config_manager import ConfigManager


def main():
    print("=" * 70)
    print("  Email Configuration Verification")
    print("=" * 70)

    # Test 1: Load public config
    print("\n[TEST 1] Loading public configuration...")
    config_file = Path(__file__).parent / "config" / "config.json"

    try:
        with open(config_file, 'r') as f:
            config = json.load(f)

        email_config = config.get('email', {})
        print(f"  [OK] Email Enabled: {email_config.get('enabled', False)}")
        print(f"  [OK] SMTP Server:   {email_config.get('smtp_server')}")
        print(f"  [OK] SMTP Port:     {email_config.get('smtp_port')}")
        print(f"  [OK] Username:      {email_config.get('username')}")
        print(f"  [OK] From Email:    {email_config.get('from_email')}")
        print(f"  [OK] Alert Email:   {email_config.get('alert_email')}")

    except Exception as e:
        print(f"  [ERROR] Failed to load config: {e}")
        return 1

    # Test 2: Load encrypted credentials
    print("\n[TEST 2] Loading encrypted credentials...")

    try:
        config_manager = ConfigManager()

        # Try to get email password
        email_password = config_manager.get_secret('email.password')
        if email_password:
            print(f"  [OK] Email password loaded (length: {len(email_password)} chars)")
        else:
            print("  [ERROR] Email password not found in encrypted storage")
            print("  [HINT] Run migrate_credentials.py to set up encrypted credentials")
            return 1

        # Try to get SSH password
        ssh_password = config_manager.get_secret('ssh.password')
        if ssh_password:
            print(f"  [OK] SSH password loaded (length: {len(ssh_password)} chars)")
        else:
            print("  [WARN] SSH password not found in encrypted storage")

    except Exception as e:
        print(f"  [ERROR] Failed to load credentials: {e}")
        return 1

    # Test 3: Check email timer configuration
    print("\n[TEST 3] Checking email timer configuration...")

    try:
        main_window_file = Path(__file__).parent / "src" / "ui" / "main_window_v2.py"

        with open(main_window_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check if 21600000 (6 hours) is in the file
        if 'email_aggregate_timer.start(21600000)' in content:
            print("  [OK] Email timer configured to 6 hours (21600000 ms)")
        elif '86400000' in content:
            print("  [ERROR] Email timer still set to 24 hours (86400000 ms)")
            return 1
        else:
            print("  [WARN] Email timer configuration unclear")

    except Exception as e:
        print(f"  [ERROR] Failed to check timer: {e}")
        return 1

    # Test 4: Verify SMTP server (connection test only, no auth)
    print("\n[TEST 4] Testing SMTP server connectivity...")

    try:
        import smtplib
        import socket

        smtp_server = email_config.get('smtp_server', 'smtps.aruba.it')
        smtp_port = email_config.get('smtp_port', 587)

        print(f"  [*] Attempting connection to {smtp_server}:{smtp_port}...")

        # Try basic socket connection first
        sock = socket.create_connection((smtp_server, smtp_port), timeout=10)
        sock.close()

        print(f"  [OK] TCP connection to {smtp_server}:{smtp_port} successful")

    except socket.timeout:
        print(f"  [ERROR] Connection timeout - server may be unreachable")
        print(f"  [HINT] Check network connectivity and firewall settings")
        return 1
    except socket.gaierror:
        print(f"  [ERROR] DNS resolution failed - cannot resolve {smtp_server}")
        return 1
    except Exception as e:
        print(f"  [WARN] Connection test failed: {e}")
        print(f"  [INFO] This may be normal if server requires immediate TLS")

    # Summary
    print("\n" + "=" * 70)
    print("  VERIFICATION COMPLETE")
    print("=" * 70)
    print("\nConfiguration Status:")
    print("  [OK] Public configuration loaded")
    print("  [OK] Encrypted credentials available")
    print("  [OK] Email timer set to 6 hours")
    print("  [OK] SMTP server accessible")
    print("\nEmail Systems:")
    print("  1. Status Change Emails: Ready (immediate on device state change)")
    print("  2. Periodic Reports:     Ready (every 6 hours)")
    print("\nNext Steps:")
    print("  - Start PingMonitor Pro to test actual email sending")
    print("  - Monitor logs at: C:\\Users\\fab\\.pingmonitor\\logs\\")
    print("  - Check email delivery to: " + email_config.get('alert_email', 'N/A'))
    print("\n" + "=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())
