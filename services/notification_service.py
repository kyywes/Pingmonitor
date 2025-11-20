"""
PingMonitor Pro v2.3 - Advanced Notification Service
Multi-channel alerts (Email, Telegram) with intelligent auto-recovery logic
"""

import smtplib
import ssl
import base64
import html
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Dict, Optional
from urllib.parse import quote
import logging

# Define logger first to avoid NameError
logger = logging.getLogger(__name__)

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    logger.warning("cryptography library not available - falling back to base64 (INSECURE)")

from .telegram_service import TelegramService


class NotificationService:
    """
    Advanced notification service with intelligent alert logic:
    - Alert only when ping OK but web page unreachable
    - Attempt SSH auto-recovery (reboot)
    - Wait 5 minutes after reboot
    - Send email only if still down after recovery attempt
    """

    def __init__(self, telegram_config: dict = None):
        self.alert_history: Dict[str, dict] = {}
        self.recovery_attempts: Dict[str, dict] = {}
        self.cooldown_period = 300  # 5 minutes

        # Thread safety locks
        self._alert_history_lock = threading.Lock()
        self._recovery_attempts_lock = threading.Lock()

        # Initialize Telegram service
        self.telegram_service = None
        if telegram_config and telegram_config.get('enabled'):
            bot_token = telegram_config.get('bot_token')
            chat_id = telegram_config.get('chat_id')
            if bot_token and chat_id:
                self.telegram_service = TelegramService(bot_token, chat_id)
                logger.info("Telegram notifications enabled")

    def _decrypt_password(self, encrypted_password: str, encryption_key: Optional[str] = None) -> str:
        """
        Decrypt password using Fernet encryption if available, otherwise base64

        Args:
            encrypted_password: Encrypted password string
            encryption_key: Optional encryption key for Fernet (44-char base64 string or password)

        Returns:
            Decrypted password
        """
        try:
            if CRYPTO_AVAILABLE and encryption_key:
                # Use Fernet encryption (secure)
                try:
                    # Check if key is already a valid Fernet key (44 characters base64)
                    if len(encryption_key) == 44:
                        fernet = Fernet(encryption_key.encode())
                    else:
                        # Derive proper Fernet key from password using PBKDF2
                        kdf = PBKDF2HMAC(
                            algorithm=hashes.SHA256(),
                            length=32,
                            salt=b'pingmonitor_stable_salt_v1',  # Stable salt for consistent keys
                            iterations=100000,
                        )
                        key = base64.urlsafe_b64encode(kdf.derive(encryption_key.encode()))
                        fernet = Fernet(key)

                    decrypted = fernet.decrypt(encrypted_password.encode()).decode()
                    return decrypted
                except Exception as e:
                    logger.error(f"Fernet decryption failed: {e}")
                    # Fall through to base64 for backward compatibility

            # Fallback to base64 (INSECURE - for backward compatibility only)
            try:
                return base64.b64decode(encrypted_password.encode()).decode()
            except:
                # Password might not be encoded
                return encrypted_password
        except Exception as e:
            logger.error(f"Password decryption failed: {e}")
            # Try returning as-is as last resort
            return encrypted_password

    def should_send_alert(self, device_ip: str, ping_ok: bool, web_ok: bool) -> bool:
        """
        Determine if alert should be sent based on intelligent logic

        Logic:
        1. Ping OK but Web NOT OK → Start recovery process
        2. After SSH reboot, wait 5 minutes
        3. Check again
        4. If still down → Send email alert

        Args:
            device_ip: Device IP address
            ping_ok: Ping check result
            web_ok: Web check result

        Returns:
            True if should send alert
        """
        # If ping fails, not our concern (network issue)
        if not ping_ok:
            logger.debug(f"{device_ip}: Ping failed, no alert needed")
            return False

        # If web is OK, no problem
        if web_ok:
            # Clear any pending recovery (thread-safe)
            with self._recovery_attempts_lock:
                if device_ip in self.recovery_attempts:
                    del self.recovery_attempts[device_ip]
            return False

        # Ping OK but Web NOT OK - this is our case!
        logger.warning(f"{device_ip}: Ping OK but Web DOWN - checking recovery status")

        # Check if recovery attempt in progress (thread-safe)
        with self._recovery_attempts_lock:
            if device_ip in self.recovery_attempts:
                recovery = self.recovery_attempts[device_ip]

                # Check if 5 minutes have passed since reboot
                time_since_reboot = (datetime.now() - recovery['reboot_time']).total_seconds()

                if time_since_reboot < 300:  # Less than 5 minutes
                    logger.info(f"{device_ip}: Waiting for recovery... {int(300-time_since_reboot)}s remaining")
                    return False
                else:
                    # 5 minutes passed and still down - SEND ALERT!
                    logger.error(f"{device_ip}: Recovery failed after 5 minutes - SENDING ALERT!")
                    # Clear recovery attempt
                    del self.recovery_attempts[device_ip]
                    return True

        # No recovery attempt yet - this is first detection
        # Mark for recovery but don't send alert yet
        logger.info(f"{device_ip}: First detection of web down - will attempt recovery")
        return False

    def mark_recovery_attempt(self, device_ip: str, reboot_time: datetime):
        """
        Mark that recovery (reboot) has been attempted

        Args:
            device_ip: Device IP
            reboot_time: When reboot was executed
        """
        with self._recovery_attempts_lock:
            self.recovery_attempts[device_ip] = {
                'reboot_time': reboot_time,
                'attempts': self.recovery_attempts.get(device_ip, {}).get('attempts', 0) + 1
            }
        logger.info(f"{device_ip}: Recovery attempt marked at {reboot_time}")

    def send_email_alert(self, config: dict, device_info: dict, alert_type: str = "manual_intervention_required") -> bool:
        """
        Send email alert for manual intervention

        Args:
            config: Email configuration
            device_info: Device information
            alert_type: Type of alert

        Returns:
            Success status
        """
        if not config.get('enabled', False):
            logger.warning("Email alerts disabled in config")
            return False

        # HTML escape to prevent XSS attacks
        device_name = html.escape(device_info.get('name', 'Unknown'))
        device_ip = html.escape(device_info.get('ip', 'Unknown'))
        device_location = html.escape(device_info.get('location', 'N/A'))
        device_port = html.escape(str(device_info.get('port', 'N/A')))

        # Check cooldown to prevent spam (thread-safe)
        last_alert_key = f"{device_ip}_{alert_type}"
        with self._alert_history_lock:
            if last_alert_key in self.alert_history:
                last_alert_time = self.alert_history[last_alert_key]
                if (datetime.now() - last_alert_time).total_seconds() < self.cooldown_period:
                    logger.info(f"Alert cooldown active for {device_ip}")
                    return False

        try:
            # Decrypt password securely
            password = self._decrypt_password(
                config['password'],
                config.get('encryption_key')
            )

            # Create email
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"[CRITICAL] Manual Intervention Required - {device_name}"
            msg['From'] = config['username']
            msg['To'] = config['alert_email']

            # Get recovery info (thread-safe)
            with self._recovery_attempts_lock:
                recovery_info = self.recovery_attempts.get(device_ip, {})
                recovery_attempts = recovery_info.get('attempts', 0)

            # HTML email body
            html_body = f"""
            <html>
            <head>
                <style>
                    body {{
                        font-family: 'Segoe UI', Arial, sans-serif;
                        background-color: #f5f5f5;
                        padding: 20px;
                    }}
                    .container {{
                        background-color: white;
                        border-radius: 10px;
                        padding: 30px;
                        max-width: 600px;
                        margin: 0 auto;
                        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                    }}
                    .header {{
                        background: linear-gradient(135deg, #dc2626 0%, #991b1b 100%);
                        color: white;
                        padding: 20px;
                        border-radius: 10px 10px 0 0;
                        margin: -30px -30px 30px -30px;
                        text-align: center;
                    }}
                    .alert-icon {{
                        font-size: 64px;
                        text-align: center;
                        margin: 20px 0;
                    }}
                    .critical-message {{
                        background-color: #fee2e2;
                        border-left: 4px solid #dc2626;
                        padding: 15px;
                        margin: 20px 0;
                        border-radius: 5px;
                    }}
                    .device-info {{
                        background-color: #f9fafb;
                        border: 1px solid #e5e7eb;
                        padding: 15px;
                        margin: 20px 0;
                        border-radius: 5px;
                    }}
                    .info-row {{
                        padding: 8px 0;
                        border-bottom: 1px solid #e5e7eb;
                    }}
                    .info-label {{
                        font-weight: bold;
                        color: #6b7280;
                        display: inline-block;
                        width: 180px;
                    }}
                    .info-value {{
                        color: #1f2937;
                    }}
                    .recovery-section {{
                        background-color: #fef3c7;
                        border-left: 4px solid #f59e0b;
                        padding: 15px;
                        margin: 20px 0;
                        border-radius: 5px;
                    }}
                    .action-steps {{
                        background-color: #e0f2fe;
                        border-left: 4px solid #0284c7;
                        padding: 15px;
                        margin: 20px 0;
                        border-radius: 5px;
                    }}
                    .footer {{
                        text-align: center;
                        margin-top: 30px;
                        padding-top: 20px;
                        border-top: 1px solid #e5e7eb;
                        color: #6b7280;
                        font-size: 12px;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>⚠️ CRITICAL ALERT</h1>
                        <p>Manual Intervention Required</p>
                    </div>

                    <div class="alert-icon">🚨</div>

                    <div class="critical-message">
                        <h2 style="color: #dc2626; margin-top: 0;">Device Requires Manual Intervention</h2>
                        <p>Automatic recovery has been attempted but <strong>failed</strong>.
                        The web service on this device is still unreachable after automatic reboot.</p>
                    </div>

                    <div class="device-info">
                        <h3>Device Information</h3>
                        <div class="info-row">
                            <span class="info-label">Device Name:</span>
                            <span class="info-value"><strong>{device_name}</strong></span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">IP Address:</span>
                            <span class="info-value"><strong>{device_ip}</strong></span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Location:</span>
                            <span class="info-value">{device_location}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Port:</span>
                            <span class="info-value">{device_port}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Alert Time:</span>
                            <span class="info-value">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</span>
                        </div>
                    </div>

                    <div class="recovery-section">
                        <h3>🔄 Auto-Recovery Attempts</h3>
                        <p><strong>Attempts Made:</strong> {recovery_attempts}</p>
                        <p><strong>Last Action:</strong> Automatic reboot via SSH</p>
                        <p><strong>Wait Time:</strong> 5 minutes post-reboot</p>
                        <p><strong>Result:</strong> ❌ Web service still unreachable</p>
                        <p><strong>Network Status:</strong> ✅ Ping responding (network OK)</p>
                        <p><strong>Web Service:</strong> ❌ HTTP/HTTPS not responding</p>
                    </div>

                    <div class="action-steps">
                        <h3>📋 Required Actions</h3>
                        <ol>
                            <li><strong>Connect via SSH:</strong> ssh root@{device_ip}</li>
                            <li><strong>Check service status:</strong> systemctl status [service-name]</li>
                            <li><strong>Check logs:</strong> journalctl -xe</li>
                            <li><strong>Check disk space:</strong> df -h</li>
                            <li><strong>Check memory:</strong> free -h</li>
                            <li><strong>Restart services manually</strong> if needed</li>
                            <li><strong>Verify web interface</strong> accessible</li>
                        </ol>
                        <p style="margin-top: 15px; padding: 10px; background-color: white; border-radius: 5px;">
                            <strong>Quick Access:</strong><br>
                            Web Interface: <a href="http://{quote(device_ip, safe='')}:{quote(device_port, safe='')}">http://{device_ip}:{device_port}</a><br>
                            SSH Command: <code>ssh root@{device_ip}</code>
                        </p>
                    </div>

                    <div class="footer">
                        <p><strong>PingMonitor Pro v2.0</strong></p>
                        <p>Automatic Network Monitoring with Intelligent Recovery</p>
                        <p>This alert was sent because automatic recovery failed</p>
                        <p style="margin-top: 10px; color: #dc2626;">
                            <strong>⚠️ IMMEDIATE ATTENTION REQUIRED</strong>
                        </p>
                    </div>
                </div>
            </body>
            </html>
            """

            # Attach HTML
            html_part = MIMEText(html_body, 'html')
            msg.attach(html_part)

            # Send email with timeout to prevent hanging
            context = ssl.create_default_context()
            smtp_timeout = 30  # 30 seconds timeout

            if config['smtp_port'] == 465:
                with smtplib.SMTP_SSL(config['smtp_server'], config['smtp_port'],
                                       context=context, timeout=smtp_timeout) as server:
                    server.login(config['username'], password)
                    server.send_message(msg)
            else:
                with smtplib.SMTP(config['smtp_server'], config['smtp_port'],
                                   timeout=smtp_timeout) as server:
                    server.starttls(context=context)
                    server.login(config['username'], password)
                    server.send_message(msg)

            # Mark alert as sent (thread-safe)
            with self._alert_history_lock:
                self.alert_history[last_alert_key] = datetime.now()
            logger.info(f"Email alert sent successfully for {device_name} ({device_ip})")

            # Also send Telegram alert if enabled
            if self.telegram_service:
                try:
                    self.telegram_service.send_alert(
                        device_info=device_info,
                        alert_type="critical",
                        recovery_info=recovery_info
                    )
                    logger.info(f"Telegram alert sent successfully for {device_name}")
                except Exception as e:
                    logger.error(f"Failed to send Telegram alert: {e}")

            return True

        except Exception as e:
            logger.error(f"Failed to send email alert: {e}", exc_info=True)
            return False

    def send_status_change_email(self, config: dict, device_info: dict, alert_type: str) -> bool:
        """
        Send email alert for device status change

        Args:
            config: Email configuration
            device_info: Device information including old_status, new_status
            alert_type: Type of alert (device_offline, device_degraded, device_recovered)

        Returns:
            Success status
        """
        if not config.get('enabled', False):
            logger.warning("Email alerts disabled in config")
            return False

        # HTML escape to prevent XSS attacks
        device_name = html.escape(device_info.get('name', 'Unknown'))
        device_ip = html.escape(device_info.get('ip', 'Unknown'))
        device_location = html.escape(device_info.get('location', 'N/A'))
        device_port = html.escape(str(device_info.get('port', 'N/A')))
        old_status = html.escape(device_info.get('old_status', 'UNKNOWN'))
        new_status = html.escape(device_info.get('new_status', 'UNKNOWN'))
        transition_time = html.escape(device_info.get('transition_time', 'N/A'))

        # Check cooldown to prevent spam (thread-safe)
        last_alert_key = f"{device_ip}_status_change"
        with self._alert_history_lock:
            if last_alert_key in self.alert_history:
                last_alert_time = self.alert_history[last_alert_key]
                cooldown = 300  # 5 minutes between status change emails
                if (datetime.now() - last_alert_time).total_seconds() < cooldown:
                    logger.info(f"Status change email cooldown active for {device_ip}")
                    return False

        try:
            # Decrypt password securely
            password = self._decrypt_password(
                config['password'],
                config.get('encryption_key')
            )

            # Create email
            msg = MIMEMultipart('alternative')

            # Set subject based on alert type
            if alert_type == 'device_offline':
                subject = f"🔴 ALERT: {device_name} è OFFLINE"
                severity = "CRITICO"
                color = "#dc2626"
            elif alert_type == 'device_degraded':
                subject = f"🟡 AVVISO: {device_name} è DEGRADED"
                severity = "ATTENZIONE"
                color = "#f59e0b"
            elif alert_type == 'device_recovered':
                subject = f"🟢 RECUPERATO: {device_name} è tornato ONLINE"
                severity = "INFO"
                color = "#10b981"
            else:
                subject = f"ℹ️ Cambio Stato: {device_name}"
                severity = "INFO"
                color = "#3b82f6"

            msg['Subject'] = subject
            msg['From'] = config['username']
            msg['To'] = config['alert_email']

            # HTML email body
            html_body = f"""
            <html>
            <head>
                <style>
                    body {{
                        font-family: 'Segoe UI', Arial, sans-serif;
                        background-color: #f5f5f5;
                        padding: 20px;
                    }}
                    .container {{
                        background-color: white;
                        border-radius: 10px;
                        padding: 30px;
                        max-width: 600px;
                        margin: 0 auto;
                        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                    }}
                    .header {{
                        background: {color};
                        color: white;
                        padding: 20px;
                        border-radius: 10px 10px 0 0;
                        margin: -30px -30px 30px -30px;
                        text-align: center;
                    }}
                    .status-change {{
                        background-color: #f9fafb;
                        border: 2px solid {color};
                        padding: 20px;
                        margin: 20px 0;
                        border-radius: 8px;
                        text-align: center;
                    }}
                    .status {{
                        display: inline-block;
                        padding: 8px 16px;
                        border-radius: 20px;
                        font-weight: bold;
                        margin: 0 10px;
                        font-size: 18px;
                    }}
                    .device-info {{
                        background-color: #f9fafb;
                        border: 1px solid #e5e7eb;
                        padding: 15px;
                        margin: 20px 0;
                        border-radius: 5px;
                    }}
                    .info-row {{
                        padding: 8px 0;
                        border-bottom: 1px solid #e5e7eb;
                    }}
                    .footer {{
                        text-align: center;
                        margin-top: 30px;
                        padding-top: 20px;
                        border-top: 1px solid #e5e7eb;
                        color: #6b7280;
                        font-size: 12px;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>{severity}</h1>
                        <p>Notifica Cambio Stato Dispositivo</p>
                    </div>

                    <div class="status-change">
                        <h2>Transizione di Stato</h2>
                        <div style="margin: 20px 0; font-size: 24px;">
                            <span class="status" style="background-color: #fee2e2; color: #991b1b;">
                                {old_status}
                            </span>
                            <span style="font-size: 32px;">→</span>
                            <span class="status" style="background-color: {color}; color: white;">
                                {new_status}
                            </span>
                        </div>
                        <p style="color: #6b7280; margin-top: 15px;">
                            Ora Transizione: {transition_time}
                        </p>
                    </div>

                    <div class="device-info">
                        <h3>Informazioni Dispositivo</h3>
                        <div class="info-row">
                            <strong>Nome Dispositivo:</strong> {device_name}
                        </div>
                        <div class="info-row">
                            <strong>Indirizzo IP:</strong> {device_ip}
                        </div>
                        <div class="info-row">
                            <strong>Posizione:</strong> {device_location}
                        </div>
                        <div class="info-row">
                            <strong>Porta:</strong> {device_port}
                        </div>
                    </div>

                    <div style="margin-top: 30px; padding: 15px; background-color: #e0f2fe; border-radius: 5px;">
                        <strong>Accesso Rapido:</strong><br>
                        <a href="http://{quote(device_ip, safe='')}:{quote(device_port, safe='')}">
                            http://{device_ip}:{device_port}
                        </a>
                    </div>

                    <div class="footer">
                        <p><strong>PingMonitor Pro v2.3</strong><br>
                        Sistema di Monitoraggio di Rete Automatico</p>
                    </div>
                </div>
            </body>
            </html>
            """

            # Attach HTML
            html_part = MIMEText(html_body, 'html')
            msg.attach(html_part)

            # Send email with timeout to prevent hanging
            context = ssl.create_default_context()
            smtp_timeout = 30  # 30 seconds timeout

            if config['smtp_port'] == 465:
                with smtplib.SMTP_SSL(config['smtp_server'], config['smtp_port'],
                                       context=context, timeout=smtp_timeout) as server:
                    server.login(config['username'], password)
                    server.send_message(msg)
            else:
                with smtplib.SMTP(config['smtp_server'], config['smtp_port'],
                                   timeout=smtp_timeout) as server:
                    server.starttls(context=context)
                    server.login(config['username'], password)
                    server.send_message(msg)

            # Mark alert as sent (thread-safe)
            with self._alert_history_lock:
                self.alert_history[last_alert_key] = datetime.now()
            logger.info(f"Status change email sent for {device_name} ({old_status} -> {new_status})")

            return True

        except Exception as e:
            logger.error(f"Failed to send status change email: {e}", exc_info=True)
            return False

    def send_telegram_alert(self, device_info: dict, alert_type: str = "critical") -> bool:
        """
        Send Telegram alert directly

        Args:
            device_info: Device information
            alert_type: Type of alert

        Returns:
            Success status
        """
        if not self.telegram_service:
            logger.warning("Telegram service not configured")
            return False

        try:
            recovery_info = self.recovery_attempts.get(device_info.get('ip'))
            return self.telegram_service.send_alert(device_info, alert_type, recovery_info)
        except Exception as e:
            logger.error(f"Failed to send Telegram alert: {e}")
            return False

    def send_status_change_telegram(self, device_name: str, device_ip: str, old_status: str, new_status: str) -> bool:
        """
        Send status change notification via Telegram

        Args:
            device_name: Device name
            device_ip: Device IP
            old_status: Previous status
            new_status: New status

        Returns:
            Success status
        """
        if not self.telegram_service:
            return False

        try:
            return self.telegram_service.send_status_change(device_name, device_ip, old_status, new_status)
        except Exception as e:
            logger.error(f"Failed to send Telegram status change: {e}")
            return False

    def clear_recovery(self, device_ip: str):
        """Clear recovery attempt for device (thread-safe)"""
        with self._recovery_attempts_lock:
            if device_ip in self.recovery_attempts:
                del self.recovery_attempts[device_ip]
                logger.info(f"{device_ip}: Recovery cleared")

    def get_recovery_status(self, device_ip: str) -> Optional[dict]:
        """Get recovery status for device (thread-safe)"""
        with self._recovery_attempts_lock:
            return self.recovery_attempts.get(device_ip)
