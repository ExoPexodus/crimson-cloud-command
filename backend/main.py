
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
import uvicorn
import traceback
from datetime import datetime, timedelta

from database import SessionLocal, engine, get_db
from models import Base
from schemas import (
    UserCreate, UserResponse, Token, 
    NodeCreate, NodeUpdate, NodeResponse, NodeHeartbeatData, NodeRegister, NodeRegisterResponse,
    PoolCreate, PoolUpdate, PoolResponse,
    MetricCreate, MetricResponse,
    ScheduleCreate, ScheduleResponse,
    SystemAnalyticsResponse
)
from services import (
    AuthService, UserService, NodeService, PoolService, 
    MetricService, ScheduleService, HeartbeatService, 
    AnalyticsService, NodeConfigurationService
)
from auth_middleware import APIKeyAuth

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="OCI Autoscaler API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

# Authentication dependency
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    user = AuthService.verify_token(credentials.credentials, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

# API Key authentication dependency
async def get_api_key_node(request: Request, db: Session = Depends(get_db)):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
        )
    
    api_key = auth_header.replace("Bearer ", "")
    node = APIKeyAuth.verify_api_key(api_key, db)
    if not node:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
    return node

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "OCI Autoscaler API is running"}

# Authentication endpoints
@app.post("/auth/register", response_model=UserResponse)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    try:
        db_user = UserService.create_user(db, user)
        return UserResponse(
            id=db_user.id,
            email=db_user.email,
            full_name=db_user.full_name,
            is_active=db_user.is_active,
            created_at=db_user.created_at
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/auth/login", response_model=Token)
async def login(email: str, password: str, db: Session = Depends(get_db)):
    user = AuthService.authenticate_user(db, email, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = AuthService.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

# Node endpoints
@app.get("/nodes", response_model=List[NodeResponse])
async def get_nodes(current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    return NodeService.get_nodes(db)

@app.post("/nodes/register", response_model=NodeRegisterResponse)
async def register_node(node: NodeRegister, current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        return NodeService.register_node(db, node)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/nodes/{node_id}")
async def delete_node(node_id: int, current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    success = NodeService.delete_node(db, node_id)
    if not success:
        raise HTTPException(status_code=404, detail="Node not found")
    return {"message": "Node deleted successfully"}

# Node configuration endpoints
@app.get("/nodes/{node_id}/config")
async def get_node_config(node_id: int, current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    config = NodeConfigurationService.get_node_config(db, node_id)
    if not config:
        return {"yaml_config": "{}"}
    return {"yaml_config": config.yaml_config}

@app.put("/nodes/{node_id}/config")
async def update_node_config(node_id: int, config_data: dict, current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    yaml_config = config_data.get("yaml_config", "{}")
    try:
        config = NodeConfigurationService.update_node_config(db, node_id, yaml_config)
        return {"message": "Configuration updated successfully", "config_hash": config.config_hash}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Node analytics endpoint
@app.get("/nodes/{node_id}/analytics")
async def get_node_analytics(node_id: int, current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        # Get the latest pool analytics for this node
        result = db.execute(text("""
            SELECT 
                AVG(avg_cpu_utilization) as avg_cpu_utilization,
                AVG(avg_memory_utilization) as avg_memory_utilization,
                AVG(current_instances) as current_instances,
                AVG(active_instances) as active_instances,
                MAX(current_instances) as max_instances,
                oracle_pool_id
            FROM pool_analytics 
            WHERE node_id = :node_id 
            AND timestamp >= NOW() - INTERVAL '5 minutes'
            GROUP BY oracle_pool_id
            ORDER BY timestamp DESC
            LIMIT 1
        """), {"node_id": node_id})
        
        row = result.fetchone()
        if not row:
            return {
                "avg_cpu_utilization": 0,
                "avg_memory_utilization": 0,
                "current_instances": 0,
                "active_instances": 0,
                "max_instances": 0,
                "oracle_pool_id": ""
            }
        
        return {
            "avg_cpu_utilization": float(row[0]) if row[0] else 0,
            "avg_memory_utilization": float(row[1]) if row[1] else 0,
            "current_instances": int(row[2]) if row[2] else 0,
            "active_instances": int(row[3]) if row[3] else 0,
            "max_instances": int(row[4]) if row[4] else 0,
            "oracle_pool_id": row[5] if row[5] else ""
        }
    except Exception as e:
        print(f"Error getting node analytics: {e}")
        return {
            "avg_cpu_utilization": 0,
            "avg_memory_utilization": 0,
            "current_instances": 0,
            "active_instances": 0,
            "max_instances": 0,
            "oracle_pool_id": ""
        }

# API Key authenticated endpoints for nodes
@app.post("/nodes/{node_id}/config/push")
async def push_node_config(node_id: int, config_data: dict, node = Depends(get_api_key_node), db: Session = Depends(get_db)):
    if node.id != node_id:
        raise HTTPException(status_code=403, detail="Node ID mismatch")
    
    yaml_config = config_data.get("yaml_config", "{}")
    try:
        config = NodeConfigurationService.update_node_config(db, node_id, yaml_config)
        return {"message": "Configuration pushed successfully", "config_hash": config.config_hash}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/nodes/{node_id}/heartbeat")
async def node_heartbeat(node_id: int, heartbeat_data: NodeHeartbeatData, node = Depends(get_api_key_node), db: Session = Depends(get_db)):
    if node.id != node_id:
        raise HTTPException(status_code=403, detail="Node ID mismatch")
    
    try:
        response = HeartbeatService.process_heartbeat(db, node_id, heartbeat_data)
        return response
    except Exception as e:
        print(f"Heartbeat processing error: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Analytics endpoints
@app.get("/analytics/system", response_model=SystemAnalyticsResponse)
async def get_system_analytics(current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    return AnalyticsService.get_system_analytics(db)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
