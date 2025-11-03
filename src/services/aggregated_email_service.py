"""
Aggregated Email Service - Send single email with all recovery results
Invia una singola email con tutti i PL recuperati e quelli che richiedono intervento manuale
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


class AggregatedEmailService:
    """
    Service to send aggregated email reports with recovery results
    """

    def __init__(self, email_config: dict):
        """
        Initialize aggregated email service

        Args:
            email_config: Email configuration (smtp_server, port, username, password, from, to)
        """
        self.email_config = email_config
        self.pending_recoveries = []  # List of successful recoveries
        self.pending_failures = []  # List of devices requiring manual intervention

    def add_recovery_success(self, device):
        """
        Add a successful recovery to the pending list

        Args:
            device: Device object that was successfully recovered
        """
        self.pending_recoveries.append({
            'name': device.name,
            'ip': device.ip_address,
            'location': device.location or 'N/A',
            'timestamp': datetime.utcnow()
        })
        logger.info(f"Added successful recovery: {device.name} ({device.ip_address})")

    def add_recovery_failure(self, device, reason=''):
        """
        Add a failed recovery to the pending list

        Args:
            device: Device object that requires manual intervention
            reason: Reason for failure
        """
        self.pending_failures.append({
            'name': device.name,
            'ip': device.ip_address,
            'location': device.location or 'N/A',
            'reason': reason,
            'timestamp': datetime.utcnow()
        })
        logger.info(f"Added failed recovery: {device.name} ({device.ip_address}) - {reason}")

    def should_send_email(self) -> bool:
        """
        Check if there are pending results to send

        Returns:
            True if there are pending successes or failures
        """
        return len(self.pending_recoveries) > 0 or len(self.pending_failures) > 0

    def send_aggregated_email(self) -> tuple[bool, str]:
        """
        Send aggregated email with all recovery results

        Returns:
            Tuple of (success, message)
        """
        if not self.should_send_email():
            return True, "No pending results to send"

        try:
            # Get recipients
            recipients = self._get_recipients()
            if not recipients:
                logger.warning("No email recipients configured")
                return False, "No recipients configured"

            # Create email
            msg = MIMEMultipart('alternative')
            msg['From'] = self.email_config.get('from_email', 'pingmonitor@localhost')
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = f"PingMonitor Pro - Report Recupero Dispositivi PAI-PL ({datetime.now().strftime('%d/%m/%Y %H:%M')})"

            # Create email body
            html_body = self._create_email_body()
            msg.attach(MIMEText(html_body, 'html'))

            # Send email
            success = self._send_email(msg, recipients)

            if success:
                # Clear pending lists after successful send
                count_success = len(self.pending_recoveries)
                count_failure = len(self.pending_failures)
                self.pending_recoveries.clear()
                self.pending_failures.clear()
                return True, f"Email inviata: {count_success} recuperi, {count_failure} fallimenti"
            else:
                return False, "Failed to send email"

        except Exception as e:
            logger.error(f"Error sending aggregated email: {e}", exc_info=True)
            return False, str(e)

    def _get_recipients(self) -> List[str]:
        """
        Get list of email recipients

        Returns:
            List of email addresses
        """
        recipients = []

        # Primary recipient
        primary_email = "fabrizio.cerchia@eredimercuri.com"
        recipients.append(primary_email)

        # Additional recipients from config
        additional = self.email_config.get('additional_recipients', [])
        if isinstance(additional, list):
            recipients.extend(additional)
        elif isinstance(additional, str):
            # Split by comma if string
            recipients.extend([e.strip() for e in additional.split(',') if e.strip()])

        return list(set(recipients))  # Remove duplicates

    def _create_email_body(self) -> str:
        """
        Create HTML email body with recovery results

        Returns:
            HTML string
        """
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; color: #333; }}
        h1 {{ color: #2563eb; border-bottom: 3px solid #2563eb; padding-bottom: 10px; }}
        h2 {{ color: #059669; margin-top: 30px; }}
        h2.failure {{ color: #ef4444; }}
        table {{ border-collapse: collapse; width: 100%; margin: 15px 0; }}
        th {{ background-color: #2563eb; color: white; padding: 12px; text-align: left; }}
        th.success {{ background-color: #10b981; }}
        th.failure {{ background-color: #ef4444; }}
        td {{ padding: 10px; border-bottom: 1px solid #ddd; }}
        tr:hover {{ background-color: #f3f4f6; }}
        .summary {{ background-color: #f0f9ff; padding: 15px; border-radius: 8px; margin: 20px 0; }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; font-size: 12px; }}
        .badge {{ display: inline-block; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: bold; }}
        .badge-success {{ background-color: #d1fae5; color: #065f46; }}
        .badge-failure {{ background-color: #fee2e2; color: #991b1b; }}
    </style>
</head>
<body>
    <h1>📊 Report Recupero Dispositivi PAI-PL</h1>

    <div class="summary">
        <p><strong>Data Report:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
        <p><strong>Dispositivi Recuperati:</strong> <span class="badge badge-success">{len(self.pending_recoveries)}</span></p>
        <p><strong>Intervento Manuale Richiesto:</strong> <span class="badge badge-failure">{len(self.pending_failures)}</span></p>
    </div>
"""

        # Successful recoveries section
        if self.pending_recoveries:
            html += """
    <h2>✅ Dispositivi Recuperati con Successo</h2>
    <p>I seguenti dispositivi sono stati recuperati automaticamente tramite riavvio SSH:</p>
    <table>
        <tr>
            <th class="success">Nome</th>
            <th class="success">Indirizzo IP</th>
            <th class="success">Posizione (km)</th>
            <th class="success">Ora Recupero</th>
        </tr>
"""
            for recovery in self.pending_recoveries:
                html += f"""
        <tr>
            <td><strong>{recovery['name']}</strong></td>
            <td>{recovery['ip']}</td>
            <td>{recovery['location']}</td>
            <td>{recovery['timestamp'].strftime('%H:%M:%S')}</td>
        </tr>
"""
            html += """
    </table>
"""

        # Failed recoveries section
        if self.pending_failures:
            html += """
    <h2 class="failure">⚠️ Dispositivi che Richiedono Intervento Manuale</h2>
    <p>I seguenti dispositivi NON sono stati recuperati e richiedono intervento manuale:</p>
    <table>
        <tr>
            <th class="failure">Nome</th>
            <th class="failure">Indirizzo IP</th>
            <th class="failure">Posizione (km)</th>
            <th class="failure">Motivo</th>
            <th class="failure">Ora Rilevamento</th>
        </tr>
"""
            for failure in self.pending_failures:
                reason = failure['reason'] if failure['reason'] else 'Dispositivo non raggiungibile'
                html += f"""
        <tr>
            <td><strong>{failure['name']}</strong></td>
            <td>{failure['ip']}</td>
            <td>{failure['location']}</td>
            <td>{reason}</td>
            <td>{failure['timestamp'].strftime('%H:%M:%S')}</td>
        </tr>
"""
            html += """
    </table>
"""

        # Footer
        html += """
    <div class="footer">
        <p>🤖 Questo è un messaggio automatico generato da PingMonitor Pro v2.3</p>
        <p>Per ulteriori informazioni, consultare il dashboard del sistema di monitoraggio.</p>
    </div>
</body>
</html>
"""
        return html

    def _send_email(self, msg: MIMEMultipart, recipients: List[str]) -> bool:
        """
        Send email via SMTP

        Args:
            msg: Email message
            recipients: List of recipients

        Returns:
            True if successful
        """
        try:
            smtp_server = self.email_config.get('smtp_server', 'smtp.gmail.com')
            smtp_port = self.email_config.get('smtp_port', 587)
            username = self.email_config.get('username', '')
            password = self.email_config.get('password', '')

            if not username or not password:
                logger.error("Email credentials not configured")
                return False

            # Create secure connection
            context = ssl.create_default_context()

            with smtplib.SMTP(smtp_server, smtp_port, timeout=30) as server:
                server.starttls(context=context)
                server.login(username, password)
                server.sendmail(msg['From'], recipients, msg.as_string())

            logger.info(f"Aggregated email sent successfully to {len(recipients)} recipients")
            return True

        except Exception as e:
            logger.error(f"Failed to send email: {e}", exc_info=True)
            return False
