"""
PingMonitor Pro v2.3 - Logs Viewer Widget
Real-time log viewer with filtering
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QComboBox, QCheckBox, QGroupBox
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QTextCharFormat, QColor, QTextCursor
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class LogsViewer(QWidget):
    """Log viewer widget with filtering and auto-refresh"""

    def __init__(self):
        super().__init__()
        self.log_path = self._get_log_path()
        self.auto_refresh = True
        self.last_position = 0
        self._setup_ui()
        self._start_auto_refresh()

    def _get_log_path(self):
        """Get log file path"""
        import os
        if os.name == 'nt':
            log_dir = Path(os.environ.get('USERPROFILE', '~')) / '.pingmonitor' / 'logs'
        else:
            log_dir = Path.home() / '.pingmonitor' / 'logs'

        log_dir.mkdir(parents=True, exist_ok=True)
        return log_dir / 'pingmonitor.log'

    def _setup_ui(self):
        """Setup UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Title
        title = QLabel("📝 Log Applicazione")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #1e40af; margin-bottom: 10px;")
        layout.addWidget(title)

        # Log file info
        log_info = QLabel(f"📁 Log file: {self.log_path}")
        log_info.setStyleSheet("color: #666; font-size: 11px; margin-bottom: 10px;")
        log_info.setWordWrap(True)
        layout.addWidget(log_info)

        # Controls
        controls_layout = QHBoxLayout()

        # Filter by level
        controls_layout.addWidget(QLabel("Filtro:"))

        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["All", "INFO", "WARNING", "ERROR", "CRITICAL", "DEBUG"])
        self.filter_combo.currentTextChanged.connect(self._apply_filter)
        controls_layout.addWidget(self.filter_combo)

        controls_layout.addSpacing(20)

        # Auto-refresh checkbox
        self.auto_refresh_check = QCheckBox("Auto-aggiornamento")
        self.auto_refresh_check.setChecked(True)
        self.auto_refresh_check.stateChanged.connect(self._toggle_auto_refresh)
        controls_layout.addWidget(self.auto_refresh_check)

        controls_layout.addSpacing(20)

        # Refresh button
        btn_refresh = QPushButton("🔄 Aggiorna")
        btn_refresh.clicked.connect(self._load_logs)
        btn_refresh.setStyleSheet("""
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
        controls_layout.addWidget(btn_refresh)

        # Clear button
        btn_clear = QPushButton("🗑️ Pulisci")
        btn_clear.clicked.connect(self._clear_display)
        btn_clear.setStyleSheet("""
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
        controls_layout.addWidget(btn_clear)

        # Open log folder button
        btn_open_folder = QPushButton("📂 Apri Cartella Log")
        btn_open_folder.clicked.connect(self._open_log_folder)
        controls_layout.addWidget(btn_open_folder)

        controls_layout.addStretch()
        layout.addLayout(controls_layout)

        # Statistics
        stats_layout = QHBoxLayout()

        self.lbl_total = QLabel("Totale: 0")
        self.lbl_total.setStyleSheet("padding: 5px 10px; background-color: #e5e7eb; border-radius: 5px;")
        stats_layout.addWidget(self.lbl_total)

        self.lbl_errors = QLabel("🔴 Errori: 0")
        self.lbl_errors.setStyleSheet("padding: 5px 10px; background-color: #fee2e2; border-radius: 5px; color: #dc2626;")
        stats_layout.addWidget(self.lbl_errors)

        self.lbl_warnings = QLabel("🟡 Avvisi: 0")
        self.lbl_warnings.setStyleSheet("padding: 5px 10px; background-color: #fef3c7; border-radius: 5px; color: #d97706;")
        stats_layout.addWidget(self.lbl_warnings)

        self.lbl_info = QLabel("🔵 Info: 0")
        self.lbl_info.setStyleSheet("padding: 5px 10px; background-color: #dbeafe; border-radius: 5px; color: #2563eb;")
        stats_layout.addWidget(self.lbl_info)

        stats_layout.addStretch()
        layout.addLayout(stats_layout)

        # Log display
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                font-size: 12px;
                border: 1px solid #333;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        layout.addWidget(self.log_display)

        # Load initial logs
        self._load_logs()

    def _load_logs(self):
        """Load logs from file"""
        try:
            if not self.log_path.exists():
                self.log_display.setPlainText("Nessun file di log trovato. Avvia il monitoraggio per generare i log.")
                return

            with open(self.log_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # Count by level
            total = len(lines)
            errors = sum(1 for line in lines if 'ERROR' in line or 'CRITICAL' in line)
            warnings = sum(1 for line in lines if 'WARNING' in line)
            info = sum(1 for line in lines if 'INFO' in line)

            # Update statistics
            self.lbl_total.setText(f"Totale: {total}")
            self.lbl_errors.setText(f"🔴 Errori: {errors}")
            self.lbl_warnings.setText(f"🟡 Avvisi: {warnings}")
            self.lbl_info.setText(f"🔵 Info: {info}")

            # Apply filter
            self._apply_filter()

        except Exception as e:
            logger.error(f"Failed to load logs: {e}")
            self.log_display.setPlainText(f"Error loading logs: {str(e)}")

    def _apply_filter(self):
        """Apply level filter to logs"""
        try:
            if not self.log_path.exists():
                return

            filter_level = self.filter_combo.currentText()

            with open(self.log_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # Filter lines
            if filter_level == "All":
                filtered_lines = lines
            else:
                filtered_lines = [line for line in lines if filter_level in line]

            # Display with colors
            self.log_display.clear()
            cursor = self.log_display.textCursor()

            for line in filtered_lines[-1000:]:  # Last 1000 lines
                # Color based on level
                if 'ERROR' in line or 'CRITICAL' in line:
                    fmt = QTextCharFormat()
                    fmt.setForeground(QColor("#ef4444"))
                    cursor.setCharFormat(fmt)
                elif 'WARNING' in line:
                    fmt = QTextCharFormat()
                    fmt.setForeground(QColor("#f59e0b"))
                    cursor.setCharFormat(fmt)
                elif 'INFO' in line:
                    fmt = QTextCharFormat()
                    fmt.setForeground(QColor("#22c55e"))
                    cursor.setCharFormat(fmt)
                elif 'DEBUG' in line:
                    fmt = QTextCharFormat()
                    fmt.setForeground(QColor("#a3a3a3"))
                    cursor.setCharFormat(fmt)
                else:
                    fmt = QTextCharFormat()
                    fmt.setForeground(QColor("#d4d4d4"))
                    cursor.setCharFormat(fmt)

                cursor.insertText(line)

            # Scroll to bottom
            self.log_display.moveCursor(QTextCursor.MoveOperation.End)

        except Exception as e:
            logger.error(f"Failed to apply filter: {e}")

    def _clear_display(self):
        """Clear log display"""
        self.log_display.clear()
        self.lbl_total.setText("Totale: 0")
        self.lbl_errors.setText("🔴 Errori: 0")
        self.lbl_warnings.setText("🟡 Avvisi: 0")
        self.lbl_info.setText("🔵 Info: 0")

    def _open_log_folder(self):
        """Open log folder in file explorer"""
        try:
            import subprocess
            import os

            log_dir = self.log_path.parent

            if os.name == 'nt':
                subprocess.run(['explorer', str(log_dir)])
            elif os.name == 'posix':
                subprocess.run(['xdg-open', str(log_dir)])
            else:
                subprocess.run(['open', str(log_dir)])

        except Exception as e:
            logger.error(f"Failed to open log folder: {e}")

    def _toggle_auto_refresh(self, state):
        """Toggle auto-refresh"""
        self.auto_refresh = bool(state)

    def _start_auto_refresh(self):
        """Start auto-refresh timer"""
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self._auto_refresh_logs)
        self.refresh_timer.start(2000)  # Refresh every 2 seconds

    def _auto_refresh_logs(self):
        """Auto-refresh logs if enabled"""
        if self.auto_refresh and self.log_path.exists():
            try:
                # Only reload if file changed
                current_size = self.log_path.stat().st_size
                if current_size != getattr(self, '_last_size', 0):
                    self._load_logs()
                    self._last_size = current_size
            except:
                pass
