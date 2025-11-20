"""
Database migration script to add ping_status and web_status columns
This fixes the "Ultimo Check" timestamp issue by adding necessary columns
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.models.base import db_manager
import sqlite3

def migrate():
    """Add ping_status and web_status columns to devices table"""
    print("\n" + "="*80)
    print("DATABASE MIGRATION: Adding ping_status and web_status columns")
    print("="*80)

    # Initialize database
    print("\nInitializing database...")
    db_manager.initialize()
    print("[OK] Database initialized")

    # Get database path (from user home directory)
    db_path = Path.home() / ".pingmonitor" / "pingmonitor.db"

    if not db_path.exists():
        print(f"\n[ERROR] Database not found at: {db_path}")
        print("The application has not been run yet, or database is in a different location.")
        return False

    print(f"\nDatabase location: {db_path}")

    # Connect to database
    print("\nConnecting to database...")
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    print("[OK] Connected")

    try:
        # Check if columns already exist
        print("\nChecking for existing columns...")
        cursor.execute("PRAGMA table_info(devices)")
        columns = [row[1] for row in cursor.fetchall()]

        has_ping_status = 'ping_status' in columns
        has_web_status = 'web_status' in columns

        print(f"  ping_status exists: {has_ping_status}")
        print(f"  web_status exists: {has_web_status}")

        # Add ping_status column if it doesn't exist
        if not has_ping_status:
            print("\nAdding ping_status column...")
            cursor.execute("""
                ALTER TABLE devices
                ADD COLUMN ping_status VARCHAR(20)
            """)
            print("[OK] ping_status column added")
        else:
            print("\n[SKIP] ping_status column already exists")

        # Add web_status column if it doesn't exist
        if not has_web_status:
            print("\nAdding web_status column...")
            cursor.execute("""
                ALTER TABLE devices
                ADD COLUMN web_status VARCHAR(20)
            """)
            print("[OK] web_status column added")
        else:
            print("\n[SKIP] web_status column already exists")

        # Commit changes
        conn.commit()
        print("\n[OK] Migration committed successfully")

        # Verify columns were added
        print("\nVerifying migration...")
        cursor.execute("PRAGMA table_info(devices)")
        columns = [row[1] for row in cursor.fetchall()]

        ping_exists = 'ping_status' in columns
        web_exists = 'web_status' in columns

        if ping_exists and web_exists:
            print("[OK] Both columns verified in database schema")
            print("\n" + "="*80)
            print("MIGRATION SUCCESSFUL")
            print("="*80)
            return True
        else:
            print("[ERROR] Column verification failed")
            print(f"  ping_status: {ping_exists}")
            print(f"  web_status: {web_exists}")
            return False

    except sqlite3.Error as e:
        print(f"\n[ERROR] Migration failed: {e}")
        conn.rollback()
        return False

    finally:
        cursor.close()
        conn.close()
        print("\nDatabase connection closed")


if __name__ == "__main__":
    success = migrate()
    if success:
        print("\nYou can now run PingMonitor Pro with the fixed timestamp feature!")
        sys.exit(0)
    else:
        print("\nMigration failed. Please check the error messages above.")
        sys.exit(1)
