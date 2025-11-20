"""
PingMonitor Pro v2.0 - HTTP/HTTPS Check Service
"""

import time
import requests
from typing import Dict
from urllib.parse import urljoin
import logging
import ssl

logger = logging.getLogger(__name__)


class HTTPService:
    """HTTP/HTTPS check service"""

    @staticmethod
    def check(device, use_https: bool = False) -> Dict:
        """
        Perform HTTP/HTTPS check

        Args:
            device: Device to check
            use_https: Use HTTPS instead of HTTP

        Returns:
            Check result dictionary
        """
        protocol = 'https' if use_https else 'http'
        port = device.https_port if use_https else device.http_port
        url = f"{protocol}://{device.ip_address}:{port}{device.http_path}"

        try:
            start_time = time.time()

            response = requests.request(
                method=device.http_method,
                url=url,
                timeout=device.timeout,
                verify=device.http_check_ssl if use_https else False,
                allow_redirects=True,
                headers={'User-Agent': 'PingMonitor-Pro/2.0'}
            )

            response_time = (time.time() - start_time) * 1000

            # Check SSL certificate validity if HTTPS
            ssl_info = {}
            if use_https and device.http_check_ssl:
                ssl_info = HTTPService._check_ssl_certificate(device.ip_address, device.https_port)

            success = response.status_code == device.http_expected_status

            return {
                'success': success,
                'response_time': response_time,
                'status_code': response.status_code,
                'response_size': len(response.content),
                'data': {
                    'headers': dict(response.headers),
                    'ssl_info': ssl_info,
                    'redirects': len(response.history),
                    'final_url': response.url
                }
            }

        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': 'HTTP request timeout',
                'response_time': device.timeout * 1000
            }
        except requests.exceptions.SSLError as e:
            return {
                'success': False,
                'error': f'SSL certificate error: {str(e)}',
                'response_time': 0
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'HTTP check failed: {str(e)}',
                'response_time': 0
            }

    @staticmethod
    def _check_ssl_certificate(hostname: str, port: int) -> Dict:
        """
        Check SSL certificate details

        Args:
            hostname: Hostname to check
            port: Port number

        Returns:
            SSL certificate information
        """
        try:
            import socket
            from datetime import datetime

            context = ssl.create_default_context()
            with socket.create_connection((hostname, port), timeout=5) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()

                    # Parse dates
                    not_before = datetime.strptime(cert['notBefore'], '%b %d %H:%M:%S %Y %Z')
                    not_after = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')

                    days_until_expiry = (not_after - datetime.now()).days

                    return {
                        'subject': dict(x[0] for x in cert['subject']),
                        'issuer': dict(x[0] for x in cert['issuer']),
                        'version': cert['version'],
                        'not_before': not_before.isoformat(),
                        'not_after': not_after.isoformat(),
                        'days_until_expiry': days_until_expiry,
                        'expired': days_until_expiry < 0
                    }

        except Exception as e:
            logger.error(f"SSL certificate check failed: {e}")
            return {'error': str(e)}
