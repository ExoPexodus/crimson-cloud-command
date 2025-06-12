
from fastapi import FastAPI, Depends, HTTPException, status, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List, Optional
import uvicorn
import logging

from database import engine, get_db, SessionLocal
import models
from models import Base
from schemas import (
    NodeCreate, NodeResponse, NodeUpdate, NodeConfigurationCreate, NodeConfigurationResponse,
    PoolCreate, PoolResponse, PoolUpdate,
    MetricCreate, MetricResponse,
    ScheduleCreate, ScheduleResponse,
    UserCreate, UserResponse,
    Token, NodeHeartbeatData, HeartbeatResponse,
    SystemAnalyticsResponse, PoolAnalyticsResponse,
    NodeRegister, NodeRegisterResponse
)
from services import (
    NodeService, PoolService, MetricService, 
    ScheduleService, UserService, AuthService,
    NodeConfigurationService, HeartbeatService, AnalyticsService
)
from auth_middleware import get_node_from_api_key
from seed_data import create_default_admin
from migration_manager import initialize_database

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Oracle Cloud Autoscaling Management API",
    description="Central management system for Oracle Cloud instance pool autoscaling",
    version="1.0.0"
)

# CORS middleware - must be added before other middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Initialize database and run migrations with reset if needed
logger.info("Initializing database...")
try:
    if initialize_database(reset_if_needed=True):
        logger.info("Database initialization completed successfully")
        
        # Seed initial data
        logger.info("Running database seeding...")
        db = SessionLocal()
        try:
            create_default_admin(db)
            logger.info("Database seeding completed")
        except Exception as e:
            logger.error(f"Database seeding failed: {str(e)}")
        finally:
            db.close()
    else:
        logger.error("Database initialization failed")
except Exception as e:
    logger.error(f"Database initialization error: {str(e)}")

security = HTTPBearer()

# Dependency to get current user
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    return AuthService.verify_token(credentials.credentials, db)

# Health check - no auth required
@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "Oracle Cloud Autoscaling Management API is running"}

# Authentication endpoints
@app.post("/auth/register", response_model=UserResponse)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    try:
        return UserService.create_user(db, user)
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@app.post("/auth/login", response_model=Token)
async def login(email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    try:
        user = AuthService.authenticate_user(db, email, password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        access_token = AuthService.create_access_token(data={"sub": user.email})
        return {"access_token": access_token, "token_type": "bearer"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

# Node registration endpoint (for autoscaling nodes)
@app.post("/nodes/register", response_model=NodeRegisterResponse)
async def register_node(node: NodeRegister, db: Session = Depends(get_db)):
    """Register a new autoscaling node and generate API key"""
    try:
        return NodeService.register_node(db, node)
    except Exception as e:
        logger.error(f"Node registration error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Node registration failed: {str(e)}")

# Node management endpoints
@app.get("/nodes", response_model=List[NodeResponse])
async def get_nodes(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    try:
        return NodeService.get_nodes(db)
    except Exception as e:
        logger.error(f"Get nodes error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get nodes: {str(e)}")

@app.post("/nodes", response_model=NodeResponse)
async def create_node(node: NodeCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    try:
        return NodeService.create_node(db, node)
    except Exception as e:
        logger.error(f"Create node error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create node: {str(e)}")

@app.get("/nodes/{node_id}", response_model=NodeResponse)
async def get_node(node_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    try:
        node = NodeService.get_node(db, node_id)
        if not node:
            raise HTTPException(status_code=404, detail="Node not found")
        return node
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get node error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get node: {str(e)}")

@app.put("/nodes/{node_id}", response_model=NodeResponse)
async def update_node(node_id: int, node: NodeUpdate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    try:
        result = NodeService.update_node(db, node_id, node)
        if not result:
            raise HTTPException(status_code=404, detail="Node not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update node error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update node: {str(e)}")

@app.delete("/nodes/{node_id}")
async def delete_node(node_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    try:
        success = NodeService.delete_node(db, node_id)
        if not success:
            raise HTTPException(status_code=404, detail="Node not found")
        return {"message": "Node deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete node error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete node: {str(e)}")

# Node Configuration endpoints
@app.get("/nodes/{node_id}/config", response_model=NodeConfigurationResponse)
async def get_node_config(node_id: int, db: Session = Depends(get_db)):
    """Get current configuration for a node - used by autoscaling nodes"""
    try:
        # First check if the node exists
        node = NodeService.get_node(db, node_id)
        if not node:
            raise HTTPException(status_code=404, detail="Node not found")
        
        config = NodeConfigurationService.get_node_config(db, node_id)
        if not config:
            # Return a default empty configuration instead of 404
            logger.info(f"No configuration found for node {node_id}, returning empty config")
            return NodeConfigurationResponse(
                id=0,
                node_id=node_id,
                yaml_config="# No configuration set yet\n",
                config_hash="",
                is_active=False,
                created_at="1970-01-01T00:00:00Z",
                updated_at="1970-01-01T00:00:00Z"
            )
        return config
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get node config error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get node config: {str(e)}")

@app.put("/nodes/{node_id}/config", response_model=NodeConfigurationResponse)
async def update_node_config(node_id: int, config: NodeConfigurationCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """Update node configuration - used by central management UI"""
    try:
        return NodeConfigurationService.update_node_config(db, node_id, config.yaml_config)
    except Exception as e:
        logger.error(f"Update node config error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update node config: {str(e)}")

# Heartbeat endpoint for autoscaling nodes (with API key auth)
@app.post("/nodes/{node_id}/heartbeat", response_model=HeartbeatResponse)
async def node_heartbeat(node_id: int, heartbeat_data: NodeHeartbeatData, node: models.Node = Depends(get_node_from_api_key), db: Session = Depends(get_db)):
    """Receive heartbeat from autoscaling nodes with metrics and status"""
    try:
        # Verify the node_id matches the authenticated node
        if node.id != node_id:
            raise HTTPException(status_code=403, detail="Node ID mismatch")
            
        response = HeartbeatService.process_heartbeat(db, node_id, heartbeat_data)
        return HeartbeatResponse(**response)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Heartbeat error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# ... keep existing code (analytics, pools, metrics, schedules endpoints remain unchanged)

# Analytics endpoints
@app.get("/analytics/system", response_model=SystemAnalyticsResponse)
async def get_system_analytics(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """Get system-wide analytics and metrics"""
    try:
        return AnalyticsService.get_system_analytics(db)
    except Exception as e:
        logger.error(f"Get system analytics error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get system analytics: {str(e)}")

@app.get("/analytics/pools", response_model=List[PoolAnalyticsResponse])
async def get_pool_analytics(node_id: Optional[int] = None, hours: int = 24, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """Get pool analytics for the specified time period"""
    try:
        from datetime import datetime, timedelta
        from models import PoolAnalytics
        
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        query = db.query(PoolAnalytics).filter(PoolAnalytics.timestamp >= cutoff_time)
        
        if node_id:
            query = query.filter(PoolAnalytics.node_id == node_id)
        
        return query.order_by(PoolAnalytics.timestamp.desc()).limit(1000).all()
    except Exception as e:
        logger.error(f"Get pool analytics error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get pool analytics: {str(e)}")

# Pool management endpoints
@app.get("/pools", response_model=List[PoolResponse])
async def get_pools(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    try:
        return PoolService.get_pools(db)
    except Exception as e:
        logger.error(f"Get pools error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get pools: {str(e)}")

@app.post("/pools", response_model=PoolResponse)
async def create_pool(pool: PoolCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    try:
        return PoolService.create_pool(db, pool)
    except Exception as e:
        logger.error(f"Create pool error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create pool: {str(e)}")

@app.get("/pools/{pool_id}", response_model=PoolResponse)
async def get_pool(pool_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    try:
        pool = PoolService.get_pool(db, pool_id)
        if not pool:
            raise HTTPException(status_code=404, detail="Pool not found")
        return pool
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get pool error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get pool: {str(e)}")

@app.put("/pools/{pool_id}", response_model=PoolResponse)
async def update_pool(pool_id: int, pool: PoolUpdate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    try:
        result = PoolService.update_pool(db, pool_id, pool)
        if not result:
            raise HTTPException(status_code=404, detail="Pool not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update pool error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update pool: {str(e)}")

@app.delete("/pools/{pool_id}")
async def delete_pool(pool_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    try:
        success = PoolService.delete_pool(db, pool_id)
        if not success:
            raise HTTPException(status_code=404, detail="Pool not found")
        return {"message": "Pool deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete pool error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete pool: {str(e)}")

# Metrics endpoints
@app.get("/metrics", response_model=List[MetricResponse])
async def get_metrics(node_id: Optional[int] = None, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    try:
        return MetricService.get_metrics(db, node_id)
    except Exception as e:
        logger.error(f"Get metrics error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")

@app.post("/metrics", response_model=MetricResponse)
async def create_metric(metric: MetricCreate, db: Session = Depends(get_db)):
    # This endpoint doesn't require authentication as it's used by nodes
    try:
        return MetricService.create_metric(db, metric)
    except Exception as e:
        logger.error(f"Create metric error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create metric: {str(e)}")

# Schedule endpoints
@app.get("/schedules", response_model=List[ScheduleResponse])
async def get_schedules(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    try:
        return ScheduleService.get_schedules(db)
    except Exception as e:
        logger.error(f"Get schedules error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get schedules: {str(e)}")

@app.post("/schedules", response_model=ScheduleResponse)
async def create_schedule(schedule: ScheduleCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    try:
        return ScheduleService.create_schedule(db, schedule)
    except Exception as e:
        logger.error(f"Create schedule error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create schedule: {str(e)}")

@app.put("/schedules/{schedule_id}", response_model=ScheduleResponse)
async def update_schedule(schedule_id: int, schedule: ScheduleCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    try:
        result = ScheduleService.update_schedule(db, schedule_id, schedule)
        if not result:
            raise HTTPException(status_code=404, detail="Schedule not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update schedule error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update schedule: {str(e)}")

@app.delete("/schedules/{schedule_id}")
async def delete_schedule(schedule_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    try:
        success = ScheduleService.delete_schedule(db, schedule_id)
        if not success:
            raise HTTPException(status_code=404, detail="Schedule not found")
        return {"message": "Schedule deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete schedule error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete schedule: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
