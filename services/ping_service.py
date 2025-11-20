"""
PingMonitor Pro v2.0 - Ping Check Service
"""

import platform
import subprocess
import time
from typing import Dict
import logging

try:
    from icmplib import ping as icmplib_ping
    ICMPLIB_AVAILABLE = True
except ImportError:
    ICMPLIB_AVAILABLE = False

logger = logging.getLogger(__name__)


class PingService:
    """
    Ping check service with fallback mechanisms
    """

    @staticmethod
    def check(device) -> Dict:
        """
        Perform ping check on device

        Args:
            device: Device to check

        Returns:
            Check result dictionary
        """
        # Try icmplib first (more accurate)
        if ICMPLIB_AVAILABLE:
            try:
                return PingService._ping_icmplib(device)
            except Exception as e:
                logger.debug(f"icmplib ping failed, falling back to system ping: {e}")

        # Fallback to system ping
        return PingService._ping_system(device)

    @staticmethod
    def _ping_icmplib(device) -> Dict:
        """
        Ping using icmplib library

        Args:
            device: Device to ping

        Returns:
            Check result dictionary
        """
        try:
            start_time = time.time()

            host = icmplib_ping(
                device.ip_address,
                count=1,
                timeout=device.timeout,
                privileged=False
            )

            response_time = (time.time() - start_time) * 1000

            return {
                'success': host.is_alive,
                'response_time': host.avg_rtt if host.is_alive else response_time,
                'packet_loss': host.packet_loss,
                'packets_sent': host.packets_sent,
                'packets_received': host.packets_received,
                'data': {
                    'min_rtt': host.min_rtt,
                    'avg_rtt': host.avg_rtt,
                    'max_rtt': host.max_rtt,
                    'jitter': host.jitter
                }
            }

        except Exception as e:
            return {
                'success': False,
                'error': f"Ping failed: {str(e)}",
                'response_time': 0
            }

    @staticmethod
    def _ping_system(device) -> Dict:
        """
        Ping using system ping command

        Args:
            device: Device to ping

        Returns:
            Check result dictionary
        """
        try:
            start_time = time.time()

            # Platform-specific ping command
            system = platform.system().lower()

            if system == 'windows':
                cmd = [
                    'ping',
                    '-n', '1',  # Count
                    '-w', str(device.timeout * 1000),  # Timeout in ms
                    device.ip_address
                ]
            else:  # Linux, macOS
                cmd = [
                    'ping',
                    '-c', '1',  # Count
                    '-W', str(device.timeout),  # Timeout in seconds
                    device.ip_address
                ]

            # Hide CMD window on Windows
            startupinfo = None
            if platform.system().lower() == 'windows':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=device.timeout + 1,
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW if platform.system().lower() == 'windows' else 0
            )

            response_time = (time.time() - start_time) * 1000
            success = result.returncode == 0

            # Parse response time from output (simple approach)
            rtt = response_time
            if success:
                output = result.stdout.lower()
                if 'time=' in output:
                    try:
                        time_str = output.split('time=')[1].split()[0]
                        rtt = float(time_str.replace('ms', ''))
                    except:
                        pass

            return {
                'success': success,
                'response_time': rtt if success else response_time,
                'output': result.stdout[:500] if success else result.stderr[:500]
            }

        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Ping timeout',
                'response_time': device.timeout * 1000
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Ping failed: {str(e)}",
                'response_time': 0
            }
