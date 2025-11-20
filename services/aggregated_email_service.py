"""
Aggregated Email Service - Send single email with all recovery results
Invia una singola email con tutti i PL recuperati e quelli che richiedono intervento manuale
"""

import smtplib
import ssl
import html
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

    def send_aggregated_email(self, force=False, all_devices=None) -> tuple[bool, str]:
        """
        Send aggregated email with all recovery results and current device statuses

        Args:
            force: If True, send email even if there are no pending results (for manual Check Now)
            all_devices: Optional list of all devices with current status (for real-time reporting)

        Returns:
            Tuple of (success, message)
        """
        logger.info(f"send_aggregated_email called - force={force}, pending_recoveries={len(self.pending_recoveries)}, pending_failures={len(self.pending_failures)}")

        if not force and not self.should_send_email():
            logger.info("Skipping email send - no pending results and force=False")
            return True, "Nessun risultato da inviare"

        try:
            # Get recipients
            recipients = self._get_recipients()
            logger.info(f"Email recipients: {recipients}")
            if not recipients:
                logger.warning("No email recipients configured")
                return False, "Destinatari email non configurati"

            # Create email
            msg = MIMEMultipart('alternative')
            msg['From'] = self.email_config.get('from_email', 'pingmonitor@localhost')
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = f"PingMonitor Pro - Report Dispositivi PAI-PL ({datetime.now().strftime('%d/%m/%Y %H:%M')})"

            # Create email body with all devices
            html_body = self._create_email_body(all_devices)
            msg.attach(MIMEText(html_body, 'html'))

            # Send email
            success, error_msg = self._send_email(msg, recipients)

            if success:
                # Clear pending lists after successful send
                count_success = len(self.pending_recoveries)
                count_failure = len(self.pending_failures)
                self.pending_recoveries.clear()
                self.pending_failures.clear()
                return True, f"Email inviata: {count_success} recuperi, {count_failure} fallimenti"
            else:
                return False, error_msg or "Errore sconosciuto nell'invio email"

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

        # Default recipients (always included)
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
            # Split by comma if string
            recipients.extend([e.strip() for e in additional.split(',') if e.strip()])

        return list(set(recipients))  # Remove duplicates

    def _create_email_body(self, all_devices=None) -> str:
        """
        Create HTML email body with recovery results and current device statuses

        Args:
            all_devices: Optional list of all devices with current status

        Returns:
            HTML string
        """
        # Calculate current offline/degraded devices from all_devices
        current_offline = []
        current_degraded = []
        if all_devices:
            for device in all_devices:
                if device.current_status == 'offline':
                    current_offline.append(device)
                elif device.current_status == 'degraded':
                    current_degraded.append(device)

        total_problems = len(current_offline) + len(current_degraded)

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; color: #333; }}
        h1 {{ color: #2563eb; border-bottom: 3px solid #2563eb; padding-bottom: 10px; }}
        h2 {{ color: #059669; margin-top: 30px; }}
        h2.failure {{ color: #ef4444; }}
        h2.warning {{ color: #f59e0b; }}
        table {{ border-collapse: collapse; width: 100%; margin: 15px 0; }}
        th {{ background-color: #2563eb; color: white; padding: 12px; text-align: left; }}
        th.success {{ background-color: #10b981; }}
        th.failure {{ background-color: #ef4444; }}
        th.warning {{ background-color: #f59e0b; }}
        td {{ padding: 10px; border-bottom: 1px solid #ddd; }}
        tr:hover {{ background-color: #f3f4f6; }}
        .summary {{ background-color: #f0f9ff; padding: 15px; border-radius: 8px; margin: 20px 0; }}
        .summary-critical {{ background-color: #fee2e2; padding: 15px; border-radius: 8px; margin: 20px 0; font-weight: bold; font-size: 16px; }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; font-size: 12px; }}
        .badge {{ display: inline-block; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: bold; }}
        .badge-success {{ background-color: #d1fae5; color: #065f46; }}
        .badge-failure {{ background-color: #fee2e2; color: #991b1b; }}
        .badge-warning {{ background-color: #fef3c7; color: #92400e; }}
    </style>
</head>
<body>
    <h1>📊 Report Stato Dispositivi PAI-PL</h1>

    <div class="summary-critical">
        <p>🚨 <strong>DISPOSITIVI CON PROBLEMI (IN TEMPO REALE):</strong> <span class="badge badge-failure">{total_problems}</span></p>
        <p style="margin-left: 30px;">• <strong>Offline (Rossi):</strong> <span class="badge badge-failure">{len(current_offline)}</span></p>
        <p style="margin-left: 30px;">• <strong>Degraded (Gialli):</strong> <span class="badge badge-warning">{len(current_degraded)}</span></p>
    </div>

    <div class="summary">
        <p><strong>Data Report:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
        <p><strong>Frequenza Report:</strong> Ogni 6 ore (automatico)</p>
        <p><strong>Dispositivi Recuperati (ultime 6 ore):</strong> <span class="badge badge-success">{len(self.pending_recoveries)}</span></p>
        <p><strong>Tentativi Recupero Falliti (ultime 6 ore):</strong> <span class="badge badge-failure">{len(self.pending_failures)}</span></p>
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

        # Current OFFLINE devices section (REAL-TIME STATUS)
        if current_offline:
            html += """
    <h2 class="failure">🔴 Dispositivi OFFLINE (Stato Attuale in Tempo Reale)</h2>
    <p>I seguenti dispositivi sono attualmente OFFLINE (non rispondono al ping):</p>
    <table>
        <tr>
            <th class="failure">Nome</th>
            <th class="failure">Indirizzo IP</th>
            <th class="failure">Posizione (km)</th>
            <th class="failure">Stato</th>
            <th class="failure">Ultimo Check</th>
        </tr>
"""
            for device in current_offline:
                last_check = device.last_check.strftime('%d/%m/%Y %H:%M:%S') if hasattr(device, 'last_check') and device.last_check else 'N/A'
                html += f"""
        <tr>
            <td><strong>{device.name}</strong></td>
            <td>{device.ip_address}</td>
            <td>{device.location or 'N/A'}</td>
            <td><span class="badge badge-failure">OFFLINE</span></td>
            <td>{last_check}</td>
        </tr>
"""
            html += """
    </table>
"""

        # Current DEGRADED devices section (REAL-TIME STATUS)
        if current_degraded:
            html += """
    <h2 class="warning">🟡 Dispositivi DEGRADED (Stato Attuale in Tempo Reale)</h2>
    <p>I seguenti dispositivi sono attualmente DEGRADED (ping OK ma pagina web non risponde):</p>
    <table>
        <tr>
            <th class="warning">Nome</th>
            <th class="warning">Indirizzo IP</th>
            <th class="warning">Posizione (km)</th>
            <th class="warning">Stato</th>
            <th class="warning">Ultimo Check</th>
        </tr>
"""
            for device in current_degraded:
                last_check = device.last_check.strftime('%d/%m/%Y %H:%M:%S') if hasattr(device, 'last_check') and device.last_check else 'N/A'
                html += f"""
        <tr>
            <td><strong>{device.name}</strong></td>
            <td>{device.ip_address}</td>
            <td>{device.location or 'N/A'}</td>
            <td><span class="badge badge-warning">DEGRADED</span></td>
            <td>{last_check}</td>
        </tr>
"""
            html += """
    </table>
"""

        # Footer
        html += """
    <div class="footer">
        <p>🤖 Questo è un messaggio automatico generato da PingMonitor</p>
        <p>Per ulteriori informazioni, consultare il dashboard del sistema di monitoraggio.</p>
    </div>
</body>
</html>
"""
        return html

    def _send_email(self, msg: MIMEMultipart, recipients: List[str]) -> tuple[bool, str]:
        """
        Send email via SMTP

        Args:
            msg: Email message
            recipients: List of recipients

        Returns:
            Tuple of (success, error_message)
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

            logger.info(f"Aggregated email sent successfully to {len(recipients)} recipients")
            return True, ""

        except smtplib.SMTPAuthenticationError as e:
            error_msg = f"Autenticazione SMTP fallita: {str(e)}"
            logger.error(f"Failed to send email: {error_msg}", exc_info=True)
            return False, error_msg
        except smtplib.SMTPException as e:
            error_msg = f"Errore SMTP: {str(e)}"
            logger.error(f"Failed to send email: {error_msg}", exc_info=True)
            return False, error_msg
        except TimeoutError as e:
            error_msg = f"Timeout connessione al server SMTP {smtp_server}:{smtp_port} - Verifica la connessione di rete"
            logger.error(f"Failed to send email: {error_msg}", exc_info=True)
            return False, error_msg
        except OSError as e:
            # Network errors like WinError 10060
            error_msg = f"Impossibile connettersi al server SMTP {smtp_server}:{smtp_port} - Verifica la connessione di rete"
            logger.error(f"Failed to send email: {error_msg} - {str(e)}", exc_info=True)
            return False, error_msg
        except Exception as e:
            error_msg = f"Errore inaspettato: {str(e)}"
            logger.error(f"Failed to send email: {error_msg}", exc_info=True)
            return False, error_msg
