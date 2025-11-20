"""
Verification script to check timer in running application
This will start the app and verify the email timer is correctly configured
"""

import sys
from pathlib import Path
import logging

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

# Setup logging to see initialization messages
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def verify_app_timer():
    """Start app and verify timer configuration"""
    logger.info("\n" + "=" * 80)
    logger.info("STARTING APPLICATION TO VERIFY EMAIL TIMER")
    logger.info("=" * 80 + "\n")

    try:
        # Import after setting up logging
        from models.base import db_manager
        from config.config_manager import ConfigManager
        from services.monitoring_engine import MonitoringEngine
        from ui.main_window_v2 import MainWindowV2

        # Initialize database
        db_manager.init_db()
        logger.info("✓ Database initialized")

        # Load config
        config = ConfigManager()
        logger.info("✓ Config loaded")

        # Create monitoring engine
        monitoring_engine = MonitoringEngine(config)
        logger.info("✓ Monitoring engine created")

        # Create Qt application
        app = QApplication(sys.argv)
        logger.info("✓ Qt application created")

        # Create main window (this initializes the email timer)
        logger.info("\nCreating main window (watch for timer initialization logs)...\n")
        main_window = MainWindowV2(config, monitoring_engine)
        logger.info("\n✓ Main window created")

        # Verify timer
        logger.info("\n" + "=" * 80)
        logger.info("TIMER VERIFICATION")
        logger.info("=" * 80)

        if hasattr(main_window, 'email_aggregate_timer'):
            timer = main_window.email_aggregate_timer
            logger.info(f"✓ Timer exists: {timer is not None}")
            logger.info(f"✓ Timer interval: {timer.interval()} ms")
            logger.info(f"✓ Timer active: {timer.isActive()}")

            expected_interval = 21600000  # 6 hours
            if timer.interval() == expected_interval:
                logger.info(f"✓ Timer interval CORRECT: {expected_interval} ms (6 hours)")
            else:
                logger.error(f"✗ Timer interval INCORRECT!")
                logger.error(f"  Expected: {expected_interval} ms (6 hours)")
                logger.error(f"  Actual: {timer.interval()} ms ({timer.interval() / 3600000} hours)")
                return False

            # Calculate next trigger
            hours = timer.interval() / 1000 / 60 / 60
            logger.info(f"✓ Next email report in: {hours} hours")

        else:
            logger.error("✗ Timer NOT found in main window!")
            return False

        # Verify email config
        logger.info("\n" + "=" * 80)
        logger.info("EMAIL CONFIGURATION")
        logger.info("=" * 80)

        if hasattr(main_window, 'email_config'):
            config_exists = main_window.email_config is not None
            logger.info(f"Email config exists: {config_exists}")

            if config_exists and main_window.email_config.get('smtp_server'):
                logger.info(f"✓ SMTP Server: {main_window.email_config.get('smtp_server')}")
                logger.info(f"✓ SMTP Port: {main_window.email_config.get('smtp_port')}")
                logger.info(f"✓ Username: {main_window.email_config.get('username')}")
            else:
                logger.warning("⚠ Email config empty - emails will be disabled")

        # Verify aggregated email service
        if hasattr(main_window, 'aggregated_email_service'):
            service = main_window.aggregated_email_service
            logger.info(f"✓ Aggregated email service exists: {service is not None}")

            recipients = service._get_recipients()
            logger.info(f"✓ Email recipients: {recipients}")

        logger.info("\n" + "=" * 80)
        logger.info("✓ VERIFICATION COMPLETE - TIMER CORRECTLY CONFIGURED")
        logger.info("=" * 80 + "\n")

        logger.info("The application is ready. The timer will:")
        logger.info("  1. Send email reports every 6 hours (21,600,000 ms)")
        logger.info("  2. Include all device statuses (online, offline, degraded)")
        logger.info("  3. Include recovery successes and failures")
        logger.info("")
        logger.info("To test immediately, use the 'Check Now' button in the app.")
        logger.info("\nClosing application...")

        return True

    except Exception as e:
        logger.error(f"\n✗ VERIFICATION FAILED: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = verify_app_timer()
    sys.exit(0 if success else 1)
