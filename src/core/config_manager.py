"""
PingMonitor Pro v2.0 - Configuration Manager
Secure configuration management with AES-256 encryption
"""

import os
import json
import base64
from pathlib import Path
from typing import Any, Dict, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import logging

logger = logging.getLogger(__name__)


class ConfigManager:
    """
    Secure configuration manager with encryption support
    """

    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize configuration manager

        Args:
            config_dir: Directory for configuration files
        """
        if config_dir is None:
            config_dir = Path.home() / ".pingmonitor"

        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)

        self.config_file = self.config_dir / "config.json"
        self.secrets_file = self.config_dir / "secrets.enc"
        self.key_file = self.config_dir / ".key"

        self._config: Dict[str, Any] = {}
        self._secrets: Dict[str, str] = {}
        self._cipher: Optional[Fernet] = None

        self._initialize_encryption()
        self.load()

    def _initialize_encryption(self):
        """Initialize or load encryption key"""
        if self.key_file.exists():
            # Load existing key
            with open(self.key_file, 'rb') as f:
                key = f.read()
        else:
            # Generate new key
            key = Fernet.generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(key)

            # Set restrictive permissions on Windows
            if os.name == 'nt':
                try:
                    import win32security
                    import ntsecuritycon as con
                    user, _, _ = win32security.LookupAccountName("", os.getenv('USERNAME'))
                    sd = win32security.GetFileSecurity(str(self.key_file),
                                                       win32security.DACL_SECURITY_INFORMATION)
                    dacl = win32security.ACL()
                    dacl.AddAccessAllowedAce(win32security.ACL_REVISION,
                                            con.FILE_ALL_ACCESS, user)
                    sd.SetSecurityDescriptorDacl(1, dacl, 0)
                    win32security.SetFileSecurity(str(self.key_file),
                                                 win32security.DACL_SECURITY_INFORMATION, sd)
                except ImportError:
                    # win32security not available, skip permission setting
                    pass

        self._cipher = Fernet(key)

    def load(self):
        """Load configuration from files"""
        # Load public config
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
                logger.info("Configuration loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load configuration: {e}")
                self._config = self._get_default_config()
        else:
            self._config = self._get_default_config()
            self.save()

        # Load encrypted secrets
        if self.secrets_file.exists():
            try:
                with open(self.secrets_file, 'rb') as f:
                    encrypted_data = f.read()

                decrypted_data = self._cipher.decrypt(encrypted_data)
                self._secrets = json.loads(decrypted_data.decode('utf-8'))
                logger.info("Secrets loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load secrets: {e}")
                self._secrets = {}
        else:
            self._secrets = {}

    def save(self):
        """Save configuration to files"""
        # Save public config
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=4, ensure_ascii=False)
            logger.info("Configuration saved successfully")
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            raise

        # Save encrypted secrets
        if self._secrets:
            try:
                json_data = json.dumps(self._secrets).encode('utf-8')
                encrypted_data = self._cipher.encrypt(json_data)

                with open(self.secrets_file, 'wb') as f:
                    f.write(encrypted_data)
                logger.info("Secrets saved successfully")
            except Exception as e:
                logger.error(f"Failed to save secrets: {e}")
                raise

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value

        Args:
            key: Configuration key (dot notation supported)
            default: Default value if key not found

        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any):
        """
        Set configuration value

        Args:
            key: Configuration key (dot notation supported)
            value: Value to set
        """
        keys = key.split('.')
        config = self._config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

    def get_secret(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get encrypted secret

        Args:
            key: Secret key
            default: Default value if key not found

        Returns:
            Decrypted secret value
        """
        return self._secrets.get(key, default)

    def set_secret(self, key: str, value: str):
        """
        Set encrypted secret

        Args:
            key: Secret key
            value: Secret value to encrypt
        """
        self._secrets[key] = value

    def remove_secret(self, key: str):
        """Remove encrypted secret"""
        if key in self._secrets:
            del self._secrets[key]

    def export_config(self, file_path: Path, include_secrets: bool = False) -> bool:
        """
        Export configuration to file

        Args:
            file_path: Target file path
            include_secrets: Whether to include secrets (not recommended)

        Returns:
            Success status
        """
        try:
            export_data = {
                'config': self._config,
            }

            if include_secrets:
                export_data['secrets'] = self._secrets
                logger.warning("Exporting configuration with secrets included!")

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=4, ensure_ascii=False)

            logger.info(f"Configuration exported to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to export configuration: {e}")
            return False

    def import_config(self, file_path: Path, import_secrets: bool = False) -> bool:
        """
        Import configuration from file

        Args:
            file_path: Source file path
            import_secrets: Whether to import secrets

        Returns:
            Success status
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)

            if 'config' in import_data:
                self._config = import_data['config']

            if import_secrets and 'secrets' in import_data:
                self._secrets = import_data['secrets']
                logger.warning("Imported configuration with secrets!")

            self.save()
            logger.info(f"Configuration imported from {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to import configuration: {e}")
            return False

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "application": {
                "name": "PingMonitor Pro",
                "version": "2.0.0",
                "author": "Fabrizio Cerchia",
                "auto_start_monitoring": True,
                "minimize_to_tray": True,
                "check_updates": True,
                "language": "en"
            },
            "monitoring": {
                "default_interval": 60,
                "default_timeout": 5,
                "concurrent_checks": 10,
                "retry_attempts": 3,
                "retry_delay": 5,
                "adaptive_interval": True,
                "fast_interval": 30,
                "slow_interval": 300
            },
            "database": {
                "type": "sqlite",
                "path": str(self.config_dir / "pingmonitor.db"),
                "backup_enabled": True,
                "backup_interval": 86400,
                "retention_days": 90
            },
            "logging": {
                "level": "INFO",
                "max_file_size": 10485760,  # 10MB
                "backup_count": 5,
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "console_output": True,
                "file_output": True
            },
            "notifications": {
                "enabled": True,
                "channels": [],
                "cooldown": 300,
                "alert_on_down": True,
                "alert_on_up": True,
                "alert_on_degraded": True
            },
            "ui": {
                "theme": "dark",
                "font_size": 12,
                "font_family": "Segoe UI",
                "window_geometry": {},
                "show_graphs": True,
                "refresh_rate": 1000,
                "table_row_height": 35
            },
            "api": {
                "enabled": False,
                "host": "127.0.0.1",
                "port": 8000,
                "enable_docs": True,
                "cors_enabled": False,
                "cors_origins": ["*"]
            },
            "devices": [],
            "device_groups": []
        }

    def reset_to_defaults(self):
        """Reset configuration to defaults"""
        self._config = self._get_default_config()
        self._secrets = {}
        self.save()
        logger.info("Configuration reset to defaults")

    def validate(self) -> tuple[bool, list[str]]:
        """
        Validate configuration

        Returns:
            Tuple of (is_valid, list of errors)
        """
        errors = []

        # Validate required sections
        required_sections = ['application', 'monitoring', 'database', 'logging', 'ui']
        for section in required_sections:
            if section not in self._config:
                errors.append(f"Missing required section: {section}")

        # Validate monitoring settings
        if self.get('monitoring.default_interval', 0) < 10:
            errors.append("Monitoring interval must be at least 10 seconds")

        if self.get('monitoring.default_timeout', 0) < 1:
            errors.append("Monitoring timeout must be at least 1 second")

        # Validate database path
        db_path = Path(self.get('database.path', ''))
        if not db_path.parent.exists():
            errors.append(f"Database directory does not exist: {db_path.parent}")

        # Validate API settings if enabled
        if self.get('api.enabled', False):
            port = self.get('api.port', 0)
            if not (1024 <= port <= 65535):
                errors.append("API port must be between 1024 and 65535")

        return (len(errors) == 0, errors)

    def __repr__(self) -> str:
        return f"<ConfigManager(config_dir={self.config_dir})>"
