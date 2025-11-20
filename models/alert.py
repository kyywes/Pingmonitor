"""
PingMonitor Pro v2.0 - Alert Models
"""

import enum
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin


class AlertChannel(enum.Enum):
    """Alert notification channels"""
    EMAIL = "email"
    TELEGRAM = "telegram"
    DISCORD = "discord"
    SLACK = "slack"
    WEBHOOK = "webhook"
    SMS = "sms"


class Alert(Base, TimestampMixin):
    """Alert model for storing alert history"""

    __tablename__ = 'alerts'

    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(Integer, ForeignKey('devices.id', ondelete='CASCADE'), nullable=False, index=True)

    # Alert information
    alert_type = Column(String(50), nullable=False)  # status_change, threshold_exceeded, etc.
    severity = Column(String(20), nullable=False, index=True)  # info, warning, error, critical
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)

    # Status information
    old_status = Column(String(20))
    new_status = Column(String(20))

    # Notification tracking
    notification_sent = Column(Boolean, default=False)
    notification_channels = Column(String(255))  # Comma-separated list
    notification_time = Column(String(30))  # ISO format
    notification_success = Column(Boolean)
    notification_error = Column(Text)

    # Alert resolved
    resolved = Column(Boolean, default=False)
    resolved_time = Column(String(30))
    resolved_by = Column(String(100))

    # Relationships
    device = relationship('Device', back_populates='alerts')

    def __repr__(self):
        return f"<Alert(id={self.id}, device_id={self.device_id}, type='{self.alert_type}', severity='{self.severity}')>"

    def to_dict(self):
        """Convert alert to dictionary"""
        return {
            'id': self.id,
            'device_id': self.device_id,
            'alert_type': self.alert_type,
            'severity': self.severity,
            'title': self.title,
            'message': self.message,
            'old_status': self.old_status,
            'new_status': self.new_status,
            'notification_sent': self.notification_sent,
            'resolved': self.resolved,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
