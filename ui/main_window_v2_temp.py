    def _update_monitoring_table(self):
        """Update monitoring table with professional status indicators"""
        try:
            devices = list(self.monitoring_engine.devices.values())
            self.monitoring_table.setRowCount(len(devices))

            for row, device in enumerate(devices):
                # Status column - Use StatusIndicatorCell with animated dot
                status_cell = StatusIndicatorCell(device.current_status)
                self.monitoring_table.setCellWidget(row, 0, status_cell)

                # IP Address
                self.monitoring_table.setItem(row, 1, QTableWidgetItem(device.ip_address))

                # Name
                self.monitoring_table.setItem(row, 2, QTableWidgetItem(device.name))

                # Device Type - Remove any emoji characters
                device_type = device.device_type
                # Remove common emoji patterns
                emoji_patterns = ['📱', '💻', '🖥', '📟', '⌚', '🔌']
                for emoji in emoji_patterns:
                    device_type = device_type.replace(emoji, '')
                device_type = device_type.strip()
                self.monitoring_table.setItem(row, 3, QTableWidgetItem(device_type))

                # Location
                self.monitoring_table.setItem(row, 4, QTableWidgetItem(device.location or "N/A"))

                # PING Status - Professional colored cells without emoji
                ping_status = getattr(device, 'ping_status', None)
                if ping_status == 'success':
                    ping_item = QTableWidgetItem("OK")
                    ping_item.setForeground(QColor(DesignSystem.COLORS['status-online']))
                    ping_item.setBackground(QColor(DesignSystem.COLORS['status-online-bg']))
                elif ping_status == 'failed':
                    ping_item = QTableWidgetItem("FAIL")
                    ping_item.setForeground(QColor(DesignSystem.COLORS['status-offline']))
                    ping_item.setBackground(QColor(DesignSystem.COLORS['status-offline-bg']))
                else:
                    ping_item = QTableWidgetItem("N/A")
                    ping_item.setForeground(QColor("#6b7280"))
                    ping_item.setBackground(QColor("rgba(100, 116, 139, 0.1)"))
                self.monitoring_table.setItem(row, 5, ping_item)

                # WEB Status - Professional colored cells without emoji
                web_status = getattr(device, 'web_status', None)
                if web_status == 'success':
                    web_item = QTableWidgetItem("OK")
                    web_item.setForeground(QColor(DesignSystem.COLORS['status-online']))
                    web_item.setBackground(QColor(DesignSystem.COLORS['status-online-bg']))
                elif web_status == 'failed':
                    web_item = QTableWidgetItem("FAIL")
                    web_item.setForeground(QColor(DesignSystem.COLORS['status-offline']))
                    web_item.setBackground(QColor(DesignSystem.COLORS['status-offline-bg']))
                else:
                    web_item = QTableWidgetItem("N/A")
                    web_item.setForeground(QColor("#6b7280"))
                    web_item.setBackground(QColor("rgba(100, 116, 139, 0.1)"))
                self.monitoring_table.setItem(row, 6, web_item)

                # Format last check time in Italian format (day/month/year hour:minute:second)
                if device.last_check_time and device.last_check_time != "Never":
                    try:
                        # Parse ISO format timestamp with robust handling
                        from datetime import datetime
                        if isinstance(device.last_check_time, str):
                            # Handle multiple ISO8601 formats:
                            # - "2025-01-17T14:30:45.123456" (microseconds)
                            # - "2025-01-17T14:30:45" (no microseconds)
                            # - "2025-01-17 14:30:45" (space separator)
                            # - "2025-01-17T14:30:45Z" (UTC indicator)
                            # - "2025-01-17T14:30:45+00:00" (timezone)
                            timestamp_str = device.last_check_time.replace('Z', '+00:00').replace(' ', 'T')
                            dt = datetime.fromisoformat(timestamp_str)
                        else:
                            # Already a datetime object
                            dt = device.last_check_time
                        # Format in Italian: day/month/year hour:minute:second
                        last_check = dt.strftime('%d/%m/%Y %H:%M:%S')
                    except (ValueError, AttributeError, TypeError) as e:
                        logger.warning(f"Failed to parse last_check_time for {device.name}: {e} - Value: {device.last_check_time}")
                        last_check = str(device.last_check_time) if device.last_check_time else "Mai"
                else:
                    last_check = "Mai"

                last_check_item = QTableWidgetItem(last_check)
                last_check_item.setForeground(QColor("#94a3b8"))  # Lighter gray for timestamps
                self.monitoring_table.setItem(row, 7, last_check_item)

                # Uptime percentage
                self.monitoring_table.setItem(row, 8, QTableWidgetItem(f"{device.uptime_percentage:.1f}%"))

                # Actions
                self.monitoring_table.setItem(row, 9, QTableWidgetItem("..."))

        except Exception as e:
            logger.error(f"Error updating monitoring table: {e}")
