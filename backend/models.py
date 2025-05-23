
from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import enum

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
    metadata = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    pools = relationship("Pool", back_populates="node")
    metrics = relationship("Metric", back_populates="node")

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
    scale_up_cooldown = Column(Integer, default=300)  # seconds
    scale_down_cooldown = Column(Integer, default=600)  # seconds
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    node = relationship("Node", back_populates="pools")
    schedules = relationship("Schedule", back_populates="pool")

class Metric(Base):
    __tablename__ = "metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    node_id = Column(Integer, ForeignKey("nodes.id"), nullable=False)
    metric_type = Column(String(100), nullable=False)  # cpu, memory, instances, etc.
    metric_source = Column(String(100), nullable=False)  # oci, prometheus
    value = Column(Float, nullable=False)
    unit = Column(String(50))
    pool_id = Column(String(255))  # Oracle pool ID
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
