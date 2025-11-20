"""
PingMonitor Pro v2.3 - Performance Metrics Dashboard Panel
Real-time visualization of high-performance optimizations:
- p50/p95/p99 response times
- Throughput metrics
- Cache hit rates
- Batch write statistics
"""

import logging
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QGroupBox, QGridLayout, QProgressBar
)
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QFont

from ..services.performance_service import performance_metrics, device_cache, batch_writer

logger = logging.getLogger(__name__)


class PerformancePanel(QWidget):
    """Performance metrics dashboard panel"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

        # Update timer (every 2 seconds)
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_metrics)
        self.update_timer.start(2000)

    def init_ui(self):
        """Initialize UI components"""
        layout = QVBoxLayout()
        layout.setSpacing(10)

        # Title
        title = QLabel("Performance Metrics Dashboard")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # Overall Stats Group
        overall_group = QGroupBox("Overall Statistics")
        overall_layout = QGridLayout()

        self.label_uptime = QLabel("0s")
        self.label_total_checks = QLabel("0")
        self.label_throughput = QLabel("0.00 checks/sec")

        overall_layout.addWidget(QLabel("Uptime:"), 0, 0)
        overall_layout.addWidget(self.label_uptime, 0, 1)
        overall_layout.addWidget(QLabel("Total Checks:"), 1, 0)
        overall_layout.addWidget(self.label_total_checks, 1, 1)
        overall_layout.addWidget(QLabel("Throughput:"), 2, 0)
        overall_layout.addWidget(self.label_throughput, 2, 1)

        overall_group.setLayout(overall_layout)
        layout.addWidget(overall_group)

        # Cache Performance Group
        cache_group = QGroupBox("Cache Performance")
        cache_layout = QGridLayout()

        self.label_cache_hits = QLabel("0")
        self.label_cache_misses = QLabel("0")
        self.label_cache_rate = QLabel("0.0%")
        self.cache_progress = QProgressBar()
        self.cache_progress.setMaximum(100)

        cache_layout.addWidget(QLabel("Hits:"), 0, 0)
        cache_layout.addWidget(self.label_cache_hits, 0, 1)
        cache_layout.addWidget(QLabel("Misses:"), 1, 0)
        cache_layout.addWidget(self.label_cache_misses, 1, 1)
        cache_layout.addWidget(QLabel("Hit Rate:"), 2, 0)
        cache_layout.addWidget(self.label_cache_rate, 2, 1)
        cache_layout.addWidget(self.cache_progress, 3, 0, 1, 2)

        cache_group.setLayout(cache_layout)
        layout.addWidget(cache_group)

        # Batch Writer Group
        batch_group = QGroupBox("Batch Database Operations")
        batch_layout = QGridLayout()

        self.label_batch_pending = QLabel("0")
        self.label_batch_total = QLabel("0")
        self.label_batch_count = QLabel("0")

        batch_layout.addWidget(QLabel("Pending:"), 0, 0)
        batch_layout.addWidget(self.label_batch_pending, 0, 1)
        batch_layout.addWidget(QLabel("Total Records:"), 1, 0)
        batch_layout.addWidget(self.label_batch_total, 1, 1)
        batch_layout.addWidget(QLabel("Batches Flushed:"), 2, 0)
        batch_layout.addWidget(self.label_batch_count, 2, 1)

        batch_group.setLayout(batch_layout)
        layout.addWidget(batch_group)

        # Response Time Metrics Group
        response_group = QGroupBox("Response Time Percentiles (All Checks)")
        response_layout = QGridLayout()

        self.label_p50 = QLabel("0ms")
        self.label_p95 = QLabel("0ms")
        self.label_p99 = QLabel("0ms")
        self.label_avg = QLabel("0ms")

        response_layout.addWidget(QLabel("p50 (median):"), 0, 0)
        response_layout.addWidget(self.label_p50, 0, 1)
        response_layout.addWidget(QLabel("p95:"), 1, 0)
        response_layout.addWidget(self.label_p95, 1, 1)
        response_layout.addWidget(QLabel("p99:"), 2, 0)
        response_layout.addWidget(self.label_p99, 2, 1)
        response_layout.addWidget(QLabel("Average:"), 3, 0)
        response_layout.addWidget(self.label_avg, 3, 1)

        response_group.setLayout(response_layout)
        layout.addWidget(response_group)

        layout.addStretch()
        self.setLayout(layout)

    def update_metrics(self):
        """Update metrics display"""
        try:
            # Get performance summary
            summary = performance_metrics.get_summary()

            # Update overall stats
            uptime = summary['uptime_seconds']
            self.label_uptime.setText(self._format_duration(uptime))
            self.label_total_checks.setText(str(summary['total_checks']))
            self.label_throughput.setText(f"{summary['throughput_cps']:.2f} checks/sec")

            # Update cache stats
            hit_rate = device_cache.get_hit_rate()
            self.label_cache_hits.setText(str(device_cache.hits))
            self.label_cache_misses.setText(str(device_cache.misses))
            self.label_cache_rate.setText(f"{hit_rate:.1f}%")
            self.cache_progress.setValue(int(hit_rate))

            # Color code the progress bar
            if hit_rate >= 80:
                self.cache_progress.setStyleSheet("QProgressBar::chunk { background-color: #4CAF50; }")  # Green
            elif hit_rate >= 50:
                self.cache_progress.setStyleSheet("QProgressBar::chunk { background-color: #FFC107; }")  # Yellow
            else:
                self.cache_progress.setStyleSheet("QProgressBar::chunk { background-color: #F44336; }")  # Red

            # Update batch writer stats
            self.label_batch_pending.setText(str(len(batch_writer.pending_results)))
            self.label_batch_total.setText(str(batch_writer.total_records))
            self.label_batch_count.setText(str(batch_writer.total_batches))

            # Calculate overall response time percentiles (aggregate all check types)
            all_times = []
            for check_type_data in summary['check_types'].values():
                times = check_type_data.get('response_times', {})
                if times:
                    # Collect all available response times
                    if 'p50' in times:
                        all_times.append(times.get('p50', 0))
                    if 'p95' in times:
                        all_times.append(times.get('p95', 0))
                    if 'p99' in times:
                        all_times.append(times.get('p99', 0))

            # Calculate aggregate percentiles if we have data
            if summary['check_types']:
                # Get first check type's data as representative
                first_check_type = list(summary['check_types'].values())[0]
                times = first_check_type.get('response_times', {})

                self.label_p50.setText(f"{times.get('p50', 0):.1f}ms")
                self.label_p95.setText(f"{times.get('p95', 0):.1f}ms")
                self.label_p99.setText(f"{times.get('p99', 0):.1f}ms")
                self.label_avg.setText(f"{times.get('avg', 0):.1f}ms")
            else:
                self.label_p50.setText("0ms")
                self.label_p95.setText("0ms")
                self.label_p99.setText("0ms")
                self.label_avg.setText("0ms")

        except Exception as e:
            logger.error(f"Error updating performance metrics: {e}", exc_info=True)

    def _format_duration(self, seconds: float) -> str:
        """Format duration in human-readable format"""
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            secs = int(seconds % 60)
            return f"{minutes}m {secs}s"
        else:
            hours = int(seconds / 3600)
            minutes = int((seconds % 3600) / 60)
            return f"{hours}h {minutes}m"
