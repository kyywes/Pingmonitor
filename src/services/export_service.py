"""
PingMonitor Pro v2.3 - Export Service
Export data to CSV and PDF formats
"""

import csv
from datetime import datetime
from pathlib import Path
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


class ExportService:
    """Service for exporting monitoring data to various formats"""

    @staticmethod
    def export_devices_to_csv(devices: List, file_path: str) -> tuple[bool, str]:
        """
        Export devices list to CSV

        Args:
            devices: List of Device objects
            file_path: Output file path

        Returns:
            (success, message) tuple
        """
        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'ID', 'Name', 'IP Address', 'Device Type', 'Location',
                    'Status', 'Uptime %', 'Response Time (ms)',
                    'Total Checks', 'Successful Checks', 'Failed Checks',
                    'Last Check', 'Enabled', 'Check Interval (s)',
                    'Ping Enabled', 'HTTP Enabled', 'HTTPS Enabled',
                    'SSH Enabled', 'DNS Enabled', 'SNMP Enabled'
                ]

                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

                for device in devices:
                    writer.writerow({
                        'ID': device.id,
                        'Name': device.name,
                        'IP Address': device.ip_address,
                        'Device Type': device.device_type,
                        'Location': device.location or 'N/A',
                        'Status': device.current_status,
                        'Uptime %': f"{device.uptime_percentage:.2f}",
                        'Response Time (ms)': f"{device.response_time:.2f}",
                        'Total Checks': device.total_checks,
                        'Successful Checks': device.successful_checks,
                        'Failed Checks': device.failed_checks,
                        'Last Check': device.last_check_time or 'Never',
                        'Enabled': 'Yes' if device.enabled else 'No',
                        'Check Interval (s)': device.check_interval,
                        'Ping Enabled': 'Yes' if device.ping_enabled else 'No',
                        'HTTP Enabled': 'Yes' if device.http_enabled else 'No',
                        'HTTPS Enabled': 'Yes' if device.https_enabled else 'No',
                        'SSH Enabled': 'Yes' if device.ssh_enabled else 'No',
                        'DNS Enabled': 'Yes' if device.dns_enabled else 'No',
                        'SNMP Enabled': 'Yes' if device.snmp_enabled else 'No'
                    })

            logger.info(f"Exported {len(devices)} devices to {file_path}")
            return True, f"Successfully exported {len(devices)} devices to {file_path}"

        except Exception as e:
            logger.error(f"Failed to export devices to CSV: {e}", exc_info=True)
            return False, f"Export failed: {str(e)}"

    @staticmethod
    def export_check_results_to_csv(check_results: List, file_path: str) -> tuple[bool, str]:
        """
        Export check results to CSV

        Args:
            check_results: List of CheckResult objects
            file_path: Output file path

        Returns:
            (success, message) tuple
        """
        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'ID', 'Device ID', 'Check Type', 'Check Time',
                    'Success', 'Response Time (ms)', 'Status Code',
                    'Error Message', 'Check Data'
                ]

                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

                for result in check_results:
                    writer.writerow({
                        'ID': result.id,
                        'Device ID': result.device_id,
                        'Check Type': result.check_type.value if hasattr(result.check_type, 'value') else result.check_type,
                        'Check Time': result.check_time,
                        'Success': 'Yes' if result.success else 'No',
                        'Response Time (ms)': f"{result.response_time:.2f}" if result.response_time else 'N/A',
                        'Status Code': result.status_code or 'N/A',
                        'Error Message': result.error_message or 'N/A',
                        'Check Data': result.check_data or 'N/A'
                    })

            logger.info(f"Exported {len(check_results)} check results to {file_path}")
            return True, f"Successfully exported {len(check_results)} check results to {file_path}"

        except Exception as e:
            logger.error(f"Failed to export check results to CSV: {e}", exc_info=True)
            return False, f"Export failed: {str(e)}"

    @staticmethod
    def export_monitoring_report_to_csv(devices: List, stats: Dict, file_path: str) -> tuple[bool, str]:
        """
        Export comprehensive monitoring report to CSV

        Args:
            devices: List of Device objects
            stats: Statistics dictionary
            file_path: Output file path

        Returns:
            (success, message) tuple
        """
        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)

                # Report header
                writer.writerow(['PingMonitor Pro v2.3 - Monitoring Report'])
                writer.writerow(['Generated:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
                writer.writerow([])

                # Overall statistics
                writer.writerow(['=== OVERALL STATISTICS ==='])
                writer.writerow(['Metric', 'Value'])
                writer.writerow(['Total Devices', stats.get('total_devices', len(devices))])
                writer.writerow(['Online Devices', stats.get('online', 0)])
                writer.writerow(['Offline Devices', stats.get('offline', 0)])
                writer.writerow(['Degraded Devices', stats.get('degraded', 0)])
                writer.writerow(['Total Checks', stats.get('total_checks', 0)])
                writer.writerow(['Successful Checks', stats.get('successful_checks', 0)])
                writer.writerow(['Failed Checks', stats.get('failed_checks', 0)])
                writer.writerow(['Average Response Time (ms)', f"{stats.get('average_response_time', 0):.2f}"])
                writer.writerow([])

                # Device details
                writer.writerow(['=== DEVICE DETAILS ==='])
                writer.writerow([
                    'Name', 'IP Address', 'Type', 'Location', 'Status',
                    'Uptime %', 'Response Time (ms)', 'Total Checks',
                    'Successful', 'Failed', 'Last Check'
                ])

                for device in devices:
                    writer.writerow([
                        device.name,
                        device.ip_address,
                        device.device_type,
                        device.location or 'N/A',
                        device.current_status,
                        f"{device.uptime_percentage:.2f}",
                        f"{device.response_time:.2f}",
                        device.total_checks,
                        device.successful_checks,
                        device.failed_checks,
                        device.last_check_time or 'Never'
                    ])

                writer.writerow([])

                # Problematic devices
                writer.writerow(['=== DEVICES REQUIRING ATTENTION ==='])
                problematic = [d for d in devices if d.current_status in ['offline', 'degraded']]

                if problematic:
                    writer.writerow(['Name', 'IP Address', 'Status', 'Last Check', 'Uptime %'])
                    for device in problematic:
                        writer.writerow([
                            device.name,
                            device.ip_address,
                            device.current_status.upper(),
                            device.last_check_time or 'Never',
                            f"{device.uptime_percentage:.2f}"
                        ])
                else:
                    writer.writerow(['All devices operating normally'])

            logger.info(f"Exported monitoring report to {file_path}")
            return True, f"Successfully exported monitoring report to {file_path}"

        except Exception as e:
            logger.error(f"Failed to export monitoring report: {e}", exc_info=True)
            return False, f"Export failed: {str(e)}"

    @staticmethod
    def get_default_export_path(export_type: str) -> Path:
        """
        Get default export path for given export type

        Args:
            export_type: Type of export (devices, checks, report)

        Returns:
            Default Path for export
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"pingmonitor_{export_type}_{timestamp}.csv"

        # Try to use user's Documents folder, fallback to current directory
        try:
            from pathlib import Path
            documents = Path.home() / "Documents" / "PingMonitorPro_Exports"
            documents.mkdir(parents=True, exist_ok=True)
            return documents / filename
        except:
            return Path.cwd() / filename
