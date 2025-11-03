"""
PingMonitor Pro v2.0 - Statistics Models
"""

from sqlalchemy import Column, Integer, String, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin


class DeviceStatistics(Base, TimestampMixin):
    """Device statistics model for time-series data"""

    __tablename__ = 'device_statistics'

    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(Integer, ForeignKey('devices.id', ondelete='CASCADE'), nullable=False, index=True)
    timestamp = Column(String(30), nullable=False, index=True)  # ISO format

    # Aggregated metrics (for the time period)
    checks_performed = Column(Integer, default=0)
    checks_successful = Column(Integer, default=0)
    checks_failed = Column(Integer, default=0)

    # Response time statistics
    avg_response_time = Column(Float)
    min_response_time = Column(Float)
    max_response_time = Column(Float)

    # Availability
    uptime_percentage = Column(Float)
    downtime_seconds = Column(Integer)

    # Status distribution (JSON)
    status_distribution = Column(JSON)  # {online: 95, offline: 5, degraded: 0}

    # Relationships
    device = relationship('Device', back_populates='statistics')

    def __repr__(self):
        return f"<DeviceStatistics(device_id={self.device_id}, timestamp='{self.timestamp}', uptime={self.uptime_percentage}%)>"

    def to_dict(self):
        """Convert statistics to dictionary"""
        return {
            'id': self.id,
            'device_id': self.device_id,
            'timestamp': self.timestamp,
            'checks_performed': self.checks_performed,
            'checks_successful': self.checks_successful,
            'checks_failed': self.checks_failed,
            'avg_response_time': self.avg_response_time,
            'min_response_time': self.min_response_time,
            'max_response_time': self.max_response_time,
            'uptime_percentage': self.uptime_percentage,
            'downtime_seconds': self.downtime_seconds
        }


class SystemStatistics(Base, TimestampMixin):
    """System-wide statistics"""

    __tablename__ = 'system_statistics'

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(String(30), nullable=False, index=True)

    # Overall metrics
    total_devices = Column(Integer, default=0)
    online_devices = Column(Integer, default=0)
    offline_devices = Column(Integer, default=0)
    degraded_devices = Column(Integer, default=0)

    # Checks statistics
    total_checks = Column(Integer, default=0)
    successful_checks = Column(Integer, default=0)
    failed_checks = Column(Integer, default=0)

    # Alerts statistics
    total_alerts = Column(Integer, default=0)
    critical_alerts = Column(Integer, default=0)
    resolved_alerts = Column(Integer, default=0)

    # System metrics
    cpu_usage = Column(Float)
    memory_usage = Column(Float)
    disk_usage = Column(Float)

    # Performance metrics
    avg_check_duration = Column(Float)
    max_check_duration = Column(Float)

    def __repr__(self):
        return f"<SystemStatistics(timestamp='{self.timestamp}', devices={self.total_devices})>"

    def to_dict(self):
        """Convert system statistics to dictionary"""
        return {
            'id': self.id,
            'timestamp': self.timestamp,
            'total_devices': self.total_devices,
            'online_devices': self.online_devices,
            'offline_devices': self.offline_devices,
            'degraded_devices': self.degraded_devices,
            'total_checks': self.total_checks,
            'successful_checks': self.successful_checks,
            'failed_checks': self.failed_checks,
            'total_alerts': self.total_alerts,
            'cpu_usage': self.cpu_usage,
            'memory_usage': self.memory_usage
        }
