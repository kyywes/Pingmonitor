"""
Telegram Test Widget - Test and configure Telegram notifications
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QTextEdit, QGroupBox, QMessageBox
)
from PyQt6.QtCore import Qt
import logging

from ..services.telegram_service import TelegramService

logger = logging.getLogger(__name__)


class TelegramTestWidget(QWidget):
    """Widget for testing Telegram notifications"""

    def __init__(self, telegram_config: dict = None):
        super().__init__()
        self.telegram_config = telegram_config or {}
        self.telegram_service = None
        self._setup_ui()

    def _setup_ui(self):
        """Setup UI"""
        layout = QVBoxLayout(self)

        # Title
        title = QLabel("🤖 Telegram Bot Configuration & Test")
        title.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            color: #2563eb;
            padding: 15px;
        """)
        layout.addWidget(title)

        # Instructions
        instructions = QLabel(
            "Configure your Telegram Bot to receive monitoring alerts.\n\n"
            "Setup Instructions:\n"
            "1. Open Telegram and search for @BotFather\n"
            "2. Send /newbot and follow the instructions\n"
            "3. Copy the Bot Token provided by BotFather\n"
            "4. Start a chat with your bot\n"
            "5. Get your Chat ID from @userinfobot or similar\n"
            "6. Enter the credentials below and test the connection"
        )
        instructions.setStyleSheet("""
            background-color: rgba(59, 130, 246, 0.1);
            border-left: 4px solid #3b82f6;
            padding: 15px;
            border-radius: 5px;
            color: #e2e8f0;
            line-height: 1.6;
        """)
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        # Configuration group
        config_group = QGroupBox("Bot Configuration")
        config_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid rgba(148, 163, 184, 0.3);
                border-radius: 8px;
                margin-top: 10px;
                padding: 20px;
                background-color: rgba(30, 41, 59, 0.5);
            }
            QGroupBox::title {
                color: #60a5fa;
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        config_layout = QVBoxLayout()

        # Bot Token
        token_layout = QHBoxLayout()
        token_label = QLabel("Bot Token:")
        token_label.setMinimumWidth(120)
        token_label.setStyleSheet("font-weight: 600; color: #94a3b8;")
        self.token_input = QLineEdit()
        self.token_input.setPlaceholderText("123456789:ABCdefGHIjklMNOpqrsTUVwxyz")
        self.token_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.token_input.setText(self.telegram_config.get('bot_token', ''))
        self.token_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 1px solid rgba(148, 163, 184, 0.3);
                border-radius: 5px;
                background-color: rgba(15, 20, 25, 0.6);
                color: #e2e8f0;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 2px solid #3b82f6;
            }
        """)

        show_token_btn = QPushButton("👁")
        show_token_btn.setFixedWidth(40)
        show_token_btn.clicked.connect(self._toggle_token_visibility)
        show_token_btn.setStyleSheet("""
            QPushButton {
                background-color: #6366f1;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #4f46e5;
            }
        """)

        token_layout.addWidget(token_label)
        token_layout.addWidget(self.token_input)
        token_layout.addWidget(show_token_btn)
        config_layout.addLayout(token_layout)

        # Chat ID
        chat_layout = QHBoxLayout()
        chat_label = QLabel("Chat ID:")
        chat_label.setMinimumWidth(120)
        chat_label.setStyleSheet("font-weight: 600; color: #94a3b8;")
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("123456789 or -100123456789")
        self.chat_input.setText(self.telegram_config.get('chat_id', ''))
        self.chat_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 1px solid rgba(148, 163, 184, 0.3);
                border-radius: 5px;
                background-color: rgba(15, 20, 25, 0.6);
                color: #e2e8f0;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 2px solid #3b82f6;
            }
        """)
        chat_layout.addWidget(chat_label)
        chat_layout.addWidget(self.chat_input)
        config_layout.addLayout(chat_layout)

        config_group.setLayout(config_layout)
        layout.addWidget(config_group)

        # Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)

        self.btn_test = QPushButton("🔬 Test Connection")
        self.btn_test.clicked.connect(self._test_connection)
        self.btn_test.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                padding: 15px 30px;
                font-size: 15px;
                font-weight: bold;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
        """)

        self.btn_send_test = QPushButton("📤 Send Test Alert")
        self.btn_send_test.clicked.connect(self._send_test_alert)
        self.btn_send_test.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: white;
                border: none;
                padding: 15px 30px;
                font-size: 15px;
                font-weight: bold;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)

        self.btn_save = QPushButton("💾 Save Configuration")
        self.btn_save.clicked.connect(self._save_config)
        self.btn_save.setStyleSheet("""
            QPushButton {
                background-color: #8b5cf6;
                color: white;
                border: none;
                padding: 15px 30px;
                font-size: 15px;
                font-weight: bold;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #7c3aed;
            }
        """)

        buttons_layout.addWidget(self.btn_test)
        buttons_layout.addWidget(self.btn_send_test)
        buttons_layout.addWidget(self.btn_save)
        buttons_layout.addStretch()

        layout.addLayout(buttons_layout)

        # Output area
        output_label = QLabel("📋 Output:")
        output_label.setStyleSheet("font-weight: bold; color: #60a5fa; margin-top: 15px;")
        layout.addWidget(output_label)

        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setPlaceholderText("Test results will appear here...")
        self.output_text.setStyleSheet("""
            QTextEdit {
                background-color: rgba(15, 20, 25, 0.8);
                color: #e2e8f0;
                border: 1px solid rgba(148, 163, 184, 0.3);
                border-radius: 8px;
                padding: 15px;
                font-family: 'Courier New', monospace;
                font-size: 12px;
            }
        """)
        layout.addWidget(self.output_text)

        layout.addStretch()

    def _toggle_token_visibility(self):
        """Toggle token visibility"""
        if self.token_input.echoMode() == QLineEdit.EchoMode.Password:
            self.token_input.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.token_input.setEchoMode(QLineEdit.EchoMode.Password)

    def _get_telegram_service(self) -> TelegramService:
        """Get or create Telegram service with current credentials"""
        bot_token = self.token_input.text().strip()
        chat_id = self.chat_input.text().strip()

        if not bot_token or not chat_id:
            raise ValueError("Please enter both Bot Token and Chat ID")

        if not self.telegram_service:
            self.telegram_service = TelegramService()

        self.telegram_service.set_credentials(bot_token, chat_id)
        return self.telegram_service

    def _test_connection(self):
        """Test Telegram connection"""
        self.output_text.append("🔄 Testing Telegram connection...\n")
        logger.info("Testing Telegram connection")

        try:
            service = self._get_telegram_service()
            success, message = service.test_connection()

            if success:
                self.output_text.append(f"✅ SUCCESS: {message}\n")
                self.output_text.append("Check your Telegram chat for the test message!\n")
                QMessageBox.information(
                    self,
                    "Connection Successful",
                    f"Successfully connected to Telegram!\n\n{message}\n\nCheck your Telegram chat for the test message."
                )
            else:
                self.output_text.append(f"❌ ERROR: {message}\n")
                QMessageBox.warning(
                    self,
                    "Connection Failed",
                    f"Failed to connect to Telegram:\n\n{message}"
                )

        except ValueError as e:
            self.output_text.append(f"⚠️ VALIDATION ERROR: {str(e)}\n")
            QMessageBox.warning(self, "Validation Error", str(e))
        except Exception as e:
            self.output_text.append(f"❌ EXCEPTION: {str(e)}\n")
            logger.error(f"Test connection error: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Error",
                f"An error occurred:\n\n{str(e)}"
            )

    def _send_test_alert(self):
        """Send a test alert message"""
        self.output_text.append("📤 Sending test alert...\n")
        logger.info("Sending test Telegram alert")

        try:
            service = self._get_telegram_service()

            # Test device info
            device_info = {
                'name': 'Test Device',
                'ip': '192.168.1.100',
                'location': 'Test Location',
                'port': '80'
            }

            recovery_info = {
                'attempts': 2
            }

            success = service.send_alert(device_info, "critical", recovery_info)

            if success:
                self.output_text.append("✅ Test alert sent successfully!\n")
                self.output_text.append("Check your Telegram chat for the alert message.\n")
                QMessageBox.information(
                    self,
                    "Alert Sent",
                    "Test alert sent successfully!\n\nCheck your Telegram chat."
                )
            else:
                self.output_text.append("❌ Failed to send test alert\n")
                QMessageBox.warning(
                    self,
                    "Send Failed",
                    "Failed to send test alert. Check the output for details."
                )

        except ValueError as e:
            self.output_text.append(f"⚠️ VALIDATION ERROR: {str(e)}\n")
            QMessageBox.warning(self, "Validation Error", str(e))
        except Exception as e:
            self.output_text.append(f"❌ EXCEPTION: {str(e)}\n")
            logger.error(f"Send test alert error: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Error",
                f"An error occurred:\n\n{str(e)}"
            )

    def _save_config(self):
        """Save Telegram configuration"""
        bot_token = self.token_input.text().strip()
        chat_id = self.chat_input.text().strip()

        if not bot_token or not chat_id:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Please enter both Bot Token and Chat ID before saving."
            )
            return

        self.telegram_config['bot_token'] = bot_token
        self.telegram_config['chat_id'] = chat_id
        self.telegram_config['enabled'] = True

        self.output_text.append("💾 Configuration saved successfully!\n")
        QMessageBox.information(
            self,
            "Configuration Saved",
            "Telegram configuration saved successfully!\n\n"
            "The settings will be used for monitoring alerts."
        )
        logger.info("Telegram configuration saved")
