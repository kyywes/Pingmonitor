"""
PingMonitor Pro v2.0 - Core Monitoring Engine
Advanced monitoring engine with async support and intelligent scheduling
"""

import asyncio
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue, PriorityQueue
import logging

from ..models.device import Device
from ..models.check_result import CheckResult, CheckType
from ..models.base import db_manager
from ..services.performance_service import batch_writer, performance_metrics, device_cache

logger = logging.getLogger(__name__)


class CheckTask:
    """Represents a monitoring check task"""

    def __init__(self, device: Device, check_type: CheckType, priority: int = 5):
        self.device = device
        self.check_type = check_type
        self.priority = priority
        self.scheduled_time = datetime.utcnow()
        self.retry_count = 0

    def __lt__(self, other):
        """For priority queue ordering"""
        return self.priority < other.priority


class MonitoringEngine:
    """
    Main monitoring engine with intelligent task scheduling
    """

    def __init__(self, max_workers: int = 10):
        """
        Initialize monitoring engine

        Args:
            max_workers: Maximum number of concurrent workers
        """
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.executor_shutdown = False  # Track if executor has been shutdown
        self.task_queue = PriorityQueue()
        self.result_queue = Queue()

        self.running = False
        self.paused = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._scheduler_thread: Optional[threading.Thread] = None

        self.devices: Dict[int, Device] = {}
        self.last_check_times: Dict[int, datetime] = {}
        self.check_services: Dict[CheckType, Callable] = {}

        # Thread safety locks
        self._last_check_times_lock = threading.Lock()
        self._recovery_attempts_lock = threading.Lock()
        self._active_timers_lock = threading.Lock()

        # Track active timers for cleanup
        self._active_timers: List[threading.Timer] = []

        self.statistics = {
            'total_checks': 0,
            'successful_checks': 0,
            'failed_checks': 0,
            'average_response_time': 0.0
        }

        self.callbacks = {
            'on_check_complete': [],
            'on_status_change': [],
            'on_alert': [],
            'on_error': [],
            'on_recovery_success': [],
            'on_recovery_failure': []
        }

        self.auto_recovery_service = None  # Set via set_auto_recovery_service()
        self.recovery_attempts = {}  # Track recovery attempts per device

        logger.info(f"Monitoring engine initialized with {max_workers} workers")

    def _schedule_timer(self, delay: float, function: Callable, args=()) -> threading.Timer:
        """
        Schedule a timer and track it for cleanup (prevents memory leaks)

        Args:
            delay: Delay in seconds
            function: Function to call
            args: Arguments for function

        Returns:
            The timer object
        """
        # Wrapper to auto-remove timer after execution
        def wrapper():
            try:
                function(*args)
            finally:
                # Remove timer from active list after execution
                with self._active_timers_lock:
                    if timer in self._active_timers:
                        self._active_timers.remove(timer)

        timer = threading.Timer(delay, wrapper)
        with self._active_timers_lock:
            self._active_timers.append(timer)
        timer.start()
        return timer

    def _cleanup_timers(self):
        """Cancel all active timers (thread-safe)"""
        with self._active_timers_lock:
            # Create a copy to iterate safely while avoiding holding lock too long
            timers_to_cancel = self._active_timers.copy()
            self._active_timers.clear()

        # Cancel outside the lock to avoid blocking other timer operations
        cancelled_count = 0
        for timer in timers_to_cancel:
            try:
                timer.cancel()
                cancelled_count += 1
            except Exception as e:
                logger.debug(f"Failed to cancel timer: {e}")

        logger.info(f"Cancelled {cancelled_count} timers")

    def register_check_service(self, check_type: CheckType, service: Callable):
        """
        Register a check service

        Args:
            check_type: Type of check
            service: Callable that performs the check
        """
        self.check_services[check_type] = service
        logger.debug(f"Registered check service: {check_type.value}")

    def set_auto_recovery_service(self, auto_recovery_service):
        """
        Set the auto-recovery service

        Args:
            auto_recovery_service: AutoRecoveryService instance
        """
        self.auto_recovery_service = auto_recovery_service
        logger.info("Auto-recovery service set for monitoring engine")

    def add_device(self, device: Device):
        """
        Add a device to monitoring

        Args:
            device: Device to monitor
        """
        # Auto-enable SSH for PAI-PL devices to allow auto-recovery
        if hasattr(device, 'device_type') and device.device_type == 'PAI-PL':
            device.ssh_enabled = True
            logger.info(f"SSH auto-enabled for PAI-PL device: {device.name}")

        self.devices[device.id] = device
        self.last_check_times[device.id] = datetime.utcnow() - timedelta(hours=1)
        logger.info(f"Device added to monitoring: {device.name} ({device.ip_address})")

    def remove_device(self, device_id: int):
        """
        Remove a device from monitoring

        Args:
            device_id: Device ID to remove
        """
        if device_id in self.devices:
            device = self.devices[device_id]
            del self.devices[device_id]
            if device_id in self.last_check_times:
                del self.last_check_times[device_id]
            logger.info(f"Device removed from monitoring: {device.name}")

    def load_devices(self):
        """Load all enabled devices from database"""
        session = db_manager.get_session()
        try:
            devices = session.query(Device).filter_by(enabled=True).all()

            for device in devices:
                # Detach from session to avoid issues with threading
                session.expunge(device)
                self.add_device(device)

            logger.info(f"Loaded {len(devices)} devices from database")
        except Exception as e:
            logger.error(f"Failed to load devices: {e}")
        finally:
            session.close()

    def start(self):
        """Start the monitoring engine"""
        if self.running:
            logger.warning("Monitoring engine is already running")
            return

        self.running = True
        self.paused = False

        # Recreate executor if it was shutdown (after stop/restart)
        if self.executor_shutdown:
            logger.info("Recreating ThreadPoolExecutor after stop")
            self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
            self.executor_shutdown = False

        # Load devices
        logger.info("=" * 80)
        logger.info("STARTING MONITORING ENGINE")
        logger.info(f"Timestamp: {datetime.utcnow().isoformat()}")
        logger.info(f"Max workers: {self.max_workers}")
        logger.info("=" * 80)
        logger.info("Loading devices from database...")
        self.load_devices()
        logger.info(f"Devices loaded: {len(self.devices)}")
        for device_id, device in self.devices.items():
            logger.info(f"  - Device #{device_id}: {device.name} ({device.ip_address}) - Status: {device.current_status} - Interval: {device.check_interval}s")

        # Start monitoring thread
        logger.info("Starting monitoring thread...")
        self._monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self._monitor_thread.start()

        # Start scheduler thread
        logger.info("Starting scheduler thread...")
        self._scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self._scheduler_thread.start()

        logger.info("=" * 80)
        logger.info("MONITORING ENGINE STARTED SUCCESSFULLY")
        logger.info("=" * 80)

        # Check for devices already in DEGRADED state and trigger recovery
        self._recover_already_degraded_devices()

    def stop(self):
        """Stop the monitoring engine with proper cleanup"""
        if not self.running:
            logger.warning("Monitoring engine is not running")
            return

        logger.info("Stopping monitoring engine...")
        self.running = False
        self.paused = False

        try:
            # 1. Cancel all active timers FIRST to prevent new tasks
            logger.info("Cancelling active timers...")
            with self._active_timers_lock:
                for timer in self._active_timers:
                    if timer.is_alive():
                        timer.cancel()
                self._active_timers.clear()

            # 2. Wait for monitor thread to finish (max 2 seconds)
            logger.info("Waiting for monitor thread...")
            if self._monitor_thread and self._monitor_thread.is_alive():
                self._monitor_thread.join(timeout=2.0)
                if self._monitor_thread.is_alive():
                    logger.warning("Monitor thread did not finish in time")

            # 3. Wait for scheduler thread to finish (max 2 seconds)
            logger.info("Waiting for scheduler thread...")
            if self._scheduler_thread and self._scheduler_thread.is_alive():
                self._scheduler_thread.join(timeout=2.0)
                if self._scheduler_thread.is_alive():
                    logger.warning("Scheduler thread did not finish in time")

            # 4. Shutdown executor with short timeout
            logger.info("Shutting down executor...")
            if self.executor and not self.executor_shutdown:
                try:
                    self.executor.shutdown(wait=True, cancel_futures=True)
                    self.executor_shutdown = True
                except Exception as e:
                    logger.warning(f"Executor shutdown warning: {e}")

            # 5. Clear queues
            logger.info("Clearing task queues...")
            while not self.task_queue.empty():
                try:
                    self.task_queue.get_nowait()
                except:
                    break

            # 6. Flush pending batch writes
            logger.info("Flushing pending database writes...")
            try:
                batch_writer.force_flush()
            except Exception as e:
                logger.warning(f"Batch writer flush warning: {e}")

            # 7. Log final performance metrics
            logger.info("Final performance summary:")
            try:
                performance_metrics.log_summary()
                logger.info(f"Device cache hit rate: {device_cache.get_hit_rate():.1f}% ({device_cache.hits} hits, {device_cache.misses} misses)")
            except Exception as e:
                logger.warning(f"Performance metrics warning: {e}")

            logger.info("Monitoring engine stopped successfully")

        except Exception as e:
            logger.error(f"Error stopping engine: {e}", exc_info=True)

    def pause(self):
        """Pause monitoring"""
        self.paused = True
        logger.info("Monitoring paused")

    def resume(self):
        """Resume monitoring"""
        self.paused = False
        logger.info("Monitoring resumed")

    def _scheduler_loop(self):
        """Main scheduler loop - schedules check tasks"""
        logger.debug("Scheduler loop started")
        last_perf_log = time.time()
        last_queue_check = time.time()

        while self.running:
            try:
                if self.paused:
                    time.sleep(1)
                    continue

                current_time = datetime.utcnow()

                # Schedule checks for all devices (thread-safe)
                for device in self.devices.values():
                    if not device.enabled:
                        continue

                    with self._last_check_times_lock:
                        last_check = self.last_check_times.get(device.id)
                        check_interval = timedelta(seconds=device.check_interval)

                        if last_check is None or (current_time - last_check) >= check_interval:
                            logger.info(f"[SCHEDULER] Scheduling checks for {device.name} ({device.ip_address}) - Last check: {last_check}, Interval: {device.check_interval}s")
                            self._schedule_device_checks(device)
                            self.last_check_times[device.id] = current_time

                # Log performance metrics every 5 minutes
                if time.time() - last_perf_log >= 300:
                    performance_metrics.log_summary()
                    last_perf_log = time.time()

                # Monitor queue size every 30 seconds for memory optimization
                if time.time() - last_queue_check >= 30:
                    queue_size = self.task_queue.qsize()
                    if queue_size > 100:
                        logger.warning(f"[MEMORY] Task queue size high: {queue_size} tasks pending")
                    last_queue_check = time.time()

                time.sleep(5)  # Scheduler runs every 5 seconds

            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}", exc_info=True)
                time.sleep(5)

    def _schedule_device_checks(self, device: Device):
        """
        Schedule all enabled checks for a device

        Args:
            device: Device to schedule checks for
        """
        # Determine priority based on device status
        priority = self._calculate_priority(device)
        checks_scheduled = []

        if device.ping_enabled:
            self.task_queue.put((priority, CheckTask(device, CheckType.PING, priority)))
            checks_scheduled.append("PING")

        if device.http_enabled:
            self.task_queue.put((priority, CheckTask(device, CheckType.HTTP, priority)))
            checks_scheduled.append("HTTP")

        if device.https_enabled:
            self.task_queue.put((priority, CheckTask(device, CheckType.HTTPS, priority)))
            checks_scheduled.append("HTTPS")

        if device.ssh_enabled:
            self.task_queue.put((priority, CheckTask(device, CheckType.SSH, priority)))
            checks_scheduled.append("SSH")

        if device.dns_enabled:
            self.task_queue.put((priority, CheckTask(device, CheckType.DNS, priority)))
            checks_scheduled.append("DNS")

        if device.snmp_enabled:
            self.task_queue.put((priority, CheckTask(device, CheckType.SNMP, priority)))
            checks_scheduled.append("SNMP")

        if checks_scheduled:
            logger.info(f"[QUEUE] Added tasks for {device.name}: {', '.join(checks_scheduled)} (priority: {priority})")

    def _calculate_priority(self, device: Device) -> int:
        """
        Calculate check priority based on device status

        Args:
            device: Device to calculate priority for

        Returns:
            Priority value (lower = higher priority)
        """
        if device.current_status == 'offline':
            return 1  # Highest priority for offline devices
        elif device.current_status == 'degraded':
            return 3
        else:
            return 5  # Normal priority for online devices

    def force_immediate_check(self, device_id: Optional[int] = None) -> None:
        """
        Force an immediate check for specific device or all devices (thread-safe)

        Args:
            device_id: Device ID to check, or None for all devices
        """
        # Set last check time to past to trigger immediate scheduling
        force_time = datetime.utcnow() - timedelta(hours=1)

        with self._last_check_times_lock:
            if device_id is not None:
                if device_id in self.last_check_times:
                    self.last_check_times[device_id] = force_time
                    logger.info(f"Forced immediate check for device {device_id}")
            else:
                # Force all devices
                for dev_id in self.devices:
                    self.last_check_times[dev_id] = force_time
                logger.info(f"Forced immediate check for all {len(self.devices)} devices")

    def reload_devices(self) -> int:
        """
        Reload devices from database without stopping monitoring

        Returns:
            Number of devices loaded
        """
        session = db_manager.get_session()
        try:
            # Get current device IDs
            current_ids = set(self.devices.keys())

            # Load fresh devices from DB
            db_devices = session.query(Device).filter_by(enabled=True).all()
            new_ids = {d.id for d in db_devices}

            # Remove devices no longer in DB
            for removed_id in current_ids - new_ids:
                self.remove_device(removed_id)

            # Add/update devices
            for device in db_devices:
                session.expunge(device)
                if device.id in self.devices:
                    # Update existing device
                    self.devices[device.id] = device
                else:
                    # Add new device
                    self.add_device(device)

            logger.info(f"Reloaded {len(db_devices)} devices from database")
            return len(db_devices)

        except Exception as e:
            logger.error(f"Failed to reload devices: {e}", exc_info=True)
            return 0
        finally:
            session.close()

    def _monitoring_loop(self):
        """Main monitoring loop - processes check tasks"""
        logger.debug("Monitoring loop started")

        while self.running:
            try:
                if self.paused:
                    time.sleep(1)
                    continue

                # Get tasks from queue and submit to executor
                tasks_to_process = []

                # Get up to max_workers tasks
                while len(tasks_to_process) < self.max_workers and not self.task_queue.empty():
                    try:
                        _, task = self.task_queue.get_nowait()
                        tasks_to_process.append(task)
                    except:
                        break

                if not tasks_to_process:
                    time.sleep(0.1)
                    continue

                # Submit tasks to executor (check if still running before submitting)
                future_to_task = {}
                for task in tasks_to_process:
                    if not self.running:
                        # Monitoring has been stopped, don't submit new tasks
                        logger.debug("Monitoring stopped, skipping task submission")
                        break
                    try:
                        future = self.executor.submit(self._execute_check, task)
                        future_to_task[future] = task
                    except RuntimeError as e:
                        # Executor has been shutdown
                        logger.warning(f"Executor shutdown, cannot submit task: {e}")
                        break

                # Process completed checks as they complete (non-blocking)
                try:
                    for future in as_completed(future_to_task, timeout=30):
                        task = future_to_task[future]
                        try:
                            result = future.result(timeout=0.1)  # Quick timeout since already completed
                            self._process_check_result(task, result)
                        except TimeoutError:
                            timeout_val = task.device.timeout + 5
                            error_msg = f"Check timed out after {timeout_val}s (device timeout: {task.device.timeout}s, check type: {task.check_type})"
                            logger.error(f"Check failed for {task.device.name}: {error_msg}")
                            self._handle_check_failure(task, error_msg)
                        except Exception as e:
                            error_msg = str(e) if str(e) else 'Unknown error - no exception message'
                            logger.error(f"Check failed for {task.device.name}: {error_msg}", exc_info=True)
                            self._handle_check_failure(task, error_msg)
                except TimeoutError:
                    # Some futures didn't complete in time - handle remaining futures
                    logger.warning(f"Some checks did not complete within 30s timeout")
                    for future, task in future_to_task.items():
                        if not future.done():
                            error_msg = f"Check exceeded 30s total timeout (device timeout: {task.device.timeout}s, check type: {task.check_type})"
                            logger.error(f"Check failed for {task.device.name}: {error_msg}")
                            self._handle_check_failure(task, error_msg)
                            future.cancel()  # Cancel the slow future

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}", exc_info=True)
                time.sleep(1)

    def _execute_check(self, task: CheckTask) -> dict:
        """
        Execute a check task

        Args:
            task: Check task to execute

        Returns:
            Check result dict
        """
        start_time = time.time()
        device = task.device
        check_type = task.check_type

        logger.info(f"[CHECK] Executing {check_type.value} check for {device.name} ({device.ip_address})")

        try:
            # Get the appropriate check service
            check_service = self.check_services.get(check_type)

            if check_service is None:
                raise ValueError(f"No check service registered for {check_type.value}")

            # Execute check
            result = check_service(device)

            # Calculate response time
            response_time = (time.time() - start_time) * 1000  # Convert to ms

            result['response_time'] = response_time
            result['check_type'] = check_type
            result['device_id'] = device.id
            result['timestamp'] = datetime.utcnow().isoformat()

            success_str = "SUCCESS" if result.get('success') else "FAILED"
            logger.info(f"[CHECK] {check_type.value} for {device.name}: {success_str} ({response_time:.1f}ms)")

            return result

        except Exception as e:
            logger.error(f"[CHECK] Execution exception for {device.name} ({check_type.value}): {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'check_type': check_type,
                'device_id': device.id,
                'timestamp': datetime.utcnow().isoformat(),
                'response_time': (time.time() - start_time) * 1000
            }

    def _process_check_result(self, task: CheckTask, result: dict):
        """
        Process a check result

        Args:
            task: Original check task
            result: Check result dict
        """
        try:
            device = task.device
            success = result.get('success', False)

            # Update statistics
            self.statistics['total_checks'] += 1
            if success:
                self.statistics['successful_checks'] += 1
            else:
                self.statistics['failed_checks'] += 1

            # Record performance metrics (p50/p95/p99 tracking)
            check_type_str = result.get('check_type').value if hasattr(result.get('check_type'), 'value') else str(result.get('check_type'))
            performance_metrics.record_check(
                check_type=check_type_str,
                response_time=result.get('response_time', 0),
                success=success
            )

            # Store result in database (using batch writer for optimal performance)
            self._store_check_result(result)

            # IMPORTANTE: Aggiorna PRIMA ping_status/web_status, POI determina lo stato
            # Track individual check statuses for UI display
            check_type = result.get('check_type')
            if check_type == CheckType.PING:
                device.ping_status = 'success' if success else 'failed'
            elif check_type in (CheckType.HTTP, CheckType.HTTPS):
                device.web_status = 'success' if success else 'failed'

            # Update device status DOPO aver aggiornato ping_status/web_status
            old_status = device.current_status
            new_status = self._determine_device_status(device, result)

            if new_status != old_status:
                self._handle_status_change(device, old_status, new_status)

            # Update device metrics
            device.current_status = new_status
            device.last_check_time = result['timestamp']
            device.response_time = result.get('response_time', 0)
            device.total_checks += 1

            # CRITICAL FIX: Persist device updates to database for real-time UI sync
            self._persist_device_updates(device)

            # AUTO-RECOVERY LOGIC:
            # Auto-recovery is now triggered in _handle_status_change when entering DEGRADED state
            # This avoids redundant recovery attempts on every check

            # Manual intervention alert for completely offline devices (both PING and WEB failed)
            if hasattr(device, 'ping_status') and hasattr(device, 'web_status'):
                if device.ping_status == 'failed' and device.web_status == 'failed':
                    # Both failed = manual intervention required
                    # Only alert once when entering this state (not every check)
                    if not hasattr(device, 'requires_manual_intervention') or not device.requires_manual_intervention:
                        logger.error(f"[MANUAL INTERVENTION] {device.name}: PING e WEB entrambi FAILED - intervento richiesto")
                        device.requires_manual_intervention = True
                        # Call callback to add to pending failures list for email
                        for callback in self.callbacks.get('on_recovery_failure', []):
                            callback(device, "PING e WEB entrambi non raggiungibili - intervento manuale necessario")
                elif device.ping_status == 'success' or device.web_status == 'success':
                    # Device is responsive again, clear manual intervention flag
                    if hasattr(device, 'requires_manual_intervention') and device.requires_manual_intervention:
                        device.requires_manual_intervention = False

            if success:
                device.successful_checks += 1
            else:
                device.failed_checks += 1

            device.uptime_percentage = (device.successful_checks / device.total_checks * 100) if device.total_checks > 0 else 100

            # Trigger callbacks
            for callback in self.callbacks.get('on_check_complete', []):
                try:
                    callback(device, result)
                except Exception as e:
                    logger.error(f"Error in check complete callback: {e}")

        except Exception as e:
            logger.error(f"Error processing check result: {e}", exc_info=True)

    def _store_check_result(self, result: dict):
        """
        Store check result in database using batch writer for optimal performance

        Args:
            result: Check result dict
        """
        try:
            # Use batch writer for high-performance database operations
            batch_writer.add_check_result(result)
        except Exception as e:
            logger.error(f"Failed to queue check result for batch write: {e}")

    def _persist_device_updates(self, device: Device):
        """
        Persist device updates to database for real-time UI synchronization

        Args:
            device: Device to persist
        """
        session = db_manager.get_session()
        try:
            # Get the device from database
            db_device = session.query(Device).filter_by(id=device.id).first()

            if db_device:
                # Update critical fields for UI display
                db_device.current_status = device.current_status
                db_device.last_check_time = device.last_check_time
                db_device.response_time = device.response_time
                db_device.total_checks = device.total_checks
                db_device.successful_checks = device.successful_checks
                db_device.failed_checks = device.failed_checks
                db_device.uptime_percentage = device.uptime_percentage

                # Persist ping/web status for DEGRADED detection
                if hasattr(device, 'ping_status'):
                    db_device.ping_status = device.ping_status
                if hasattr(device, 'web_status'):
                    db_device.web_status = device.web_status

                session.commit()
                logger.debug(f"Persisted device updates to DB: {device.name} - Status: {device.current_status}, Last Check: {device.last_check_time}")
            else:
                logger.warning(f"Device {device.id} not found in database - cannot persist updates")

        except Exception as e:
            logger.error(f"Failed to persist device updates for {device.name}: {e}")
            session.rollback()
        finally:
            session.close()

    def _determine_device_status(self, device: Device, result: dict) -> str:
        """
        Determine device status based on PING and WEB check results

        LOGICA CHIARA E RIGOROSA:
        - OFFLINE (rosso): PING FAIL (indipendentemente da WEB)
        - DEGRADED (giallo): PING OK + WEB FAIL → trigger auto-recovery SSH
        - ONLINE (verde): PING OK + WEB OK (o PING OK se WEB non abilitato)

        Args:
            device: Device being checked
            result: Check result

        Returns:
            Status string (online, offline, degraded)
        """
        # Get current ping and web statuses (after they've been updated)
        ping_status = getattr(device, 'ping_status', None)
        web_status = getattr(device, 'web_status', None)

        # REGOLA 1: PING FAIL = sempre OFFLINE (rosso)
        if ping_status == 'failed':
            return 'offline'

        # REGOLA 2: PING OK + WEB FAIL = DEGRADED (giallo) - richiede auto-recovery
        if ping_status == 'success':
            # Se il dispositivo ha WEB check abilitato
            if device.http_enabled or device.https_enabled:
                # Se web_status esiste ed è failed = DEGRADED
                if web_status == 'failed':
                    return 'degraded'
                # Se web_status è success = ONLINE
                elif web_status == 'success':
                    return 'online'
                # Se web_status non è ancora stato determinato, aspetta
                else:
                    return device.current_status or 'unknown'
            else:
                # Dispositivo con solo PING enabled = ONLINE se ping OK
                return 'online'

        # Fallback: usa current_status se disponibile, altrimenti 'unknown'
        return device.current_status or 'unknown'

    def _handle_status_change(self, device: Device, old_status: str, new_status: str):
        """
        Handle device status change

        Args:
            device: Device with status change
            old_status: Previous status
            new_status: New status
        """
        # Only log significant status changes (not same-to-same or minor fluctuations)
        if old_status != new_status:
            # Use WARNING for critical changes, INFO for recoveries
            if new_status == 'offline':
                logger.warning(f"[OFFLINE] {device.name}: {old_status.upper()} -> OFFLINE")
            elif new_status == 'degraded':
                logger.warning(f"[DEGRADED] {device.name}: {old_status.upper()} -> DEGRADED")
            elif new_status == 'online' and old_status in ['offline', 'degraded']:
                logger.info(f"[RECOVERED] {device.name}: {old_status.upper()} -> ONLINE")
            else:
                logger.debug(f"{device.name}: {old_status} -> {new_status}")

        device.last_status_change = datetime.utcnow().isoformat()

        # TRIGGER AUTO-RECOVERY when entering DEGRADED state (PING OK + WEB FAIL)
        if new_status == 'degraded' and old_status != 'degraded':
            if device.ssh_enabled and self.auto_recovery_service:
                logger.warning(f"[AUTO-RECOVERY] {device.name} DEGRADED - triggering SSH recovery")
                self._attempt_auto_recovery(device)

        # Trigger callbacks
        for callback in self.callbacks.get('on_status_change', []):
            try:
                callback(device, old_status, new_status)
            except Exception as e:
                logger.error(f"Error in status change callback: {e}")

        # Trigger alert if configured
        if device.alert_enabled:
            should_alert = (
                    (new_status == 'offline' and device.alert_on_down) or
                    (new_status == 'online' and old_status in ['offline', 'degraded'] and device.alert_on_up) or
                    (new_status == 'degraded' and device.alert_on_degraded)
            )

            if should_alert:
                self._trigger_alert(device, old_status, new_status)

    def _recover_already_degraded_devices(self):
        """
        Check and recover devices that are already DEGRADED at startup
        This handles devices that were degraded before monitoring started
        """
        degraded_devices = [
            d for d in self.devices.values()
            if d.current_status == 'degraded'
        ]

        if degraded_devices:
            logger.warning(
                f"Found {len(degraded_devices)} devices already in DEGRADED state - "
                f"triggering recovery"
            )

            for device in degraded_devices:
                if device.ssh_enabled and self.auto_recovery_service:
                    logger.info(f"Attempting recovery for already-degraded device: {device.name}")
                    # Schedule recovery after a short delay (5 seconds)
                    # to allow monitoring to fully initialize
                    self._schedule_timer(
                        5.0,
                        self._attempt_auto_recovery,
                        args=(device,)
                    )
                else:
                    if not device.ssh_enabled:
                        logger.warning(
                            f"Cannot recover {device.name}: SSH not enabled"
                        )
                    if not self.auto_recovery_service:
                        logger.warning(
                            f"Cannot recover {device.name}: Auto-recovery service not configured"
                        )

    def _trigger_alert(self, device: Device, old_status: str, new_status: str):
        """
        Trigger an alert for status change

        Args:
            device: Device triggering alert
            old_status: Previous status
            new_status: New status
        """
        alert_data = {
            'device': device,
            'old_status': old_status,
            'new_status': new_status,
            'timestamp': datetime.utcnow()
        }

        for callback in self.callbacks.get('on_alert', []):
            try:
                callback(alert_data)
            except Exception as e:
                logger.error(f"Error in alert callback: {e}")

    def _attempt_auto_recovery(self, device: Device):
        """
        Attempt automatic SSH recovery for a device

        Args:
            device: Device to recover
        """
        try:
            # Check if we already attempted recovery recently (cooldown period) - thread-safe atomic operation
            device_key = f"{device.ip_address}"

            with self._recovery_attempts_lock:
                last_attempt = self.recovery_attempts.get(device_key, None)

                if last_attempt:
                    # Cooldown of 5 minutes between recovery attempts
                    time_since_last = (datetime.utcnow() - last_attempt).total_seconds()
                    if time_since_last < 300:  # 5 minutes
                        logger.info(f"Recovery cooldown active for {device.name} - skipping (last attempt {int(time_since_last)}s ago)")
                        return

                # Record attempt atomically within same lock to prevent race condition
                self.recovery_attempts[device_key] = datetime.utcnow()

            # Attempt recovery
            logger.info(f"Attempting SSH recovery for {device.name} ({device.ip_address})")
            success, message = self.auto_recovery_service.attempt_recovery(
                device.ip_address,
                device.name
            )

            # Store recovery result for email aggregation
            if not hasattr(device, 'recovery_results'):
                device.recovery_results = []

            device.recovery_results.append({
                'timestamp': datetime.utcnow(),
                'success': success,
                'message': message
            })

            if success:
                logger.info(f"[AUTO-RECOVERY] ✓ Recovery successful for {device.name}: {message}")
                device.recovery_success = True
                device.requires_manual_intervention = False

                # Schedule immediate re-check after 30 seconds to verify recovery
                logger.info(f"[AUTO-RECOVERY] Scheduling immediate re-check for {device.name} in 30s")
                self._schedule_timer(
                    30.0,  # 30 seconds to allow device to reboot
                    lambda: self.force_immediate_check(device.id)
                )

                # Trigger callback
                for callback in self.callbacks.get('on_recovery_success', []):
                    try:
                        callback(device, message)
                    except Exception as e:
                        logger.error(f"Error in recovery success callback: {e}")
            else:
                logger.error(f"Recovery failed for {device.name}: {message}")
                device.recovery_success = False
                device.requires_manual_intervention = True
                # Trigger callback
                for callback in self.callbacks.get('on_recovery_failure', []):
                    try:
                        callback(device, message)
                    except Exception as e:
                        logger.error(f"Error in recovery failure callback: {e}")

        except Exception as e:
            logger.error(f"Exception during auto-recovery for {device.name}: {e}", exc_info=True)
            device.requires_manual_intervention = True

    def _handle_check_failure(self, task: CheckTask, error: str):
        """
        Handle check failure

        Args:
            task: Failed check task
            error: Error message
        """
        result = {
            'device_id': task.device.id,
            'check_type': task.check_type,
            'success': False,
            'error': error,
            'timestamp': datetime.utcnow().isoformat(),
            'response_time': 0
        }

        self._process_check_result(task, result)

    def register_callback(self, event: str, callback: Callable):
        """
        Register a callback for an event

        Args:
            event: Event name (on_check_complete, on_status_change, on_alert, on_error)
            callback: Callback function
        """
        if event in self.callbacks:
            self.callbacks[event].append(callback)
            logger.debug(f"Registered callback for event: {event}")

    def get_statistics(self) -> dict:
        """Get monitoring statistics"""
        return self.statistics.copy()

    def __repr__(self):
        return f"<MonitoringEngine(devices={len(self.devices)}, running={self.running})>"
