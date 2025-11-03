"""
PingMonitor Pro v2.0 - Device Models
"""

from sqlalchemy import Column, Integer, String, Boolean, Float, ForeignKey, Table, JSON
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin


# Association table for many-to-many relationship between devices and groups
device_groups_association = Table(
    'device_groups_association',
    Base.metadata,
    Column('device_id', Integer, ForeignKey('devices.id', ondelete='CASCADE')),
    Column('group_id', Integer, ForeignKey('device_groups.id', ondelete='CASCADE'))
)


class Device(Base, TimestampMixin):
    """Device model for monitored devices"""

    __tablename__ = 'devices'

    id = Column(Integer, primary_key=True, autoincrement=True)
    ip_address = Column(String(45), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(String(500))
    device_type = Column(String(50), default='generic')  # router, switch, server, etc.

    # Monitoring configuration
    enabled = Column(Boolean, default=True, nullable=False)
    check_interval = Column(Integer, default=60)  # seconds
    timeout = Column(Integer, default=5)  # seconds
    retry_attempts = Column(Integer, default=3)

    # Check types enabled
    ping_enabled = Column(Boolean, default=True)
    http_enabled = Column(Boolean, default=False)
    https_enabled = Column(Boolean, default=False)
    ssh_enabled = Column(Boolean, default=False)
    dns_enabled = Column(Boolean, default=False)
    snmp_enabled = Column(Boolean, default=False)

    # Service ports
    http_port = Column(Integer, default=80)
    https_port = Column(Integer, default=443)
    ssh_port = Column(Integer, default=22)
    snmp_port = Column(Integer, default=161)

    # HTTP(S) check configuration
    http_path = Column(String(500), default='/')
    http_method = Column(String(10), default='GET')
    http_expected_status = Column(Integer, default=200)
    http_check_ssl = Column(Boolean, default=True)

    # SSH configuration
    ssh_username = Column(String(100))
    ssh_auth_method = Column(String(20), default='password')  # password, key

    # SNMP configuration
    snmp_community = Column(String(100), default='public')
    snmp_version = Column(String(5), default='2c')  # 1, 2c, 3

    # Location and metadata
    location = Column(String(255))
    tags = Column(JSON)  # List of tags
    custom_fields = Column(JSON)  # Custom key-value pairs

    # Current status
    current_status = Column(String(20), default='unknown')  # online, offline, degraded, unknown
    last_check_time = Column(String(30))  # ISO format timestamp
    last_status_change = Column(String(30))
    response_time = Column(Float, default=0.0)  # milliseconds

    # Statistics
    total_checks = Column(Integer, default=0)
    successful_checks = Column(Integer, default=0)
    failed_checks = Column(Integer, default=0)
    uptime_percentage = Column(Float, default=100.0)

    # Alert configuration
    alert_enabled = Column(Boolean, default=True)
    alert_on_down = Column(Boolean, default=True)
    alert_on_up = Column(Boolean, default=True)
    alert_on_degraded = Column(Boolean, default=True)

    # Thresholds
    degraded_threshold = Column(Integer, default=200)  # Response time in ms
    down_threshold = Column(Integer, default=3)  # Consecutive failures

    # Auto-recovery
    recovery_enabled = Column(Boolean, default=False)
    recovery_command = Column(String(500))
    recovery_max_attempts = Column(Integer, default=3)

    # Relationships
    groups = relationship('DeviceGroup', secondary=device_groups_association, back_populates='devices')
    check_results = relationship('CheckResult', back_populates='device', cascade='all, delete-orphan')
    alerts = relationship('Alert', back_populates='device', cascade='all, delete-orphan')
    statistics = relationship('DeviceStatistics', back_populates='device', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Device(id={self.id}, ip='{self.ip_address}', name='{self.name}', status='{self.current_status}')>"

    def to_dict(self):
        """Convert device to dictionary"""
        return {
            'id': self.id,
            'ip_address': self.ip_address,
            'name': self.name,
            'description': self.description,
            'device_type': self.device_type,
            'enabled': self.enabled,
            'current_status': self.current_status,
            'response_time': self.response_time,
            'uptime_percentage': self.uptime_percentage,
            'location': self.location,
            'tags': self.tags,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class DeviceGroup(Base, TimestampMixin):
    """Device group model for organizing devices"""

    __tablename__ = 'device_groups'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True, nullable=False)
    description = Column(String(500))
    color = Column(String(7), default='#2563eb')  # Hex color code
    icon = Column(String(50))

    # Group configuration
    enabled = Column(Boolean, default=True)
    inherit_settings = Column(Boolean, default=False)

    # Default settings for devices in this group
    default_check_interval = Column(Integer)
    default_timeout = Column(Integer)

    # Relationships
    devices = relationship('Device', secondary=device_groups_association, back_populates='groups')

    def __repr__(self):
        return f"<DeviceGroup(id={self.id}, name='{self.name}', devices={len(self.devices)})>"

    def to_dict(self):
        """Convert group to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'color': self.color,
            'enabled': self.enabled,
            'device_count': len(self.devices),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
