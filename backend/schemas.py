from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class NodeStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"

class PoolStatus(str, Enum):
    HEALTHY = "healthy"
    WARNING = "warning" 
    ERROR = "error"

class UserRole(str, Enum):
    USER = "user"
    DEVOPS = "devops"
    ADMIN = "admin"

class AuthProvider(str, Enum):
    LOCAL = "local"
    KEYCLOAK = "keycloak"

# Node schemas
class NodeCreate(BaseModel):
    name: str
    region: str
    ip_address: Optional[str] = None
    description: Optional[str] = None

class NodeRegister(BaseModel):
    name: str
    region: str
    ip_address: Optional[str] = None
    description: Optional[str] = None

class NodeRegisterResponse(BaseModel):
    node_id: int
    api_key: str
    name: str
    region: str
    
class NodeUpdate(BaseModel):
    name: Optional[str] = None
    region: Optional[str] = None
    ip_address: Optional[str] = None
    description: Optional[str] = None
    status: Optional[NodeStatus] = None

class NodeResponse(BaseModel):
    id: int
    name: str
    region: str
    ip_address: Optional[str]
    description: Optional[str]
    status: NodeStatus
    last_heartbeat: Optional[datetime]
    created_at: datetime
    has_api_key: bool = False

    class Config:
        from_attributes = True

# Node Configuration schemas
class NodeConfigurationCreate(BaseModel):
    yaml_config: str

class NodeConfigurationResponse(BaseModel):
    id: int
    node_id: int
    yaml_config: str
    config_hash: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

# Pool schemas
class PoolCreate(BaseModel):
    node_id: int
    oracle_pool_id: str
    name: str
    region: str
    min_instances: int = 1
    max_instances: int = 10
    current_instances: int = 1

class PoolUpdate(BaseModel):
    name: Optional[str] = None
    min_instances: Optional[int] = None
    max_instances: Optional[int] = None
    current_instances: Optional[int] = None

class PoolResponse(BaseModel):
    id: int
    node_id: int
    oracle_pool_id: str
    name: str
    region: str
    min_instances: int
    max_instances: int
    current_instances: int
    status: PoolStatus
    created_at: datetime

    class Config:
        from_attributes = True

# Metrics schemas
class MetricCreate(BaseModel):
    node_id: int
    pool_id: Optional[int] = None
    metric_type: str
    value: float
    unit: str

class MetricResponse(BaseModel):
    id: int
    node_id: int
    pool_id: Optional[int]
    metric_type: str
    value: float
    unit: str
    timestamp: datetime

    class Config:
        from_attributes = True

# Schedule schemas
class ScheduleCreate(BaseModel):
    node_id: int
    name: str
    start_time: str
    end_time: str
    target_instances: int
    is_active: bool = True

class ScheduleResponse(BaseModel):
    id: int
    node_id: int
    name: str
    start_time: str
    end_time: str
    target_instances: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

# User schemas
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: UserRole
    auth_provider: AuthProvider
    keycloak_user_id: Optional[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class UserUpdateRole(BaseModel):
    role: UserRole

class UserListResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: UserRole
    auth_provider: AuthProvider
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

# Auth schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class KeycloakLoginRequest(BaseModel):
    code: str
    redirect_uri: str

class AuthResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

# Heartbeat schemas
class PoolAnalyticsData(BaseModel):
    pool_id: Optional[int] = None  # Make this optional since nodes only know oracle_pool_id
    oracle_pool_id: str
    current_instances: int
    active_instances: int
    avg_cpu_utilization: float
    avg_memory_utilization: float
    max_cpu_utilization: Optional[float] = None
    max_memory_utilization: Optional[float] = None
    pool_status: str
    is_active: bool = True
    scaling_event: Optional[str] = None
    scaling_reason: Optional[str] = None

class NodeHeartbeatData(BaseModel):
    status: str
    config_hash: Optional[str] = None
    error_message: Optional[str] = None
    pool_analytics: Optional[List[PoolAnalyticsData]] = None
    metrics_data: Optional[Dict[str, Any]] = None

class HeartbeatResponse(BaseModel):
    status: str
    config_update_needed: bool
    current_config_hash: Optional[str] = None
    new_config: Optional[str] = None

# Analytics schemas
class SystemAnalyticsResponse(BaseModel):
    total_active_pools: int  # Active pools in last 24h
    total_current_instances: int  # Currently running instances
    peak_instances_24h: int  # Peak instances in last 24h
    max_active_pools_24h: int  # Max pools at any point today
    avg_system_cpu: float  # Average CPU across all active pools
    avg_system_memory: float  # Average memory across all active pools
    active_nodes: int  # Nodes with recent heartbeats
    last_updated: datetime  # Timestamp of this analytics snapshot

class PoolAnalyticsResponse(BaseModel):
    id: int
    pool_id: int
    node_id: int
    oracle_pool_id: str
    timestamp: datetime
    current_instances: int
    active_instances: int
    avg_cpu_utilization: float
    avg_memory_utilization: float
    max_cpu_utilization: Optional[float]
    max_memory_utilization: Optional[float]
    pool_status: str
    is_active: bool
    scaling_event: Optional[str]
    scaling_reason: Optional[str]

    class Config:
        from_attributes = True
