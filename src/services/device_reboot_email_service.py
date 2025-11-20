"""
PingMonitor Pro - Device Reboot Email Service
Invia email specifiche per ogni dispositivo riavviato con dettagli del reboot
"""

import smtplib
import ssl
import html
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict
import logging

logger = logging.getLogger(__name__)


class DeviceRebootEmailService:
    """
    Servizio per inviare email individuali dopo ogni reboot di dispositivo
    """

    def __init__(self, email_config: dict):
        """
        Initialize device reboot email service

        Args:
            email_config: Configurazione email (smtp_server, port, username, password, from, to)
        """
        self.email_config = email_config

    def send_reboot_notification(self, device_info: dict, recovery_log: dict) -> tuple[bool, str]:
        """
        Invia email di notifica per un dispositivo riavviato

        Args:
            device_info: Informazioni dispositivo (name, ip, location, etc.)
            recovery_log: Log del recupero (diagnostics, memory_percent, reboot_reason, etc.)

        Returns:
            Tuple (success, message)
        """
        try:
            # Get recipients
            recipients = self._get_recipients()
            if not recipients:
                logger.warning("Nessun destinatario email configurato")
                return False, "Destinatari email non configurati"

            # Extract info
            device_name = html.escape(device_info.get('name', 'Unknown'))
            device_ip = html.escape(device_info.get('ip', 'Unknown'))
            device_location = html.escape(device_info.get('location', 'N/A'))

            memory_percent = recovery_log.get('memory_percent', 0)
            high_memory = recovery_log.get('high_memory', False)
            reboot_reason = html.escape(recovery_log.get('reboot_reason', 'Servizio web non risponde'))
            reboot_time = recovery_log.get('time', datetime.now()).strftime('%d/%m/%Y %H:%M:%S')

            # Get diagnostics
            diagnostics = recovery_log.get('diagnostics', {})
            uptime = html.escape(diagnostics.get('uptime', 'N/A'))
            memory = html.escape(diagnostics.get('memory', 'N/A'))
            disk = html.escape(diagnostics.get('disk', 'N/A'))
            load_avg = html.escape(diagnostics.get('load_average', 'N/A'))

            # Create email
            msg = MIMEMultipart('alternative')
            msg['From'] = self.email_config.get('from_email', 'pingmonitor@localhost')
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = f"🔄 Reboot Automatico: {device_name} - PingMonitor Pro"

            # HTML body
            html_body = self._create_email_body(
                device_name, device_ip, device_location,
                memory_percent, high_memory, reboot_reason, reboot_time,
                uptime, memory, disk, load_avg
            )

            msg.attach(MIMEText(html_body, 'html'))

            # Send email
            success, error_msg = self._send_email(msg, recipients)

            if success:
                logger.info(f"Email reboot inviata per {device_name} ({device_ip})")
                return True, "Email reboot inviata con successo"
            else:
                return False, error_msg or "Errore invio email"

        except Exception as e:
            logger.error(f"Errore invio email reboot: {e}", exc_info=True)
            return False, str(e)

    def _get_recipients(self) -> list[str]:
        """
        Ottiene lista destinatari email

        Returns:
            Lista indirizzi email
        """
        recipients = []

        # Default recipients
        default_recipients = [
            "fabrizio.cerchia@eredimercuri.com",
            "assistenza.paipl@eredimercuri.com"
        ]
        recipients.extend(default_recipients)

        # Additional recipients from config
        additional = self.email_config.get('additional_recipients', [])
        if isinstance(additional, list):
            recipients.extend(additional)
        elif isinstance(additional, str):
            recipients.extend([e.strip() for e in additional.split(',') if e.strip()])

        return list(set(recipients))  # Remove duplicates

    def _create_email_body(self, device_name, device_ip, device_location,
                          memory_percent, high_memory, reboot_reason, reboot_time,
                          uptime, memory, disk, load_avg) -> str:
        """
        Crea HTML email body per notifica reboot

        Returns:
            HTML string
        """
        # Determina colore basato su motivo reboot
        header_color = "#dc2626" if high_memory else "#f59e0b"
        status_badge = "MEMORIA ALTA" if high_memory else "SERVIZIO DOWN"
        status_color = "#fee2e2" if high_memory else "#fef3c7"
        status_text_color = "#991b1b" if high_memory else "#92400e"

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
            color: #333;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            background-color: white;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: {header_color};
            color: white;
            padding: 30px 20px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 28px;
            font-weight: 700;
        }}
        .header p {{
            margin: 10px 0 0 0;
            font-size: 16px;
            opacity: 0.9;
        }}
        .content {{
            padding: 30px;
        }}
        .alert-box {{
            background-color: {status_color};
            border-left: 4px solid {header_color};
            padding: 20px;
            margin-bottom: 25px;
            border-radius: 6px;
        }}
        .alert-box h2 {{
            margin: 0 0 10px 0;
            color: {status_text_color};
            font-size: 20px;
            font-weight: 600;
        }}
        .alert-box p {{
            margin: 0;
            color: {status_text_color};
            font-size: 14px;
        }}
        .info-section {{
            background-color: #f9fafb;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
        }}
        .info-section h3 {{
            margin: 0 0 15px 0;
            color: #1f2937;
            font-size: 18px;
            font-weight: 600;
        }}
        .info-row {{
            display: flex;
            padding: 10px 0;
            border-bottom: 1px solid #e5e7eb;
        }}
        .info-row:last-child {{
            border-bottom: none;
        }}
        .info-label {{
            flex: 0 0 160px;
            font-weight: 600;
            color: #6b7280;
            font-size: 14px;
        }}
        .info-value {{
            flex: 1;
            color: #1f2937;
            font-size: 14px;
        }}
        .diagnostic-box {{
            background-color: #0f172a;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 20px;
            font-family: 'Courier New', monospace;
            color: #10b981;
            font-size: 12px;
            overflow-x: auto;
        }}
        .diagnostic-box h4 {{
            margin: 0 0 10px 0;
            color: #cbd5e1;
            font-size: 14px;
            font-weight: 600;
        }}
        .diagnostic-box pre {{
            margin: 0;
            white-space: pre-wrap;
        }}
        .footer {{
            background-color: #f9fafb;
            padding: 20px;
            text-align: center;
            border-top: 1px solid #e5e7eb;
        }}
        .footer p {{
            margin: 5px 0;
            color: #6b7280;
            font-size: 13px;
        }}
        .badge {{
            display: inline-block;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 700;
            background-color: {status_color};
            color: {status_text_color};
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔄 Reboot Automatico Eseguito</h1>
            <p>Sistema di Monitoraggio Automatico</p>
        </div>

        <div class="content">
            <div class="alert-box">
                <h2>Azione Automatica Completata</h2>
                <p><strong>Dispositivo riavviato automaticamente dal sistema PingMonitor Pro</strong></p>
                <p style="margin-top: 10px;">
                    <span class="badge">{status_badge}</span>
                </p>
            </div>

            <div class="info-section">
                <h3>📋 Informazioni Dispositivo</h3>
                <div class="info-row">
                    <div class="info-label">Nome Dispositivo:</div>
                    <div class="info-value"><strong>{device_name}</strong></div>
                </div>
                <div class="info-row">
                    <div class="info-label">Indirizzo IP:</div>
                    <div class="info-value"><strong>{device_ip}</strong></div>
                </div>
                <div class="info-row">
                    <div class="info-label">Posizione (km):</div>
                    <div class="info-value">{device_location}</div>
                </div>
                <div class="info-row">
                    <div class="info-label">Ora Reboot:</div>
                    <div class="info-value">{reboot_time}</div>
                </div>
            </div>

            <div class="info-section">
                <h3>🔍 Motivo Reboot</h3>
                <div class="info-row">
                    <div class="info-label">Causa:</div>
                    <div class="info-value"><strong>{reboot_reason}</strong></div>
                </div>
                <div class="info-row">
                    <div class="info-label">Utilizzo Memoria:</div>
                    <div class="info-value"><strong>{memory_percent:.1f}%</strong></div>
                </div>
            </div>

            <div class="diagnostic-box">
                <h4>💻 Diagnostica Pre-Reboot</h4>
                <pre><strong>Uptime:</strong>
{uptime}

<strong>Memoria (free -h):</strong>
{memory}

<strong>Disco (df -h):</strong>
{disk[:200]}...

<strong>Load Average:</strong>
{load_avg}</pre>
            </div>

            <div style="background-color: #e0f2fe; border-left: 4px solid #0284c7; padding: 15px; border-radius: 6px; margin-bottom: 20px;">
                <h3 style="margin: 0 0 10px 0; color: #0c4a6e; font-size: 16px;">ℹ️ Prossimi Passi</h3>
                <p style="margin: 0; color: #075985; font-size: 14px;">
                    • Il dispositivo si riavvierà automaticamente<br>
                    • Il sistema attenderà 5 minuti per il riavvio<br>
                    • Verranno eseguiti controlli automatici<br>
                    • Se il problema persiste, riceverai un'altra notifica
                </p>
            </div>
        </div>

        <div class="footer">
            <p><strong>PingMonitor Pro v2.3</strong></p>
            <p>Sistema di Monitoraggio Automatico con Recupero Intelligente</p>
            <p>Questa è un'email automatica generata dal sistema</p>
        </div>
    </div>
</body>
</html>
"""
        return html

    def _send_email(self, msg: MIMEMultipart, recipients: list[str]) -> tuple[bool, str]:
        """
        Invia email via SMTP

        Args:
            msg: Email message
            recipients: Lista destinatari

        Returns:
            Tuple (success, error_message)
        """
        try:
            smtp_server = self.email_config.get('smtp_server', 'smtp.gmail.com')
            smtp_port = self.email_config.get('smtp_port', 587)
            username = self.email_config.get('username', '')
            password = self.email_config.get('password', '')

            if not username or not password:
                error_msg = "Credenziali email non configurate"
                logger.error(error_msg)
                return False, error_msg

            # Create secure connection
            context = ssl.create_default_context()

            with smtplib.SMTP(smtp_server, smtp_port, timeout=30) as server:
                server.starttls(context=context)
                server.login(username, password)
                server.sendmail(msg['From'], recipients, msg.as_string())

            logger.info(f"Email reboot inviata a {len(recipients)} destinatari")
            return True, ""

        except Exception as e:
            error_msg = f"Errore invio email: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return False, error_msg
