"""
PingMonitor Pro v2.0 - DNS Check Service
"""

import time
from typing import Dict
import logging

try:
    import dns.resolver
    DNS_AVAILABLE = True
except ImportError:
    DNS_AVAILABLE = False

logger = logging.getLogger(__name__)


class DNSService:
    """DNS resolution check service"""

    @staticmethod
    def check(device) -> Dict:
        """
        Perform DNS resolution check

        Args:
            device: Device to check

        Returns:
            Check result dictionary
        """
        if not DNS_AVAILABLE:
            return {
                'success': False,
                'error': 'DNS library not available. Install dnspython.',
                'response_time': 0
            }

        try:
            start_time = time.time()

            resolver = dns.resolver.Resolver()
            resolver.timeout = device.timeout
            resolver.lifetime = device.timeout

            # Perform A record lookup
            answers = resolver.resolve(device.ip_address, 'A')

            response_time = (time.time() - start_time) * 1000

            ip_addresses = [str(rdata) for rdata in answers]

            return {
                'success': len(ip_addresses) > 0,
                'response_time': response_time,
                'data': {
                    'ip_addresses': ip_addresses,
                    'nameservers': [str(ns) for ns in resolver.nameservers]
                }
            }

        except dns.exception.Timeout:
            return {
                'success': False,
                'error': 'DNS query timeout',
                'response_time': device.timeout * 1000
            }
        except dns.resolver.NXDOMAIN:
            return {
                'success': False,
                'error': 'Domain does not exist (NXDOMAIN)',
                'response_time': (time.time() - start_time) * 1000
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'DNS check failed: {str(e)}',
                'response_time': 0
            }
