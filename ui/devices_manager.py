"""
PingMonitor Pro v2.3 - Devices Manager Widget
Complete device CRUD management interface
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QDialog, QFormLayout, QLineEdit, QSpinBox, QCheckBox, QComboBox,
    QFileDialog, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor
from pathlib import Path
import logging
import json

from ..models.device import Device
from ..models.base import db_manager

logger = logging.getLogger(__name__)


class DeviceDialog(QDialog):
    """Dialog for adding/editing devices"""

    def __init__(self, device=None, parent=None):
        super().__init__(parent)
        self.device = device
        self.setWindowTitle("Modifica PAI-PL" if device else "Aggiungi Nuova PAI-PL")
        self.setModal(True)
        self.setMinimumWidth(500)
        self._setup_ui()

        if device:
            self._load_device_data()

    def _setup_ui(self):
        """Setup dialog UI"""
        layout = QVBoxLayout(self)

        # Form layout
        form = QFormLayout()

        # Basic Info Group
        basic_group = QGroupBox("Informazioni Base")
        basic_layout = QFormLayout()

        self.txt_name = QLineEdit()
        self.txt_name.setPlaceholderText("es. PL km 161+672")
        basic_layout.addRow("Nome Dispositivo:", self.txt_name)

        self.txt_ip = QLineEdit()
        self.txt_ip.setPlaceholderText("es. 192.168.2.1")
        basic_layout.addRow("Indirizzo IP:", self.txt_ip)

        self.combo_type = QComboBox()
        self.combo_type.addItems(["PAI-PL"])
        basic_layout.addRow("Tipo Dispositivo:", self.combo_type)

        self.txt_location = QLineEdit()
        self.txt_location.setPlaceholderText("es. PGPL km 161+672, NAPOLI C.LE - FOGGIA")
        basic_layout.addRow("Posizione:", self.txt_location)

        basic_group.setLayout(basic_layout)
        layout.addWidget(basic_group)

        # Monitoring Config Group
        monitor_group = QGroupBox("Configurazione Monitoraggio")
        monitor_layout = QFormLayout()

        self.chk_ping = QCheckBox("Abilita Controllo Ping")
        self.chk_ping.setChecked(True)
        monitor_layout.addRow("", self.chk_ping)

        self.spin_interval = QSpinBox()
        self.spin_interval.setRange(10, 86400)
        self.spin_interval.setValue(3600)
        self.spin_interval.setSuffix(" secondi")
        monitor_layout.addRow("Intervallo Controllo:", self.spin_interval)

        monitor_group.setLayout(monitor_layout)
        layout.addWidget(monitor_group)

        # HTTP/HTTPS Group
        http_group = QGroupBox("Controllo Pagina Web")
        http_layout = QFormLayout()

        self.chk_http = QCheckBox("Abilita Controllo HTTP")
        http_layout.addRow("", self.chk_http)

        self.spin_http_port = QSpinBox()
        self.spin_http_port.setRange(1, 65535)
        self.spin_http_port.setValue(80)
        http_layout.addRow("Porta HTTP:", self.spin_http_port)

        self.chk_https = QCheckBox("Abilita Controllo HTTPS")
        http_layout.addRow("", self.chk_https)

        self.spin_https_port = QSpinBox()
        self.spin_https_port.setRange(1, 65535)
        self.spin_https_port.setValue(443)
        http_layout.addRow("Porta HTTPS:", self.spin_https_port)

        http_group.setLayout(http_layout)
        layout.addWidget(http_group)

        # SSH Group
        ssh_group = QGroupBox("Configurazione SSH (per auto-recupero)")
        ssh_layout = QFormLayout()

        self.chk_ssh = QCheckBox("Abilita SSH")
        ssh_layout.addRow("", self.chk_ssh)

        self.spin_ssh_port = QSpinBox()
        self.spin_ssh_port.setRange(1, 65535)
        self.spin_ssh_port.setValue(22)
        ssh_layout.addRow("Porta SSH:", self.spin_ssh_port)

        self.txt_ssh_user = QLineEdit()
        self.txt_ssh_user.setPlaceholderText("es. root")
        ssh_layout.addRow("Nome Utente SSH:", self.txt_ssh_user)

        ssh_group.setLayout(ssh_layout)
        layout.addWidget(ssh_group)

        # Buttons
        btn_layout = QHBoxLayout()

        btn_save = QPushButton("💾 Save")
        btn_save.clicked.connect(self.accept)
        btn_save.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: white;
                border: none;
                padding: 10px 20px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)

        btn_cancel = QPushButton("❌ Cancel")
        btn_cancel.clicked.connect(self.reject)
        btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #6b7280;
                color: white;
                border: none;
                padding: 10px 20px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #4b5563;
            }
        """)

        btn_layout.addStretch()
        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(btn_cancel)

        layout.addLayout(btn_layout)

    def _load_device_data(self):
        """Load device data into form"""
        if not self.device:
            return

        self.txt_name.setText(self.device.name)
        self.txt_ip.setText(self.device.ip_address)

        # Set device type
        index = self.combo_type.findText(self.device.device_type)
        if index >= 0:
            self.combo_type.setCurrentIndex(index)

        self.txt_location.setText(self.device.location or "")

        self.chk_ping.setChecked(self.device.ping_enabled)
        self.spin_interval.setValue(self.device.check_interval)

        self.chk_http.setChecked(self.device.http_enabled)
        self.spin_http_port.setValue(self.device.http_port)

        self.chk_https.setChecked(self.device.https_enabled)
        self.spin_https_port.setValue(self.device.https_port)

        self.chk_ssh.setChecked(self.device.ssh_enabled)
        self.spin_ssh_port.setValue(self.device.ssh_port)
        self.txt_ssh_user.setText(self.device.ssh_username or "")

    def get_device_data(self):
        """Get device data from form"""
        return {
            'name': self.txt_name.text().strip(),
            'ip_address': self.txt_ip.text().strip(),
            'device_type': self.combo_type.currentText(),
            'location': self.txt_location.text().strip() or None,
            'ping_enabled': self.chk_ping.isChecked(),
            'check_interval': self.spin_interval.value(),
            'http_enabled': self.chk_http.isChecked(),
            'http_port': self.spin_http_port.value(),
            'https_enabled': self.chk_https.isChecked(),
            'https_port': self.spin_https_port.value(),
            'ssh_enabled': self.chk_ssh.isChecked(),
            'ssh_port': self.spin_ssh_port.value(),
            'ssh_username': self.txt_ssh_user.text().strip() or None,
        }


class DevicesManager(QWidget):
    """Devices management widget with full CRUD operations"""

    devices_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._setup_ui()
        self._load_devices()

    def _setup_ui(self):
        """Setup UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Title
        title = QLabel("🖥 Gestione PAI-PL")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #1e40af; margin-bottom: 10px;")
        layout.addWidget(title)

        # Info label
        info = QLabel("Gestisci tutte le centraline PAI-PL - Aggiungi, Modifica, Elimina o Importa da config.json")
        info.setStyleSheet("color: #666; font-size: 12px; margin-bottom: 10px;")
        layout.addWidget(info)

        # Controls
        controls_layout = QHBoxLayout()

        btn_add = QPushButton("➕ Aggiungi Dispositivo")
        btn_add.clicked.connect(self._add_device)
        btn_add.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: white;
                border: none;
                padding: 8px 16px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        controls_layout.addWidget(btn_add)

        btn_edit = QPushButton("✏️ Edit Device")
        btn_edit.clicked.connect(self._edit_device)
        btn_edit.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: white;
                border: none;
                padding: 8px 16px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
        """)
        controls_layout.addWidget(btn_edit)

        btn_delete = QPushButton("🗑️ Delete Device")
        btn_delete.clicked.connect(self._delete_device)
        btn_delete.setStyleSheet("""
            QPushButton {
                background-color: #ef4444;
                color: white;
                border: none;
                padding: 8px 16px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #dc2626;
            }
        """)
        controls_layout.addWidget(btn_delete)

        controls_layout.addSpacing(20)

        btn_import = QPushButton("📂 Import from Config.json")
        btn_import.clicked.connect(self._import_from_config)
        controls_layout.addWidget(btn_import)

        btn_refresh = QPushButton("🔄 Aggiorna")
        btn_refresh.clicked.connect(self._load_devices)
        controls_layout.addWidget(btn_refresh)

        controls_layout.addStretch()
        layout.addLayout(controls_layout)

        # Statistics
        stats_layout = QHBoxLayout()

        self.lbl_total = QLabel("Totale Dispositivi: 0")
        self.lbl_total.setStyleSheet("padding: 5px 10px; background-color: #e5e7eb; border-radius: 5px; font-weight: bold;")
        stats_layout.addWidget(self.lbl_total)

        self.lbl_enabled = QLabel("🟢 Abilitati: 0")
        self.lbl_enabled.setStyleSheet("padding: 5px 10px; background-color: #d1fae5; border-radius: 5px; color: #059669;")
        stats_layout.addWidget(self.lbl_enabled)

        self.lbl_disabled = QLabel("🔴 Disabilitati: 0")
        self.lbl_disabled.setStyleSheet("padding: 5px 10px; background-color: #fee2e2; border-radius: 5px; color: #dc2626;")
        stats_layout.addWidget(self.lbl_disabled)

        stats_layout.addStretch()
        layout.addLayout(stats_layout)

        # Devices table
        self.devices_table = QTableWidget()
        self.devices_table.setColumnCount(8)
        self.devices_table.setHorizontalHeaderLabels([
            "Abilitato", "Nome", "Indirizzo IP", "Tipo", "Posizione",
            "Ping", "Pagina Web", "SSH"
        ])

        self.devices_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.devices_table.setAlternatingRowColors(True)
        self.devices_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.devices_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #444;
                border-radius: 5px;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QHeaderView::section {
                background-color: #2563eb;
                color: white;
                padding: 8px;
                font-weight: bold;
                border: none;
            }
        """)

        # Double click to edit
        self.devices_table.doubleClicked.connect(self._edit_device)

        layout.addWidget(self.devices_table)

    def _load_devices(self):
        """Load devices from database"""
        try:
            session = db_manager.get_session()
            devices = session.query(Device).all()

            self.devices_table.setRowCount(len(devices))

            enabled_count = 0

            for row, device in enumerate(devices):
                # Enabled checkbox
                chk_enabled = QCheckBox()
                chk_enabled.setChecked(device.enabled)
                chk_enabled.setProperty("device_id", device.id)
                chk_enabled.stateChanged.connect(self._toggle_device_enabled)

                # Center the checkbox
                chk_widget = QWidget()
                chk_layout = QHBoxLayout(chk_widget)
                chk_layout.addWidget(chk_enabled)
                chk_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
                chk_layout.setContentsMargins(0, 0, 0, 0)

                self.devices_table.setCellWidget(row, 0, chk_widget)

                if device.enabled:
                    enabled_count += 1

                # Name
                self.devices_table.setItem(row, 1, QTableWidgetItem(device.name))

                # IP Address
                self.devices_table.setItem(row, 2, QTableWidgetItem(device.ip_address))

                # Type
                self.devices_table.setItem(row, 3, QTableWidgetItem(device.device_type))

                # Location
                self.devices_table.setItem(row, 4, QTableWidgetItem(device.location or "N/A"))

                # Ping
                ping_status = "✅" if device.ping_enabled else "❌"
                self.devices_table.setItem(row, 5, QTableWidgetItem(ping_status))

                # HTTP/HTTPS
                http_status = ""
                if device.http_enabled:
                    http_status += f"HTTP:{device.http_port} "
                if device.https_enabled:
                    http_status += f"HTTPS:{device.https_port}"
                if not http_status:
                    http_status = "❌"
                self.devices_table.setItem(row, 6, QTableWidgetItem(http_status.strip()))

                # SSH
                ssh_status = f"✅ Port {device.ssh_port}" if device.ssh_enabled else "❌"
                self.devices_table.setItem(row, 7, QTableWidgetItem(ssh_status))

                # Store device ID in first column
                self.devices_table.item(row, 1).setData(Qt.ItemDataRole.UserRole, device.id)

            # Update statistics
            self.lbl_total.setText(f"Totale Dispositivi: {len(devices)}")
            self.lbl_enabled.setText(f"🟢 Abilitati: {enabled_count}")
            self.lbl_disabled.setText(f"🔴 Disabilitati: {len(devices) - enabled_count}")

            session.close()

        except Exception as e:
            logger.error(f"Failed to load devices: {e}")
            QMessageBox.critical(self, "Errore", f"Failed to load devices:\n{str(e)}")

    def _add_device(self):
        """Add new device"""
        dialog = DeviceDialog(parent=self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                device_data = dialog.get_device_data()

                # Validate
                if not device_data['name'] or not device_data['ip_address']:
                    QMessageBox.warning(self, "Errore Validazione", "Nome e Indirizzo IP sono obbligatori!")
                    return

                # Create device
                session = db_manager.get_session()

                # Check if IP already exists
                existing = session.query(Device).filter_by(ip_address=device_data['ip_address']).first()
                if existing:
                    QMessageBox.warning(self, "Duplicate Device",
                                      f"A device with IP {device_data['ip_address']} already exists!")
                    session.close()
                    return

                device = Device(**device_data)
                session.add(device)
                session.commit()
                session.close()

                self._load_devices()
                self.devices_changed.emit()

                QMessageBox.information(self, "Successo", f"Device '{device_data['name']}' added successfully!")

            except Exception as e:
                logger.error(f"Failed to add device: {e}")
                QMessageBox.critical(self, "Errore", f"Failed to add device:\n{str(e)}")

    def _edit_device(self):
        """Edit selected device"""
        selected = self.devices_table.currentRow()

        if selected < 0:
            QMessageBox.warning(self, "No Selection", "Please select a device to edit!")
            return

        try:
            # Get device ID
            device_id = self.devices_table.item(selected, 1).data(Qt.ItemDataRole.UserRole)

            session = db_manager.get_session()
            device = session.query(Device).filter_by(id=device_id).first()

            if not device:
                QMessageBox.warning(self, "Errore", "Device not found!")
                session.close()
                return

            dialog = DeviceDialog(device=device, parent=self)

            if dialog.exec() == QDialog.DialogCode.Accepted:
                device_data = dialog.get_device_data()

                # Validate
                if not device_data['name'] or not device_data['ip_address']:
                    QMessageBox.warning(self, "Errore Validazione", "Nome e Indirizzo IP sono obbligatori!")
                    session.close()
                    return

                # Update device
                for key, value in device_data.items():
                    setattr(device, key, value)

                session.commit()
                session.close()

                self._load_devices()
                self.devices_changed.emit()

                QMessageBox.information(self, "Successo", f"Device '{device_data['name']}' updated successfully!")
            else:
                session.close()

        except Exception as e:
            logger.error(f"Failed to edit device: {e}")
            QMessageBox.critical(self, "Errore", f"Failed to edit device:\n{str(e)}")

    def _delete_device(self):
        """Delete selected device"""
        selected = self.devices_table.currentRow()

        if selected < 0:
            QMessageBox.warning(self, "No Selection", "Please select a device to delete!")
            return

        device_name = self.devices_table.item(selected, 1).text()

        reply = QMessageBox.question(self, "Confirm Delete",
                                     f"Are you sure you want to delete '{device_name}'?\n\n"
                                     f"This action cannot be undone!",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            try:
                device_id = self.devices_table.item(selected, 1).data(Qt.ItemDataRole.UserRole)

                session = db_manager.get_session()
                device = session.query(Device).filter_by(id=device_id).first()

                if device:
                    session.delete(device)
                    session.commit()

                session.close()

                self._load_devices()
                self.devices_changed.emit()

                QMessageBox.information(self, "Successo", f"Device '{device_name}' deleted successfully!")

            except Exception as e:
                logger.error(f"Failed to delete device: {e}")
                QMessageBox.critical(self, "Errore", f"Failed to delete device:\n{str(e)}")

    def _toggle_device_enabled(self, state):
        """Toggle device enabled status"""
        try:
            checkbox = self.sender()
            device_id = checkbox.property("device_id")

            session = db_manager.get_session()
            device = session.query(Device).filter_by(id=device_id).first()

            if device:
                device.enabled = bool(state)
                session.commit()
                self.devices_changed.emit()

            session.close()

            # Update statistics
            self._load_devices()

        except Exception as e:
            logger.error(f"Failed to toggle device: {e}")

    def _import_from_config(self):
        """Import devices from config.json"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Config File", "", "JSON Files (*.json);;All Files (*)"
        )

        if not file_path:
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            devices_data = config.get('devices', [])

            if not devices_data:
                QMessageBox.warning(self, "No Devices", "No devices found in config file!")
                return

            session = db_manager.get_session()
            imported_count = 0
            skipped_count = 0

            for dev_data in devices_data:
                ip_address = dev_data.get('ip_address')

                # Check if already exists
                existing = session.query(Device).filter_by(ip_address=ip_address).first()

                if existing:
                    skipped_count += 1
                    continue

                # Create device
                device = Device(
                    name=dev_data.get('name', ip_address),
                    ip_address=ip_address,
                    device_type=dev_data.get('type', 'Other'),
                    location=dev_data.get('location'),
                    ping_enabled=dev_data.get('ping_enabled', True),
                    check_interval=dev_data.get('interval', 3600),
                    http_enabled=dev_data.get('http_enabled', False),
                    http_port=dev_data.get('http_port', 80),
                    https_enabled=dev_data.get('https_enabled', False),
                    https_port=dev_data.get('https_port', 443),
                    ssh_enabled=dev_data.get('ssh_enabled', False),
                    ssh_port=dev_data.get('ssh_port', 22),
                    ssh_username=dev_data.get('ssh_username')
                )

                session.add(device)
                imported_count += 1

            session.commit()
            session.close()

            self._load_devices()
            self.devices_changed.emit()

            msg = f"Import completed!\n\n"
            msg += f"Imported: {imported_count}\n"
            msg += f"Skipped (already exists): {skipped_count}"

            QMessageBox.information(self, "Import Complete", msg)

        except Exception as e:
            logger.error(f"Failed to import devices: {e}")
            QMessageBox.critical(self, "Import Error", f"Failed to import devices:\n{str(e)}")
