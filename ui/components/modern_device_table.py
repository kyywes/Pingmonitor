"""
Modern Professional Device Table
Clean, readable, with status indicators and actions
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton, QLabel, QFrame, QMenu
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QCursor
import logging

from .status_indicator import StatusIndicatorCell
from ..design_system import DesignSystem as DS

logger = logging.getLogger(__name__)


class ActionButton(QPushButton):
    """Small action button for table rows"""

    def __init__(self, text, icon=''):
        super().__init__(f"{icon} {text}" if icon else text)
        self.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #6366f1;
                border: 1px solid #6366f1;
                border-radius: 4px;
                padding: 4px 10px;
                font-size: 12px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: rgba(99, 102, 241, 0.1);
                border-color: #4f46e5;
                color: #4f46e5;
            }
            QPushButton:pressed {
                background-color: rgba(99, 102, 241, 0.2);
            }
        """)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setFixedHeight(28)


class ModernDeviceTable(QWidget):
    """
    Professional device monitoring table
    Features:
    - Clean design with proper spacing
    - Animated status indicators
    - Quick action buttons
    - Responsive layout
    - Proper typography
    """

    # Signals
    device_selected = pyqtSignal(int)  # device_id
    edit_device = pyqtSignal(int)
    delete_device = pyqtSignal(int)
    ssh_connect = pyqtSignal(int)
    ping_now = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        """Setup table UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        # Header
        header = self._create_header()
        layout.addWidget(header)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            'Status',
            'Device Name',
            'IP Address',
            'Type',
            'Response',
            'Uptime',
            'Last Check',
            'Location',
            'Actions'
        ])

        # Table configuration
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setStretchLastSection(False)

        # Set specific column widths
        self.table.setColumnWidth(0, 120)   # Status
        self.table.setColumnWidth(1, 200)   # Name
        self.table.setColumnWidth(2, 140)   # IP
        self.table.setColumnWidth(3, 100)   # Type
        self.table.setColumnWidth(4, 100)   # Response
        self.table.setColumnWidth(5, 90)    # Uptime
        self.table.setColumnWidth(6, 160)   # Last Check
        self.table.setColumnWidth(7, 180)   # Location
        self.table.setColumnWidth(8, 180)   # Actions

        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(True)

        # Apply professional table styling
        self.table.setStyleSheet(DS.table_modern())

        # Row height
        self.table.verticalHeader().setDefaultSectionSize(56)

        # Context menu
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)

        # Selection
        self.table.itemSelectionChanged.connect(self._on_selection_changed)

        layout.addWidget(self.table)

    def _create_header(self):
        """Create table header with controls"""
        header = QFrame()
        header.setStyleSheet(f"""
            QFrame {{
                background-color: {DS.COLORS['surface-01']};
                border: 1px solid {DS.COLORS['border-subtle']};
                border-radius: {DS.RADIUS['radius-lg']};
                padding: 12px 16px;
            }}
        """)

        layout = QHBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 0)

        # Title
        title = QLabel('Devices Overview')
        title.setStyleSheet(DS.heading_3())
        layout.addWidget(title)

        # Device count
        self.count_label = QLabel('0 devices')
        self.count_label.setStyleSheet(f"""
            QLabel {{
                color: {DS.COLORS['text-tertiary']};
                font-size: {DS.TYPOGRAPHY['text-sm']};
                background: transparent;
            }}
        """)
        layout.addWidget(self.count_label)

        layout.addStretch()

        # Filter buttons (future enhancement)
        filter_all = QPushButton('All')
        filter_online = QPushButton('Online')
        filter_offline = QPushButton('Offline')

        for btn in [filter_all, filter_online, filter_offline]:
            btn.setStyleSheet(DS.button_ghost())
            btn.setFixedHeight(32)
            layout.addWidget(btn)

        return header

    def set_devices(self, devices):
        """
        Populate table with device data

        Args:
            devices: List of Device objects
        """
        self.table.setRowCount(len(devices))

        for row, device in enumerate(devices):
            # Status indicator
            status_widget = StatusIndicatorCell(device.current_status)
            self.table.setCellWidget(row, 0, status_widget)

            # Device name
            name_item = QTableWidgetItem(device.name)
            name_item.setFont(QFont(DS.TYPOGRAPHY['font-primary'], 13, int(DS.TYPOGRAPHY['weight-medium'])))
            name_item.setForeground(Qt.GlobalColor.white)
            name_item.setData(Qt.ItemDataRole.UserRole, device.id)
            self.table.setItem(row, 1, name_item)

            # IP Address
            ip_item = QTableWidgetItem(device.ip_address)
            ip_item.setFont(QFont(DS.TYPOGRAPHY['font-mono'], 12))
            ip_item.setForeground(Qt.GlobalColor.lightGray)
            self.table.setItem(row, 2, ip_item)

            # Type
            type_item = QTableWidgetItem(device.device_type)
            type_item.setForeground(Qt.GlobalColor.lightGray)
            self.table.setItem(row, 3, type_item)

            # Response time
            if device.response_time > 0:
                response_text = f"{device.response_time:.0f} ms"
                response_color = self._get_response_color(device.response_time)
            else:
                response_text = "—"
                response_color = Qt.GlobalColor.gray

            response_item = QTableWidgetItem(response_text)
            response_item.setForeground(response_color)
            response_item.setFont(QFont(DS.TYPOGRAPHY['font-mono'], 12))
            self.table.setItem(row, 4, response_item)

            # Uptime
            uptime_text = f"{device.uptime_percentage:.1f}%"
            uptime_color = self._get_uptime_color(device.uptime_percentage)
            uptime_item = QTableWidgetItem(uptime_text)
            uptime_item.setForeground(uptime_color)
            uptime_item.setFont(QFont(DS.TYPOGRAPHY['font-mono'], 12, int(DS.TYPOGRAPHY['weight-semibold'])))
            self.table.setItem(row, 5, uptime_item)

            # Last check
            last_check = device.last_check_time.strftime('%Y-%m-%d %H:%M') if device.last_check_time else 'Never'
            check_item = QTableWidgetItem(last_check)
            check_item.setForeground(Qt.GlobalColor.lightGray)
            check_item.setFont(QFont(DS.TYPOGRAPHY['font-mono'], 11))
            self.table.setItem(row, 6, check_item)

            # Location
            location = device.location if device.location else '—'
            location_item = QTableWidgetItem(location)
            location_item.setForeground(Qt.GlobalColor.lightGray)
            self.table.setItem(row, 7, location_item)

            # Actions
            actions_widget = self._create_action_buttons(device.id)
            self.table.setCellWidget(row, 8, actions_widget)

        # Update count
        self.count_label.setText(f"{len(devices)} devices")

    def _create_action_buttons(self, device_id):
        """Create action buttons for a row"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Ping button
        btn_ping = ActionButton('Ping', '📡')
        btn_ping.clicked.connect(lambda: self.ping_now.emit(device_id))
        layout.addWidget(btn_ping)

        # Edit button
        btn_edit = ActionButton('Edit', '✏️')
        btn_edit.clicked.connect(lambda: self.edit_device.emit(device_id))
        layout.addWidget(btn_edit)

        # More actions menu button
        btn_more = ActionButton('•••')
        btn_more.clicked.connect(lambda: self._show_more_actions(device_id))
        layout.addWidget(btn_more)

        layout.addStretch()
        return widget

    def _get_response_color(self, response_time):
        """Get color based on response time"""
        from PyQt6.QtGui import QColor

        if response_time < 50:
            return QColor(DS.COLORS['status-online'])  # Green
        elif response_time < 150:
            return QColor(DS.COLORS['status-warning'])  # Yellow
        else:
            return QColor(DS.COLORS['status-offline'])  # Red

    def _get_uptime_color(self, uptime):
        """Get color based on uptime percentage"""
        from PyQt6.QtGui import QColor

        if uptime >= 99:
            return QColor(DS.COLORS['status-online'])
        elif uptime >= 95:
            return QColor(DS.COLORS['status-warning'])
        else:
            return QColor(DS.COLORS['status-offline'])

    def _on_selection_changed(self):
        """Handle row selection"""
        selected = self.table.currentRow()
        if selected >= 0:
            device_id = self.table.item(selected, 1).data(Qt.ItemDataRole.UserRole)
            self.device_selected.emit(device_id)

    def _show_context_menu(self, pos):
        """Show context menu on right-click"""
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {DS.COLORS['surface-02']};
                border: 1px solid {DS.COLORS['border-default']};
                border-radius: {DS.RADIUS['radius-lg']};
                padding: 6px;
            }}
            QMenu::item {{
                padding: 8px 16px;
                border-radius: {DS.RADIUS['radius-md']};
                color: {DS.COLORS['text-secondary']};
            }}
            QMenu::item:selected {{
                background-color: {DS.COLORS['brand-subtle']};
                color: {DS.COLORS['brand-primary']};
            }}
        """)

        # Get selected device
        row = self.table.currentRow()
        if row < 0:
            return

        device_id = self.table.item(row, 1).data(Qt.ItemDataRole.UserRole)

        # Menu actions
        ping_action = menu.addAction('📡 Ping Now')
        ping_action.triggered.connect(lambda: self.ping_now.emit(device_id))

        ssh_action = menu.addAction('🔌 SSH Connect')
        ssh_action.triggered.connect(lambda: self.ssh_connect.emit(device_id))

        menu.addSeparator()

        edit_action = menu.addAction('✏️ Edit Device')
        edit_action.triggered.connect(lambda: self.edit_device.emit(device_id))

        delete_action = menu.addAction('🗑️ Delete Device')
        delete_action.triggered.connect(lambda: self.delete_device.emit(device_id))

        # Show menu
        menu.exec(self.table.viewport().mapToGlobal(pos))

    def _show_more_actions(self, device_id):
        """Show more actions menu"""
        # This can show a popup menu with additional actions
        pass

    def update_device_status(self, device_id, status):
        """Update a single device's status without full refresh"""
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 1)
            if item and item.data(Qt.ItemDataRole.UserRole) == device_id:
                # Update status indicator
                status_widget = self.table.cellWidget(row, 0)
                if isinstance(status_widget, StatusIndicatorCell):
                    status_widget.set_status(status)
                break
