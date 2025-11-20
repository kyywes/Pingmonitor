"""
PingMonitor Pro v2.0 - Settings Widget
Widget to configure application settings including email
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QGroupBox, QSpinBox, QCheckBox, QTextEdit,
    QMessageBox, QTabWidget, QFormLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class SettingsWidget(QWidget):
    """Settings configuration widget"""

    settings_changed = pyqtSignal(dict)

    def __init__(self, config_path=None):
        super().__init__()
        # Use user directory for config to avoid permission issues
        if config_path:
            self.config_path = config_path
        else:
            self.config_path = self._get_user_config_path()
        self.config = self._load_config()
        self._setup_ui()

    def _get_user_config_path(self):
        """Get config path in user directory (to avoid Program Files permission issues)"""
        import os

        # User config directory
        if os.name == 'nt':
            user_config_dir = Path(os.environ.get('APPDATA', '~')) / 'PingMonitorPro'
        else:
            user_config_dir = Path.home() / '.pingmonitor'

        user_config_dir.mkdir(parents=True, exist_ok=True)
        user_config_file = user_config_dir / 'config.json'

        # If user config doesn't exist, try to copy from installation directory
        if not user_config_file.exists():
            install_config = Path(__file__).parent.parent.parent / "config" / "config.json"
            if install_config.exists():
                import shutil
                try:
                    shutil.copy2(install_config, user_config_file)
                    logger.info(f"Copied config from {install_config} to {user_config_file}")
                except Exception as e:
                    logger.warning(f"Could not copy config: {e}")

        return user_config_file

    def _load_config(self):
        """Load configuration from file"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")

        return self._get_default_config()

    def _get_default_config(self):
        """Get default configuration"""
        return {
            "email": {
                "enabled": True,
                "smtp_server": "",
                "smtp_port": 465,
                "smtp_username": "",
                "smtp_password": "",
                "alert_recipients": []
            },
            "ssh": {
                "enabled": True,
                "username": "root",
                "password": "",
                "recovery_attempts": 3
            },
            "general": {
                "auto_start": True,
                "minimize_to_tray": True,
                "sound_alerts": False,
                "log_to_file": True,
                "check_interval": 15,  # Real-time monitoring (15 seconds)
                "timeout": 5
            }
        }

    def _setup_ui(self):
        """Setup UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)

        # Title
        title = QLabel("⚙️ Impostazioni")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #1e40af; margin-bottom: 10px;")
        layout.addWidget(title)

        # Config location info
        config_info = QLabel(f"📁 Config saved to: {self.config_path}")
        config_info.setStyleSheet("color: #666; font-size: 11px; margin-bottom: 10px;")
        config_info.setWordWrap(True)
        layout.addWidget(config_info)

        # Tabs for different settings categories
        tab_widget = QTabWidget()

        # Email Settings Tab
        email_tab = self._create_email_settings_tab()
        tab_widget.addTab(email_tab, "📧 Email Alerts")

        # SSH Settings Tab
        ssh_tab = self._create_ssh_settings_tab()
        tab_widget.addTab(ssh_tab, "🔐 SSH Configuration")

        # General Settings Tab
        general_tab = self._create_general_settings_tab()
        tab_widget.addTab(general_tab, "⚙️ General")

        layout.addWidget(tab_widget)

        # Buttons
        button_layout = QHBoxLayout()

        self.btn_save = QPushButton("💾 Save Settings")
        self.btn_save.clicked.connect(self._save_settings)
        self.btn_save.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: white;
                border: none;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        button_layout.addWidget(self.btn_save)

        self.btn_reset = QPushButton("🔄 Reset to Defaults")
        self.btn_reset.clicked.connect(self._reset_to_defaults)
        self.btn_reset.setStyleSheet("""
            QPushButton {
                background-color: #ef4444;
                color: white;
                border: none;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #dc2626;
            }
        """)
        button_layout.addWidget(self.btn_reset)

        button_layout.addStretch()
        layout.addLayout(button_layout)

        layout.addStretch()

    def _create_email_settings_tab(self):
        """Create email settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)

        # Email enabled
        self.email_enabled = QCheckBox("Enable Email Alerts")
        self.email_enabled.setChecked(self.config.get('email', {}).get('enabled', True))
        self.email_enabled.setStyleSheet("font-weight: bold; font-size: 13px;")
        layout.addWidget(self.email_enabled)

        # SMTP Settings
        smtp_group = QGroupBox("SMTP Server Configuration")
        smtp_layout = QFormLayout()

        self.smtp_server = QLineEdit()
        self.smtp_server.setPlaceholderText("e.g., smtp.gmail.com or smtps.aruba.it")
        self.smtp_server.setText(self.config.get('email', {}).get('smtp_server', ''))
        smtp_layout.addRow("SMTP Server:", self.smtp_server)

        self.smtp_port = QSpinBox()
        self.smtp_port.setRange(1, 65535)
        self.smtp_port.setValue(self.config.get('email', {}).get('smtp_port', 465))
        smtp_layout.addRow("SMTP Port:", self.smtp_port)

        port_hint = QLabel("Common ports: 465 (SSL), 587 (TLS), 25 (Plain)")
        port_hint.setStyleSheet("color: #666; font-size: 11px;")
        smtp_layout.addRow("", port_hint)

        smtp_group.setLayout(smtp_layout)
        layout.addWidget(smtp_group)

        # Authentication
        auth_group = QGroupBox("SMTP Authentication")
        auth_layout = QFormLayout()

        self.smtp_username = QLineEdit()
        self.smtp_username.setPlaceholderText("Usually your email address")
        self.smtp_username.setText(self.config.get('email', {}).get('smtp_username', ''))
        auth_layout.addRow("Username / Email:", self.smtp_username)

        self.smtp_password = QLineEdit()
        self.smtp_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.smtp_password.setPlaceholderText("Enter SMTP password")
        self.smtp_password.setText(self.config.get('email', {}).get('smtp_password', ''))
        auth_layout.addRow("Password:", self.smtp_password)

        show_password = QCheckBox("Show password")
        show_password.stateChanged.connect(
            lambda state: self.smtp_password.setEchoMode(
                QLineEdit.EchoMode.Normal if state else QLineEdit.EchoMode.Password
            )
        )
        auth_layout.addRow("", show_password)

        auth_group.setLayout(auth_layout)
        layout.addWidget(auth_group)

        # Recipients
        recipients_group = QGroupBox("Alert Recipients")
        recipients_layout = QVBoxLayout()

        recipients_label = QLabel("Enter email addresses (one per line):")
        recipients_layout.addWidget(recipients_label)

        self.alert_recipients = QTextEdit()
        self.alert_recipients.setMaximumHeight(100)
        self.alert_recipients.setPlaceholderText("admin@example.com\nalerts@example.com")

        # Load recipients
        recipients = self.config.get('email', {}).get('alert_recipients', [])
        if isinstance(recipients, list):
            self.alert_recipients.setText('\n'.join(recipients))
        elif isinstance(recipients, str):
            self.alert_recipients.setText(recipients)

        recipients_layout.addWidget(self.alert_recipients)

        recipients_group.setLayout(recipients_layout)
        layout.addWidget(recipients_group)

        # Additional options
        options_group = QGroupBox("Alert Options")
        options_layout = QVBoxLayout()

        self.alert_on_down = QCheckBox("Send alert when device goes DOWN")
        self.alert_on_down.setChecked(self.config.get('email', {}).get('alert_on_down', True))
        options_layout.addWidget(self.alert_on_down)

        self.alert_on_up = QCheckBox("Send alert when device comes back UP")
        self.alert_on_up.setChecked(self.config.get('email', {}).get('alert_on_up', True))
        options_layout.addWidget(self.alert_on_up)

        options_group.setLayout(options_layout)
        layout.addWidget(options_group)

        layout.addStretch()
        return tab

    def _create_ssh_settings_tab(self):
        """Create SSH settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)

        # SSH enabled
        self.ssh_enabled = QCheckBox("Enable SSH Auto-Recovery")
        self.ssh_enabled.setChecked(self.config.get('ssh', {}).get('enabled', True))
        self.ssh_enabled.setStyleSheet("font-weight: bold; font-size: 13px;")
        layout.addWidget(self.ssh_enabled)

        info_label = QLabel(
            "SSH auto-recovery will automatically connect to devices and execute 'reboot' "
            "when a device is unreachable but ping is working."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(info_label)

        # SSH Credentials
        cred_group = QGroupBox("SSH Credentials")
        cred_layout = QFormLayout()

        self.ssh_username = QLineEdit()
        self.ssh_username.setPlaceholderText("e.g., root or admin")
        self.ssh_username.setText(self.config.get('ssh', {}).get('username', 'root'))
        cred_layout.addRow("Username:", self.ssh_username)

        self.ssh_password = QLineEdit()
        self.ssh_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.ssh_password.setPlaceholderText("Enter SSH password")
        self.ssh_password.setText(self.config.get('ssh', {}).get('password', ''))
        cred_layout.addRow("Password:", self.ssh_password)

        show_ssh_password = QCheckBox("Show password")
        show_ssh_password.stateChanged.connect(
            lambda state: self.ssh_password.setEchoMode(
                QLineEdit.EchoMode.Normal if state else QLineEdit.EchoMode.Password
            )
        )
        cred_layout.addRow("", show_ssh_password)

        cred_group.setLayout(cred_layout)
        layout.addWidget(cred_group)

        # Recovery Settings
        recovery_group = QGroupBox("Recovery Settings")
        recovery_layout = QFormLayout()

        self.recovery_attempts = QSpinBox()
        self.recovery_attempts.setRange(1, 10)
        self.recovery_attempts.setValue(self.config.get('ssh', {}).get('recovery_attempts', 3))
        recovery_layout.addRow("Max Recovery Attempts:", self.recovery_attempts)

        recovery_hint = QLabel("Number of automatic reboot attempts before sending email alert")
        recovery_hint.setStyleSheet("color: #666; font-size: 11px;")
        recovery_layout.addRow("", recovery_hint)

        recovery_group.setLayout(recovery_layout)
        layout.addWidget(recovery_group)

        layout.addStretch()
        return tab

    def _create_general_settings_tab(self):
        """Create general settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)

        # Startup
        startup_group = QGroupBox("Startup Options")
        startup_layout = QVBoxLayout()

        self.auto_start = QCheckBox("Start monitoring automatically when application launches")
        self.auto_start.setChecked(self.config.get('general', {}).get('auto_start', True))
        startup_layout.addWidget(self.auto_start)

        self.minimize_to_tray = QCheckBox("Minimize to system tray instead of closing")
        self.minimize_to_tray.setChecked(self.config.get('general', {}).get('minimize_to_tray', True))
        startup_layout.addWidget(self.minimize_to_tray)

        startup_group.setLayout(startup_layout)
        layout.addWidget(startup_group)

        # Monitoring
        monitoring_group = QGroupBox("Monitoring Settings")
        monitoring_layout = QFormLayout()

        self.check_interval = QSpinBox()
        self.check_interval.setRange(10, 86400)  # Allow real-time monitoring (10s minimum)
        self.check_interval.setSuffix(" seconds")
        self.check_interval.setValue(self.config.get('general', {}).get('check_interval', 15))
        monitoring_layout.addRow("Check Interval:", self.check_interval)

        interval_hint = QLabel("Real-time: 10-15s | Normale: 60s (1 min) | Lento: 300s (5 min)")
        interval_hint.setStyleSheet("color: #666; font-size: 11px;")
        monitoring_layout.addRow("", interval_hint)

        self.timeout = QSpinBox()
        self.timeout.setRange(1, 60)
        self.timeout.setSuffix(" seconds")
        self.timeout.setValue(self.config.get('general', {}).get('timeout', 5))
        monitoring_layout.addRow("Check Timeout:", self.timeout)

        monitoring_group.setLayout(monitoring_layout)
        layout.addWidget(monitoring_group)

        # Notifications
        notifications_group = QGroupBox("Notifications")
        notifications_layout = QVBoxLayout()

        self.sound_alerts = QCheckBox("Play sound on alerts")
        self.sound_alerts.setChecked(self.config.get('general', {}).get('sound_alerts', False))
        notifications_layout.addWidget(self.sound_alerts)

        self.log_to_file = QCheckBox("Save logs to file")
        self.log_to_file.setChecked(self.config.get('general', {}).get('log_to_file', True))
        notifications_layout.addWidget(self.log_to_file)

        notifications_group.setLayout(notifications_layout)
        layout.addWidget(notifications_group)

        layout.addStretch()
        return tab

    def _save_settings(self):
        """Save settings to file"""
        try:
            # Collect all settings
            new_config = {
                "email": {
                    "enabled": self.email_enabled.isChecked(),
                    "smtp_server": self.smtp_server.text().strip(),
                    "smtp_port": self.smtp_port.value(),
                    "smtp_username": self.smtp_username.text().strip(),
                    "smtp_password": self.smtp_password.text(),
                    "alert_recipients": [
                        line.strip() for line in self.alert_recipients.toPlainText().split('\n')
                        if line.strip()
                    ],
                    "alert_on_down": self.alert_on_down.isChecked(),
                    "alert_on_up": self.alert_on_up.isChecked()
                },
                "ssh": {
                    "enabled": self.ssh_enabled.isChecked(),
                    "username": self.ssh_username.text().strip(),
                    "password": self.ssh_password.text(),
                    "recovery_attempts": self.recovery_attempts.value()
                },
                "general": {
                    "auto_start": self.auto_start.isChecked(),
                    "minimize_to_tray": self.minimize_to_tray.isChecked(),
                    "sound_alerts": self.sound_alerts.isChecked(),
                    "log_to_file": self.log_to_file.isChecked(),
                    "check_interval": self.check_interval.value(),
                    "timeout": self.timeout.value()
                }
            }

            # Merge with existing devices config
            if 'devices' in self.config:
                new_config['devices'] = self.config['devices']

            # Save to file
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(new_config, f, indent=4)

            self.config = new_config
            self.settings_changed.emit(new_config)

            QMessageBox.information(
                self,
                "Settings Saved",
                "Settings have been saved successfully!\n\n"
                "Some changes may require restarting the application to take effect."
            )

            logger.info("Settings saved successfully")

        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
            QMessageBox.critical(
                self,
                "Save Failed",
                f"Failed to save settings:\n{str(e)}"
            )

    def _reset_to_defaults(self):
        """Reset settings to defaults"""
        reply = QMessageBox.question(
            self,
            "Reset to Defaults",
            "Are you sure you want to reset all settings to default values?\n\n"
            "This will NOT delete your device list.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            defaults = self._get_default_config()

            # Email
            self.email_enabled.setChecked(defaults['email']['enabled'])
            self.smtp_server.setText(defaults['email']['smtp_server'])
            self.smtp_port.setValue(defaults['email']['smtp_port'])
            self.smtp_username.setText(defaults['email']['smtp_username'])
            self.smtp_password.setText(defaults['email']['smtp_password'])
            self.alert_recipients.setText('\n'.join(defaults['email']['alert_recipients']))

            # SSH
            self.ssh_enabled.setChecked(defaults['ssh']['enabled'])
            self.ssh_username.setText(defaults['ssh']['username'])
            self.ssh_password.setText(defaults['ssh']['password'])
            self.recovery_attempts.setValue(defaults['ssh']['recovery_attempts'])

            # General
            self.auto_start.setChecked(defaults['general']['auto_start'])
            self.minimize_to_tray.setChecked(defaults['general']['minimize_to_tray'])
            self.sound_alerts.setChecked(defaults['general']['sound_alerts'])
            self.log_to_file.setChecked(defaults['general']['log_to_file'])
            self.check_interval.setValue(defaults['general']['check_interval'])
            self.timeout.setValue(defaults['general']['timeout'])

            QMessageBox.information(
                self,
                "Reset Complete",
                "Settings have been reset to default values.\n\n"
                "Click 'Save Settings' to apply the changes."
            )
