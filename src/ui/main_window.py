"""
PingMonitor Pro v2.0 - Main Window
Modern PyQt6 UI with professional design
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QSystemTrayIcon, QMenu, QMessageBox, QStatusBar
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QBrush, QColor, QAction
import logging

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Main application window"""

    # Signals
    status_update_signal = pyqtSignal(dict)

    def __init__(self, config, monitoring_engine):
        """
        Initialize main window

        Args:
            config: ConfigManager instance
            monitoring_engine: MonitoringEngine instance
        """
        super().__init__()

        self.config = config
        self.monitoring_engine = monitoring_engine

        # Setup UI
        self._setup_window()
        self._create_menu_bar()
        self._create_toolbar()
        self._create_central_widget()
        self._create_status_bar()
        self._create_system_tray()

        # Setup monitoring callbacks
        self.monitoring_engine.register_callback('on_status_change', self._on_device_status_change)
        self.monitoring_engine.register_callback('on_check_complete', self._on_check_complete)

        # Setup update timer for UI refresh
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_ui)
        self.update_timer.start(1000)  # Update every second

        logger.info("Main window initialized")

    def _setup_window(self):
        """Setup main window properties"""
        self.setWindowTitle("PingMonitor Pro v2.0 - by Fabrizio Cerchia")

        # Window geometry
        geometry = self.config.get('ui.window_geometry', {})
        width = geometry.get('width', 1400)
        height = geometry.get('height', 900)

        self.resize(width, height)

        # Center window on screen
        screen = self.screen().geometry()
        x = (screen.width() - width) // 2
        y = (screen.height() - height) // 2
        self.move(x, y)

    def _create_menu_bar(self):
        """Create menu bar"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        export_action = QAction("&Export Configuration", self)
        export_action.setShortcut("Ctrl+E")
        export_action.triggered.connect(self._export_config)
        file_menu.addAction(export_action)

        import_action = QAction("&Import Configuration", self)
        import_action.setShortcut("Ctrl+I")
        import_action.triggered.connect(self._import_config)
        file_menu.addAction(import_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # View menu
        view_menu = menubar.addMenu("&View")

        fullscreen_action = QAction("&Fullscreen", self)
        fullscreen_action.setShortcut("F11")
        fullscreen_action.triggered.connect(self._toggle_fullscreen)
        view_menu.addAction(fullscreen_action)

        # Tools menu
        tools_menu = menubar.addMenu("&Tools")

        settings_action = QAction("&Settings", self)
        settings_action.setShortcut("Ctrl+,")
        settings_action.triggered.connect(self._show_settings)
        tools_menu.addAction(settings_action)

        # Help menu
        help_menu = menubar.addMenu("&Help")

        about_action = QAction("&About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _create_toolbar(self):
        """Create toolbar"""
        toolbar = self.addToolBar("Main Toolbar")
        toolbar.setMovable(False)

        # Start button
        self.btn_start = QPushButton("▶ Start Monitoring")
        self.btn_start.clicked.connect(self.start_monitoring)
        self.btn_start.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #059669;
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
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #dc2626;
            }
            QPushButton:disabled {
                background-color: #6b7280;
                color: #9ca3af;
            }
        """)
        toolbar.addWidget(self.btn_stop)

        toolbar.addSeparator()

        # Refresh button
        btn_refresh = QPushButton("🔄 Refresh")
        btn_refresh.clicked.connect(self._refresh_data)
        toolbar.addWidget(btn_refresh)

        # Add device button
        btn_add_device = QPushButton("➕ Add Device")
        btn_add_device.clicked.connect(self._add_device)
        toolbar.addWidget(btn_add_device)

    def _create_central_widget(self):
        """Create central widget with tabs"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        # Header with statistics
        header = self._create_header()
        layout.addWidget(header)

        # Tab widget
        self.tab_widget = QTabWidget()

        # Monitoring tab
        self.monitoring_tab = self._create_monitoring_tab()
        self.tab_widget.addTab(self.monitoring_tab, "📊 Monitoring")

        # Devices tab
        self.devices_tab = self._create_devices_tab()
        self.tab_widget.addTab(self.devices_tab, "🖥 Devices")

        # Statistics tab
        self.statistics_tab = self._create_statistics_tab()
        self.tab_widget.addTab(self.statistics_tab, "📈 Statistics")

        # Logs tab
        self.logs_tab = self._create_logs_tab()
        self.tab_widget.addTab(self.logs_tab, "📝 Logs")

        layout.addWidget(self.tab_widget)

    def _create_header(self):
        """Create header widget with stats"""
        header = QWidget()
        header.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1e3a8a, stop:1 #2563eb);
                border-radius: 10px;
                padding: 15px;
            }
        """)

        layout = QHBoxLayout(header)

        # Title
        title = QLabel("🌐 PingMonitor Pro")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: white;")
        layout.addWidget(title)

        layout.addStretch()

        # Stats
        self.lbl_total = QLabel("Total: 0")
        self.lbl_online = QLabel("🟢 Online: 0")
        self.lbl_offline = QLabel("🔴 Offline: 0")

        for lbl in [self.lbl_total, self.lbl_online, self.lbl_offline]:
            lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: white; margin: 0 10px;")
            layout.addWidget(lbl)

        return header

    def _create_monitoring_tab(self):
        """Create monitoring tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Monitoring table
        self.monitoring_table = QTableWidget()
        self.monitoring_table.setColumnCount(8)
        self.monitoring_table.setHorizontalHeaderLabels([
            "Status", "IP Address", "Name", "Type",
            "Response (ms)", "Last Check", "Uptime %", "Actions"
        ])

        # Table styling
        self.monitoring_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.monitoring_table.setAlternatingRowColors(True)
        self.monitoring_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        layout.addWidget(self.monitoring_table)

        return widget

    def _create_devices_tab(self):
        """Create devices management tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        label = QLabel("Device Management")
        label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(label)

        # TODO: Add device management form

        return widget

    def _create_statistics_tab(self):
        """Create statistics tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        label = QLabel("Statistics & Analytics")
        label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(label)

        # TODO: Add charts and statistics

        return widget

    def _create_logs_tab(self):
        """Create logs tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        label = QLabel("System Logs")
        label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(label)

        # TODO: Add log viewer

        return widget

    def _create_status_bar(self):
        """Create status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

    def _create_system_tray(self):
        """Create system tray icon"""
        if self.config.get('application.minimize_to_tray', True):
            self.tray_icon = QSystemTrayIcon(self)

            # Create icon
            pixmap = QPixmap(64, 64)
            pixmap.fill(Qt.GlobalColor.transparent)
            painter = QPainter(pixmap)
            painter.setBrush(QBrush(QColor("#2563eb")))
            painter.drawEllipse(0, 0, 64, 64)
            painter.end()

            self.tray_icon.setIcon(QIcon(pixmap))
            self.tray_icon.setToolTip("PingMonitor Pro")

            # Create menu
            tray_menu = QMenu()
            show_action = QAction("Show", self)
            show_action.triggered.connect(self.show)
            tray_menu.addAction(show_action)

            quit_action = QAction("Exit", self)
            quit_action.triggered.connect(self.close)
            tray_menu.addAction(quit_action)

            self.tray_icon.setContextMenu(tray_menu)
            self.tray_icon.show()

    def start_monitoring(self):
        """Start monitoring"""
        try:
            self.monitoring_engine.start()
            self.btn_start.setEnabled(False)
            self.btn_stop.setEnabled(True)
            self.status_bar.showMessage("🟢 Monitoring Active")
            logger.info("Monitoring started")
        except Exception as e:
            logger.error(f"Failed to start monitoring: {e}")
            QMessageBox.critical(self, "Error", f"Failed to start monitoring:\n{str(e)}")

    def stop_monitoring(self):
        """Stop monitoring"""
        try:
            self.monitoring_engine.stop()
            self.btn_start.setEnabled(True)
            self.btn_stop.setEnabled(False)
            self.status_bar.showMessage("🔴 Monitoring Stopped")
            logger.info("Monitoring stopped")
        except Exception as e:
            logger.error(f"Failed to stop monitoring: {e}")

    def _update_ui(self):
        """Update UI with latest data"""
        try:
            # Update header stats
            total = len(self.monitoring_engine.devices)
            online = sum(1 for d in self.monitoring_engine.devices.values() if d.current_status == 'online')
            offline = sum(1 for d in self.monitoring_engine.devices.values() if d.current_status == 'offline')

            self.lbl_total.setText(f"Total: {total}")
            self.lbl_online.setText(f"🟢 Online: {online}")
            self.lbl_offline.setText(f"🔴 Offline: {offline}")

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
                status_icon = "🟢" if device.current_status == 'online' else "🔴"
                self.monitoring_table.setItem(row, 0, QTableWidgetItem(f"{status_icon} {device.current_status.upper()}"))

                # IP Address
                self.monitoring_table.setItem(row, 1, QTableWidgetItem(device.ip_address))

                # Name
                self.monitoring_table.setItem(row, 2, QTableWidgetItem(device.name))

                # Type
                self.monitoring_table.setItem(row, 3, QTableWidgetItem(device.device_type))

                # Response time
                self.monitoring_table.setItem(row, 4, QTableWidgetItem(f"{device.response_time:.1f}"))

                # Last check
                last_check = device.last_check_time if device.last_check_time else "Never"
                self.monitoring_table.setItem(row, 5, QTableWidgetItem(str(last_check)))

                # Uptime
                self.monitoring_table.setItem(row, 6, QTableWidgetItem(f"{device.uptime_percentage:.1f}%"))

                # Actions
                self.monitoring_table.setItem(row, 7, QTableWidgetItem("..."))

        except Exception as e:
            logger.error(f"Error updating monitoring table: {e}")

    def _on_device_status_change(self, device, old_status, new_status):
        """Handle device status change"""
        logger.info(f"Device {device.name} status changed: {old_status} -> {new_status}")
        # Update UI will be called by timer

    def _on_check_complete(self, device, result):
        """Handle check completion"""
        # Update UI will be called by timer
        pass

    def _refresh_data(self):
        """Refresh data"""
        self._update_ui()

    def _add_device(self):
        """Show add device dialog"""
        QMessageBox.information(self, "Add Device", "Add device dialog - Coming soon!")

    def _export_config(self):
        """Export configuration"""
        QMessageBox.information(self, "Export", "Export configuration - Coming soon!")

    def _import_config(self):
        """Import configuration"""
        QMessageBox.information(self, "Import", "Import configuration - Coming soon!")

    def _toggle_fullscreen(self):
        """Toggle fullscreen mode"""
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def _show_settings(self):
        """Show settings dialog"""
        QMessageBox.information(self, "Settings", "Settings dialog - Coming soon!")

    def _show_about(self):
        """Show about dialog"""
        QMessageBox.about(self, "About PingMonitor Pro",
                          "<h2>PingMonitor Pro v2.0</h2>"
                          "<p>Professional Network Monitoring Solution</p>"
                          "<p><b>Created by:</b> Fabrizio Cerchia</p>"
                          "<p><b>Features:</b></p>"
                          "<ul>"
                          "<li>Multi-protocol monitoring (Ping, HTTP, SSH, DNS)</li>"
                          "<li>Secure configuration with AES-256 encryption</li>"
                          "<li>Real-time alerts and notifications</li>"
                          "<li>Advanced statistics and analytics</li>"
                          "<li>REST API support</li>"
                          "<li>Plugin system</li>"
                          "</ul>")

    def closeEvent(self, event):
        """Handle window close event"""
        if self.config.get('application.minimize_to_tray', True):
            event.ignore()
            self.hide()
            if hasattr(self, 'tray_icon'):
                self.tray_icon.showMessage(
                    "PingMonitor Pro",
                    "Application minimized to tray",
                    QSystemTrayIcon.MessageIcon.Information,
                    2000
                )
        else:
            reply = QMessageBox.question(self, "Confirm Exit",
                                         "Are you sure you want to exit?",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

            if reply == QMessageBox.StandardButton.Yes:
                # Stop monitoring
                if self.monitoring_engine.running:
                    self.monitoring_engine.stop()

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
