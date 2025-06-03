from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import enum
from datetime import datetime

class NodeStatus(enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"

class PoolStatus(enum.Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    ERROR = "error"
    INACTIVE = "inactive"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Node(Base):
    __tablename__ = "nodes"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    region = Column(String(100), nullable=False)
    ip_address = Column(String(45), nullable=False)
    port = Column(Integer, default=8080)
    api_key = Column(String(255), nullable=False)
    status = Column(Enum(NodeStatus), default=NodeStatus.ACTIVE)
    last_heartbeat = Column(DateTime(timezone=True))
    version = Column(String(50))
    node_metadata = Column(Text)
    config_hash = Column(String(255))  # For configuration drift detection
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    pools = relationship("Pool", back_populates="node")
    metrics = relationship("Metric", back_populates="node")
    configurations = relationship("NodeConfiguration", back_populates="node")
    heartbeats = relationship("NodeHeartbeat", back_populates="node")
    pool_analytics = relationship("PoolAnalytics", back_populates="node")
    api_keys = relationship("NodeApiKey", back_populates="node")

class NodeApiKey(Base):
    __tablename__ = "node_api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    key = Column(String, unique=True, nullable=False, index=True)
    node_id = Column(Integer, ForeignKey("nodes.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationship
    node = relationship("Node", back_populates="api_keys")

class NodeConfiguration(Base):
    __tablename__ = "node_configurations"
    
    id = Column(Integer, primary_key=True, index=True)
    node_id = Column(Integer, ForeignKey("nodes.id"), nullable=False)
    yaml_config = Column(Text, nullable=False)
    config_hash = Column(String(255), nullable=False)
    version = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    node = relationship("Node", back_populates="configurations")

class NodeHeartbeat(Base):
    __tablename__ = "node_heartbeats"
    
    id = Column(Integer, primary_key=True, index=True)
    node_id = Column(Integer, ForeignKey("nodes.id"), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    config_hash = Column(String(255))
    status = Column(String(50))
    error_message = Column(Text)
    metrics_data = Column(JSON)  # Store pool metrics and analytics data
    
    # Relationships
    node = relationship("Node", back_populates="heartbeats")

class Pool(Base):
    __tablename__ = "pools"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    oracle_pool_id = Column(String(255), nullable=False)
    compartment_id = Column(String(255), nullable=False)
    node_id = Column(Integer, ForeignKey("nodes.id"), nullable=False)
    current_instances = Column(Integer, default=0)
    min_instances = Column(Integer, default=1)
    max_instances = Column(Integer, default=10)
    target_instances = Column(Integer, default=2)
    status = Column(Enum(PoolStatus), default=PoolStatus.HEALTHY)
    cpu_threshold_scale_up = Column(Float, default=80.0)
    cpu_threshold_scale_down = Column(Float, default=30.0)
    memory_threshold_scale_up = Column(Float, default=85.0)
    memory_threshold_scale_down = Column(Float, default=40.0)
    scale_up_cooldown = Column(Integer, default=300)
    scale_down_cooldown = Column(Integer, default=600)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    node = relationship("Node", back_populates="pools")
    schedules = relationship("Schedule", back_populates="pool")
    analytics = relationship("PoolAnalytics", back_populates="pool")

class PoolAnalytics(Base):
    __tablename__ = "pool_analytics"
    
    id = Column(Integer, primary_key=True, index=True)
    pool_id = Column(Integer, ForeignKey("pools.id"), nullable=False)
    node_id = Column(Integer, ForeignKey("nodes.id"), nullable=False)
    oracle_pool_id = Column(String(255), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Instance metrics
    current_instances = Column(Integer, nullable=False)
    active_instances = Column(Integer, nullable=False)
    
    # Performance metrics
    avg_cpu_utilization = Column(Float, nullable=False)
    avg_memory_utilization = Column(Float, nullable=False)
    max_cpu_utilization = Column(Float)
    max_memory_utilization = Column(Float)
    
    # Pool status
    pool_status = Column(String(50), nullable=False)
    is_active = Column(Boolean, default=True)
    
    # Scaling events
    scaling_event = Column(String(50))  # SCALE_UP, SCALE_DOWN, NO_ACTION
    scaling_reason = Column(Text)
    
    # Relationships
    pool = relationship("Pool", back_populates="analytics")
    node = relationship("Node", back_populates="pool_analytics")

class SystemAnalytics(Base):
    __tablename__ = "system_analytics"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # System-wide metrics (calculated from pool analytics)
    total_active_pools = Column(Integer, nullable=False)
    total_current_instances = Column(Integer, nullable=False)
    total_active_instances = Column(Integer, nullable=False)
    
    # Performance aggregates
    avg_system_cpu = Column(Float)
    avg_system_memory = Column(Float)
    max_system_cpu = Column(Float)
    max_system_memory = Column(Float)
    
    # Daily peaks (calculated for 24h periods)
    peak_instances_24h = Column(Integer)
    max_active_pools_24h = Column(Integer)
    
    # Additional metrics
    total_scaling_events = Column(Integer, default=0)
    active_nodes = Column(Integer, default=0)

class Metric(Base):
    __tablename__ = "metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    node_id = Column(Integer, ForeignKey("nodes.id"), nullable=False)
    metric_type = Column(String(100), nullable=False)
    metric_source = Column(String(100), nullable=False)
    value = Column(Float, nullable=False)
    unit = Column(String(50))
    pool_id = Column(String(255))
    region = Column(String(100))
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    node = relationship("Node", back_populates="metrics")

class Schedule(Base):
    __tablename__ = "schedules"
    
    id = Column(Integer, primary_key=True, index=True)
    pool_id = Column(Integer, ForeignKey("pools.id"), nullable=False)
    name = Column(String(255), nullable=False)
    cron_expression = Column(String(100), nullable=False)
    target_instances = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    pool = relationship("Pool", back_populates="schedules")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String(100), nullable=False)
    resource_type = Column(String(100), nullable=False)
    resource_id = Column(String(255))
    details = Column(Text)
    ip_address = Column(String(45))
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User")
