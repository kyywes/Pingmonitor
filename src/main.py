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
from src.utils.version_checker import check_and_notify_updates
from src.utils.github_updater import check_github_updates_silent

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
        self._setup_dark_theme()

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

        # VERSION CHECK: Detect source code modifications
        try:
            has_updates = check_and_notify_updates()
            if has_updates:
                logger.warning("🔄 Source code has been modified - changes detected!")
                logger.warning("🔄 Auto-patch mode: Running with latest modifications")
        except Exception as e:
            logger.error(f"VERSION CHECK FAILED: {e}", exc_info=True)

        # GITHUB AUTO-UPDATE: Check for updates from GitHub (silent)
        self._github_update_available = False
        self._github_updater = None
        self._github_details = {}
        try:
            has_github_updates, github_updater, github_details = check_github_updates_silent()
            if has_github_updates:
                logger.warning("🌐 GITHUB UPDATE AVAILABLE!")
                logger.warning(f"🌐 {github_details.get('commit_message', 'New version available')}")
                self._github_update_available = True
                self._github_updater = github_updater
                self._github_details = github_details
        except Exception as e:
            logger.error(f"GITHUB CHECK FAILED: {e}", exc_info=True)

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

        # Show auto-sync notification if devices were updated
        if hasattr(self, '_auto_sync_updated') and self._auto_sync_updated:
            self.main_window.status_bar.showMessage(
                "✓ Auto-sync completato: configurazione dispositivi aggiornata automaticamente",
                10000  # Show for 10 seconds
            )

        # Show GitHub update notification if available
        if self._github_update_available:
            self._show_github_update_notification()

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        logger.info("Application initialized successfully")

    def _setup_dark_theme(self):
        """Setup dark theme for application"""
        dark_palette = QPalette()

        # Define colors
        dark_color = QColor(26, 26, 46)  # #1a1a2e
        darker_color = QColor(15, 20, 25)  # #0f1419
        light_color = QColor(96, 165, 250)  # #60a5fa
        text_color = QColor(229, 231, 235)  # #e5e7eb
        disabled_color = QColor(156, 163, 175)  # #9ca3af

        # Set palette colors
        dark_palette.setColor(QPalette.ColorRole.Window, dark_color)
        dark_palette.setColor(QPalette.ColorRole.WindowText, text_color)
        dark_palette.setColor(QPalette.ColorRole.Base, darker_color)
        dark_palette.setColor(QPalette.ColorRole.AlternateBase, dark_color)
        dark_palette.setColor(QPalette.ColorRole.ToolTipBase, darker_color)
        dark_palette.setColor(QPalette.ColorRole.ToolTipText, text_color)
        dark_palette.setColor(QPalette.ColorRole.Text, text_color)
        dark_palette.setColor(QPalette.ColorRole.Button, dark_color)
        dark_palette.setColor(QPalette.ColorRole.ButtonText, text_color)
        dark_palette.setColor(QPalette.ColorRole.Link, light_color)
        dark_palette.setColor(QPalette.ColorRole.Highlight, light_color)
        dark_palette.setColor(QPalette.ColorRole.HighlightedText, dark_color)
        dark_palette.setColor(QPalette.ColorRole.PlaceholderText, disabled_color)

        dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, disabled_color)
        dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, disabled_color)
        dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, disabled_color)

        self.qt_app.setPalette(dark_palette)

        # Set global stylesheet
        self.qt_app.setStyleSheet("""
            QToolTip {
                background-color: #1a1a2e;
                color: #e5e7eb;
                border: 1px solid #60a5fa;
                padding: 5px;
                border-radius: 3px;
            }
        """)

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

    def _show_github_update_notification(self):
        """Show notification about GitHub update availability"""
        try:
            from PyQt6.QtWidgets import QMessageBox, QPushButton

            commit_msg = self._github_details.get('commit_message', 'Nuova versione disponibile')
            remote_hash = self._github_details.get('remote_hash', '')[:8]

            # Create message box
            msg_box = QMessageBox(self.main_window)
            msg_box.setWindowTitle("🌐 Aggiornamento Disponibile")
            msg_box.setIcon(QMessageBox.Icon.Information)

            msg_box.setText("È disponibile un aggiornamento da GitHub!")
            msg_box.setInformativeText(
                f"<b>Commit:</b> {remote_hash}<br>"
                f"<b>Messaggio:</b> {commit_msg}<br><br>"
                f"Vuoi scaricare e installare l'aggiornamento ora?<br><br>"
                f"<i>L'applicazione verrà riavviata dopo l'aggiornamento.</i>"
            )

            # Add buttons
            install_btn = msg_box.addButton("Installa Ora", QMessageBox.ButtonRole.AcceptRole)
            later_btn = msg_box.addButton("Più Tardi", QMessageBox.ButtonRole.RejectRole)
            msg_box.setDefaultButton(install_btn)

            # Show notification in status bar
            self.main_window.status_bar.showMessage(
                f"🌐 Aggiornamento disponibile: {commit_msg}",
                15000
            )

            # Execute dialog
            msg_box.exec()

            # Check which button was clicked
            if msg_box.clickedButton() == install_btn:
                self._apply_github_update()

        except Exception as e:
            logger.error(f"Error showing GitHub update notification: {e}", exc_info=True)

    def _apply_github_update(self):
        """Apply GitHub update"""
        try:
            from PyQt6.QtWidgets import QMessageBox, QProgressDialog
            from PyQt6.QtCore import Qt

            # Show progress dialog
            progress = QProgressDialog(
                "Download e applicazione aggiornamento in corso...",
                "Annulla",
                0, 0,
                self.main_window
            )
            progress.setWindowTitle("Aggiornamento GitHub")
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            progress.setCancelButton(None)  # Non annullabile
            progress.show()

            # Process events to show dialog
            self.qt_app.processEvents()

            # Apply updates
            success, message = self._github_updater.apply_updates(self._github_details)

            # Close progress
            progress.close()

            if success:
                # Success message
                msg_box = QMessageBox(self.main_window)
                msg_box.setWindowTitle("✅ Aggiornamento Completato")
                msg_box.setIcon(QMessageBox.Icon.Information)
                msg_box.setText("Aggiornamento installato con successo!")
                msg_box.setInformativeText(
                    f"{message}\n\n"
                    f"L'applicazione verrà riavviata per applicare le modifiche."
                )
                msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
                msg_box.exec()

                # Restart application
                logger.info("Restarting application after update...")
                self.shutdown()

                # Restart
                import subprocess
                subprocess.Popen([sys.executable] + sys.argv)
                sys.exit(0)

            else:
                # Error message
                msg_box = QMessageBox(self.main_window)
                msg_box.setWindowTitle("❌ Errore Aggiornamento")
                msg_box.setIcon(QMessageBox.Icon.Critical)
                msg_box.setText("Errore durante l'aggiornamento")
                msg_box.setInformativeText(f"{message}\n\nL'applicazione continuerà a funzionare con la versione corrente.")
                msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
                msg_box.exec()

        except Exception as e:
            logger.error(f"Error applying GitHub update: {e}", exc_info=True)

            # Error message
            msg_box = QMessageBox(self.main_window)
            msg_box.setWindowTitle("❌ Errore")
            msg_box.setIcon(QMessageBox.Icon.Critical)
            msg_box.setText("Errore durante l'aggiornamento")
            msg_box.setInformativeText(f"{str(e)}\n\nL'applicazione continuerà a funzionare.")
            msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg_box.exec()

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
