"""
PingMonitor Pro v2.0 - Main Application
Professional Network Monitoring Solution
by Fabrizio Cerchia
"""

import sys
import signal
from pathlib import Path

# Add src directory to path
src_dir = Path(__file__).parent
sys.path.insert(0, str(src_dir.parent))

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt, QSharedMemory
from PyQt6.QtGui import QIcon, QPalette, QColor
import ctypes
import platform

from src.core.config_manager import ConfigManager
from src.core.logger import log_manager
from src.core.monitoring_engine import MonitoringEngine
from src.models.base import db_manager
from src.models.check_result import CheckType
from src.services.ping_service import PingService
from src.services.http_service import HTTPService
from src.services.ssh_service import SSHService
from src.services.dns_service import DNSService
from src.ui.main_window_v2 import MainWindowV2 as MainWindow
from src.utils.auto_updater import AutoUpdater
from src.ui.design_system import DesignSystem as DS

import logging

logger = logging.getLogger(__name__)


def set_windows_appid():
    """
    Set Windows AppUserModelID to show correct icon in taskbar
    """
    if platform.system() == 'Windows':
        try:
            # Set AppUserModelID so Windows recognizes this as a separate app
            app_id = 'FabrizioCerchia.PingMonitorPro.v2.3'
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
            logger.info(f"Windows AppUserModelID set: {app_id}")
        except Exception as e:
            logger.warning(f"Failed to set AppUserModelID: {e}")


class PingMonitorApp:
    """Main application class"""

    def __init__(self, qt_app):
        """Initialize application

        Args:
            qt_app: Existing QApplication instance
        """
        # Use existing Qt Application
        self.qt_app = qt_app

        # Set application style
        self.qt_app.setStyle('Fusion')

        # Load professional theme from QSS file
        self._load_professional_theme()

        # Initialize configuration
        self.config = ConfigManager()

        # Setup logging
        log_config = self.config.get('logging', {})
        log_manager.setup_logging(
            log_level=log_config.get('level', 'INFO'),
            max_file_size=log_config.get('max_file_size', 10485760),
            backup_count=log_config.get('backup_count', 5),
            console_output=log_config.get('console_output', True),
            file_output=log_config.get('file_output', True)
        )

        logger.info("="*60)
        logger.info("PingMonitor Pro v2.0 - Starting")
        logger.info("by Fabrizio Cerchia")
        logger.info("="*60)

        # Initialize database
        db_path = self.config.get('database.path')
        db_manager.initialize(f"sqlite:///{db_path}")
        logger.info(f"Database initialized: {db_path}")

        # AUTO-SYNC: Check and update device configuration
        self._auto_sync_updated = False
        try:
            session = db_manager.get_session()
            updated, message = AutoUpdater.auto_sync_on_startup(session)
            session.close()

            self._auto_sync_updated = updated

            if updated:
                logger.info(f"AUTO-SYNC COMPLETED: {message}")
            else:
                logger.info("AUTO-SYNC: No updates needed")
        except Exception as e:
            logger.error(f"AUTO-SYNC FAILED: {e}", exc_info=True)

        # Initialize monitoring engine
        max_workers = self.config.get('monitoring.concurrent_checks', 10)
        self.monitoring_engine = MonitoringEngine(max_workers=max_workers)

        # Register check services
        self._register_check_services()

        # Create main window
        self.main_window = MainWindow(self.config, self.monitoring_engine)

        # Connect auto-recovery service to monitoring engine
        if hasattr(self.main_window, 'auto_recovery_service'):
            self.monitoring_engine.set_auto_recovery_service(self.main_window.auto_recovery_service)
            logger.info("Auto-recovery service connected to monitoring engine")

        # Connect device reboot email service to monitoring engine
        if hasattr(self.main_window, 'email_config'):
            self.monitoring_engine.set_device_reboot_email_service(self.main_window.email_config)
            logger.info("Device reboot email service connected to monitoring engine")

        # Show auto-sync notification if devices were updated
        if hasattr(self, '_auto_sync_updated') and self._auto_sync_updated:
            self.main_window.status_bar.showMessage(
                "✓ Auto-sync completato: configurazione dispositivi aggiornata automaticamente",
                10000  # Show for 10 seconds
            )

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        logger.info("Application initialized successfully")

    def _load_professional_theme(self):
        """Load professional theme from QSS file"""
        try:
            # Load professional QSS theme
            qss_path = Path(__file__).parent / 'ui' / 'styles' / 'professional_theme.qss'

            if qss_path.exists():
                with open(qss_path, 'r', encoding='utf-8') as f:
                    qss_content = f.read()
                    self.qt_app.setStyleSheet(qss_content)
                logger.info(f"Professional theme loaded successfully from {qss_path}")
            else:
                logger.warning(f"Professional theme file not found at {qss_path}")
                logger.warning("Falling back to basic dark theme")
                self._setup_fallback_theme()

        except Exception as e:
            logger.error(f"Error loading professional theme: {e}")
            logger.warning("Falling back to basic dark theme")
            self._setup_fallback_theme()

    def _setup_fallback_theme(self):
        """Fallback dark theme if QSS file cannot be loaded"""
        dark_palette = QPalette()

        # Define colors using Design System
        bg_primary = QColor(DS.COLORS['bg-primary'])
        bg_secondary = QColor(DS.COLORS['bg-secondary'])
        text_primary = QColor(DS.COLORS['text-primary'])
        text_secondary = QColor(DS.COLORS['text-secondary'])
        brand_primary = QColor(DS.COLORS['brand-primary'])

        # Set palette colors
        dark_palette.setColor(QPalette.ColorRole.Window, bg_secondary)
        dark_palette.setColor(QPalette.ColorRole.WindowText, text_primary)
        dark_palette.setColor(QPalette.ColorRole.Base, bg_primary)
        dark_palette.setColor(QPalette.ColorRole.AlternateBase, bg_secondary)
        dark_palette.setColor(QPalette.ColorRole.Text, text_primary)
        dark_palette.setColor(QPalette.ColorRole.Button, bg_secondary)
        dark_palette.setColor(QPalette.ColorRole.ButtonText, text_primary)
        dark_palette.setColor(QPalette.ColorRole.Link, brand_primary)
        dark_palette.setColor(QPalette.ColorRole.Highlight, brand_primary)

        self.qt_app.setPalette(dark_palette)

    def _register_check_services(self):
        """Register all check services with monitoring engine"""
        self.monitoring_engine.register_check_service(CheckType.PING, PingService.check)
        self.monitoring_engine.register_check_service(CheckType.HTTP,
            lambda device: HTTPService.check(device, use_https=False))
        self.monitoring_engine.register_check_service(CheckType.HTTPS,
            lambda device: HTTPService.check(device, use_https=True))
        self.monitoring_engine.register_check_service(CheckType.SSH, SSHService.check)
        self.monitoring_engine.register_check_service(CheckType.DNS, DNSService.check)

        logger.info("Check services registered")

    def _signal_handler(self, signum, frame):
        """Handle system signals for graceful shutdown"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.shutdown()
        sys.exit(0)

    def run(self):
        """Run the application"""
        # Show main window
        self.main_window.show()

        # Start monitoring if configured
        if self.config.get('application.auto_start_monitoring', True):
            self.main_window.start_monitoring()

        logger.info("Application running")

        # Execute Qt event loop
        return self.qt_app.exec()

    def shutdown(self):
        """Shutdown application gracefully"""
        logger.info("Shutting down application...")

        try:
            # Stop monitoring
            if self.monitoring_engine.running:
                self.monitoring_engine.stop()

            # Save configuration
            self.config.save()

            # Close database
            db_manager.close()

            # Cleanup logs
            log_manager.cleanup_old_logs(
                days=self.config.get('database.retention_days', 90)
            )

            logger.info("Application shutdown complete")

        except Exception as e:
            logger.error(f"Error during shutdown: {e}", exc_info=True)


def main():
    """Main entry point"""
    try:
        # Set Windows AppUserModelID FIRST (before creating QApplication)
        set_windows_appid()

        # Create QApplication ONCE
        qt_app = QApplication(sys.argv)
        qt_app.setApplicationName("PingMonitor Pro")
        qt_app.setOrganizationName("Fabrizio Cerchia")
        qt_app.setApplicationVersion("2.3.0")

        # Set application icon for taskbar
        icon_path = Path(__file__).parent.parent / "icon.ico"
        if icon_path.exists():
            app_icon = QIcon(str(icon_path))
            qt_app.setWindowIcon(app_icon)
            print(f"[OK] Application icon loaded: {icon_path}")
        else:
            print(f"[WARNING] Application icon not found: {icon_path}")

        # Check for single instance (singleton pattern)
        shared_memory = QSharedMemory("PingMonitorProSingleInstance")

        # Try to attach to existing shared memory
        if shared_memory.attach():
            # Instance already running
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setWindowTitle("PingMonitor Pro - Already Running")
            msg.setText("PingMonitor Pro is already running!")
            msg.setInformativeText("Only one instance can run at a time.\n\nPlease check the system tray.")
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg.exec()
            sys.exit(0)

        # Try to create new shared memory
        if not shared_memory.create(1):
            # Failed to create (probably already exists)
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setWindowTitle("PingMonitor Pro - Already Running")
            msg.setText("PingMonitor Pro is already running!")
            msg.setInformativeText("Only one instance can run at a time.\n\nPlease check the system tray.")
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg.exec()
            sys.exit(0)

        # We're the first instance - proceed
        app = PingMonitorApp(qt_app)
        exit_code = app.run()

        # Cleanup shared memory on exit
        shared_memory.detach()

        sys.exit(exit_code)

    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
