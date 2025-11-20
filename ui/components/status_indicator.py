"""
Professional Status Indicator Components
Modern, animated status badges with pulse effects
"""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QRadialGradient
import logging

logger = logging.getLogger(__name__)


class StatusDot(QWidget):
    """
    Animated status dot with pulse effect
    Professional design with gradient and glow
    """

    STATUS_COLORS = {
        'online': {
            'primary': QColor(16, 185, 129),    # Emerald 500
            'glow': QColor(16, 185, 129, 100),
            'text': '#10b981',
            'bg': 'rgba(16, 185, 129, 0.1)',
            'label': 'Online',
        },
        'offline': {
            'primary': QColor(239, 68, 68),     # Red 500
            'glow': QColor(239, 68, 68, 100),
            'text': '#ef4444',
            'bg': 'rgba(239, 68, 68, 0.1)',
            'label': 'Offline',
        },
        'degraded': {
            'primary': QColor(245, 158, 11),    # Amber 500
            'glow': QColor(245, 158, 11, 100),
            'text': '#f59e0b',
            'bg': 'rgba(245, 158, 11, 0.1)',
            'label': 'Degraded',
        },
        'warning': {
            'primary': QColor(245, 158, 11),    # Amber 500
            'glow': QColor(245, 158, 11, 100),
            'text': '#f59e0b',
            'bg': 'rgba(245, 158, 11, 0.1)',
            'label': 'Warning',
        },
        'unknown': {
            'primary': QColor(100, 116, 139),   # Slate 500
            'glow': QColor(100, 116, 139, 80),
            'text': '#64748b',
            'bg': 'rgba(100, 116, 139, 0.1)',
            'label': 'Unknown',
        },
        'pending': {
            'primary': QColor(59, 130, 246),    # Blue 500
            'glow': QColor(59, 130, 246, 100),
            'text': '#3b82f6',
            'bg': 'rgba(59, 130, 246, 0.1)',
            'label': 'Pending',
        },
    }

    def __init__(self, status='unknown', size=10, animate=True):
        """
        Initialize status dot

        Args:
            status: Status type ('online', 'offline', 'degraded', 'warning', 'unknown', 'pending')
            size: Dot diameter in pixels
            animate: Enable pulse animation
        """
        super().__init__()
        self._status = status
        self._size = size
        self._animate = animate
        self._pulse_opacity = 1.0

        self.setFixedSize(size * 2, size * 2)  # Extra space for glow

        # Setup pulse animation
        if animate and status in ['online', 'degraded', 'pending']:
            self._setup_pulse_animation()

    def _setup_pulse_animation(self):
        """Setup pulse animation for active statuses"""
        self._pulse_anim = QPropertyAnimation(self, b"pulseOpacity")
        self._pulse_anim.setDuration(2000)  # 2 second cycle
        self._pulse_anim.setStartValue(1.0)
        self._pulse_anim.setKeyValueAt(0.5, 0.3)
        self._pulse_anim.setEndValue(1.0)
        self._pulse_anim.setEasingCurve(QEasingCurve.Type.InOutSine)
        self._pulse_anim.setLoopCount(-1)  # Infinite loop
        self._pulse_anim.start()

    def get_pulse_opacity(self):
        return self._pulse_opacity

    def set_pulse_opacity(self, value):
        self._pulse_opacity = value
        self.update()

    pulseOpacity = pyqtProperty(float, get_pulse_opacity, set_pulse_opacity)

    def set_status(self, status):
        """Update status and restart animation if needed"""
        if self._status == status:
            return

        self._status = status

        # Stop existing animation
        if hasattr(self, '_pulse_anim'):
            self._pulse_anim.stop()

        # Start new animation if needed
        if self._animate and status in ['online', 'degraded', 'pending']:
            self._setup_pulse_animation()

        self.update()

    def paintEvent(self, event):
        """Custom paint for status dot with glow effect"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        colors = self.STATUS_COLORS.get(self._status, self.STATUS_COLORS['unknown'])
        center_x = self.width() / 2
        center_y = self.height() / 2

        # Draw glow (pulsing outer circle)
        if self._animate and self._status in ['online', 'degraded', 'pending']:
            glow_color = QColor(colors['glow'])
            glow_color.setAlphaF(self._pulse_opacity * 0.5)

            gradient = QRadialGradient(center_x, center_y, self._size)
            gradient.setColorAt(0, glow_color)
            gradient.setColorAt(1, QColor(0, 0, 0, 0))

            painter.setBrush(QBrush(gradient))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(
                int(center_x - self._size),
                int(center_y - self._size),
                self._size * 2,
                self._size * 2
            )

        # Draw main dot
        painter.setBrush(QBrush(colors['primary']))
        painter.setPen(Qt.PenStyle.NoPen)
        dot_radius = self._size // 2
        painter.drawEllipse(
            int(center_x - dot_radius),
            int(center_y - dot_radius),
            dot_radius * 2,
            dot_radius * 2
        )

        # Draw highlight (make it shiny)
        highlight = QRadialGradient(
            center_x - dot_radius * 0.3,
            center_y - dot_radius * 0.3,
            dot_radius * 0.8
        )
        highlight_color = QColor(255, 255, 255, 80)
        highlight.setColorAt(0, highlight_color)
        highlight.setColorAt(1, QColor(255, 255, 255, 0))

        painter.setBrush(QBrush(highlight))
        painter.drawEllipse(
            int(center_x - dot_radius),
            int(center_y - dot_radius),
            dot_radius * 2,
            dot_radius * 2
        )


class StatusBadge(QWidget):
    """
    Professional status badge with dot and label
    """

    def __init__(self, status='unknown', show_label=True, size='md'):
        """
        Initialize status badge

        Args:
            status: Status type
            show_label: Show text label
            size: Badge size ('sm', 'md', 'lg')
        """
        super().__init__()
        self._status = status
        self._show_label = show_label

        # Size configurations
        sizes = {
            'sm': {'dot': 6, 'font': 11, 'padding': 6},
            'md': {'dot': 8, 'font': 13, 'padding': 8},
            'lg': {'dot': 10, 'font': 14, 'padding': 10},
        }
        config = sizes.get(size, sizes['md'])

        self._setup_ui(config)

    def _setup_ui(self, config):
        """Setup badge UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(config['padding'], config['padding'] // 2,
                                 config['padding'], config['padding'] // 2)
        layout.setSpacing(6)

        # Status dot
        self.dot = StatusDot(self._status, size=config['dot'], animate=True)
        layout.addWidget(self.dot)

        # Label
        if self._show_label:
            colors = StatusDot.STATUS_COLORS.get(self._status, StatusDot.STATUS_COLORS['unknown'])
            self.label = QLabel(colors['label'])
            self.label.setStyleSheet(f"""
                QLabel {{
                    color: {colors['text']};
                    font-size: {config['font']}px;
                    font-weight: 600;
                    background: transparent;
                }}
            """)
            layout.addWidget(self.label)

        # Badge background
        colors = StatusDot.STATUS_COLORS.get(self._status, StatusDot.STATUS_COLORS['unknown'])
        self.setStyleSheet(f"""
            StatusBadge {{
                background-color: {colors['bg']};
                border: 1px solid {colors['text']};
                border-radius: 12px;
            }}
        """)

    def set_status(self, status):
        """Update badge status"""
        if self._status == status:
            return

        self._status = status
        self.dot.set_status(status)

        colors = StatusDot.STATUS_COLORS.get(status, StatusDot.STATUS_COLORS['unknown'])

        if self._show_label:
            self.label.setText(colors['label'])
            self.label.setStyleSheet(f"""
                QLabel {{
                    color: {colors['text']};
                    font-size: 13px;
                    font-weight: 600;
                    background: transparent;
                }}
            """)

        self.setStyleSheet(f"""
            StatusBadge {{
                background-color: {colors['bg']};
                border: 1px solid {colors['text']};
                border-radius: 12px;
            }}
        """)


class StatusIndicatorCell(QWidget):
    """
    Status cell for table usage with dot + text
    Optimized for table rows
    """

    def __init__(self, status='unknown'):
        super().__init__()
        self._status = status
        self._setup_ui()

    def _setup_ui(self):
        """Setup cell UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        # Status dot
        self.dot = StatusDot(self._status, size=8, animate=True)
        layout.addWidget(self.dot)

        # Status label
        colors = StatusDot.STATUS_COLORS.get(self._status, StatusDot.STATUS_COLORS['unknown'])
        self.label = QLabel(colors['label'].upper())
        self.label.setStyleSheet(f"""
            QLabel {{
                color: {colors['text']};
                font-size: 12px;
                font-weight: 600;
                letter-spacing: 0.5px;
                background: transparent;
            }}
        """)
        layout.addWidget(self.label)
        layout.addStretch()

        # Transparent background
        self.setStyleSheet("background: transparent;")

    def set_status(self, status):
        """Update cell status"""
        if self._status == status:
            return

        self._status = status
        self.dot.set_status(status)

        colors = StatusDot.STATUS_COLORS.get(status, StatusDot.STATUS_COLORS['unknown'])
        self.label.setText(colors['label'].upper())
        self.label.setStyleSheet(f"""
            QLabel {{
                color: {colors['text']};
                font-size: 12px;
                font-weight: 600;
                letter-spacing: 0.5px;
                background: transparent;
            }}
        """)


class StatusCard(QWidget):
    """
    Large status card for dashboard
    Shows status with icon, label, and count
    """

    def __init__(self, status='online', count=0, title=None):
        super().__init__()
        self._status = status
        self._count = count
        self._title = title
        self._setup_ui()

    def _setup_ui(self):
        """Setup card UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 16, 20, 16)

        colors = StatusDot.STATUS_COLORS.get(self._status, StatusDot.STATUS_COLORS['unknown'])

        # Header with dot
        header = QHBoxLayout()
        dot = StatusDot(self._status, size=12, animate=True)
        header.addWidget(dot)

        if self._title:
            title_label = QLabel(self._title)
            title_label.setStyleSheet(f"""
                QLabel {{
                    color: #94a3b8;
                    font-size: 12px;
                    font-weight: 600;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                    background: transparent;
                }}
            """)
            header.addWidget(title_label)

        header.addStretch()
        layout.addLayout(header)

        # Count
        self.count_label = QLabel(str(self._count))
        self.count_label.setStyleSheet(f"""
            QLabel {{
                color: {colors['text']};
                font-size: 36px;
                font-weight: 700;
                background: transparent;
            }}
        """)
        layout.addWidget(self.count_label)

        # Status label
        status_label = QLabel(colors['label'])
        status_label.setStyleSheet("""
            QLabel {
                color: #cbd5e1;
                font-size: 14px;
                font-weight: 500;
                background: transparent;
            }
        """)
        layout.addWidget(status_label)

        # Card styling
        self.setStyleSheet(f"""
            StatusCard {{
                background-color: #1e293b;
                border: 1px solid {colors['text']};
                border-radius: 12px;
            }}
        """)

        self.setFixedHeight(140)

    def update_count(self, count):
        """Update count with animation"""
        self._count = count
        self.count_label.setText(str(count))
