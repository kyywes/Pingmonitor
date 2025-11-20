"""
PingMonitor Pro v2.0 - Check Result Models
"""

import enum
from sqlalchemy import Column, Integer, String, Boolean, Float, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin


class CheckType(enum.Enum):
    """Types of checks"""
    PING = "ping"
    HTTP = "http"
    HTTPS = "https"
    SSH = "ssh"
    DNS = "dns"
    SNMP = "snmp"
    TCP = "tcp"
    UDP = "udp"


class CheckResult(Base, TimestampMixin):
    """Check result model for storing monitoring check results"""

    __tablename__ = 'check_results'

    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(Integer, ForeignKey('devices.id', ondelete='CASCADE'), nullable=False, index=True)

    # Check information
    check_type = Column(Enum(CheckType), nullable=False)
    check_time = Column(String(30), nullable=False, index=True)  # ISO format
    success = Column(Boolean, nullable=False, index=True)

    # Response metrics
    response_time = Column(Float)  # milliseconds
    status_code = Column(Integer)  # For HTTP checks
    response_size = Column(Integer)  # bytes

    # Error information
    error_message = Column(Text)
    error_type = Column(String(100))

    # Additional data (JSON serialized)
    check_data = Column(Text)  # JSON string with additional check-specific data

    # Relationships
    device = relationship('Device', back_populates='check_results')

    def __repr__(self):
        return f"<CheckResult(id={self.id}, device_id={self.device_id}, type={self.check_type.value}, success={self.success})>"

    def to_dict(self):
        """Convert check result to dictionary"""
        return {
            'id': self.id,
            'device_id': self.device_id,
            'check_type': self.check_type.value if self.check_type else None,
            'check_time': self.check_time,
            'success': self.success,
            'response_time': self.response_time,
            'status_code': self.status_code,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
