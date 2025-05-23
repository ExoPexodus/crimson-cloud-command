
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List, Optional
import uvicorn

from database import engine, get_db
from models import Base
from schemas import (
    NodeCreate, NodeResponse, NodeUpdate,
    PoolCreate, PoolResponse, PoolUpdate,
    MetricCreate, MetricResponse,
    ScheduleCreate, ScheduleResponse,
    UserCreate, UserResponse,
    Token
)
from services import (
    NodeService, PoolService, MetricService, 
    ScheduleService, UserService, AuthService
)

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Oracle Cloud Autoscaling Management API",
    description="Central management system for Oracle Cloud instance pool autoscaling",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

# Dependency to get current user
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    return AuthService.verify_token(credentials.credentials, db)

# Authentication endpoints
@app.post("/auth/register", response_model=UserResponse)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    return UserService.create_user(db, user)

@app.post("/auth/login", response_model=Token)
async def login(email: str, password: str, db: Session = Depends(get_db)):
    user = AuthService.authenticate_user(db, email, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    access_token = AuthService.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

# Node management endpoints
@app.get("/nodes", response_model=List[NodeResponse])
async def get_nodes(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    return NodeService.get_nodes(db)

@app.post("/nodes", response_model=NodeResponse)
async def create_node(node: NodeCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    return NodeService.create_node(db, node)

@app.get("/nodes/{node_id}", response_model=NodeResponse)
async def get_node(node_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    node = NodeService.get_node(db, node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    return node

@app.put("/nodes/{node_id}", response_model=NodeResponse)
async def update_node(node_id: int, node: NodeUpdate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    return NodeService.update_node(db, node_id, node)

@app.delete("/nodes/{node_id}")
async def delete_node(node_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    return NodeService.delete_node(db, node_id)

# Pool management endpoints
@app.get("/pools", response_model=List[PoolResponse])
async def get_pools(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    return PoolService.get_pools(db)

@app.post("/pools", response_model=PoolResponse)
async def create_pool(pool: PoolCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    return PoolService.create_pool(db, pool)

@app.get("/pools/{pool_id}", response_model=PoolResponse)
async def get_pool(pool_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    pool = PoolService.get_pool(db, pool_id)
    if not pool:
        raise HTTPException(status_code=404, detail="Pool not found")
    return pool

@app.put("/pools/{pool_id}", response_model=PoolResponse)
async def update_pool(pool_id: int, pool: PoolUpdate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    return PoolService.update_pool(db, pool_id, pool)

@app.delete("/pools/{pool_id}")
async def delete_pool(pool_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    return PoolService.delete_pool(db, pool_id)

# Metrics endpoints
@app.get("/metrics", response_model=List[MetricResponse])
async def get_metrics(node_id: Optional[int] = None, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    return MetricService.get_metrics(db, node_id)

@app.post("/metrics", response_model=MetricResponse)
async def create_metric(metric: MetricCreate, db: Session = Depends(get_db)):
    # This endpoint doesn't require authentication as it's used by nodes
    return MetricService.create_metric(db, metric)

# Schedule endpoints
@app.get("/schedules", response_model=List[ScheduleResponse])
async def get_schedules(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    return ScheduleService.get_schedules(db)

@app.post("/schedules", response_model=ScheduleResponse)
async def create_schedule(schedule: ScheduleCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    return ScheduleService.create_schedule(db, schedule)

@app.put("/schedules/{schedule_id}", response_model=ScheduleResponse)
async def update_schedule(schedule_id: int, schedule: ScheduleCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    return ScheduleService.update_schedule(db, schedule_id, schedule)

@app.delete("/schedules/{schedule_id}")
async def delete_schedule(schedule_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    return ScheduleService.delete_schedule(db, schedule_id)

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "Oracle Cloud Autoscaling Management API is running"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
