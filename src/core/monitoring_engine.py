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
        self.task_queue = PriorityQueue()
        self.result_queue = Queue()

        self.running = False
        self.paused = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._scheduler_thread: Optional[threading.Thread] = None

        self.devices: Dict[int, Device] = {}
        self.last_check_times: Dict[int, datetime] = {}
        self.check_services: Dict[CheckType, Callable] = {}

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
        try:
            session = db_manager.get_session()
            devices = session.query(Device).filter_by(enabled=True).all()

            for device in devices:
                # Detach from session to avoid issues with threading
                session.expunge(device)
                self.add_device(device)

            session.close()
            logger.info(f"Loaded {len(devices)} devices from database")
        except Exception as e:
            logger.error(f"Failed to load devices: {e}")

    def start(self):
        """Start the monitoring engine"""
        if self.running:
            logger.warning("Monitoring engine is already running")
            return

        self.running = True
        self.paused = False

        # Load devices
        self.load_devices()

        # Start monitoring thread
        self._monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self._monitor_thread.start()

        # Start scheduler thread
        self._scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self._scheduler_thread.start()

        logger.info("Monitoring engine started")

    def stop(self):
        """Stop the monitoring engine"""
        if not self.running:
            logger.warning("Monitoring engine is not running")
            return

        logger.info("Stopping monitoring engine...")
        self.running = False

        # Clear task queue to prevent new tasks from being processed
        while not self.task_queue.empty():
            try:
                self.task_queue.get_nowait()
            except:
                break

        # Wait for threads to finish (with shorter timeout)
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=2)
        if self._scheduler_thread and self._scheduler_thread.is_alive():
            self._scheduler_thread.join(timeout=2)

        # Shutdown executor gracefully without waiting (non-blocking)
        self.executor.shutdown(wait=False, cancel_futures=True)

        logger.info("Monitoring engine stopped")

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

        while self.running:
            try:
                if self.paused:
                    time.sleep(1)
                    continue

                current_time = datetime.utcnow()

                # Schedule checks for all devices
                for device in self.devices.values():
                    if not device.enabled:
                        continue

                    last_check = self.last_check_times.get(device.id)
                    check_interval = timedelta(seconds=device.check_interval)

                    if last_check is None or (current_time - last_check) >= check_interval:
                        self._schedule_device_checks(device)
                        self.last_check_times[device.id] = current_time

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

        if device.ping_enabled:
            self.task_queue.put((priority, CheckTask(device, CheckType.PING, priority)))

        if device.http_enabled:
            self.task_queue.put((priority, CheckTask(device, CheckType.HTTP, priority)))

        if device.https_enabled:
            self.task_queue.put((priority, CheckTask(device, CheckType.HTTPS, priority)))

        if device.ssh_enabled:
            self.task_queue.put((priority, CheckTask(device, CheckType.SSH, priority)))

        if device.dns_enabled:
            self.task_queue.put((priority, CheckTask(device, CheckType.DNS, priority)))

        if device.snmp_enabled:
            self.task_queue.put((priority, CheckTask(device, CheckType.SNMP, priority)))

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

                # Submit tasks to executor
                futures = []
                for task in tasks_to_process:
                    future = self.executor.submit(self._execute_check, task)
                    futures.append((future, task))

                # Process completed checks
                for future, task in futures:
                    try:
                        result = future.result(timeout=task.device.timeout + 5)
                        self._process_check_result(task, result)
                    except Exception as e:
                        logger.error(f"Check failed for {task.device.name}: {e}")
                        self._handle_check_failure(task, str(e))

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

            return result

        except Exception as e:
            logger.error(f"Check execution failed: {e}")
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

            # Store result in database
            self._store_check_result(result)

            # Update device status
            old_status = device.current_status
            new_status = self._determine_device_status(device, result)

            if new_status != old_status:
                self._handle_status_change(device, old_status, new_status)

            # Update device metrics
            device.current_status = new_status
            device.last_check_time = result['timestamp']
            device.response_time = result.get('response_time', 0)
            device.total_checks += 1

            # Track individual check statuses for UI display
            check_type = result.get('check_type')
            if check_type == CheckType.PING:
                device.ping_status = 'success' if success else 'failed'
            elif check_type in (CheckType.HTTP, CheckType.HTTPS):
                device.web_status = 'success' if success else 'failed'

            # AUTO-RECOVERY LOGIC:
            # If PING is OK but WEB is DOWN → attempt SSH recovery
            # If both PING and WEB are DOWN → send alert (manual intervention required)
            if hasattr(device, 'ping_status') and hasattr(device, 'web_status'):
                if device.ping_status == 'success' and device.web_status == 'failed':
                    # PING OK + WEB FAIL = Auto-recovery candidate
                    if device.ssh_enabled and self.auto_recovery_service:
                        logger.warning(f"Device {device.name} ({device.ip_address}): PING OK but WEB FAILED - attempting SSH recovery")
                        self._attempt_auto_recovery(device)
                elif device.ping_status == 'failed' and device.web_status == 'failed':
                    # Both failed = manual intervention required
                    logger.error(f"Device {device.name} ({device.ip_address}): PING and WEB both FAILED - manual intervention required")
                    # Store for aggregated email alert
                    if not hasattr(device, 'requires_manual_intervention'):
                        device.requires_manual_intervention = True

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
        Store check result in database

        Args:
            result: Check result dict
        """
        try:
            session = db_manager.get_session()

            check_result = CheckResult(
                device_id=result['device_id'],
                check_type=result['check_type'],
                check_time=result['timestamp'],
                success=result.get('success', False),
                response_time=result.get('response_time'),
                status_code=result.get('status_code'),
                error_message=result.get('error'),
                check_data=str(result.get('data', {}))
            )

            session.add(check_result)
            session.commit()
            session.close()

        except Exception as e:
            logger.error(f"Failed to store check result: {e}")

    def _determine_device_status(self, device: Device, result: dict) -> str:
        """
        Determine device status based on check result

        Args:
            device: Device being checked
            result: Check result

        Returns:
            Status string (online, offline, degraded)
        """
        if not result.get('success', False):
            # Check for consecutive failures
            if device.failed_checks >= device.down_threshold:
                return 'offline'
            else:
                return 'degraded'

        # Check response time threshold
        response_time = result.get('response_time', 0)
        if response_time > device.degraded_threshold:
            return 'degraded'

        return 'online'

    def _handle_status_change(self, device: Device, old_status: str, new_status: str):
        """
        Handle device status change

        Args:
            device: Device with status change
            old_status: Previous status
            new_status: New status
        """
        logger.warning(f"Status change for {device.name}: {old_status} → {new_status}")

        device.last_status_change = datetime.utcnow().isoformat()

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
            # Check if we already attempted recovery recently (cooldown period)
            device_key = f"{device.ip_address}"
            last_attempt = self.recovery_attempts.get(device_key, None)

            if last_attempt:
                # Cooldown of 5 minutes between recovery attempts
                time_since_last = (datetime.utcnow() - last_attempt).total_seconds()
                if time_since_last < 300:  # 5 minutes
                    logger.info(f"Recovery cooldown active for {device.name} - skipping (last attempt {int(time_since_last)}s ago)")
                    return

            # Record attempt
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
                logger.info(f"Recovery successful for {device.name}: {message}")
                device.recovery_success = True
                device.requires_manual_intervention = False
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
