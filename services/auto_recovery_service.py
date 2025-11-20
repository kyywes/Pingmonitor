"""
PingMonitor Pro v2.0 - Auto-Recovery Service
Automatic SSH-based device recovery with reboot
"""

import paramiko
import time
from datetime import datetime
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class AutoRecoveryService:
    """
    Automatic recovery service that:
    1. Detects ping OK but web DOWN
    2. Connects via SSH
    3. Executes reboot command
    4. Monitors recovery
    """

    def __init__(self, ssh_config: dict):
        """
        Initialize auto-recovery service

        Args:
            ssh_config: SSH configuration (username, password, etc.)
        """
        self.ssh_config = ssh_config
        self.recovery_log = {}
        self._active_connections = []  # Track active SSH connections for cleanup

    def attempt_recovery(self, device_ip: str, device_name: str = "Unknown") -> Tuple[bool, str]:
        """
        Attempt automatic recovery via SSH reboot

        Args:
            device_ip: Device IP address
            device_name: Device friendly name

        Returns:
            Tuple of (success, message)
        """
        logger.info(f"Starting auto-recovery for {device_name} ({device_ip})")

        if not self.ssh_config.get('enabled', False):
            logger.warning("SSH auto-recovery is disabled in config")
            return False, "SSH auto-recovery disabled"

        try:
            # Step 1: Connect via SSH
            logger.info(f"{device_ip}: Connecting via SSH...")
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # Track connection for cleanup
            self._active_connections.append(client)

            try:
                client.connect(
                    hostname=device_ip,
                    port=22,
                    username=self.ssh_config.get('username', 'root'),
                    password=self.ssh_config.get('password', ''),
                    timeout=10,
                    allow_agent=False,
                    look_for_keys=False
                )

                logger.info(f"{device_ip}: SSH connection established")

            except paramiko.AuthenticationException:
                error_msg = f"{device_ip}: SSH authentication failed"
                logger.error(error_msg)
                return False, error_msg

            except Exception as e:
                error_msg = f"{device_ip}: SSH connection failed: {str(e)}"
                logger.error(error_msg)
                return False, error_msg

            # Step 2: Execute diagnostics before reboot
            logger.info(f"{device_ip}: Running pre-reboot diagnostics...")
            diagnostics = self._run_diagnostics(client, device_ip)

            # Step 3: Execute reboot command
            logger.warning(f"{device_ip}: Executing REBOOT command...")

            try:
                # Execute reboot (this will disconnect)
                stdin, stdout, stderr = client.exec_command('sudo reboot', timeout=5)

                # Try to read output (may fail due to disconnect)
                try:
                    output = stdout.read().decode('utf-8', errors='ignore')
                    error = stderr.read().decode('utf-8', errors='ignore')
                except:
                    output = ""
                    error = ""

                logger.info(f"{device_ip}: Reboot command sent successfully")

                # Log recovery attempt
                self.recovery_log[device_ip] = {
                    'time': datetime.now(),
                    'device_name': device_name,
                    'diagnostics': diagnostics,
                    'reboot_sent': True
                }

                return True, f"Reboot command sent to {device_name}. Waiting 5 minutes for recovery..."

            except Exception as e:
                # Reboot command often causes connection to close, which is expected
                if "Connection closed" in str(e) or "EOF" in str(e):
                    logger.info(f"{device_ip}: Connection closed after reboot (expected)")

                    self.recovery_log[device_ip] = {
                        'time': datetime.now(),
                        'device_name': device_name,
                        'diagnostics': diagnostics,
                        'reboot_sent': True
                    }

                    return True, f"Reboot initiated for {device_name}"
                else:
                    error_msg = f"{device_ip}: Reboot command failed: {str(e)}"
                    logger.error(error_msg)
                    return False, error_msg

            finally:
                try:
                    client.close()
                    # Remove from active connections
                    if client in self._active_connections:
                        self._active_connections.remove(client)
                except:
                    pass

        except Exception as e:
            error_msg = f"{device_ip}: Auto-recovery failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return False, error_msg

    def _run_diagnostics(self, client: paramiko.SSHClient, device_ip: str) -> dict:
        """
        Run diagnostic commands before reboot

        Args:
            client: Connected SSH client
            device_ip: Device IP

        Returns:
            Diagnostics results
        """
        diagnostics = {}

        diagnostic_commands = {
            'uptime': 'uptime',
            'memory': 'free -h',
            'disk': 'df -h',
            'load_average': 'cat /proc/loadavg',
            'network': 'ip addr show',
        }

        for name, command in diagnostic_commands.items():
            try:
                stdin, stdout, stderr = client.exec_command(command, timeout=5)
                output = stdout.read().decode('utf-8', errors='ignore')
                diagnostics[name] = output[:500]  # Limit output size
            except Exception as e:
                diagnostics[name] = f"Failed: {str(e)}"
                logger.debug(f"{device_ip}: Diagnostic '{name}' failed: {e}")

        return diagnostics

    def check_ssh_connectivity(self, device_ip: str) -> Tuple[bool, str]:
        """
        Check if device is reachable via SSH

        Args:
            device_ip: Device IP address

        Returns:
            Tuple of (reachable, message)
        """
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            client.connect(
                hostname=device_ip,
                port=22,
                username=self.ssh_config.get('username', 'root'),
                password=self.ssh_config.get('password', ''),
                timeout=5,
                allow_agent=False,
                look_for_keys=False
            )

            client.close()
            return True, "SSH accessible"

        except paramiko.AuthenticationException:
            return False, "Authentication failed"
        except Exception as e:
            return False, f"Connection failed: {str(e)}"

    def get_recovery_log(self, device_ip: str) -> Optional[dict]:
        """Get recovery log for device"""
        return self.recovery_log.get(device_ip)

    def clear_recovery_log(self, device_ip: str):
        """Clear recovery log for device"""
        if device_ip in self.recovery_log:
            del self.recovery_log[device_ip]

    def cleanup(self):
        """Close all SSH connections for clean shutdown"""
        logger.info("Closing all active SSH connections...")
        closed_count = 0

        for client in self._active_connections[:]:  # Create a copy to iterate
            try:
                client.close()
                closed_count += 1
            except Exception as e:
                logger.debug(f"Error closing SSH connection: {e}")

        self._active_connections.clear()
        logger.info(f"Closed {closed_count} SSH connections")
