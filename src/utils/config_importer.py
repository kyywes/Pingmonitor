"""
PingMonitor Pro v2.0 - Configuration Importer
Import devices from legacy config.json
"""

import json
from pathlib import Path
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


class ConfigImporter:
    """Import devices from legacy configuration format"""

    @staticmethod
    def import_from_legacy_config(config_path: Path) -> tuple[List[Dict], Dict, Dict]:
        """
        Import devices, email config, and SSH config from legacy format

        Args:
            config_path: Path to config.json

        Returns:
            Tuple of (devices_list, email_config, ssh_config)
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            devices = config.get('devices', [])
            email_config = config.get('email', {})
            ssh_config = config.get('ssh', {})

            logger.info(f"Imported {len(devices)} devices from legacy config")

            # Convert legacy device format to new format
            converted_devices = []
            for device in devices:
                converted = ConfigImporter._convert_device_format(device)
                converted_devices.append(converted)

            return converted_devices, email_config, ssh_config

        except FileNotFoundError:
            logger.warning(f"Config file not found: {config_path}")
            return [], {}, {}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file: {e}")
            return [], {}, {}
        except Exception as e:
            logger.error(f"Failed to import config: {e}", exc_info=True)
            return [], {}, {}

    @staticmethod
    def _convert_device_format(legacy_device: Dict) -> Dict:
        """
        Convert legacy device format to new format

        Args:
            legacy_device: Legacy device dict

        Returns:
            Converted device dict
        """
        device_type = legacy_device.get('type', 'Ping Only')

        # Determine which checks to enable
        ping_enabled = True  # Always enable ping
        http_enabled = 'Web' in device_type
        https_enabled = 'Web' in device_type and legacy_device.get('port', 80) == 443
        ssh_enabled = 'SSH' in device_type or 'All' in device_type

        return {
            'ip_address': legacy_device.get('ip', ''),
            'name': legacy_device.get('name', 'Unknown'),
            'description': f"Imported from legacy config - {device_type}",
            'device_type': ConfigImporter._guess_device_type(legacy_device.get('name', '')),
            'enabled': legacy_device.get('enabled', True),
            'check_interval': legacy_device.get('interval', 60),
            'timeout': legacy_device.get('timeout', 5),
            'retry_attempts': 3,

            # Check types
            'ping_enabled': ping_enabled,
            'http_enabled': http_enabled,
            'https_enabled': https_enabled,
            'ssh_enabled': ssh_enabled,
            'dns_enabled': False,
            'snmp_enabled': False,

            # Ports
            'http_port': legacy_device.get('port', 80) if http_enabled else 80,
            'https_port': 443,
            'ssh_port': legacy_device.get('port', 22) if ssh_enabled else 22,

            # HTTP config
            'http_path': '/',
            'http_method': 'GET',
            'http_expected_status': 200,
            'http_check_ssl': True,

            # Location and metadata
            'location': legacy_device.get('location', ''),
            'tags': [],
            'custom_fields': {},

            # Alert configuration
            'alert_enabled': True,
            'alert_on_down': True,
            'alert_on_up': True,
            'alert_on_degraded': True,

            # Thresholds
            'degraded_threshold': 200,
            'down_threshold': 3,

            # Auto-recovery
            'recovery_enabled': ssh_enabled,  # Enable recovery if SSH available
            'recovery_command': 'reboot',
            'recovery_max_attempts': 3
        }

    @staticmethod
    def _guess_device_type(name: str) -> str:
        """Guess device type from name"""
        name_lower = name.lower()

        if any(x in name_lower for x in ['router', 'gateway']):
            return 'router'
        elif any(x in name_lower for x in ['switch', 'core']):
            return 'switch'
        elif any(x in name_lower for x in ['server', 'db', 'mail', 'web']):
            return 'server'
        elif any(x in name_lower for x in ['firewall', 'fw']):
            return 'firewall'
        elif any(x in name_lower for x in ['access point', 'ap', 'wifi']):
            return 'access_point'
        elif any(x in name_lower for x in ['nas', 'storage']):
            return 'nas'
        elif any(x in name_lower for x in ['printer']):
            return 'printer'
        elif any(x in name_lower for x in ['camera', 'cctv']):
            return 'camera'
        elif any(x in name_lower for x in ['voip', 'pbx', 'phone']):
            return 'voip'
        else:
            return 'generic'
