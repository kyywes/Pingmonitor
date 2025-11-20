"""
Dashboard Widget - Modern Professional UI
Design ispirato a Grafana, DataDog e moderne dashboard enterprise
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QGridLayout, QScrollArea, QProgressBar
)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt6.QtGui import QFont, QLinearGradient, QColor, QPalette
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class ModernStatCard(QFrame):
    """
    Card statistica moderna stile Grafana/DataDog
    Con animazioni, gradients e design professionale
    """

    def __init__(self, title, value, icon, gradient_start, gradient_end, trend=""):
        super().__init__()
        self._value = value
        self._setup_ui(title, value, icon, gradient_start, gradient_end, trend)

    def _setup_ui(self, title, value, icon, gradient_start, gradient_end, trend):
        self.setFixedHeight(140)
        self.setStyleSheet(f"""
            ModernStatCard {{
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 {gradient_start},
                    stop:1 {gradient_end}
                );
                border-radius: 12px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }}
            ModernStatCard:hover {{
                border: 1px solid rgba(255, 255, 255, 0.4);
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 {gradient_start},
                    stop:1 {gradient_end}
                );
            }}
        """)

        # Add hover enter/leave events for smooth scale animation
        self.installEventFilter(self)
        self._hover_anim = None

        # Add initial shadow effect
        self.setGraphicsEffect(self._create_shadow_effect(blur_radius=10, y_offset=2))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(8)

        # Header - Icon e trend
        header = QHBoxLayout()

        icon_label = QLabel(icon)
        icon_label.setStyleSheet("""
            font-size: 28px;
            color: rgba(255, 255, 255, 0.9);
        """)
        header.addWidget(icon_label)

        header.addStretch()

        if trend:
            trend_label = QLabel(trend)
            trend_label.setStyleSheet("""
                color: rgba(255, 255, 255, 0.7);
                font-size: 12px;
                font-weight: 500;
            """)
            header.addWidget(trend_label)

        layout.addLayout(header)

        # Value con animazione
        self.value_label = QLabel(str(value))
        self.value_label.setStyleSheet("""
            color: white;
            font-size: 42px;
            font-weight: 700;
            letter-spacing: -1px;
        """)
        layout.addWidget(self.value_label)

        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            color: rgba(255, 255, 255, 0.8);
            font-size: 13px;
            font-weight: 500;
            letter-spacing: 0.5px;
            text-transform: uppercase;
        """)
        layout.addWidget(title_label)

    def update_value(self, value, animate=True):
        """Aggiorna valore con animazione opzionale"""
        old_value = self._value
        self._value = value
        self.value_label.setText(str(value))

        # Aggiungi effetto pulse se il valore cambia
        if animate and old_value != value:
            self._pulse_effect()

    def _pulse_effect(self):
        """Effetto pulse quando il valore cambia"""
        try:
            # Create scale animation
            self.scale_anim = QPropertyAnimation(self, b"geometry")
            self.scale_anim.setDuration(300)

            # Get current geometry
            current_geo = self.geometry()

            # Create slightly larger geometry for pulse
            expanded_geo = current_geo.adjusted(-3, -3, 3, 3)

            # Animate: normal -> expanded -> normal
            self.scale_anim.setStartValue(current_geo)
            self.scale_anim.setKeyValueAt(0.5, expanded_geo)
            self.scale_anim.setEndValue(current_geo)
            self.scale_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
            self.scale_anim.start()

            # Add glow effect to value label
            original_style = self.value_label.styleSheet()
            self.value_label.setStyleSheet(original_style + """
                text-shadow: 0 0 10px rgba(255, 255, 255, 0.8);
            """)

            # Reset glow after animation
            QTimer.singleShot(300, lambda: self.value_label.setStyleSheet(original_style))

        except Exception as e:
            pass  # Silently fail if animation doesn't work

    def eventFilter(self, obj, event):
        """Handle hover events for smooth animations"""
        if obj == self:
            if event.type() == event.Type.Enter:
                # Mouse entered - subtle lift effect
                self.setGraphicsEffect(self._create_shadow_effect(blur_radius=20, y_offset=5))
            elif event.type() == event.Type.Leave:
                # Mouse left - reset shadow
                self.setGraphicsEffect(self._create_shadow_effect(blur_radius=10, y_offset=2))
        return super().eventFilter(obj, event)

    def _create_shadow_effect(self, blur_radius=10, y_offset=2):
        """Create drop shadow effect"""
        from PyQt6.QtWidgets import QGraphicsDropShadowEffect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(blur_radius)
        shadow.setXOffset(0)
        shadow.setYOffset(y_offset)
        shadow.setColor(QColor(0, 0, 0, 80))
        return shadow


class DashboardWidget(QWidget):
    """Widget principale della Dashboard"""

    def __init__(self):
        super().__init__()
        logger.info("Initializing Dashboard Widget")
        self._setup_ui()

        # Timer per aggiornamento automatico
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.refresh_data)
        self.update_timer.start(2000)  # Aggiorna ogni 2 secondi

        # Add fade-in animation
        self._apply_fade_in_animation()

        logger.info("Dashboard Widget initialized")

    def _apply_fade_in_animation(self):
        """Apply smooth fade-in animation on widget load"""
        try:
            from PyQt6.QtCore import QPropertyAnimation, QEasingCurve
            from PyQt6.QtWidgets import QGraphicsOpacityEffect

            # Create opacity effect
            self.opacity_effect = QGraphicsOpacityEffect(self)
            self.setGraphicsEffect(self.opacity_effect)

            # Create animation
            self.fade_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
            self.fade_animation.setDuration(800)  # 800ms
            self.fade_animation.setStartValue(0.0)
            self.fade_animation.setEndValue(1.0)
            self.fade_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
            self.fade_animation.start()

        except Exception as e:
            logger.error(f"Failed to apply fade-in animation: {e}")

    def _setup_ui(self):
        """Setup UI della dashboard"""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)

        # Scroll area per contenuto
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(20)

        # Header
        header = self._create_header()
        content_layout.addWidget(header)

        # Stats Cards
        stats_row = self._create_stats_cards()
        content_layout.addLayout(stats_row)

        # Charts row
        charts_row = self._create_charts_section()
        content_layout.addWidget(charts_row)

        # Add stretch
        content_layout.addStretch()

        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)

    def _create_header(self):
        """Crea header della dashboard"""
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1e3a8a, stop:1 #2563eb);
                border-radius: 10px;
                padding: 20px;
            }
        """)

        layout = QHBoxLayout(header)

        # Title
        title = QLabel("📊 Dashboard Panoramica")
        title.setStyleSheet("""
            color: white;
            font-size: 24px;
            font-weight: bold;
        """)
        layout.addWidget(title)

        layout.addStretch()

        # Last update time
        self.last_update_label = QLabel()
        self.last_update_label.setStyleSheet("""
            color: rgba(255, 255, 255, 0.8);
            font-size: 12px;
        """)
        self._update_timestamp()
        layout.addWidget(self.last_update_label)

        return header

    def _create_stats_cards(self):
        """Crea le card con le statistiche - Modern Design"""
        layout = QGridLayout()
        layout.setSpacing(20)

        # Modern Stat Cards con gradienti professionali
        self.card_total = ModernStatCard(
            "Total Devices", "0", "🖥️",
            "#667eea", "#764ba2"  # Purple gradient
        )

        self.card_online = ModernStatCard(
            "Online", "0", "✓",
            "#11998e", "#38ef7d",  # Green gradient
            trend="↗ 100%"
        )

        self.card_offline = ModernStatCard(
            "Offline", "0", "✗",
            "#eb3349", "#f45c43",  # Red gradient
            trend="↘ 0%"
        )

        self.card_degraded = ModernStatCard(
            "Degraded", "0", "⚠",
            "#f2994a", "#f2c94c",  # Orange gradient
            trend="— 0%"
        )

        # Add to grid - 4 cards per row
        layout.addWidget(self.card_total, 0, 0)
        layout.addWidget(self.card_online, 0, 1)
        layout.addWidget(self.card_offline, 0, 2)
        layout.addWidget(self.card_degraded, 0, 3)

        return layout

    def _create_charts_section(self):
        """Crea sezione informativa moderna - NO grafici"""
        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: rgba(30, 41, 59, 0.4);
                border-radius: 15px;
                border: 1px solid rgba(148, 163, 184, 0.2);
            }
        """)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(25, 20, 25, 20)
        layout.setSpacing(15)

        # Title
        title = QLabel("📊 System Overview")
        title.setStyleSheet("""
            color: #e2e8f0;
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 10px;
        """)
        layout.addWidget(title)

        # Health Score Progress Bar
        health_label = QLabel("System Health Score")
        health_label.setStyleSheet("""
            color: #94a3b8;
            font-size: 13px;
            margin-bottom: 5px;
        """)
        layout.addWidget(health_label)

        self.health_bar = QProgressBar()
        self.health_bar.setValue(95)
        self.health_bar.setTextVisible(True)
        self.health_bar.setFormat("%p%")
        self.health_bar.setMinimumHeight(30)
        self.health_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 5px;
                background-color: rgba(30, 41, 59, 0.8);
                color: white;
                font-weight: 600;
                text-align: center;
            }
            QProgressBar::chunk {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #10b981, stop:1 #059669
                );
                border-radius: 5px;
            }
        """)
        layout.addWidget(self.health_bar)

        # Quick Stats Grid
        stats_grid = QGridLayout()
        stats_grid.setSpacing(15)

        # Uptime
        uptime_widget = self._create_info_widget("⏱", "Avg Uptime", "99.2%", "#10b981")
        stats_grid.addWidget(uptime_widget, 0, 0)

        # Response Time
        response_widget = self._create_info_widget("⚡", "Avg Response", "45ms", "#3b82f6")
        stats_grid.addWidget(response_widget, 0, 1)

        # Alerts Today
        alerts_widget = self._create_info_widget("🔔", "Alerts Today", "3", "#f59e0b")
        stats_grid.addWidget(alerts_widget, 1, 0)

        # Last Check
        check_widget = self._create_info_widget("🔄", "Last Check", "2s ago", "#8b5cf6")
        stats_grid.addWidget(check_widget, 1, 1)

        layout.addLayout(stats_grid)

        return container

    def _create_info_widget(self, icon, label, value, color):
        """Crea widget informativo compatto"""
        widget = QFrame()
        widget.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(30, 41, 59, 0.6);
                border-radius: 10px;
                border: 1px solid rgba(148, 163, 184, 0.1);
                padding: 12px;
            }}
            QFrame:hover {{
                border: 1px solid {color};
                background-color: rgba(30, 41, 59, 0.8);
            }}
        """)

        # Add subtle shadow effect
        from PyQt6.QtWidgets import QGraphicsDropShadowEffect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(8)
        shadow.setXOffset(0)
        shadow.setYOffset(2)
        shadow.setColor(QColor(0, 0, 0, 60))
        widget.setGraphicsEffect(shadow)

        layout = QVBoxLayout(widget)
        layout.setSpacing(5)

        # Icon e label
        header = QHBoxLayout()
        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet("font-size: 20px;")
        header.addWidget(icon_lbl)

        label_lbl = QLabel(label)
        label_lbl.setStyleSheet("""
            color: #94a3b8;
            font-size: 11px;
            font-weight: 500;
        """)
        header.addWidget(label_lbl)
        header.addStretch()

        layout.addLayout(header)

        # Value
        value_lbl = QLabel(value)
        value_lbl.setStyleSheet(f"""
            color: {color};
            font-size: 24px;
            font-weight: 700;
        """)
        layout.addWidget(value_lbl)

        return widget

    def _update_timestamp(self):
        """Aggiorna timestamp ultimo aggiornamento"""
        # Use UTC consistently with monitoring engine, then convert to local for display
        from datetime import timezone
        now_utc = datetime.utcnow().replace(tzinfo=timezone.utc)
        now_local = now_utc.astimezone()
        self.last_update_label.setText(
            f"Ultimo aggiornamento: {now_local.strftime('%d/%m/%Y %H:%M:%S')}"
        )

    def refresh_data(self):
        """Aggiorna i dati della dashboard"""
        try:
            # Leggi dati dal monitoring engine se disponibile
            if hasattr(self, 'monitoring_engine') and self.monitoring_engine:
                devices = list(self.monitoring_engine.devices.values())
                total = len(devices)
                online = sum(1 for d in devices if d.current_status == 'online')
                offline = sum(1 for d in devices if d.current_status == 'offline')
                degraded = sum(1 for d in devices if d.current_status == 'degraded')
            else:
                # Fallback a dati di esempio se engine non disponibile
                total = 14
                online = 10
                offline = 2
                degraded = 2

            # Aggiorna cards con animazione
            self.card_total.update_value(total, animate=True)
            self.card_online.update_value(online, animate=True)
            self.card_offline.update_value(offline, animate=True)
            self.card_degraded.update_value(degraded, animate=True)

            # Calcola e aggiorna Health Score
            if total > 0:
                health_score = int((online / total) * 100)

                # Animate health bar value change
                old_value = self.health_bar.value()
                if old_value != health_score:
                    self._animate_health_bar(old_value, health_score)
                else:
                    self.health_bar.setValue(health_score)

                # Cambia colore in base allo score
                if health_score >= 90:
                    color_start, color_end = "#10b981", "#059669"  # Verde
                elif health_score >= 70:
                    color_start, color_end = "#f59e0b", "#ea580c"  # Arancione
                else:
                    color_start, color_end = "#ef4444", "#dc2626"  # Rosso

                self.health_bar.setStyleSheet(f"""
                    QProgressBar {{
                        border: none;
                        border-radius: 5px;
                        background-color: rgba(30, 41, 59, 0.8);
                        color: white;
                        font-weight: 600;
                        text-align: center;
                    }}
                    QProgressBar::chunk {{
                        background: qlineargradient(
                            x1:0, y1:0, x2:1, y2:0,
                            stop:0 {color_start}, stop:1 {color_end}
                        );
                        border-radius: 5px;
                    }}
                """)

            # Aggiorna timestamp
            self._update_timestamp()

            logger.debug(f"Dashboard refreshed: total={total}, online={online}, offline={offline}, degraded={degraded}")

        except Exception as e:
            logger.error(f"Error refreshing dashboard data: {e}")

    def _animate_health_bar(self, start_value, end_value):
        """Animate health bar value change smoothly"""
        try:
            # Create value animation
            self.health_bar_anim = QPropertyAnimation(self.health_bar, b"value")
            self.health_bar_anim.setDuration(600)  # 600ms smooth animation
            self.health_bar_anim.setStartValue(start_value)
            self.health_bar_anim.setEndValue(end_value)
            self.health_bar_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
            self.health_bar_anim.start()
        except Exception as e:
            # Fallback to instant update if animation fails
            self.health_bar.setValue(end_value)

    def set_monitoring_engine(self, engine):
        """Imposta il monitoring engine per leggere dati reali"""
        self.monitoring_engine = engine
        logger.info("Monitoring engine set for dashboard")
