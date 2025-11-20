"""
PingMonitor Pro v2.0 - SSH Check Service
"""

import time
import socket
from typing import Dict
import logging

try:
    import paramiko
    PARAMIKO_AVAILABLE = True
except ImportError:
    PARAMIKO_AVAILABLE = False

logger = logging.getLogger(__name__)


class SSHService:
    """SSH connectivity check service"""

    @staticmethod
    def check(device) -> Dict:
        """
        Perform SSH check

        Args:
            device: Device to check

        Returns:
            Check result dictionary
        """
        if not PARAMIKO_AVAILABLE:
            return SSHService._check_port_only(device)

        return SSHService._check_full_ssh(device)

    @staticmethod
    def _check_port_only(device) -> Dict:
        """Check if SSH port is open"""
        try:
            start_time = time.time()

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(device.timeout)

            result = sock.connect_ex((device.ip_address, device.ssh_port))

            response_time = (time.time() - start_time) * 1000

            sock.close()

            return {
                'success': result == 0,
                'response_time': response_time,
                'data': {'port_open': result == 0}
            }

        except Exception as e:
            return {
                'success': False,
                'error': f'SSH port check failed: {str(e)}',
                'response_time': 0
            }

    @staticmethod
    def _check_full_ssh(device) -> Dict:
        """Full SSH authentication check"""
        try:
            start_time = time.time()

            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # Try connection without authentication first (just to check if SSH responds)
            try:
                transport = paramiko.Transport((device.ip_address, device.ssh_port))
                transport.connect(timeout=device.timeout)

                response_time = (time.time() - start_time) * 1000

                server_version = transport.remote_version if hasattr(transport, 'remote_version') else 'Unknown'

                transport.close()

                return {
                    'success': True,
                    'response_time': response_time,
                    'data': {
                        'server_version': server_version,
                        'port_open': True,
                        'authentication': 'not_attempted'
                    }
                }

            finally:
                client.close()

        except paramiko.SSHException as e:
            return {
                'success': False,
                'error': f'SSH error: {str(e)}',
                'response_time': (time.time() - start_time) * 1000
            }
        except socket.timeout:
            return {
                'success': False,
                'error': 'SSH connection timeout',
                'response_time': device.timeout * 1000
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'SSH check failed: {str(e)}',
                'response_time': 0
            }
