"""
PingMonitor v2.3 - Enhanced Main Window
Complete integration of all advanced features
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QSystemTrayIcon, QMenu, QMessageBox, QStatusBar, QProgressBar,
    QFileDialog, QInputDialog
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPoint
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QBrush, QColor, QAction, QCursor
import subprocess
import webbrowser
from pathlib import Path
import logging

from .ssh_terminal import SSHTerminal
from .email_test_widget import EmailTestWidget
from .telegram_test_widget import TelegramTestWidget
from .settings_widget import SettingsWidget
from .logs_viewer import LogsViewer
from .devices_manager import DevicesManager
from .dashboard_widget import DashboardWidget
from ..services.notification_service import NotificationService
from ..services.auto_recovery_service import AutoRecoveryService
from ..services.aggregated_email_service import AggregatedEmailService
from ..services.export_service import ExportService
from ..utils.config_importer import ConfigImporter
from ..models.device import Device
from ..models.check_result import CheckResult
from ..models.base import db_manager
import os

logger = logging.getLogger(__name__)


class MainWindowV2(QMainWindow):
    """Enhanced main application window with all advanced features"""

    status_update_signal = pyqtSignal(dict)

    def __init__(self, config, monitoring_engine):
        super().__init__()

        self.config = config
        self.monitoring_engine = monitoring_engine

        # Initialize advanced services
        email_config = {}
        ssh_config = {}

        # Try to load from legacy config if available
        legacy_config_path = Path(__file__).parent.parent.parent / "config" / "config.json"
        if legacy_config_path.exists():
            _, email_config, ssh_config = ConfigImporter.import_from_legacy_config(legacy_config_path)

        self.notification_service = NotificationService()
        self.auto_recovery_service = AutoRecoveryService(ssh_config)
        self.aggregated_email_service = AggregatedEmailService(email_config)

        self.email_config = email_config
        self.ssh_config = ssh_config

        # Device tracking for recovery
        self.device_recovery_status = {}

        # Setup UI
        self._setup_window()
        self._create_menu_bar()
        self._create_toolbar()
        self._create_central_widget()
        self._create_status_bar()
        self._create_system_tray()

        # Setup monitoring callbacks
        self.monitoring_engine.register_callback('on_check_complete', self._on_check_complete)
        self.monitoring_engine.register_callback('on_status_change', self._on_device_status_change)
        self.monitoring_engine.register_callback('on_recovery_success', self._on_recovery_success)
        self.monitoring_engine.register_callback('on_recovery_failure', self._on_recovery_failure)

        # Setup update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_ui)
        self.update_timer.start(1000)

        # Setup aggregated email timer (every hour)
        self.email_aggregate_timer = QTimer()
        self.email_aggregate_timer.timeout.connect(self._send_aggregated_email)
        self.email_aggregate_timer.start(3600000)  # 1 hour = 3600000 ms

        # Auto-import devices from legacy config
        self._auto_import_devices()

        logger.info("Enhanced main window initialized")

    def _setup_window(self):
        """Setup main window properties"""
        self.setWindowTitle("PingMonitor - Monitoraggio Professionale Rete PAI-PL")

        # Load icon if available
        icon_path = Path(__file__).parent.parent.parent / "icon.ico"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        geometry = self.config.get('ui.window_geometry', {})
        width = geometry.get('width', 1600)
        height = geometry.get('height', 900)

        self.resize(width, height)

        screen = self.screen().geometry()
        x = (screen.width() - width) // 2
        y = (screen.height() - height) // 2
        self.move(x, y)

    def _create_menu_bar(self):
        """Create enhanced menu bar"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        import_devices_action = QAction("&Importa Dispositivi da Config.json", self)
        import_devices_action.triggered.connect(self._import_devices_dialog)
        file_menu.addAction(import_devices_action)

        # Export submenu
        export_menu = file_menu.addMenu("&Esporta")

        export_devices_action = QAction("📊 Esporta Dispositivi (CSV)", self)
        export_devices_action.triggered.connect(self._export_devices_csv)
        export_menu.addAction(export_devices_action)

        export_report_action = QAction("📈 Esporta Report Completo (CSV)", self)
        export_report_action.triggered.connect(self._export_monitoring_report)
        export_menu.addAction(export_report_action)

        export_checks_action = QAction("📋 Esporta Check Results (CSV)", self)
        export_checks_action.triggered.connect(self._export_check_results)
        export_menu.addAction(export_checks_action)

        file_menu.addSeparator()

        exit_action = QAction("E&sci", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # View menu
        view_menu = menubar.addMenu("&View")

        fullscreen_action = QAction("&Schermo Intero", self)
        fullscreen_action.setShortcut("F11")
        fullscreen_action.triggered.connect(self._toggle_fullscreen)
        view_menu.addAction(fullscreen_action)

        # Tools menu
        tools_menu = menubar.addMenu("&Tools")

        settings_action = QAction("&Impostazioni", self)
        settings_action.setShortcut("Ctrl+,")
        settings_action.triggered.connect(self._show_settings)
        tools_menu.addAction(settings_action)

        ssh_terminal_action = QAction("Terminale &SSH", self)
        ssh_terminal_action.setShortcut("Ctrl+T")
        ssh_terminal_action.triggered.connect(self._show_ssh_terminal)
        tools_menu.addAction(ssh_terminal_action)

        # Help menu
        help_menu = menubar.addMenu("&Help")

        about_action = QAction("&Informazioni", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _create_toolbar(self):
        """Create enhanced toolbar"""
        toolbar = self.addToolBar("Main Toolbar")
        toolbar.setMovable(False)

        # Start button
        self.btn_start = QPushButton("▶ Avvia Monitoraggio")
        self.btn_start.clicked.connect(self.start_monitoring)
        self.btn_start.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: white;
                border: none;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 6px;
                transition: all 0.3s ease;
            }
            QPushButton:hover {
                background-color: #059669;
                padding: 12px 28px;
            }
            QPushButton:pressed {
                background-color: #047857;
                padding: 12px 24px;
            }
        """)
        toolbar.addWidget(self.btn_start)

        # Stop button
        self.btn_stop = QPushButton("⏹ Stop")
        self.btn_stop.clicked.connect(self.stop_monitoring)
        self.btn_stop.setEnabled(False)
        self.btn_stop.setStyleSheet("""
            QPushButton {
                background-color: #ef4444;
                color: white;
                border: none;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 6px;
                transition: all 0.3s ease;
            }
            QPushButton:hover {
                background-color: #dc2626;
                padding: 12px 28px;
            }
            QPushButton:pressed {
                background-color: #b91c1c;
                padding: 12px 24px;
            }
            QPushButton:disabled {
                background-color: #6b7280;
                color: #9ca3af;
            }
        """)
        toolbar.addWidget(self.btn_stop)

        toolbar.addSeparator()

        # Refresh button
        btn_refresh = QPushButton("🔄 Aggiorna")
        btn_refresh.clicked.connect(self._refresh_data)
        btn_refresh.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 6px;
                transition: all 0.3s ease;
            }
            QPushButton:hover {
                background-color: #2563eb;
                padding: 12px 28px;
            }
            QPushButton:pressed {
                background-color: #1d4ed8;
                padding: 12px 24px;
            }
        """)
        toolbar.addWidget(btn_refresh)

        # Check Now button - Instant monitoring check
        btn_check_now = QPushButton("⚡ Check Now")
        btn_check_now.clicked.connect(self._check_now)
        btn_check_now.setStyleSheet("""
            QPushButton {
                background-color: #f59e0b;
                color: white;
                border: none;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 6px;
                transition: all 0.3s ease;
            }
            QPushButton:hover {
                background-color: #d97706;
                padding: 12px 28px;
            }
            QPushButton:pressed {
                background-color: #b45309;
                padding: 12px 24px;
            }
        """)
        toolbar.addWidget(btn_check_now)

        toolbar.addSeparator()

        # Add device button
        btn_add_device = QPushButton("➕ Aggiungi Dispositivo")
        btn_add_device.clicked.connect(self._add_device)
        btn_add_device.setStyleSheet("""
            QPushButton {
                background-color: #8b5cf6;
                color: white;
                border: none;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 6px;
                transition: all 0.3s ease;
            }
            QPushButton:hover {
                background-color: #7c3aed;
                padding: 12px 28px;
            }
            QPushButton:pressed {
                background-color: #6d28d9;
                padding: 12px 24px;
            }
        """)
        toolbar.addWidget(btn_add_device)

        # SSH Terminal button
        btn_ssh = QPushButton("💻 Terminale SSH")
        btn_ssh.clicked.connect(self._show_ssh_terminal)
        btn_ssh.setStyleSheet("""
            QPushButton {
                background-color: #6366f1;
                color: white;
                border: none;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 6px;
                transition: all 0.3s ease;
            }
            QPushButton:hover {
                background-color: #4f46e5;
                padding: 12px 28px;
            }
            QPushButton:pressed {
                background-color: #4338ca;
                padding: 12px 24px;
            }
        """)
        toolbar.addWidget(btn_ssh)

    def _create_central_widget(self):
        """Create central widget with enhanced tabs"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        # Header with statistics
        header = self._create_header()
        layout.addWidget(header)

        # Tab widget with modern styling
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid rgba(148, 163, 184, 0.2);
                background-color: rgba(15, 20, 25, 0.5);
                border-radius: 8px;
                margin-top: -1px;
            }
            QTabBar::tab {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(30, 41, 59, 0.8),
                    stop:1 rgba(15, 20, 25, 0.9));
                color: #94a3b8;
                padding: 12px 24px;
                margin-right: 4px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                border: 1px solid rgba(148, 163, 184, 0.1);
                font-size: 14px;
                font-weight: 500;
            }
            QTabBar::tab:selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2563eb,
                    stop:1 #1e40af);
                color: white;
                border-bottom: 3px solid #60a5fa;
                font-weight: 600;
            }
            QTabBar::tab:hover:!selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(37, 99, 235, 0.3),
                    stop:1 rgba(30, 64, 175, 0.4));
                color: #e2e8f0;
            }
        """)

        # Dashboard tab (nuovo)
        self.dashboard = DashboardWidget()
        self.dashboard.set_monitoring_engine(self.monitoring_engine)
        self.tab_widget.addTab(self.dashboard, "📊 Dashboard")

        # Monitoring tab
        self.monitoring_tab = self._create_monitoring_tab()
        self.tab_widget.addTab(self.monitoring_tab, "📋 Monitoraggio")

        # SSH Terminal tab
        self.ssh_terminal = SSHTerminal()
        self.tab_widget.addTab(self.ssh_terminal, "💻 Terminale SSH")

        # Email Test tab
        self.email_test_widget = EmailTestWidget(self.email_config)
        self.tab_widget.addTab(self.email_test_widget, "📧 Test Email")

        # Telegram Test tab
        telegram_config = {}  # Will be loaded from settings
        self.telegram_test_widget = TelegramTestWidget(telegram_config)
        self.tab_widget.addTab(self.telegram_test_widget, "🤖 Test Telegram")

        # Settings tab
        self.settings_widget = SettingsWidget()
        self.settings_widget.settings_changed.connect(self._on_settings_changed)
        self.tab_widget.addTab(self.settings_widget, "⚙️ Impostazioni")

        # Devices tab
        self.devices_tab = self._create_devices_tab()
        self.tab_widget.addTab(self.devices_tab, "🖥 Dispositivi")

        # Logs tab
        self.logs_tab = self._create_logs_tab()
        self.tab_widget.addTab(self.logs_tab, "📝 Log")

        layout.addWidget(self.tab_widget)

    def _create_header(self):
        """Create enhanced header with modern design"""
        header = QWidget()
        header.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1e3a8a, stop:0.5 #2563eb, stop:1 #3b82f6);
                border-radius: 12px;
                padding: 20px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
        """)

        layout = QHBoxLayout(header)
        layout.setSpacing(30)

        # Title section
        title_container = QWidget()
        title_layout = QVBoxLayout(title_container)
        title_layout.setSpacing(5)
        title_layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel("🌐 PingMonitor")
        title.setStyleSheet("font-size: 26px; font-weight: 700; color: white; letter-spacing: -0.5px;")
        title_layout.addWidget(title)

        subtitle = QLabel("Monitoraggio Professionale Rete PAI-PL")
        subtitle.setStyleSheet("font-size: 12px; font-weight: 500; color: rgba(255, 255, 255, 0.7);")
        title_layout.addWidget(subtitle)

        layout.addWidget(title_container)

        layout.addStretch()

        # Stats section with modern cards
        stats_container = QHBoxLayout()
        stats_container.setSpacing(15)

        # Stats labels
        self.lbl_total = self._create_stat_label("Totale", "0", "#60a5fa")
        self.lbl_online = self._create_stat_label("Online", "0", "#10b981")
        self.lbl_offline = self._create_stat_label("Offline", "0", "#ef4444")
        self.lbl_degraded = self._create_stat_label("Degradato", "0", "#f59e0b")

        for lbl in [self.lbl_total, self.lbl_online, self.lbl_offline, self.lbl_degraded]:
            stats_container.addWidget(lbl)

        layout.addLayout(stats_container)

        return header

    def _create_stat_label(self, title, value, color):
        """Create a modern stat label"""
        container = QWidget()
        container.setStyleSheet(f"""
            QWidget {{
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                padding: 10px 16px;
                border: 1px solid rgba(255, 255, 255, 0.15);
            }}
            QWidget:hover {{
                background-color: rgba(255, 255, 255, 0.15);
                border: 1px solid rgba(255, 255, 255, 0.25);
            }}
        """)

        layout = QVBoxLayout(container)
        layout.setSpacing(2)
        layout.setContentsMargins(0, 0, 0, 0)

        title_label = QLabel(title.upper())
        title_label.setStyleSheet("""
            font-size: 10px;
            font-weight: 600;
            color: rgba(255, 255, 255, 0.7);
            letter-spacing: 0.5px;
        """)
        layout.addWidget(title_label)

        value_label = QLabel(value)
        value_label.setObjectName("stat_value")
        value_label.setStyleSheet(f"""
            font-size: 24px;
            font-weight: 700;
            color: {color};
            letter-spacing: -1px;
        """)
        layout.addWidget(value_label)

        container.value_label = value_label
        return container

    def _create_monitoring_tab(self):
        """Create enhanced monitoring tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Monitoring table
        self.monitoring_table = QTableWidget()
        self.monitoring_table.setColumnCount(9)
        self.monitoring_table.setHorizontalHeaderLabels([
            "Stato", "Indirizzo IP", "Nome", "Tipo", "Posizione",
            "Risposta (ms)", "Ultimo Controllo", "Uptime %", "Azioni"
        ])

        # Enable context menu
        self.monitoring_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.monitoring_table.customContextMenuRequested.connect(self._show_device_context_menu)

        # Table styling - Modern Professional Design
        self.monitoring_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.monitoring_table.setAlternatingRowColors(True)
        self.monitoring_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.monitoring_table.setStyleSheet("""
            QTableWidget {
                background-color: rgba(15, 20, 25, 0.6);
                border: 1px solid rgba(148, 163, 184, 0.2);
                border-radius: 10px;
                gridline-color: rgba(148, 163, 184, 0.1);
                selection-background-color: rgba(37, 99, 235, 0.3);
            }
            QTableWidget::item {
                padding: 12px 8px;
                color: #e2e8f0;
                font-size: 13px;
                border-bottom: 1px solid rgba(148, 163, 184, 0.05);
            }
            QTableWidget::item:selected {
                background-color: rgba(37, 99, 235, 0.4);
                color: white;
            }
            QTableWidget::item:hover {
                background-color: rgba(37, 99, 235, 0.2);
            }
            QHeaderView::section {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2563eb,
                    stop:1 #1e40af);
                color: white;
                padding: 14px 8px;
                font-weight: 600;
                font-size: 13px;
                border: none;
                border-right: 1px solid rgba(255, 255, 255, 0.1);
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            QHeaderView::section:first {
                border-top-left-radius: 10px;
            }
            QHeaderView::section:last {
                border-top-right-radius: 10px;
                border-right: none;
            }
            QTableWidget::item:alternate {
                background-color: rgba(30, 41, 59, 0.3);
            }
        """)

        layout.addWidget(self.monitoring_table)

        return widget

    def _show_device_context_menu(self, position: QPoint):
        """Show context menu on device right-click"""
        item = self.monitoring_table.itemAt(position)
        if item is None:
            return

        row = item.row()

        # Get device IP from table
        ip_item = self.monitoring_table.item(row, 1)
        if not ip_item:
            return

        device_ip = ip_item.text()
        device_name = self.monitoring_table.item(row, 2).text() if self.monitoring_table.item(row, 2) else device_ip

        # Create context menu
        menu = QMenu(self)

        # Open in Web Browser
        web_action = QAction("🌐 Apri nel Browser", self)
        web_action.triggered.connect(lambda: self._open_in_browser(device_ip))
        menu.addAction(web_action)

        # Open in PuTTY (integrated terminal)
        putty_action = QAction("🖥 Apri in PuTTY", self)
        putty_action.triggered.connect(lambda: self._open_in_putty(device_ip, device_name))
        menu.addAction(putty_action)

        menu.addSeparator()

        # Force reboot
        reboot_action = QAction("🔄 Forza Riavvio (SSH)", self)
        reboot_action.triggered.connect(lambda: self._force_reboot_device(device_ip, device_name))
        menu.addAction(reboot_action)

        # Force check
        check_action = QAction("🔍 Forza Controllo Ora", self)
        check_action.triggered.connect(lambda: self._force_check_device(device_ip))
        menu.addAction(check_action)

        menu.addSeparator()

        # Device details
        details_action = QAction("📊 Mostra Dettagli", self)
        details_action.triggered.connect(lambda: self._show_device_details(device_ip, device_name))
        menu.addAction(details_action)

        # Show menu at cursor
        menu.exec(QCursor.pos())

    def _open_in_browser(self, device_ip: str):
        """Open device in web browser"""
        try:
            # Try to get port from device config
            url = f"http://{device_ip}"
            webbrowser.open(url)
            logger.info(f"Opening {url} in browser")
            self.status_bar.showMessage(f"Opening {url} in browser...", 3000)
        except Exception as e:
            logger.error(f"Failed to open browser: {e}")
            QMessageBox.warning(self, "Errore", f"Failed to open browser:\n{str(e)}")

    def _open_in_putty(self, device_ip: str, device_name: str):
        """Open device in integrated SSH terminal (plink-like interface)"""
        # Switch to SSH Terminal tab
        self.tab_widget.setCurrentWidget(self.ssh_terminal)

        # Connect to device
        username = self.ssh_config.get('username', 'root')
        password = self.ssh_config.get('password', '')

        self.ssh_terminal.connect_to_device(device_ip, username, password)
        logger.info(f"Opening integrated SSH terminal (PuTTY) for {device_name} ({device_ip})")
        self.status_bar.showMessage(f"Connessione SSH a {device_name}...", 3000)

    def _open_in_ssh_terminal(self, device_ip: str):
        """Open device in integrated SSH terminal"""
        # Switch to SSH Terminal tab
        self.tab_widget.setCurrentWidget(self.ssh_terminal)

        # Connect to device
        username = self.ssh_config.get('username', 'root')
        password = self.ssh_config.get('password', '')

        self.ssh_terminal.connect_to_device(device_ip, username, password)
        logger.info(f"Opening integrated SSH terminal for {device_ip}")

    def _force_reboot_device(self, device_ip: str, device_name: str):
        """Force reboot device via SSH"""
        reply = QMessageBox.question(self, "Confirm Reboot",
                                     f"Are you sure you want to reboot {device_name} ({device_ip})?\n\n"
                                     f"This will execute 'reboot' command via SSH.",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            success, message = self.auto_recovery_service.attempt_recovery(device_ip, device_name)

            if success:
                QMessageBox.information(self, "Reboot Initiated",
                                      f"Reboot command sent to {device_name}.\n\n{message}")
                logger.info(f"Manual reboot initiated for {device_name} ({device_ip})")
            else:
                QMessageBox.warning(self, "Reboot Failed",
                                  f"Failed to reboot {device_name}.\n\n{message}")

    def _force_check_device(self, device_ip: str):
        """Force immediate check of device"""
        self.monitoring_engine.force_check()
        self.status_bar.showMessage(f"Forcing check for {device_ip}...", 3000)

    def _show_device_details(self, device_ip: str, device_name: str):
        """Show detailed device information"""
        QMessageBox.information(self, "Device Details",
                              f"Device: {device_name}\n"
                              f"IP: {device_ip}\n\n"
                              f"Detailed statistics coming soon!")

    def _create_devices_tab(self):
        """Create devices management tab"""
        # Return the DevicesManager widget directly
        devices_manager = DevicesManager()
        devices_manager.devices_changed.connect(self._on_devices_changed)
        return devices_manager

    def _create_logs_tab(self):
        """Create logs tab"""
        # Return the LogsViewer widget directly
        return LogsViewer()

    def _create_status_bar(self):
        """Create status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Pronto")

        # Add progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(200)
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)

    def _create_system_tray(self):
        """Create system tray icon"""
        if self.config.get('application.minimize_to_tray', True):
            self.tray_icon = QSystemTrayIcon(self)

            # Load icon
            icon_path = Path(__file__).parent.parent.parent / "icon.ico"
            if icon_path.exists():
                self.tray_icon.setIcon(QIcon(str(icon_path)))
            else:
                # Fallback icon
                pixmap = QPixmap(64, 64)
                pixmap.fill(Qt.GlobalColor.transparent)
                painter = QPainter(pixmap)
                painter.setBrush(QBrush(QColor("#2563eb")))
                painter.drawEllipse(0, 0, 64, 64)
                painter.end()
                self.tray_icon.setIcon(QIcon(pixmap))

            self.tray_icon.setToolTip("PingMonitor v2.3")

            # Create menu
            tray_menu = QMenu()
            show_action = QAction("Mostra", self)
            show_action.triggered.connect(self.show)
            tray_menu.addAction(show_action)

            quit_action = QAction("Esci", self)
            quit_action.triggered.connect(self.quit_application)
            tray_menu.addAction(quit_action)

            self.tray_icon.setContextMenu(tray_menu)
            self.tray_icon.show()

    def start_monitoring(self):
        """Start monitoring"""
        try:
            self.monitoring_engine.start()
            self.btn_start.setEnabled(False)
            self.btn_stop.setEnabled(True)
            self.status_bar.showMessage("🟢 Monitoraggio Attivo")
            logger.info("Monitoring started")
        except Exception as e:
            logger.error(f"Failed to start monitoring: {e}")
            QMessageBox.critical(self, "Errore", f"Failed to start monitoring:\n{str(e)}")

    def stop_monitoring(self):
        """Stop monitoring"""
        try:
            self.monitoring_engine.stop()
            self.btn_start.setEnabled(True)
            self.btn_stop.setEnabled(False)
            self.status_bar.showMessage("🔴 Monitoraggio Fermato")
            logger.info("Monitoring stopped")
        except Exception as e:
            logger.error(f"Failed to stop monitoring: {e}")

    def _on_check_complete(self, device, result):
        """Handle check completion with intelligent alert logic"""
        device_ip = device.ip_address
        ping_ok = result.get('success', False)

        # Check if web is OK (if web check enabled)
        web_ok = True  # Default to true
        if device.http_enabled or device.https_enabled:
            # Would need to check web result here
            # For now, simulate based on result
            web_ok = result.get('success', False)

        # Check if we should send alert using intelligent logic
        if self.notification_service.should_send_alert(device_ip, ping_ok, web_ok):
            # Prepare device info
            device_info = {
                'name': device.name,
                'ip': device_ip,
                'location': device.location,
                'port': device.http_port if device.http_enabled else device.https_port
            }

            # Send email alert
            self.notification_service.send_email_alert(
                self.email_config,
                device_info,
                'manual_intervention_required'
            )

        # If ping OK but web NOT OK and no recovery attempt yet
        if ping_ok and not web_ok and device_ip not in self.device_recovery_status:
            # Attempt auto-recovery
            logger.warning(f"Attempting auto-recovery for {device.name} ({device_ip})")

            success, message = self.auto_recovery_service.attempt_recovery(device_ip, device.name)

            if success:
                # Mark recovery attempt
                from datetime import datetime
                self.notification_service.mark_recovery_attempt(device_ip, datetime.now())
                self.device_recovery_status[device_ip] = {
                    'status': 'recovering',
                    'start_time': datetime.now()
                }
                self.status_bar.showMessage(f"Auto-recovery initiated for {device.name}", 5000)
            else:
                logger.error(f"Auto-recovery failed for {device.name}: {message}")

    def _on_device_status_change(self, device, old_status, new_status):
        """Handle device status change"""
        logger.info(f"Device {device.name} status changed: {old_status} → {new_status}")

        # Clear recovery status if device comes back online
        if new_status == 'online' and device.ip_address in self.device_recovery_status:
            del self.device_recovery_status[device.ip_address]
            self.notification_service.clear_recovery(device.ip_address)

    def _on_devices_changed(self):
        """Handle devices being added/edited/deleted"""
        logger.info("Devices changed - reloading monitoring engine")
        try:
            # Reload devices in monitoring engine
            self.monitoring_engine.load_devices()
            self._update_ui()
            logger.info("Devices reloaded successfully")
        except Exception as e:
            logger.error(f"Failed to reload devices: {e}")

    def _update_ui(self):
        """Update UI with latest data"""
        try:
            # Update header stats
            total = len(self.monitoring_engine.devices)
            online = sum(1 for d in self.monitoring_engine.devices.values() if d.current_status == 'online')
            offline = sum(1 for d in self.monitoring_engine.devices.values() if d.current_status == 'offline')
            degraded = sum(1 for d in self.monitoring_engine.devices.values() if d.current_status == 'degraded')

            # Update the value labels in the stat containers
            self.lbl_total.value_label.setText(str(total))
            self.lbl_online.value_label.setText(str(online))
            self.lbl_offline.value_label.setText(str(offline))
            self.lbl_degraded.value_label.setText(str(degraded))

            # Update monitoring table
            self._update_monitoring_table()

        except Exception as e:
            logger.error(f"Error updating UI: {e}")

    def _update_monitoring_table(self):
        """Update monitoring table"""
        try:
            devices = list(self.monitoring_engine.devices.values())
            self.monitoring_table.setRowCount(len(devices))

            for row, device in enumerate(devices):
                # Status
                if device.current_status == 'online':
                    status_icon = "🟢 ONLINE"
                elif device.current_status == 'offline':
                    status_icon = "🔴 OFFLINE"
                elif device.current_status == 'degraded':
                    status_icon = "🟡 DEGRADED"
                else:
                    status_icon = "⚪ UNKNOWN"

                self.monitoring_table.setItem(row, 0, QTableWidgetItem(status_icon))
                self.monitoring_table.setItem(row, 1, QTableWidgetItem(device.ip_address))
                self.monitoring_table.setItem(row, 2, QTableWidgetItem(device.name))
                self.monitoring_table.setItem(row, 3, QTableWidgetItem(device.device_type))
                self.monitoring_table.setItem(row, 4, QTableWidgetItem(device.location or "N/A"))

                # Risposta (ms) - mostra il tempo di risposta
                response_time = getattr(device, 'last_response_time', None)
                if response_time is not None and response_time > 0:
                    response_item = QTableWidgetItem(f"{response_time:.1f}")
                else:
                    response_item = QTableWidgetItem("0.0")
                self.monitoring_table.setItem(row, 5, response_item)

                last_check = device.last_check_time if device.last_check_time else "Never"
                self.monitoring_table.setItem(row, 6, QTableWidgetItem(str(last_check)))

                self.monitoring_table.setItem(row, 7, QTableWidgetItem(f"{device.uptime_percentage:.1f}%"))
                self.monitoring_table.setItem(row, 8, QTableWidgetItem("..."))

        except Exception as e:
            logger.error(f"Error updating monitoring table: {e}")

    def _on_settings_changed(self, new_config):
        """Handle settings change"""
        try:
            logger.info("Settings changed - updating configuration")

            # Update email config
            if 'email' in new_config:
                self.email_config = new_config['email']
                # Update email test widget
                self.email_test_widget.email_config = self.email_config

            # Update SSH config
            if 'ssh' in new_config:
                self.ssh_config = new_config['ssh']
                # Recreate auto-recovery service with new SSH config
                self.auto_recovery_service = AutoRecoveryService(self.ssh_config)

            # Show notification
            self.status_bar.showMessage("Settings updated successfully!", 5000)

            QMessageBox.information(
                self,
                "Settings Updated",
                "Settings have been updated.\n\n"
                "Note: Some changes may require restarting the monitoring to take full effect."
            )

        except Exception as e:
            logger.error(f"Failed to apply settings: {e}")
            QMessageBox.warning(
                self,
                "Settings Error",
                f"Failed to apply some settings:\n{str(e)}"
            )

    def _auto_import_devices(self):
        """Auto-import devices from legacy config on startup"""
        legacy_config_path = Path(__file__).parent.parent.parent / "config" / "config.json"

        if legacy_config_path.exists():
            try:
                devices, email_cfg, ssh_cfg = ConfigImporter.import_from_legacy_config(legacy_config_path)

                if devices:
                    # Update configs
                    if email_cfg:
                        self.email_config = email_cfg
                    if ssh_cfg:
                        self.ssh_config = ssh_cfg
                        self.auto_recovery_service = AutoRecoveryService(ssh_cfg)

                    # Add devices to database
                    session = db_manager.get_session()
                    imported_count = 0

                    for device_data in devices:
                        # Check if device already exists
                        existing = session.query(Device).filter_by(ip_address=device_data['ip_address']).first()

                        if not existing:
                            device = Device(**device_data)
                            session.add(device)
                            imported_count += 1

                    session.commit()
                    session.close()

                    if imported_count > 0:
                        logger.info(f"Auto-imported {imported_count} devices from legacy config")
                        QMessageBox.information(self, "Devices Imported",
                                              f"Successfully imported {imported_count} devices from config.json")

                    # Reload devices in monitoring engine
                    self.monitoring_engine.load_devices()

            except Exception as e:
                logger.error(f"Failed to auto-import devices: {e}", exc_info=True)

    def _import_devices_dialog(self):
        """Show dialog to import devices"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Config File", "", "JSON Files (*.json);;All Files (*)"
        )

        if file_path:
            self._auto_import_devices()

    def _refresh_data(self):
        """Refresh data"""
        self._update_ui()
        self.status_bar.showMessage("Data refreshed", 2000)

    def _check_now(self):
        """Force immediate check of all devices"""
        try:
            if not self.monitoring_engine.running:
                QMessageBox.warning(
                    self,
                    "Monitoraggio Non Attivo",
                    "Il monitoraggio non è attivo.\n\nAvvia il monitoraggio prima di eseguire un check manuale."
                )
                return

            # Show loading message
            self.status_bar.showMessage("⚡ Esecuzione check istantaneo su tutti i dispositivi...", 5000)

            # Force immediate check by resetting last check times
            logger.info("MANUAL CHECK NOW: Forcing immediate check on all devices")
            for device_id in self.monitoring_engine.devices.keys():
                # Reset last check time to force immediate check
                from datetime import timedelta
                self.monitoring_engine.last_check_times[device_id] = datetime.utcnow() - timedelta(hours=10)

            # Update UI
            self._update_ui()

            # Show confirmation
            QMessageBox.information(
                self,
                "Check Istantaneo",
                f"Check istantaneo avviato su {len(self.monitoring_engine.devices)} dispositivi.\n\n"
                "I risultati saranno disponibili a breve."
            )

        except Exception as e:
            logger.error(f"Error in check now: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Errore",
                f"Errore durante il check istantaneo:\n{str(e)}"
            )

    def _add_device(self):
        """Show add device dialog"""
        QMessageBox.information(self, "Add Device", "Add device dialog - Coming soon!")

    def _export_devices_csv(self):
        """Export devices list to CSV"""
        try:
            # Get file path from user
            default_path = str(ExportService.get_default_export_path("devices"))
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Esporta Dispositivi",
                default_path,
                "CSV Files (*.csv);;All Files (*)"
            )

            if not file_path:
                return  # User cancelled

            # Get devices
            devices = list(self.monitoring_engine.devices.values())

            if not devices:
                QMessageBox.warning(
                    self,
                    "Nessun Dispositivo",
                    "Non ci sono dispositivi da esportare."
                )
                return

            # Export
            success, message = ExportService.export_devices_to_csv(devices, file_path)

            if success:
                QMessageBox.information(
                    self,
                    "Esportazione Completata",
                    f"Dispositivi esportati con successo!\n\n{message}"
                )
                logger.info(f"Devices exported to {file_path}")
            else:
                QMessageBox.warning(
                    self,
                    "Errore Esportazione",
                    f"Errore durante l'esportazione:\n\n{message}"
                )

        except Exception as e:
            logger.error(f"Export devices error: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Errore",
                f"Errore durante l'esportazione:\n\n{str(e)}"
            )

    def _export_check_results(self):
        """Export check results to CSV"""
        try:
            # Ask for time range
            days, ok = QInputDialog.getInt(
                self,
                "Periodo Esportazione",
                "Esporta check results degli ultimi N giorni:",
                7, 1, 365, 1
            )

            if not ok:
                return  # User cancelled

            # Get file path
            default_path = str(ExportService.get_default_export_path("check_results"))
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Esporta Check Results",
                default_path,
                "CSV Files (*.csv);;All Files (*)"
            )

            if not file_path:
                return

            # Get check results from database
            from datetime import datetime, timedelta
            session = db_manager.get_session()
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            check_results = session.query(CheckResult).filter(
                CheckResult.check_time >= cutoff_date.isoformat()
            ).all()

            session.close()

            if not check_results:
                QMessageBox.warning(
                    self,
                    "Nessun Dato",
                    f"Non ci sono check results negli ultimi {days} giorni."
                )
                return

            # Export
            success, message = ExportService.export_check_results_to_csv(check_results, file_path)

            if success:
                QMessageBox.information(
                    self,
                    "Esportazione Completata",
                    f"Check results esportati con successo!\n\n{message}"
                )
                logger.info(f"Check results exported to {file_path}")
            else:
                QMessageBox.warning(
                    self,
                    "Errore Esportazione",
                    f"Errore durante l'esportazione:\n\n{message}"
                )

        except Exception as e:
            logger.error(f"Export check results error: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Errore",
                f"Errore durante l'esportazione:\n\n{str(e)}"
            )

    def _export_monitoring_report(self):
        """Export comprehensive monitoring report to CSV"""
        try:
            # Get file path
            default_path = str(ExportService.get_default_export_path("report"))
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Esporta Report Monitoraggio",
                default_path,
                "CSV Files (*.csv);;All Files (*)"
            )

            if not file_path:
                return

            # Get devices and statistics
            devices = list(self.monitoring_engine.devices.values())
            stats = self.monitoring_engine.get_statistics()

            # Calculate additional stats
            total = len(devices)
            online = sum(1 for d in devices if d.current_status == 'online')
            offline = sum(1 for d in devices if d.current_status == 'offline')
            degraded = sum(1 for d in devices if d.current_status == 'degraded')

            stats.update({
                'total_devices': total,
                'online': online,
                'offline': offline,
                'degraded': degraded
            })

            if not devices:
                QMessageBox.warning(
                    self,
                    "Nessun Dato",
                    "Non ci sono dati da esportare."
                )
                return

            # Export
            success, message = ExportService.export_monitoring_report_to_csv(
                devices, stats, file_path
            )

            if success:
                QMessageBox.information(
                    self,
                    "Esportazione Completata",
                    f"Report esportato con successo!\n\n{message}"
                )
                logger.info(f"Monitoring report exported to {file_path}")
            else:
                QMessageBox.warning(
                    self,
                    "Errore Esportazione",
                    f"Errore durante l'esportazione:\n\n{message}"
                )

        except Exception as e:
            logger.error(f"Export report error: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Errore",
                f"Errore durante l'esportazione:\n\n{str(e)}"
            )

    def _toggle_fullscreen(self):
        """Toggle fullscreen mode"""
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def _show_settings(self):
        """Show settings dialog"""
        QMessageBox.information(self, "Settings", "Settings dialog - Coming soon!")

    def _show_ssh_terminal(self):
        """Show SSH terminal tab"""
        self.tab_widget.setCurrentWidget(self.ssh_terminal)

    def _show_about(self):
        """Show about dialog"""
        QMessageBox.about(self, "About PingMonitor",
                          "<h2>PingMonitor v2.3</h2>"
                          "<p>Professional Network Monitoring Solution with Advanced Features</p>"
                          "<p><b>Created by:</b> Fabrizio Cerchia</p>"
                          "<p><b>New Features:</b></p>"
                          "<ul>"
                          "<li>Intelligent email alerts with auto-recovery</li>"
                          "<li>SSH auto-reboot on web service failure</li>"
                          "<li>Integrated SSH terminal</li>"
                          "<li>Right-click context menu (Browser/PuTTY/SSH)</li>"
                          "<li>Automatic device import</li>"
                          "<li>Real-time monitoring with adaptive intervals</li>"
                          "</ul>")

    def quit_application(self):
        """Force quit application (from tray Exit)"""
        reply = QMessageBox.question(self, "Conferma Uscita",
                                     "Sei sicuro di voler uscire da PingMonitor?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            # Stop monitoring
            if self.monitoring_engine.running:
                self.monitoring_engine.stop()

            # Close SSH terminal
            if hasattr(self, 'ssh_terminal'):
                self.ssh_terminal.close()

            # Save window geometry
            geometry = {
                'width': self.width(),
                'height': self.height()
            }
            self.config.set('ui.window_geometry', geometry)
            self.config.save()

            # Hide tray icon
            if hasattr(self, 'tray_icon'):
                self.tray_icon.hide()

            # Quit application
            QApplication.quit()

    def closeEvent(self, event):
        """Handle window close event"""
        if self.config.get('application.minimize_to_tray', True):
            event.ignore()
            self.hide()
            if hasattr(self, 'tray_icon'):
                self.tray_icon.showMessage(
                    "PingMonitor",
                    "Applicazione minimizzata nella tray",
                    QSystemTrayIcon.MessageIcon.Information,
                    2000
                )
        else:
            reply = QMessageBox.question(self, "Conferma Uscita",
                                         "Sei sicuro di voler uscire?",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

            if reply == QMessageBox.StandardButton.Yes:
                # Stop monitoring
                if self.monitoring_engine.running:
                    self.monitoring_engine.stop()

                # Close SSH terminal
                if hasattr(self, 'ssh_terminal'):
                    self.ssh_terminal.close()

                # Save window geometry
                geometry = {
                    'width': self.width(),
                    'height': self.height()
                }
                self.config.set('ui.window_geometry', geometry)
                self.config.save()

                event.accept()
            else:
                event.ignore()

    def _on_recovery_success(self, device, message):
        """
        Callback when auto-recovery succeeds

        Args:
            device: Device that was recovered
            message: Recovery success message
        """
        try:
            logger.info(f"Recovery callback - SUCCESS: {device.name} ({device.ip_address})")
            self.aggregated_email_service.add_recovery_success(device)
        except Exception as e:
            logger.error(f"Error in recovery success callback: {e}")

    def _on_recovery_failure(self, device, message):
        """
        Callback when auto-recovery fails

        Args:
            device: Device that failed recovery
            message: Failure reason
        """
        try:
            logger.info(f"Recovery callback - FAILURE: {device.name} ({device.ip_address}) - {message}")
            self.aggregated_email_service.add_recovery_failure(device, message)
        except Exception as e:
            logger.error(f"Error in recovery failure callback: {e}")

    def _send_aggregated_email(self):
        """
        Send aggregated email with all recovery results (called every hour)
        """
        try:
            if self.aggregated_email_service.should_send_email():
                logger.info("Sending aggregated recovery email...")
                success, message = self.aggregated_email_service.send_aggregated_email()

                if success:
                    logger.info(f"Aggregated email sent successfully: {message}")
                    self.status_bar.showMessage(f"Email report inviata: {message}", 10000)
                else:
                    logger.error(f"Failed to send aggregated email: {message}")
            else:
                logger.debug("No pending recovery results to send")
        except Exception as e:
            logger.error(f"Error sending aggregated email: {e}", exc_info=True)
