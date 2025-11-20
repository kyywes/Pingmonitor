"""
Charts Widget - Grafici con matplotlib integrati in PyQt6
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import logging

logger = logging.getLogger(__name__)


class MatplotlibWidget(QWidget):
    """Widget base per grafici matplotlib"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.figure = Figure(figsize=(5, 4), dpi=100)
        self.canvas = FigureCanvas(self.figure)

        layout = QVBoxLayout(self)
        layout.addWidget(self.canvas)
        layout.setContentsMargins(0, 0, 0, 0)


class PieChartWidget(MatplotlibWidget):
    """Widget per Pie Chart - Distribuzione stati dispositivi"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ax = self.figure.add_subplot(111)
        self.update_data(0, 0, 0)

    def update_data(self, online, offline, degraded):
        """Aggiorna i dati del grafico"""
        try:
            self.ax.clear()

            # Se tutti i valori sono 0, mostra placeholder
            if online == 0 and offline == 0 and degraded == 0:
                self.ax.text(0.5, 0.5, 'Nessun dato disponibile',
                           ha='center', va='center',
                           transform=self.ax.transAxes,
                           fontsize=12, color='gray')
                self.ax.axis('off')
                self.canvas.draw()
                return

            # Dati
            sizes = []
            labels = []
            colors = []

            if online > 0:
                sizes.append(online)
                labels.append(f'Online ({online})')
                colors.append('#10b981')  # Verde

            if offline > 0:
                sizes.append(offline)
                labels.append(f'Offline ({offline})')
                colors.append('#ef4444')  # Rosso

            if degraded > 0:
                sizes.append(degraded)
                labels.append(f'Degradati ({degraded})')
                colors.append('#f59e0b')  # Arancione

            # Crea pie chart
            self.ax.pie(sizes, labels=labels, colors=colors,
                       autopct='%1.1f%%', startangle=90)
            self.ax.axis('equal')
            self.ax.set_title('Distribuzione Stati Dispositivi',
                            fontsize=12, fontweight='bold', pad=10)

            self.canvas.draw()
            logger.debug(f"Pie chart updated: online={online}, offline={offline}, degraded={degraded}")

        except Exception as e:
            logger.error(f"Error updating pie chart: {e}")


class LineChartWidget(MatplotlibWidget):
    """Widget per Line Chart - Trend uptime"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ax = self.figure.add_subplot(111)

        # Dati iniziali vuoti
        self.hours = []
        self.uptime_values = []

        self._plot_initial()

    def _plot_initial(self):
        """Plot iniziale con dati di esempio"""
        try:
            self.ax.clear()

            # Dati di esempio per le ultime 24 ore
            import random
            self.hours = list(range(24))
            self.uptime_values = [95 + random.randint(-3, 5) for _ in range(24)]

            self.ax.plot(self.hours, self.uptime_values,
                        marker='o', color='#2563eb',
                        linewidth=2, markersize=4)

            self.ax.set_xlabel('Ore', fontsize=10)
            self.ax.set_ylabel('Uptime %', fontsize=10)
            self.ax.set_title('Trend Uptime Ultime 24h',
                            fontsize=12, fontweight='bold', pad=10)
            self.ax.grid(True, alpha=0.3)
            self.ax.set_ylim(85, 105)

            # Aggiungi linea di riferimento al 95%
            self.ax.axhline(y=95, color='#10b981',
                          linestyle='--', linewidth=1, alpha=0.5)

            self.figure.tight_layout()
            self.canvas.draw()

            logger.debug("Line chart initialized with sample data")

        except Exception as e:
            logger.error(f"Error plotting line chart: {e}")

    def update_data(self, hours, uptime_values):
        """Aggiorna i dati del grafico"""
        try:
            self.ax.clear()

            if not hours or not uptime_values:
                self.ax.text(0.5, 0.5, 'Nessun dato disponibile',
                           ha='center', va='center',
                           transform=self.ax.transAxes,
                           fontsize=12, color='gray')
                self.canvas.draw()
                return

            self.hours = hours
            self.uptime_values = uptime_values

            self.ax.plot(self.hours, self.uptime_values,
                        marker='o', color='#2563eb',
                        linewidth=2, markersize=4)

            self.ax.set_xlabel('Ore', fontsize=10)
            self.ax.set_ylabel('Uptime %', fontsize=10)
            self.ax.set_title('Trend Uptime Ultime 24h',
                            fontsize=12, fontweight='bold', pad=10)
            self.ax.grid(True, alpha=0.3)
            self.ax.set_ylim(85, 105)

            # Linea di riferimento
            self.ax.axhline(y=95, color='#10b981',
                          linestyle='--', linewidth=1, alpha=0.5)

            self.figure.tight_layout()
            self.canvas.draw()

            logger.debug(f"Line chart updated with {len(hours)} data points")

        except Exception as e:
            logger.error(f"Error updating line chart: {e}")


class BarChartWidget(MatplotlibWidget):
    """Widget per Bar Chart - Statistiche per DOIT"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ax = self.figure.add_subplot(111)
        self._plot_initial()

    def _plot_initial(self):
        """Plot iniziale con dati di esempio"""
        try:
            self.ax.clear()

            # Dati di esempio per DOIT
            doit_names = ['NAPOLI', 'BOLOGNA', 'VENEZIA', 'TORINO', 'MILANO']
            online = [8, 12, 10, 6, 9]
            offline = [1, 2, 1, 0, 1]

            x = range(len(doit_names))
            width = 0.35

            bars1 = self.ax.bar([i - width/2 for i in x], online,
                               width, label='Online', color='#10b981')
            bars2 = self.ax.bar([i + width/2 for i in x], offline,
                               width, label='Offline', color='#ef4444')

            self.ax.set_xlabel('DOIT', fontsize=10)
            self.ax.set_ylabel('Numero Dispositivi', fontsize=10)
            self.ax.set_title('Dispositivi per DOIT',
                            fontsize=12, fontweight='bold', pad=10)
            self.ax.set_xticks(x)
            self.ax.set_xticklabels(doit_names, rotation=45, ha='right')
            self.ax.legend()
            self.ax.grid(True, alpha=0.3, axis='y')

            self.figure.tight_layout()
            self.canvas.draw()

            logger.debug("Bar chart initialized with sample data")

        except Exception as e:
            logger.error(f"Error plotting bar chart: {e}")

    def update_data(self, doit_stats):
        """
        Aggiorna i dati del grafico
        doit_stats: dict con formato {'DOIT_NAME': {'online': N, 'offline': M}}
        """
        try:
            self.ax.clear()

            if not doit_stats:
                self.ax.text(0.5, 0.5, 'Nessun dato disponibile',
                           ha='center', va='center',
                           transform=self.ax.transAxes,
                           fontsize=12, color='gray')
                self.canvas.draw()
                return

            doit_names = list(doit_stats.keys())
            online = [doit_stats[d]['online'] for d in doit_names]
            offline = [doit_stats[d]['offline'] for d in doit_names]

            x = range(len(doit_names))
            width = 0.35

            self.ax.bar([i - width/2 for i in x], online,
                       width, label='Online', color='#10b981')
            self.ax.bar([i + width/2 for i in x], offline,
                       width, label='Offline', color='#ef4444')

            self.ax.set_xlabel('DOIT', fontsize=10)
            self.ax.set_ylabel('Numero Dispositivi', fontsize=10)
            self.ax.set_title('Dispositivi per DOIT',
                            fontsize=12, fontweight='bold', pad=10)
            self.ax.set_xticks(x)
            self.ax.set_xticklabels(doit_names, rotation=45, ha='right')
            self.ax.legend()
            self.ax.grid(True, alpha=0.3, axis='y')

            self.figure.tight_layout()
            self.canvas.draw()

            logger.debug(f"Bar chart updated with {len(doit_names)} DOIT entries")

        except Exception as e:
            logger.error(f"Error updating bar chart: {e}")
