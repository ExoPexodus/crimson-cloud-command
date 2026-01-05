
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Float, ForeignKey, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

Base = declarative_base()

class NodeStatus(enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    ERROR = "ERROR"
    OFFLINE = "OFFLINE"

class PoolStatus(enum.Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    ERROR = "error"

class UserRole(enum.Enum):
    USER = "USER"
    DEVOPS = "DEVOPS"
    ADMIN = "ADMIN"

class AuthProvider(enum.Enum):
    LOCAL = "local"
    KEYCLOAK = "keycloak"

class Node(Base):
    __tablename__ = "nodes"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    region = Column(String(100), nullable=False)
    ip_address = Column(String(45), nullable=True)
    description = Column(Text, nullable=True)
    status = Column(SQLEnum(NodeStatus), default=NodeStatus.INACTIVE)
    api_key_hash = Column(String(64), nullable=True, unique=True)
    last_heartbeat = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    pools = relationship("Pool", back_populates="node")
    metrics = relationship("Metric", back_populates="node")
    schedules = relationship("Schedule", back_populates="node")
    configurations = relationship("NodeConfiguration", back_populates="node")
    heartbeats = relationship("NodeHeartbeat", back_populates="node")

class Pool(Base):
    __tablename__ = "pools"
    
    id = Column(Integer, primary_key=True, index=True)
    node_id = Column(Integer, ForeignKey("nodes.id"), nullable=False)
    oracle_pool_id = Column(String(255), nullable=False, unique=True)
    name = Column(String(255), nullable=False)
    region = Column(String(100), nullable=False)
    min_instances = Column(Integer, default=1)
    max_instances = Column(Integer, default=10)
    current_instances = Column(Integer, default=1)
    status = Column(SQLEnum(PoolStatus), default=PoolStatus.HEALTHY)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    node = relationship("Node", back_populates="pools")
    metrics = relationship("Metric", back_populates="pool")
    analytics = relationship("PoolAnalytics", back_populates="pool")

class Metric(Base):
    __tablename__ = "metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    node_id = Column(Integer, ForeignKey("nodes.id"), nullable=False)
    pool_id = Column(Integer, ForeignKey("pools.id"), nullable=True)
    metric_type = Column(String(100), nullable=False)
    value = Column(Float, nullable=False)
    unit = Column(String(50), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    node = relationship("Node", back_populates="metrics")
    pool = relationship("Pool", back_populates="metrics")

class Schedule(Base):
    __tablename__ = "schedules"
    
    id = Column(Integer, primary_key=True, index=True)
    node_id = Column(Integer, ForeignKey("nodes.id"), nullable=False)
    name = Column(String(255), nullable=False)
    start_time = Column(String(5), nullable=False)  # HH:MM format
    end_time = Column(String(5), nullable=False)    # HH:MM format
    target_instances = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    node = relationship("Node", back_populates="schedules")

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=True)  # Nullable for Keycloak users
    full_name = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.USER)
    auth_provider = Column(SQLEnum(AuthProvider), default=AuthProvider.LOCAL)
    keycloak_user_id = Column(String(255), nullable=True, unique=True, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class AuditLog(Base):
    """Enterprise audit log for tracking all user and system actions"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    user_email = Column(String(255), nullable=True)
    user_role = Column(String(50), nullable=True)
    action = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False)  # AUTH, NODE, POOL, USER, CONFIG, SYSTEM
    resource_type = Column(String(100), nullable=True)
    resource_id = Column(String(255), nullable=True)
    resource_name = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    details = Column(Text, nullable=True)  # JSON data
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    status = Column(String(20), default="SUCCESS")  # SUCCESS, FAILURE
    error_message = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

class NodeConfiguration(Base):
    __tablename__ = "node_configurations"
    
    id = Column(Integer, primary_key=True, index=True)
    node_id = Column(Integer, ForeignKey("nodes.id"), nullable=False)
    yaml_config = Column(Text, nullable=False)
    config_hash = Column(String(64), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    node = relationship("Node", back_populates="configurations")

class NodeHeartbeat(Base):
    __tablename__ = "node_heartbeats"
    
    id = Column(Integer, primary_key=True, index=True)
    node_id = Column(Integer, ForeignKey("nodes.id"), nullable=False)
    config_hash = Column(String(64), nullable=True)
    status = Column(String(50), nullable=False)
    error_message = Column(Text, nullable=True)
    metrics_data = Column(Text, nullable=True)  # JSON data
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    node = relationship("Node", back_populates="heartbeats")


class NodeLifecycleLog(Base):
    """Audit log for tracking node lifecycle events (online/offline transitions)"""
    __tablename__ = "node_lifecycle_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    node_id = Column(Integer, ForeignKey("nodes.id"), nullable=False)
    event_type = Column(String(50), nullable=False)  # WENT_OFFLINE, CAME_ONLINE
    previous_status = Column(String(50), nullable=True)
    new_status = Column(String(50), nullable=False)
    reason = Column(Text, nullable=True)
    triggered_by = Column(String(100), nullable=True)  # heartbeat, manual, system
    extra_data = Column(Text, nullable=True)  # JSON metadata (renamed from 'metadata' which is reserved)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    node = relationship("Node")

class PoolAnalytics(Base):
    __tablename__ = "pool_analytics"
    
    id = Column(Integer, primary_key=True, index=True)
    pool_id = Column(Integer, ForeignKey("pools.id"), nullable=False)
    node_id = Column(Integer, ForeignKey("nodes.id"), nullable=False)
    oracle_pool_id = Column(String(255), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    current_instances = Column(Integer, nullable=False)
    active_instances = Column(Integer, nullable=False)
    avg_cpu_utilization = Column(Float, nullable=False)
    avg_memory_utilization = Column(Float, nullable=False)
    max_cpu_utilization = Column(Float, nullable=True)
    max_memory_utilization = Column(Float, nullable=True)
    pool_status = Column(String(50), default="healthy")
    is_active = Column(Boolean, default=True)
    scaling_event = Column(String(100), nullable=True)
    scaling_reason = Column(Text, nullable=True)
    
    # Relationships
    pool = relationship("Pool", back_populates="analytics")
    node = relationship("Node")

class SystemAnalytics(Base):
    __tablename__ = "system_analytics"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    total_active_pools = Column(Integer, default=0)
    total_current_instances = Column(Integer, default=0)
    total_active_instances = Column(Integer, default=0)
    avg_system_cpu = Column(Float, default=0.0)
    avg_system_memory = Column(Float, default=0.0)
    max_system_cpu = Column(Float, default=0.0)
    max_system_memory = Column(Float, default=0.0)
    peak_instances_24h = Column(Integer, default=0)
    max_active_pools_24h = Column(Integer, default=0)
    active_nodes = Column(Integer, default=0)
