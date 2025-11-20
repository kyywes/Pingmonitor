"""
PingMonitor Pro v2.0 - Integrated SSH Terminal
Full-featured SSH terminal widget with PuTTY-like interface
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit,
    QPushButton, QLabel, QComboBox, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QTextCursor, QColor, QPalette
import paramiko
import time
import logging

logger = logging.getLogger(__name__)


class SSHWorker(QThread):
    """Worker thread for SSH connection"""

    output_received = pyqtSignal(str, str)  # text, type (stdout/stderr)
    connection_status = pyqtSignal(bool, str)  # connected, message

    def __init__(self, hostname, port, username, password):
        super().__init__()
        self.hostname = hostname
        self.port = port
        self.username = username
        self.password = password
        self.client = None
        self.channel = None
        self.running = False

    def run(self):
        """Connect and maintain SSH session"""
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            self.client.connect(
                hostname=self.hostname,
                port=self.port,
                username=self.username,
                password=self.password,
                timeout=10,
                allow_agent=False,
                look_for_keys=False
            )

            self.connection_status.emit(True, f"Connected to {self.hostname}")

            # Open interactive shell
            self.channel = self.client.invoke_shell(term='xterm', width=80, height=24)
            self.running = True

            # Read output continuously
            while self.running:
                if self.channel.recv_ready():
                    data = self.channel.recv(4096).decode('utf-8', errors='ignore')
                    self.output_received.emit(data, 'stdout')

                if self.channel.recv_stderr_ready():
                    data = self.channel.recv_stderr(4096).decode('utf-8', errors='ignore')
                    self.output_received.emit(data, 'stderr')

                time.sleep(0.01)

        except paramiko.AuthenticationException:
            self.connection_status.emit(False, "Authentication failed")
        except Exception as e:
            self.connection_status.emit(False, f"Connection failed: {str(e)}")
        finally:
            self.cleanup()

    def send_command(self, command):
        """Send command to SSH channel"""
        if self.channel and not self.channel.closed:
            try:
                self.channel.send(command + '\n')
                return True
            except Exception as e:
                logger.error(f"Failed to send command: {e}")
                return False
        return False

    def stop(self):
        """Stop SSH worker"""
        self.running = False
        self.cleanup()

    def cleanup(self):
        """Clean up SSH connection"""
        try:
            if self.channel:
                self.channel.close()
            if self.client:
                self.client.close()
        except:
            pass


class SSHTerminal(QWidget):
    """
    Integrated SSH terminal widget
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ssh_worker = None
        self.command_history = []
        self.history_index = -1
        self.setup_ui()

    def setup_ui(self):
        """Setup terminal UI"""
        layout = QVBoxLayout(self)

        # Connection bar
        conn_layout = QHBoxLayout()

        conn_layout.addWidget(QLabel("Host:"))
        self.host_input = QLineEdit()
        self.host_input.setPlaceholderText("192.168.1.1")
        conn_layout.addWidget(self.host_input)

        conn_layout.addWidget(QLabel("Porta:"))
        self.port_input = QLineEdit("22")
        self.port_input.setFixedWidth(60)
        conn_layout.addWidget(self.port_input)

        conn_layout.addWidget(QLabel("Utente:"))
        self.user_input = QLineEdit("root")
        self.user_input.setFixedWidth(80)
        conn_layout.addWidget(self.user_input)

        conn_layout.addWidget(QLabel("Password:"))
        self.pass_input = QLineEdit()
        self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pass_input.setFixedWidth(100)
        conn_layout.addWidget(self.pass_input)

        self.connect_btn = QPushButton("Connetti")
        self.connect_btn.clicked.connect(self.toggle_connection)
        self.connect_btn.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: white;
                border: none;
                padding: 8px 20px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        conn_layout.addWidget(self.connect_btn)

        conn_layout.addStretch()

        layout.addLayout(conn_layout)

        # Terminal output
        self.terminal_output = QTextEdit()
        self.terminal_output.setReadOnly(True)
        self.terminal_output.setFont(QFont("Consolas", 10))

        # Dark terminal theme
        self.terminal_output.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #00ff00;
                border: 1px solid #444;
                border-radius: 4px;
            }
        """)

        layout.addWidget(self.terminal_output)

        # Command input
        cmd_layout = QHBoxLayout()

        self.prompt_label = QLabel("$")
        self.prompt_label.setStyleSheet("color: #00ff00; font-weight: bold; font-family: Consolas;")
        cmd_layout.addWidget(self.prompt_label)

        self.command_input = QLineEdit()
        self.command_input.setFont(QFont("Consolas", 10))
        self.command_input.setStyleSheet("""
            QLineEdit {
                background-color: #2d2d2d;
                color: #00ff00;
                border: 1px solid #444;
                padding: 5px;
                border-radius: 4px;
            }
        """)
        self.command_input.returnPressed.connect(self.send_command)
        self.command_input.setEnabled(False)
        cmd_layout.addWidget(self.command_input)

        layout.addLayout(cmd_layout)

        # Status bar
        self.status_label = QLabel("Non connesso")
        self.status_label.setStyleSheet("color: #ef4444; font-weight: bold;")
        layout.addWidget(self.status_label)

    def connect_to_device(self, ip: str, username: str = "root", password: str = ""):
        """
        Connect to device automatically (called from context menu)

        Args:
            ip: Device IP address
            username: SSH username
            password: SSH password
        """
        self.host_input.setText(ip)
        self.user_input.setText(username)
        self.pass_input.setText(password)
        self.toggle_connection()

    def toggle_connection(self):
        """Toggle SSH connection"""
        if self.ssh_worker and self.ssh_worker.isRunning():
            # Disconnect
            self.disconnect_ssh()
        else:
            # Connect
            self.connect_ssh()

    def connect_ssh(self):
        """Connect to SSH"""
        hostname = self.host_input.text().strip()
        port = int(self.port_input.text().strip() or 22)
        username = self.user_input.text().strip()
        password = self.pass_input.text()

        if not hostname or not username:
            QMessageBox.warning(self, "Input Error", "Please enter hostname and username")
            return

        # Clear terminal
        self.terminal_output.clear()
        self.terminal_output.append(f"Connecting to {username}@{hostname}:{port}...")

        # Disable inputs
        self.host_input.setEnabled(False)
        self.port_input.setEnabled(False)
        self.user_input.setEnabled(False)
        self.pass_input.setEnabled(False)
        self.connect_btn.setText("Disconnect")
        self.connect_btn.setStyleSheet("""
            QPushButton {
                background-color: #ef4444;
                color: white;
                border: none;
                padding: 8px 20px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #dc2626;
            }
        """)

        # Start SSH worker
        self.ssh_worker = SSHWorker(hostname, port, username, password)
        self.ssh_worker.output_received.connect(self.handle_output)
        self.ssh_worker.connection_status.connect(self.handle_connection_status)
        self.ssh_worker.start()

    def disconnect_ssh(self):
        """Disconnect from SSH"""
        if self.ssh_worker:
            self.ssh_worker.stop()
            self.ssh_worker.wait()
            self.ssh_worker = None

        self.terminal_output.append("\nDisconnected from server")

        # Re-enable inputs
        self.host_input.setEnabled(True)
        self.port_input.setEnabled(True)
        self.user_input.setEnabled(True)
        self.pass_input.setEnabled(True)
        self.command_input.setEnabled(False)
        self.connect_btn.setText("Connect")
        self.connect_btn.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: white;
                border: none;
                padding: 8px 20px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        self.status_label.setText("Not connected")
        self.status_label.setStyleSheet("color: #ef4444; font-weight: bold;")

    def handle_connection_status(self, connected, message):
        """Handle connection status update"""
        if connected:
            self.status_label.setText(f"Connected: {message}")
            self.status_label.setStyleSheet("color: #10b981; font-weight: bold;")
            self.command_input.setEnabled(True)
            self.command_input.setFocus()
        else:
            self.terminal_output.append(f"\nERROR: {message}")
            self.status_label.setText(f"Error: {message}")
            self.status_label.setStyleSheet("color: #ef4444; font-weight: bold;")
            QMessageBox.critical(self, "Connection Failed", message)
            self.disconnect_ssh()

    def handle_output(self, text, output_type):
        """Handle output from SSH"""
        cursor = self.terminal_output.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)

        if output_type == 'stderr':
            cursor.insertHtml(f'<span style="color: #ff4444;">{text.replace("<", "&lt;").replace(">", "&gt;")}</span>')
        else:
            cursor.insertText(text)

        self.terminal_output.setTextCursor(cursor)
        self.terminal_output.ensureCursorVisible()

    def send_command(self):
        """Send command to SSH"""
        command = self.command_input.text()
        if not command:
            return

        if self.ssh_worker and self.ssh_worker.send_command(command):
            # Add to history
            self.command_history.append(command)
            self.history_index = len(self.command_history)

            # Clear input
            self.command_input.clear()
        else:
            QMessageBox.warning(self, "Error", "Not connected to SSH")

    def keyPressEvent(self, event):
        """Handle key press for command history"""
        if event.key() == Qt.Key.Key_Up:
            if self.history_index > 0:
                self.history_index -= 1
                self.command_input.setText(self.command_history[self.history_index])
        elif event.key() == Qt.Key.Key_Down:
            if self.history_index < len(self.command_history) - 1:
                self.history_index += 1
                self.command_input.setText(self.command_history[self.history_index])
            else:
                self.history_index = len(self.command_history)
                self.command_input.clear()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        """Handle widget close"""
        self.disconnect_ssh()
        super().closeEvent(event)
