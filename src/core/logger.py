"""
PingMonitor Pro v2.0 - Logging System
Professional logging with rotation, formatting, and multiple handlers
"""

import sys
import logging
from pathlib import Path
from typing import Optional
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from datetime import datetime
from rich.console import Console
from rich.logging import RichHandler
from rich.theme import Theme


class LogManager:
    """
    Centralized logging manager with multiple handlers
    """

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.console = Console(theme=Theme({
                "info": "cyan",
                "warning": "yellow",
                "error": "red bold",
                "critical": "red bold reverse"
            }))
            self.loggers = {}
            self.__class__._initialized = True

    def setup_logging(
            self,
            log_dir: Optional[Path] = None,
            log_level: str = "INFO",
            max_file_size: int = 10485760,  # 10MB
            backup_count: int = 5,
            console_output: bool = True,
            file_output: bool = True
    ):
        """
        Setup logging configuration

        Args:
            log_dir: Directory for log files
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            max_file_size: Maximum size of log file before rotation
            backup_count: Number of backup files to keep
            console_output: Enable console logging
            file_output: Enable file logging
        """
        if log_dir is None:
            log_dir = Path.home() / ".pingmonitor" / "logs"

        log_dir = Path(log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)

        # Remove existing handlers
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        # Set root logger level
        level = getattr(logging, log_level.upper(), logging.INFO)
        root_logger.setLevel(level)

        # Console handler with Rich
        if console_output:
            console_handler = RichHandler(
                console=self.console,
                show_time=True,
                show_path=True,
                markup=True,
                rich_tracebacks=True,
                tracebacks_show_locals=True
            )
            console_handler.setLevel(level)
            console_formatter = logging.Formatter(
                '%(message)s',
                datefmt='[%X]'
            )
            console_handler.setFormatter(console_formatter)
            root_logger.addHandler(console_handler)

        # File handlers
        if file_output:
            # Main application log with rotation
            app_log_file = log_dir / "pingmonitor.log"
            file_handler = RotatingFileHandler(
                app_log_file,
                maxBytes=max_file_size,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(level)
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            root_logger.addHandler(file_handler)

            # Error log (only errors and critical)
            error_log_file = log_dir / "errors.log"
            error_handler = RotatingFileHandler(
                error_log_file,
                maxBytes=max_file_size,
                backupCount=backup_count,
                encoding='utf-8'
            )
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(file_formatter)
            root_logger.addHandler(error_handler)

            # Daily rotating log
            daily_log_file = log_dir / "daily.log"
            daily_handler = TimedRotatingFileHandler(
                daily_log_file,
                when='midnight',
                interval=1,
                backupCount=30,
                encoding='utf-8'
            )
            daily_handler.setLevel(logging.INFO)
            daily_handler.setFormatter(file_formatter)
            root_logger.addHandler(daily_handler)

            # Monitoring events log (separate from application logs)
            monitoring_log_file = log_dir / "monitoring.log"
            monitoring_handler = RotatingFileHandler(
                monitoring_log_file,
                maxBytes=max_file_size,
                backupCount=backup_count,
                encoding='utf-8'
            )
            monitoring_handler.setLevel(logging.INFO)
            monitoring_formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            monitoring_handler.setFormatter(monitoring_formatter)

            # Create monitoring logger
            monitoring_logger = logging.getLogger('monitoring')
            monitoring_logger.setLevel(logging.INFO)
            monitoring_logger.addHandler(monitoring_handler)
            monitoring_logger.propagate = False

        # Suppress noisy loggers
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        logging.getLogger('paramiko').setLevel(logging.WARNING)
        logging.getLogger('asyncio').setLevel(logging.WARNING)

        logging.info(f"Logging initialized - Level: {log_level}, Directory: {log_dir}")

    def get_logger(self, name: str) -> logging.Logger:
        """
        Get or create a logger with the given name

        Args:
            name: Logger name

        Returns:
            Logger instance
        """
        if name not in self.loggers:
            self.loggers[name] = logging.getLogger(name)

        return self.loggers[name]

    def log_event(self, event_type: str, device: str, message: str, level: str = "INFO"):
        """
        Log a monitoring event

        Args:
            event_type: Type of event (STATUS_CHANGE, CHECK_FAILED, etc.)
            device: Device name or IP
            message: Event message
            level: Log level
        """
        monitoring_logger = logging.getLogger('monitoring')
        log_level = getattr(logging, level.upper(), logging.INFO)

        formatted_message = f"[{event_type}] {device} - {message}"
        monitoring_logger.log(log_level, formatted_message)

    def log_exception(self, exception: Exception, context: str = ""):
        """
        Log an exception with full traceback

        Args:
            exception: Exception to log
            context: Additional context information
        """
        logger = logging.getLogger(__name__)

        if context:
            logger.exception(f"Exception in {context}: {str(exception)}")
        else:
            logger.exception(f"Exception occurred: {str(exception)}")

    def cleanup_old_logs(self, days: int = 30):
        """
        Clean up log files older than specified days

        Args:
            days: Number of days to keep logs
        """
        log_dir = Path.home() / ".pingmonitor" / "logs"

        if not log_dir.exists():
            return

        cutoff_time = datetime.now().timestamp() - (days * 86400)
        cleaned_count = 0

        for log_file in log_dir.glob("*.log*"):
            if log_file.stat().st_mtime < cutoff_time:
                try:
                    log_file.unlink()
                    cleaned_count += 1
                except Exception as e:
                    logging.warning(f"Failed to delete old log file {log_file}: {e}")

        if cleaned_count > 0:
            logging.info(f"Cleaned up {cleaned_count} old log files")

    def get_recent_logs(self, lines: int = 100, log_file: str = "pingmonitor.log") -> list[str]:
        """
        Get recent log entries

        Args:
            lines: Number of lines to retrieve
            log_file: Log file name

        Returns:
            List of recent log lines
        """
        log_path = Path.home() / ".pingmonitor" / "logs" / log_file

        if not log_path.exists():
            return []

        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                return f.readlines()[-lines:]
        except Exception as e:
            logging.error(f"Failed to read log file: {e}")
            return []

    def export_logs(self, output_file: Path, start_date: Optional[datetime] = None,
                    end_date: Optional[datetime] = None):
        """
        Export logs to a file

        Args:
            output_file: Output file path
            start_date: Start date for log export (optional)
            end_date: End date for log export (optional)
        """
        log_dir = Path.home() / ".pingmonitor" / "logs"

        try:
            with open(output_file, 'w', encoding='utf-8') as out:
                out.write(f"PingMonitor Pro - Log Export\n")
                out.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                if start_date:
                    out.write(f"Start Date: {start_date.strftime('%Y-%m-%d %H:%M:%S')}\n")
                if end_date:
                    out.write(f"End Date: {end_date.strftime('%Y-%m-%d %H:%M:%S')}\n")
                out.write("=" * 80 + "\n\n")

                for log_file in sorted(log_dir.glob("*.log")):
                    out.write(f"\n{'=' * 80}\n")
                    out.write(f"File: {log_file.name}\n")
                    out.write(f"{'=' * 80}\n\n")

                    with open(log_file, 'r', encoding='utf-8') as f:
                        for line in f:
                            # Simple date filtering (could be improved)
                            if start_date or end_date:
                                # Parse date from log line and filter
                                # This is a simplified version
                                pass

                            out.write(line)

            logging.info(f"Logs exported to {output_file}")
        except Exception as e:
            logging.error(f"Failed to export logs: {e}")
            raise


# Global instance
log_manager = LogManager()


def get_logger(name: str) -> logging.Logger:
    """Convenience function to get a logger"""
    return log_manager.get_logger(name)
