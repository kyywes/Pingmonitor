# Migration Guide - Applying Professional Design System

## Quick Start

### 1. Load the Professional Theme

In your main application file (`main.py` or `app.py`):

```python
from PyQt6.QtWidgets import QApplication
from pathlib import Path
import sys

def main():
    app = QApplication(sys.argv)

    # Load professional theme
    theme_path = Path(__file__).parent / 'src/ui/styles/professional_theme.qss'
    with open(theme_path, 'r', encoding='utf-8') as f:
        app.setStyleSheet(f.read())

    # Continue with your app initialization...
    window = MainWindow()
    window.show()

    sys.exit(app.exec())
```

---

## 2. Update Main Window Header

### Before (Old Code)
```python
def _create_header(self):
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

    title = QLabel("🌐 PingMonitor Pro")
    title.setStyleSheet("font-size: 24px; font-weight: bold; color: white;")
    layout.addWidget(title)

    self.lbl_online = QLabel("🟢 Online: 0")
    self.lbl_online.setStyleSheet("font-size: 16px; font-weight: bold; color: white;")
    layout.addWidget(self.lbl_online)
```

### After (Professional Design)
```python
from src.ui.design_system import DesignSystem as DS
from src.ui.components import StatusCard

def _create_header(self):
    header = QWidget()
    header.setStyleSheet(f"""
        QWidget {{
            background-color: {DS.COLORS['surface-01']};
            border: 1px solid {DS.COLORS['border-subtle']};
            border-radius: {DS.RADIUS['radius-xl']};
            padding: 20px;
        }}
    """)

    layout = QHBoxLayout(header)

    # Title - no emoji, professional font
    title = QLabel("PingMonitor Pro")
    title.setStyleSheet(DS.heading_2())
    layout.addWidget(title)

    layout.addStretch()

    # Status cards instead of labels
    self.card_online = StatusCard(status='online', count=0, title='Online')
    self.card_offline = StatusCard(status='offline', count=0, title='Offline')

    layout.addWidget(self.card_online)
    layout.addWidget(self.card_offline)

    return header
```

---

## 3. Update Buttons

### Before (Inline Styles)
```python
self.btn_start = QPushButton("▶ Start Monitoring")
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
```

### After (Design System)
```python
from src.ui.design_system import DesignSystem as DS

self.btn_start = QPushButton("Start Monitoring")  # No emoji
self.btn_start.setStyleSheet(DS.button_success())
self.btn_start.setMinimumWidth(140)

self.btn_stop = QPushButton("Stop")
self.btn_stop.setStyleSheet(DS.button_danger())
self.btn_stop.setMinimumWidth(140)
```

---

## 4. Replace Device Table

### Before (Basic Table)
```python
def _create_monitoring_tab(self):
    widget = QWidget()
    layout = QVBoxLayout(widget)

    self.monitoring_table = QTableWidget()
    self.monitoring_table.setColumnCount(8)
    self.monitoring_table.setHorizontalHeaderLabels([...])
    self.monitoring_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

    layout.addWidget(self.monitoring_table)
    return widget
```

### After (Modern Table Component)
```python
from src.ui.components import ModernDeviceTable

def _create_monitoring_tab(self):
    widget = QWidget()
    layout = QVBoxLayout(widget)
    layout.setContentsMargins(16, 16, 16, 16)

    # Use modern table component
    self.device_table = ModernDeviceTable()

    # Connect signals
    self.device_table.device_selected.connect(self._on_device_selected)
    self.device_table.edit_device.connect(self._on_edit_device)
    self.device_table.delete_device.connect(self._on_delete_device)
    self.device_table.ping_now.connect(self._on_ping_device)

    layout.addWidget(self.device_table)
    return widget

def _update_monitoring_table(self):
    """Update table with device data"""
    devices = list(self.monitoring_engine.devices.values())
    self.device_table.set_devices(devices)
```

---

## 5. Update Status Indicators

### Before (Emoji-based)
```python
# In table update
for row, device in enumerate(devices):
    status_icon = "🟢" if device.current_status == 'online' else "🔴"
    self.monitoring_table.setItem(row, 0,
        QTableWidgetItem(f"{status_icon} {device.current_status.upper()}")
    )
```

### After (Professional Components)
```python
from src.ui.components import StatusIndicatorCell

# The ModernDeviceTable handles this automatically!
# But if you need manual control:

def _update_device_row(self, row, device):
    # Status indicator (handled by ModernDeviceTable component)
    status_widget = StatusIndicatorCell(device.current_status)
    self.table.setCellWidget(row, 0, status_widget)
```

---

## 6. Update Dialog Styling

### Before
```python
class DeviceDialog(QDialog):
    def __init__(self):
        super().__init__()
        # No specific styling
        self.setWindowTitle("Add Device")
```

### After
```python
from src.ui.design_system import DesignSystem as DS

class DeviceDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Add Device")

        # Apply dialog styling
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {DS.COLORS['bg-secondary']};
            }}
        """)

        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
```

---

## 7. Update Form Inputs

### Before
```python
self.txt_name = QLineEdit()
self.txt_name.setPlaceholderText("Device name")
# No custom styling
```

### After
```python
from src.ui.design_system import DesignSystem as DS

self.txt_name = QLineEdit()
self.txt_name.setPlaceholderText("Device name")
self.txt_name.setStyleSheet(DS.input_field())
self.txt_name.setMinimumHeight(40)
```

---

## 8. Statistics Display

### Before
```python
self.lbl_total = QLabel("Total: 0")
self.lbl_total.setStyleSheet("padding: 5px; background: #e5e7eb; border-radius: 5px;")
```

### After
```python
from src.ui.components import StatusCard

# Use proper status cards
self.card_total = StatusCard(status='pending', count=0, title='Total Devices')
self.card_online = StatusCard(status='online', count=0, title='Online')
self.card_offline = StatusCard(status='offline', count=0, title='Offline')

# Update counts
def update_stats(self, total, online, offline):
    self.card_total.update_count(total)
    self.card_online.update_count(online)
    self.card_offline.update_count(offline)
```

---

## Complete Example: Updated Main Window

```python
"""
PingMonitor Pro v2.0 - Main Window (Professional Design)
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLabel, QPushButton
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon

from src.ui.design_system import DesignSystem as DS
from src.ui.components import ModernDeviceTable, StatusCard

import logging

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Professional Main Window with Modern Design System"""

    def __init__(self, config, monitoring_engine):
        super().__init__()
        self.config = config
        self.monitoring_engine = monitoring_engine

        self._setup_window()
        self._create_ui()
        self._connect_signals()

        # Start UI update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_ui)
        self.update_timer.start(1000)

    def _setup_window(self):
        """Setup window properties"""
        self.setWindowTitle("PingMonitor Pro v2.0")
        self.resize(1400, 900)

        # Center on screen
        screen = self.screen().geometry()
        x = (screen.width() - 1400) // 2
        y = (screen.height() - 900) // 2
        self.move(x, y)

    def _create_ui(self):
        """Create modern UI"""
        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Header with stats
        header = self._create_header()
        layout.addWidget(header)

        # Control bar
        controls = self._create_controls()
        layout.addWidget(controls)

        # Tab widget
        tabs = self._create_tabs()
        layout.addWidget(tabs)

    def _create_header(self):
        """Create professional header"""
        header = QWidget()
        header.setStyleSheet(f"""
            QWidget {{
                background-color: {DS.COLORS['surface-01']};
                border: 1px solid {DS.COLORS['border-subtle']};
                border-radius: {DS.RADIUS['radius-xl']};
            }}
        """)

        layout = QHBoxLayout(header)
        layout.setContentsMargins(24, 20, 24, 20)

        # Title
        title = QLabel("PingMonitor Pro")
        title.setStyleSheet(DS.heading_2())
        layout.addWidget(title)

        # Subtitle
        subtitle = QLabel("Professional Network Monitoring")
        subtitle.setStyleSheet(DS.text_secondary())
        layout.addWidget(subtitle)

        layout.addStretch()

        # Status cards
        self.card_total = StatusCard('pending', 0, 'Total')
        self.card_online = StatusCard('online', 0, 'Online')
        self.card_offline = StatusCard('offline', 0, 'Offline')

        for card in [self.card_total, self.card_online, self.card_offline]:
            card.setFixedWidth(140)
            layout.addWidget(card)

        return header

    def _create_controls(self):
        """Create control buttons"""
        controls = QWidget()
        layout = QHBoxLayout(controls)
        layout.setContentsMargins(0, 0, 0, 0)

        # Start/Stop buttons
        self.btn_start = QPushButton("Start Monitoring")
        self.btn_start.setStyleSheet(DS.button_success())
        self.btn_start.setMinimumWidth(150)
        self.btn_start.clicked.connect(self.start_monitoring)

        self.btn_stop = QPushButton("Stop Monitoring")
        self.btn_stop.setStyleSheet(DS.button_danger())
        self.btn_stop.setMinimumWidth(150)
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.stop_monitoring)

        layout.addWidget(self.btn_start)
        layout.addWidget(self.btn_stop)
        layout.addStretch()

        # Additional controls
        btn_refresh = QPushButton("Refresh")
        btn_refresh.setStyleSheet(DS.button_ghost())
        btn_refresh.clicked.connect(self._update_ui)

        btn_add = QPushButton("Add Device")
        btn_add.setStyleSheet(DS.button_primary())
        btn_add.clicked.connect(self._add_device)

        layout.addWidget(btn_refresh)
        layout.addWidget(btn_add)

        return controls

    def _create_tabs(self):
        """Create tab widget"""
        tabs = QTabWidget()

        # Monitoring tab with modern table
        monitoring_widget = QWidget()
        monitoring_layout = QVBoxLayout(monitoring_widget)
        monitoring_layout.setContentsMargins(0, 0, 0, 0)

        self.device_table = ModernDeviceTable()
        self.device_table.edit_device.connect(self._edit_device)
        self.device_table.delete_device.connect(self._delete_device)

        monitoring_layout.addWidget(self.device_table)

        tabs.addTab(monitoring_widget, "Monitoring")
        tabs.addTab(QWidget(), "Statistics")
        tabs.addTab(QWidget(), "Logs")

        return tabs

    def _connect_signals(self):
        """Connect monitoring engine signals"""
        self.monitoring_engine.register_callback(
            'on_status_change',
            self._on_device_status_change
        )

    def start_monitoring(self):
        """Start monitoring"""
        self.monitoring_engine.start()
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)

    def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring_engine.stop()
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)

    def _update_ui(self):
        """Update UI with latest data"""
        devices = list(self.monitoring_engine.devices.values())

        # Update stats
        total = len(devices)
        online = sum(1 for d in devices if d.current_status == 'online')
        offline = sum(1 for d in devices if d.current_status == 'offline')

        self.card_total.update_count(total)
        self.card_online.update_count(online)
        self.card_offline.update_count(offline)

        # Update table
        self.device_table.set_devices(devices)

    def _on_device_status_change(self, device, old_status, new_status):
        """Handle device status change"""
        logger.info(f"Device {device.name}: {old_status} -> {new_status}")
        # UI update happens in timer

    def _add_device(self):
        """Show add device dialog"""
        # TODO: Implement dialog
        pass

    def _edit_device(self, device_id):
        """Edit device"""
        # TODO: Implement
        pass

    def _delete_device(self, device_id):
        """Delete device"""
        # TODO: Implement
        pass
```

---

## Testing the New Design

### Visual Checklist
- [ ] Theme loads without errors
- [ ] All colors match the design system
- [ ] Status indicators show proper colors
- [ ] Buttons have correct hover states
- [ ] Table is readable and well-spaced
- [ ] Text hierarchy is clear
- [ ] Spacing is consistent

### Functionality Checklist
- [ ] Status indicators animate properly
- [ ] Buttons respond to clicks
- [ ] Table sorting works
- [ ] Context menu appears
- [ ] Dialogs display correctly

---

## Troubleshooting

### Theme Not Loading
```python
# Check file path
from pathlib import Path
theme_path = Path(__file__).parent / 'src/ui/styles/professional_theme.qss'
print(f"Theme path exists: {theme_path.exists()}")

# Check file encoding
with open(theme_path, 'r', encoding='utf-8') as f:
    content = f.read()
    print(f"Theme loaded: {len(content)} characters")
```

### Components Not Importing
```python
# Ensure __init__.py exists in components folder
# Check import path
import sys
print(sys.path)

# Try absolute import
from src.ui.components.status_indicator import StatusDot
```

### Colors Not Matching
```python
# Verify design system values
from src.ui.design_system import DesignSystem as DS
print(DS.COLORS['brand-primary'])  # Should print #6366f1
```

---

## Next Steps

1. Apply the professional theme globally
2. Replace status indicators with components
3. Update all buttons to use design system
4. Migrate tables to ModernDeviceTable
5. Update dialogs with proper styling
6. Test accessibility and contrast
7. Gather user feedback

---

**Migration support: Fabrizio Cerchia**
