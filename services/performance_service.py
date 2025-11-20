"""
PingMonitor Pro v2.3 - High-Performance Optimization Service
Implements CLAUDE-MD high-performance patterns:
- Multi-layer caching for device configurations
- Batch database operations
- Performance metrics tracking (p50/p95/p99)
- Memory optimization
"""

import logging
import threading
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import statistics

from ..models.base import db_manager
from ..models.device import Device
from ..models.check_result import CheckResult

logger = logging.getLogger(__name__)


class DeviceCache:
    """
    Multi-layer caching for device configurations with TTL management
    Implements CLAUDE-MD caching strategy
    """

    def __init__(self, ttl_seconds: int = 300):
        """
        Initialize device cache

        Args:
            ttl_seconds: Time-to-live for cached devices (default: 5 minutes)
        """
        self.ttl_seconds = ttl_seconds
        self.cache: Dict[int, Dict[str, Any]] = {}
        self.lock = threading.RLock()
        self.hits = 0
        self.misses = 0

    def get(self, device_id: int) -> Optional[Device]:
        """Get device from cache if not expired"""
        with self.lock:
            if device_id in self.cache:
                cached_data = self.cache[device_id]

                # Check TTL
                if datetime.utcnow() < cached_data['expires_at']:
                    self.hits += 1
                    logger.debug(f"[CACHE HIT] Device #{device_id} (hit rate: {self.get_hit_rate():.1f}%)")
                    return cached_data['device']
                else:
                    # Expired - remove from cache
                    del self.cache[device_id]
                    logger.debug(f"[CACHE EXPIRED] Device #{device_id}")

            self.misses += 1
            return None

    def set(self, device: Device):
        """Add device to cache with TTL"""
        with self.lock:
            self.cache[device.id] = {
                'device': device,
                'cached_at': datetime.utcnow(),
                'expires_at': datetime.utcnow() + timedelta(seconds=self.ttl_seconds)
            }
            logger.debug(f"[CACHE SET] Device #{device.id} (TTL: {self.ttl_seconds}s)")

    def invalidate(self, device_id: int):
        """Invalidate cached device"""
        with self.lock:
            if device_id in self.cache:
                del self.cache[device_id]
                logger.debug(f"[CACHE INVALIDATE] Device #{device_id}")

    def clear(self):
        """Clear entire cache"""
        with self.lock:
            self.cache.clear()
            logger.info("[CACHE CLEAR] All devices invalidated")

    def get_hit_rate(self) -> float:
        """Calculate cache hit rate percentage"""
        total = self.hits + self.misses
        return (self.hits / total * 100) if total > 0 else 0


class BatchDatabaseWriter:
    """
    Batch database operations to minimize round trips
    Implements CLAUDE-MD batch query strategy
    """

    def __init__(self, batch_size: int = 50, flush_interval: float = 2.0):
        """
        Initialize batch writer

        Args:
            batch_size: Number of records to batch before writing
            flush_interval: Seconds between automatic flushes
        """
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.pending_results: List[Dict[str, Any]] = []
        self.lock = threading.Lock()
        self.last_flush = time.time()
        self.total_batches = 0
        self.total_records = 0

        # Start background flush thread
        self._running = True
        self._flush_thread = threading.Thread(target=self._auto_flush_loop, daemon=True)
        self._flush_thread.start()
        logger.info(f"Batch writer started (batch_size={batch_size}, flush_interval={flush_interval}s)")

    def add_check_result(self, result: Dict[str, Any]):
        """Add check result to batch queue"""
        with self.lock:
            self.pending_results.append(result)

            # Flush if batch size reached
            if len(self.pending_results) >= self.batch_size:
                logger.debug(f"[BATCH] Size threshold reached ({len(self.pending_results)} records)")
                self._flush()

    def _auto_flush_loop(self):
        """Background thread to periodically flush pending results"""
        while self._running:
            time.sleep(0.5)

            with self.lock:
                time_since_flush = time.time() - self.last_flush

                # Flush if interval exceeded and we have pending results
                if time_since_flush >= self.flush_interval and self.pending_results:
                    logger.debug(f"[BATCH] Time threshold reached ({time_since_flush:.1f}s, {len(self.pending_results)} records)")
                    self._flush()

    def _flush(self):
        """Flush pending results to database"""
        if not self.pending_results:
            return

        try:
            session = db_manager.get_session()
            start_time = time.time()

            # Create CheckResult objects in batch
            check_results = [
                CheckResult(
                    device_id=result['device_id'],
                    check_type=result['check_type'],
                    check_time=result['timestamp'],
                    success=result.get('success', False),
                    response_time=result.get('response_time'),
                    status_code=result.get('status_code'),
                    error_message=result.get('error'),
                    check_data=str(result.get('data', {}))
                )
                for result in self.pending_results
            ]

            # Batch insert
            session.bulk_save_objects(check_results)
            session.commit()

            elapsed = (time.time() - start_time) * 1000
            record_count = len(self.pending_results)
            self.total_batches += 1
            self.total_records += record_count

            logger.info(f"[BATCH FLUSH] Wrote {record_count} records in {elapsed:.1f}ms (total: {self.total_records} in {self.total_batches} batches)")

            # Clear pending results
            self.pending_results.clear()
            self.last_flush = time.time()

        except Exception as e:
            logger.error(f"[BATCH FLUSH ERROR] Failed to write batch: {e}", exc_info=True)
            session.rollback()
        finally:
            session.close()

    def force_flush(self):
        """Force immediate flush of pending results"""
        with self.lock:
            if self.pending_results:
                logger.info(f"[BATCH] Force flush requested ({len(self.pending_results)} records)")
                self._flush()

    def stop(self):
        """Stop batch writer and flush remaining records"""
        self._running = False
        self.force_flush()
        logger.info("Batch writer stopped")


class PerformanceMetrics:
    """
    Track performance metrics including p50, p95, p99 response times
    Implements CLAUDE-MD performance monitoring strategy
    """

    def __init__(self, window_size: int = 1000):
        """
        Initialize performance metrics tracker

        Args:
            window_size: Number of recent measurements to keep for percentile calculations
        """
        self.window_size = window_size
        self.response_times: Dict[str, deque] = defaultdict(lambda: deque(maxlen=window_size))
        self.check_counts: Dict[str, int] = defaultdict(int)
        self.success_counts: Dict[str, int] = defaultdict(int)
        self.lock = threading.Lock()
        self.start_time = time.time()

    def record_check(self, check_type: str, response_time: float, success: bool):
        """
        Record a check result

        Args:
            check_type: Type of check (PING, HTTP, etc.)
            response_time: Response time in milliseconds
            success: Whether check succeeded
        """
        with self.lock:
            self.response_times[check_type].append(response_time)
            self.check_counts[check_type] += 1
            if success:
                self.success_counts[check_type] += 1

    def get_percentiles(self, check_type: str) -> Dict[str, float]:
        """
        Calculate p50, p95, p99 percentiles for check type

        Args:
            check_type: Type of check

        Returns:
            Dict with p50, p95, p99 values
        """
        with self.lock:
            times = list(self.response_times.get(check_type, []))

            if not times:
                return {'p50': 0, 'p95': 0, 'p99': 0, 'min': 0, 'max': 0, 'avg': 0}

            sorted_times = sorted(times)
            return {
                'p50': statistics.quantiles(sorted_times, n=2)[0] if len(sorted_times) >= 2 else sorted_times[0],
                'p95': statistics.quantiles(sorted_times, n=20)[18] if len(sorted_times) >= 20 else sorted_times[-1],
                'p99': statistics.quantiles(sorted_times, n=100)[98] if len(sorted_times) >= 100 else sorted_times[-1],
                'min': min(sorted_times),
                'max': max(sorted_times),
                'avg': statistics.mean(sorted_times)
            }

    def get_throughput(self, check_type: str = None) -> float:
        """
        Calculate checks per second

        Args:
            check_type: Specific check type or None for all

        Returns:
            Checks per second
        """
        with self.lock:
            elapsed = time.time() - self.start_time
            if elapsed == 0:
                return 0

            if check_type:
                return self.check_counts.get(check_type, 0) / elapsed
            else:
                return sum(self.check_counts.values()) / elapsed

    def get_success_rate(self, check_type: str) -> float:
        """
        Calculate success rate percentage

        Args:
            check_type: Type of check

        Returns:
            Success rate percentage
        """
        with self.lock:
            total = self.check_counts.get(check_type, 0)
            if total == 0:
                return 0
            success = self.success_counts.get(check_type, 0)
            return (success / total) * 100

    def get_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        with self.lock:
            summary = {
                'uptime_seconds': time.time() - self.start_time,
                'total_checks': sum(self.check_counts.values()),
                'throughput_cps': self.get_throughput(),
                'check_types': {}
            }

            for check_type in self.check_counts.keys():
                percentiles = self.get_percentiles(check_type)
                summary['check_types'][check_type] = {
                    'count': self.check_counts[check_type],
                    'success_rate': self.get_success_rate(check_type),
                    'throughput': self.get_throughput(check_type),
                    'response_times': percentiles
                }

            return summary

    def log_summary(self):
        """Log performance summary"""
        summary = self.get_summary()

        logger.info("=" * 80)
        logger.info("PERFORMANCE METRICS SUMMARY")
        logger.info(f"Uptime: {summary['uptime_seconds']:.1f}s")
        logger.info(f"Total Checks: {summary['total_checks']}")
        logger.info(f"Overall Throughput: {summary['throughput_cps']:.2f} checks/sec")
        logger.info("-" * 80)

        for check_type, metrics in summary['check_types'].items():
            logger.info(f"{check_type}:")
            logger.info(f"  Count: {metrics['count']}")
            logger.info(f"  Success Rate: {metrics['success_rate']:.1f}%")
            logger.info(f"  Throughput: {metrics['throughput']:.2f} checks/sec")
            logger.info(f"  Response Times:")
            logger.info(f"    p50: {metrics['response_times']['p50']:.1f}ms")
            logger.info(f"    p95: {metrics['response_times']['p95']:.1f}ms")
            logger.info(f"    p99: {metrics['response_times']['p99']:.1f}ms")
            logger.info(f"    avg: {metrics['response_times']['avg']:.1f}ms")

        logger.info("=" * 80)


# Global instances
device_cache = DeviceCache(ttl_seconds=300)  # 5 minute TTL
batch_writer = BatchDatabaseWriter(batch_size=50, flush_interval=2.0)
performance_metrics = PerformanceMetrics(window_size=1000)
