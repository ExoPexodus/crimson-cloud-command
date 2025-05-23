
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from models import NodeStatus, PoolStatus

# User schemas
class UserBase(BaseModel):
    email: EmailStr
    full_name: str

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# Node schemas
class NodeBase(BaseModel):
    name: str
    region: str
    ip_address: str
    port: Optional[int] = 8080
    version: Optional[str] = None
    metadata: Optional[str] = None

class NodeCreate(NodeBase):
    api_key: str

class NodeUpdate(BaseModel):
    name: Optional[str] = None
    region: Optional[str] = None
    ip_address: Optional[str] = None
    port: Optional[int] = None
    status: Optional[NodeStatus] = None
    version: Optional[str] = None
    metadata: Optional[str] = None

class NodeResponse(NodeBase):
    id: int
    status: NodeStatus
    last_heartbeat: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

# Pool schemas
class PoolBase(BaseModel):
    name: str
    oracle_pool_id: str
    compartment_id: str
    min_instances: int = 1
    max_instances: int = 10
    target_instances: int = 2
    cpu_threshold_scale_up: float = 80.0
    cpu_threshold_scale_down: float = 30.0
    memory_threshold_scale_up: float = 85.0
    memory_threshold_scale_down: float = 40.0
    scale_up_cooldown: int = 300
    scale_down_cooldown: int = 600

class PoolCreate(PoolBase):
    node_id: int

class PoolUpdate(BaseModel):
    name: Optional[str] = None
    min_instances: Optional[int] = None
    max_instances: Optional[int] = None
    target_instances: Optional[int] = None
    cpu_threshold_scale_up: Optional[float] = None
    cpu_threshold_scale_down: Optional[float] = None
    memory_threshold_scale_up: Optional[float] = None
    memory_threshold_scale_down: Optional[float] = None
    scale_up_cooldown: Optional[int] = None
    scale_down_cooldown: Optional[int] = None

class PoolResponse(PoolBase):
    id: int
    node_id: int
    current_instances: int
    status: PoolStatus
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

# Metric schemas
class MetricBase(BaseModel):
    metric_type: str
    metric_source: str
    value: float
    unit: Optional[str] = None
    pool_id: Optional[str] = None
    region: Optional[str] = None

class MetricCreate(MetricBase):
    node_id: int

class MetricResponse(MetricBase):
    id: int
    node_id: int
    timestamp: datetime
    
    class Config:
        from_attributes = True

# Schedule schemas
class ScheduleBase(BaseModel):
    name: str
    cron_expression: str
    target_instances: int
    description: Optional[str] = None
    is_active: bool = True

class ScheduleCreate(ScheduleBase):
    pool_id: int

class ScheduleResponse(ScheduleBase):
    id: int
    pool_id: int
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

# Auth schemas
class Token(BaseModel):
    access_token: str
    token_type: str
