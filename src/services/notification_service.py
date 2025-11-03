"""
PingMonitor Pro v2.3 - Advanced Notification Service
Multi-channel alerts (Email, Telegram) with intelligent auto-recovery logic
"""

import smtplib
import ssl
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Dict, Optional
import logging

from .telegram_service import TelegramService

logger = logging.getLogger(__name__)


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

        # Initialize Telegram service
        self.telegram_service = None
        if telegram_config and telegram_config.get('enabled'):
            bot_token = telegram_config.get('bot_token')
            chat_id = telegram_config.get('chat_id')
            if bot_token and chat_id:
                self.telegram_service = TelegramService(bot_token, chat_id)
                logger.info("Telegram notifications enabled")

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
            # Clear any pending recovery
            if device_ip in self.recovery_attempts:
                del self.recovery_attempts[device_ip]
            return False

        # Ping OK but Web NOT OK - this is our case!
        logger.warning(f"{device_ip}: Ping OK but Web DOWN - checking recovery status")

        # Check if recovery attempt in progress
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

        device_name = device_info.get('name', 'Unknown')
        device_ip = device_info.get('ip', 'Unknown')

        # Check cooldown to prevent spam
        last_alert_key = f"{device_ip}_{alert_type}"
        if last_alert_key in self.alert_history:
            last_alert_time = self.alert_history[last_alert_key]
            if (datetime.now() - last_alert_time).total_seconds() < self.cooldown_period:
                logger.info(f"Alert cooldown active for {device_ip}")
                return False

        try:
            # Decode password (base64 encoded in config)
            try:
                password = base64.b64decode(config['password'].encode()).decode()
            except:
                password = config['password']

            # Create email
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"[CRITICAL] Manual Intervention Required - {device_name}"
            msg['From'] = config['username']
            msg['To'] = config['alert_email']

            # Get recovery info
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
                            <span class="info-value">{device_info.get('location', 'N/A')}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Port:</span>
                            <span class="info-value">{device_info.get('port', 'N/A')}</span>
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
                            Web Interface: <a href="http://{device_ip}:{device_info.get('port', 80)}">http://{device_ip}:{device_info.get('port', 80)}</a><br>
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

            # Send email
            context = ssl.create_default_context()

            if config['smtp_port'] == 465:
                with smtplib.SMTP_SSL(config['smtp_server'], config['smtp_port'], context=context) as server:
                    server.login(config['username'], password)
                    server.send_message(msg)
            else:
                with smtplib.SMTP(config['smtp_server'], config['smtp_port']) as server:
                    server.starttls(context=context)
                    server.login(config['username'], password)
                    server.send_message(msg)

            # Mark alert as sent
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
        """Clear recovery attempt for device"""
        if device_ip in self.recovery_attempts:
            del self.recovery_attempts[device_ip]
            logger.info(f"{device_ip}: Recovery cleared")

    def get_recovery_status(self, device_ip: str) -> Optional[dict]:
        """Get recovery status for device"""
        return self.recovery_attempts.get(device_ip)
