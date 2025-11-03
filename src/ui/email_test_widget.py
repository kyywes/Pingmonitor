"""
PingMonitor Pro v2.0 - Email Alert Test Widget
Widget to test email alert functionality
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTextEdit, QGroupBox, QComboBox, QMessageBox,
    QProgressBar
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class EmailTestWorker(QThread):
    """Worker thread for email testing"""
    result = pyqtSignal(bool, str)
    progress = pyqtSignal(str)

    def __init__(self, email_config, test_type, test_recipient=None):
        super().__init__()
        self.email_config = email_config
        self.test_type = test_type
        self.test_recipient = test_recipient

    def run(self):
        try:
            self.progress.emit("Connecting to SMTP server...")

            # SMTP connection
            smtp_server = self.email_config.get('smtp_server', '')
            smtp_port = self.email_config.get('smtp_port', 587)
            smtp_username = self.email_config.get('username', self.email_config.get('smtp_username', ''))
            smtp_password = self.email_config.get('password', self.email_config.get('smtp_password', ''))
            from_email = self.email_config.get('from_email', smtp_username)
            alert_email = self.email_config.get('alert_email', '')

            if not smtp_server or not smtp_username:
                self.result.emit(False, "Email configuration missing. Please check config.json")
                return

            # Parse multiple recipients (comma-separated)
            recipients = [r.strip() for r in alert_email.split(',') if r.strip()]
            to_email = self.test_recipient or (recipients[0] if recipients else '')

            if not to_email:
                self.result.emit(False, "No recipient email configured. Please check config.json")
                return

            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = from_email
            msg['To'] = to_email

            if self.test_type == 'simple':
                msg['Subject'] = "PingMonitor Pro - Email di Test"
                body = self._create_simple_test_email()
            else:
                msg['Subject'] = "[TEST] PingMonitor Pro - Test Allerta Critica"
                body = self._create_full_alert_test()

            msg.attach(MIMEText(body, 'html'))

            self.progress.emit(f"Sending email to {msg['To']}...")

            # Send email using STARTTLS for port 587
            if smtp_port == 465:
                # Use SSL for port 465
                with smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=30) as server:
                    server.login(smtp_username, smtp_password)
                    server.send_message(msg)
            else:
                # Use STARTTLS for port 587 (and others)
                with smtplib.SMTP(smtp_server, smtp_port, timeout=30) as server:
                    server.starttls()
                    server.login(smtp_username, smtp_password)
                    server.send_message(msg)

            self.progress.emit("Email sent successfully!")
            self.result.emit(True, f"✅ Email sent successfully to {msg['To']}")

        except smtplib.SMTPAuthenticationError:
            self.result.emit(False, "❌ SMTP Authentication failed. Check username/password in config.json")
        except smtplib.SMTPException as e:
            self.result.emit(False, f"❌ SMTP Error: {str(e)}")
        except Exception as e:
            self.result.emit(False, f"❌ Failed to send email: {str(e)}")

    def _create_simple_test_email(self):
        """Create simple test email (Italian)"""
        return f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; text-align: center; }}
        .content {{ padding: 20px 0; }}
        .success {{ color: #10b981; font-weight: bold; font-size: 18px; text-align: center; margin: 20px 0; }}
        .footer {{ text-align: center; color: #666; font-size: 12px; margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>✅ Test Email Riuscito</h1>
        </div>
        <div class="content">
            <p class="success">Sistema Email PingMonitor Pro Funzionante!</p>
            <p>Questa è una email di test da <strong>PingMonitor Pro v2.3</strong>.</p>
            <p>Se hai ricevuto questa email, significa che il sistema di allerte email è configurato correttamente.</p>
            <p><strong>Dettagli Test:</strong></p>
            <ul>
                <li>Ora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</li>
                <li>Tipo: Test Semplice</li>
                <li>Stato: ✅ Funzionante</li>
            </ul>
        </div>
        <div class="footer">
            PingMonitor Pro v2.3 - Monitoraggio di Rete Professionale<br>
            by Fabrizio Cerchia
        </div>
    </div>
</body>
</html>
"""

    def _create_full_alert_test(self):
        """Create full alert test email (simulates real alert) - Italian"""
        return f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); color: white; padding: 20px; border-radius: 10px; }}
        .alert-icon {{ font-size: 48px; text-align: center; margin: 10px 0; }}
        .device-info {{ background-color: #fef2f2; border-left: 4px solid #ef4444; padding: 15px; margin: 20px 0; border-radius: 5px; }}
        .recovery-info {{ background-color: #fff7ed; border-left: 4px solid #f59e0b; padding: 15px; margin: 20px 0; border-radius: 5px; }}
        .action-required {{ background-color: #fee2e2; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .button {{ display: inline-block; background-color: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; margin: 5px; }}
        .footer {{ text-align: center; color: #666; font-size: 12px; margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="alert-icon">⚠️</div>
            <h1>[TEST] ALLERTA CRITICA</h1>
            <p>Intervento Manuale Richiesto</p>
        </div>

        <div class="device-info">
            <h3>📱 Informazioni Dispositivo (TEST)</h3>
            <p><strong>Nome Dispositivo:</strong> Dispositivo Test</p>
            <p><strong>Indirizzo IP:</strong> 192.168.1.100</p>
            <p><strong>Posizione:</strong> Posizione Test</p>
            <p><strong>Stato:</strong> 🔴 Servizio Web NON Attivo</p>
        </div>

        <div class="recovery-info">
            <h3>🔄 Recupero Automatico Tentato</h3>
            <p><strong>Azione di Recupero:</strong> Riavvio SSH eseguito</p>
            <p><strong>Ora Riavvio:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
            <p><strong>Periodo di Attesa:</strong> 5 minuti trascorsi</p>
            <p><strong>Risultato:</strong> ❌ Dispositivo ancora NON attivo dopo recupero</p>
        </div>

        <div class="action-required">
            <h3>⚡ Azione Richiesta</h3>
            <p><strong>Questa è una allerta di TEST.</strong> In uno scenario reale, dovresti:</p>
            <ol>
                <li>Connetterti via SSH per investigare</li>
                <li>Controllare i log di sistema e i servizi</li>
                <li>Eseguire diagnostica manuale</li>
                <li>Riavviare servizi o riavviare il dispositivo</li>
            </ol>
        </div>

        <div style="text-align: center; margin: 30px 0;">
            <a href="http://192.168.1.100" class="button">🌐 Apri Interfaccia Web</a>
            <a href="#" class="button">💻 Connessione SSH</a>
        </div>

        <div class="footer">
            <p><strong>Questa è una email di TEST</strong></p>
            <p>PingMonitor Pro v2.3 - Monitoraggio di Rete Professionale<br>
            by Fabrizio Cerchia</p>
        </div>
    </div>
</body>
</html>
"""


class EmailTestWidget(QWidget):
    """Email alert testing widget"""

    def __init__(self, email_config):
        super().__init__()
        self.email_config = email_config
        self.test_worker = None
        self._setup_ui()

    def _setup_ui(self):
        """Setup UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)

        # Title
        title = QLabel("📧 Centro Test Allerte Email")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #1e40af; margin-bottom: 10px;")
        layout.addWidget(title)

        description = QLabel(
            "Test your email alert system to ensure notifications are working correctly.\n"
            "You can send a simple test email or simulate a full critical alert."
        )
        description.setWordWrap(True)
        description.setStyleSheet("color: #666; margin-bottom: 20px;")
        layout.addWidget(description)

        # Email configuration display
        config_group = QGroupBox("📝 Configurazione Email Attuale")
        config_layout = QVBoxLayout()

        smtp_info = QLabel()
        smtp_server = self.email_config.get('smtp_server', 'Not configured')
        smtp_port = self.email_config.get('smtp_port', 'N/A')
        smtp_username = self.email_config.get('username', self.email_config.get('smtp_username', 'Not configured'))
        from_email = self.email_config.get('from_email', smtp_username)
        alert_email = self.email_config.get('alert_email', 'Not configured')

        smtp_info.setText(
            f"<b>SMTP Server:</b> {smtp_server}:{smtp_port}<br>"
            f"<b>From Email:</b> {from_email}<br>"
            f"<b>Alert Recipients:</b> {alert_email}"
        )
        smtp_info.setStyleSheet("padding: 10px; background-color: #f0f9ff; border-radius: 5px;")
        config_layout.addWidget(smtp_info)

        config_group.setLayout(config_layout)
        layout.addWidget(config_group)

        # Test options
        test_group = QGroupBox("🧪 Opzioni Test")
        test_layout = QVBoxLayout()

        # Test type selection
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Tipo Test:"))

        self.test_type_combo = QComboBox()
        self.test_type_combo.addItem("📨 Email di Test Semplice", "simple")
        self.test_type_combo.addItem("⚠️ Allerta Critica Completa (Simulazione)", "full")
        type_layout.addWidget(self.test_type_combo)
        type_layout.addStretch()
        test_layout.addLayout(type_layout)

        # Recipient override
        recipient_layout = QHBoxLayout()
        recipient_layout.addWidget(QLabel("Invia A (opzionale):"))

        self.recipient_input = QLineEdit()
        self.recipient_input.setPlaceholderText("Lascia vuoto per usare predefinito da config.json")
        recipient_layout.addWidget(self.recipient_input)
        test_layout.addLayout(recipient_layout)

        test_group.setLayout(test_layout)
        layout.addWidget(test_group)

        # Test buttons
        button_layout = QHBoxLayout()

        self.btn_send_test = QPushButton("📧 Invia Email di Test")
        self.btn_send_test.clicked.connect(self._send_test_email)
        self.btn_send_test.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: white;
                border: none;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
            QPushButton:disabled {
                background-color: #9ca3af;
            }
        """)
        button_layout.addWidget(self.btn_send_test)

        self.btn_verify_config = QPushButton("🔍 Verifica Configurazione")
        self.btn_verify_config.clicked.connect(self._verify_configuration)
        self.btn_verify_config.setStyleSheet("""
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
        button_layout.addWidget(self.btn_verify_config)

        button_layout.addStretch()
        layout.addLayout(button_layout)

        # Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setMaximum(0)  # Indeterminate
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        # Status log
        status_group = QGroupBox("📊 Test Results")
        status_layout = QVBoxLayout()

        self.status_log = QTextEdit()
        self.status_log.setReadOnly(True)
        self.status_log.setMaximumHeight(200)
        self.status_log.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #00ff00;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 12px;
                border: 1px solid #333;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        self._log("Centro Test Email inizializzato. Pronto per testare.")
        status_layout.addWidget(self.status_log)

        status_group.setLayout(status_layout)
        layout.addWidget(status_group)

        layout.addStretch()

    def _log(self, message):
        """Add message to status log"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.status_log.append(f"[{timestamp}] {message}")

    def _verify_configuration(self):
        """Verify email configuration"""
        self._log("Verifica configurazione email...")

        errors = []

        if not self.email_config.get('smtp_server'):
            errors.append("❌ Server SMTP non configurato")
        else:
            self._log(f"✅ SMTP Server: {self.email_config['smtp_server']}")

        if not self.email_config.get('smtp_port'):
            errors.append("❌ SMTP port not configured")
        else:
            self._log(f"✅ SMTP Port: {self.email_config['smtp_port']}")

        smtp_username = self.email_config.get('username', self.email_config.get('smtp_username'))
        if not smtp_username:
            errors.append("❌ SMTP username not configured")
        else:
            self._log(f"✅ SMTP Username: {smtp_username}")

        smtp_password = self.email_config.get('password', self.email_config.get('smtp_password'))
        if not smtp_password:
            errors.append("❌ SMTP password not configured")
        else:
            self._log("✅ Password SMTP: Impostata")

        alert_email = self.email_config.get('alert_email', '')
        if not alert_email:
            errors.append("❌ Alert recipients not configured")
        else:
            self._log(f"✅ Alert Recipients: {alert_email}")

        if errors:
            self._log("\n⚠️ Configuration Issues Found:")
            for error in errors:
                self._log(f"  {error}")
            self._log("\n💡 Please check config/config.json file")
            QMessageBox.warning(self, "Problemi di Configurazione",
                              "\n".join(errors) + "\n\nPlease check config/config.json")
        else:
            self._log("\n✅ All configuration checks passed!")
            QMessageBox.information(self, "Configurazione OK",
                                   "La configurazione email è completa e valida!")

    def _send_test_email(self):
        """Send test email"""
        if not self.email_config.get('smtp_server'):
            QMessageBox.warning(self, "Configurazione Mancante",
                              "Configurazione email mancante. Controlla config/config.json")
            return

        test_type = self.test_type_combo.currentData()
        test_recipient = self.recipient_input.text().strip() or None

        self._log(f"Starting {self.test_type_combo.currentText()} test...")
        if test_recipient:
            self._log(f"Sending to: {test_recipient}")
        else:
            self._log(f"Sending to default recipients")

        self.btn_send_test.setEnabled(False)
        self.progress_bar.show()

        # Start worker thread
        self.test_worker = EmailTestWorker(self.email_config, test_type, test_recipient)
        self.test_worker.progress.connect(self._on_progress)
        self.test_worker.result.connect(self._on_result)
        self.test_worker.start()

    def _on_progress(self, message):
        """Handle progress update"""
        self._log(message)

    def _on_result(self, success, message):
        """Handle test result"""
        self._log(message)
        self.btn_send_test.setEnabled(True)
        self.progress_bar.hide()

        if success:
            QMessageBox.information(self, "Successo", message)
        else:
            QMessageBox.critical(self, "Failed", message)
