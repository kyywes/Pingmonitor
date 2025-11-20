"""
PingMonitor Pro v2.3 - Telegram Notification Service
Send alerts via Telegram Bot API
"""

import requests
from datetime import datetime
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class TelegramService:
    """
    Telegram notification service for sending alerts
    """

    def __init__(self, bot_token: str = None, chat_id: str = None):
        """
        Initialize Telegram service

        Args:
            bot_token: Telegram Bot API token
            chat_id: Telegram chat/channel ID
        """
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{bot_token}" if bot_token else None

    def set_credentials(self, bot_token: str, chat_id: str):
        """
        Set or update Telegram credentials

        Args:
            bot_token: Bot API token
            chat_id: Chat/channel ID
        """
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{bot_token}"

    def send_message(self, message: str, parse_mode: str = "HTML") -> bool:
        """
        Send a simple text message

        Args:
            message: Message text
            parse_mode: Message parse mode (HTML or Markdown)

        Returns:
            Success status
        """
        if not self.bot_token or not self.chat_id:
            logger.warning("Telegram credentials not configured")
            return False

        try:
            url = f"{self.api_url}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": parse_mode,
                "disable_web_page_preview": True
            }

            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()

            logger.info("Telegram message sent successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False

    def send_alert(self, device_info: dict, alert_type: str = "critical", recovery_info: dict = None) -> bool:
        """
        Send formatted alert message

        Args:
            device_info: Device information
            alert_type: Type of alert (critical, warning, info, recovery)
            recovery_info: Recovery attempt information

        Returns:
            Success status
        """
        if not self.bot_token or not self.chat_id:
            logger.warning("Telegram credentials not configured")
            return False

        device_name = device_info.get('name', 'Unknown')
        device_ip = device_info.get('ip', 'Unknown')
        location = device_info.get('location', 'N/A')
        port = device_info.get('port', 'N/A')

        # Alert emoji and title based on type
        if alert_type == "critical":
            emoji = "🚨"
            title = "CRITICAL ALERT"
            status_emoji = "🔴"
        elif alert_type == "warning":
            emoji = "⚠️"
            title = "WARNING"
            status_emoji = "🟡"
        elif alert_type == "recovery":
            emoji = "✅"
            title = "DEVICE RECOVERED"
            status_emoji = "🟢"
        else:
            emoji = "ℹ️"
            title = "INFO"
            status_emoji = "🔵"

        # Build message
        message = f"{emoji} <b>{title}</b>\n\n"
        message += f"<b>Device:</b> {device_name}\n"
        message += f"<b>IP Address:</b> <code>{device_ip}</code>\n"
        message += f"<b>Location:</b> {location}\n"
        message += f"<b>Port:</b> {port}\n"
        message += f"<b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"

        # Add recovery info if available
        if recovery_info:
            attempts = recovery_info.get('attempts', 0)
            message += f"\n<b>🔄 Recovery Attempts:</b> {attempts}\n"

            if alert_type == "critical":
                message += f"<b>Status:</b> {status_emoji} Auto-recovery failed\n"
                message += f"<b>Network:</b> ✅ Ping OK\n"
                message += f"<b>Web Service:</b> ❌ Not responding\n"
                message += f"\n<b>⚠️ MANUAL INTERVENTION REQUIRED</b>\n"
            elif alert_type == "recovery":
                message += f"<b>Status:</b> {status_emoji} Device back online\n"

        # Add action items for critical alerts
        if alert_type == "critical":
            message += f"\n<b>📋 Required Actions:</b>\n"
            message += f"• Connect via SSH: <code>ssh root@{device_ip}</code>\n"
            message += f"• Check service status\n"
            message += f"• Review system logs\n"
            message += f"• Verify web interface\n"
            message += f"\n<b>Quick Access:</b>\n"
            message += f"• Web: http://{device_ip}:{port}\n"

        message += f"\n<i>PingMonitor Pro v2.3 - Auto Monitoring</i>"

        return self.send_message(message)

    def send_status_change(self, device_name: str, device_ip: str, old_status: str, new_status: str) -> bool:
        """
        Send device status change notification

        Args:
            device_name: Device name
            device_ip: Device IP
            old_status: Previous status
            new_status: New status

        Returns:
            Success status
        """
        # Status emojis
        status_map = {
            'online': '🟢',
            'offline': '🔴',
            'degraded': '🟡',
            'unknown': '⚪'
        }

        old_emoji = status_map.get(old_status, '⚪')
        new_emoji = status_map.get(new_status, '⚪')

        message = f"<b>📊 Status Change</b>\n\n"
        message += f"<b>Device:</b> {device_name}\n"
        message += f"<b>IP:</b> <code>{device_ip}</code>\n"
        message += f"<b>Status:</b> {old_emoji} {old_status.upper()} → {new_emoji} {new_status.upper()}\n"
        message += f"<b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        message += f"\n<i>PingMonitor Pro v2.3</i>"

        return self.send_message(message)

    def test_connection(self) -> tuple[bool, str]:
        """
        Test Telegram bot connection

        Returns:
            (success, message) tuple
        """
        if not self.bot_token or not self.chat_id:
            return False, "Bot token and chat ID not configured"

        try:
            # Test getMe API
            url = f"{self.api_url}/getMe"
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            data = response.json()
            if data.get('ok'):
                bot_info = data.get('result', {})
                bot_name = bot_info.get('username', 'Unknown')

                # Send test message
                test_msg = f"✅ <b>Connection Test Successful!</b>\n\n"
                test_msg += f"<b>Bot:</b> @{bot_name}\n"
                test_msg += f"<b>Chat ID:</b> {self.chat_id}\n"
                test_msg += f"<b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                test_msg += f"\n<i>PingMonitor Pro v2.3 is ready to send notifications!</i>"

                if self.send_message(test_msg):
                    return True, f"Connection successful! Bot: @{bot_name}"
                else:
                    return False, "Failed to send test message"
            else:
                return False, "Invalid bot token"

        except requests.exceptions.RequestException as e:
            return False, f"Connection error: {str(e)}"
        except Exception as e:
            return False, f"Error: {str(e)}"

    def send_daily_report(self, stats: dict) -> bool:
        """
        Send daily monitoring report

        Args:
            stats: Statistics dictionary

        Returns:
            Success status
        """
        message = f"📊 <b>Daily Monitoring Report</b>\n\n"
        message += f"<b>Date:</b> {datetime.now().strftime('%Y-%m-%d')}\n\n"

        message += f"<b>📈 Statistics:</b>\n"
        message += f"• Total Devices: {stats.get('total_devices', 0)}\n"
        message += f"• 🟢 Online: {stats.get('online', 0)}\n"
        message += f"• 🔴 Offline: {stats.get('offline', 0)}\n"
        message += f"• 🟡 Degraded: {stats.get('degraded', 0)}\n\n"

        message += f"<b>🔍 Checks:</b>\n"
        message += f"• Total: {stats.get('total_checks', 0)}\n"
        message += f"• ✅ Successful: {stats.get('successful_checks', 0)}\n"
        message += f"• ❌ Failed: {stats.get('failed_checks', 0)}\n\n"

        avg_uptime = stats.get('average_uptime', 0)
        message += f"<b>Avg Uptime:</b> {avg_uptime:.2f}%\n"

        avg_response = stats.get('average_response_time', 0)
        message += f"<b>Avg Response:</b> {avg_response:.1f}ms\n"

        message += f"\n<i>PingMonitor Pro v2.3 - Daily Report</i>"

        return self.send_message(message)
