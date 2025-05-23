
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
import os

from models import Node, Pool, Metric, Schedule, User, AuditLog
from schemas import (
    NodeCreate, NodeUpdate, PoolCreate, PoolUpdate, 
    MetricCreate, ScheduleCreate, UserCreate
)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

class AuthService:
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        return pwd_context.hash(password)
    
    @staticmethod
    def create_access_token(data: dict):
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str, db: Session):
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            email: str = payload.get("sub")
            if email is None:
                return None
            user = db.query(User).filter(User.email == email).first()
            return user
        except JWTError:
            return None
    
    @staticmethod
    def authenticate_user(db: Session, email: str, password: str):
        user = db.query(User).filter(User.email == email).first()
        if not user or not AuthService.verify_password(password, user.hashed_password):
            return None
        return user

class UserService:
    @staticmethod
    def create_user(db: Session, user: UserCreate):
        hashed_password = AuthService.get_password_hash(user.password)
        db_user = User(
            email=user.email,
            hashed_password=hashed_password,
            full_name=user.full_name
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

class NodeService:
    @staticmethod
    def get_nodes(db: Session) -> List[Node]:
        return db.query(Node).all()
    
    @staticmethod
    def get_node(db: Session, node_id: int) -> Optional[Node]:
        return db.query(Node).filter(Node.id == node_id).first()
    
    @staticmethod
    def create_node(db: Session, node: NodeCreate) -> Node:
        db_node = Node(**node.dict())
        db.add(db_node)
        db.commit()
        db.refresh(db_node)
        return db_node
    
    @staticmethod
    def update_node(db: Session, node_id: int, node: NodeUpdate) -> Optional[Node]:
        db_node = db.query(Node).filter(Node.id == node_id).first()
        if db_node:
            update_data = node.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(db_node, field, value)
            db.commit()
            db.refresh(db_node)
        return db_node
    
    @staticmethod
    def delete_node(db: Session, node_id: int) -> bool:
        db_node = db.query(Node).filter(Node.id == node_id).first()
        if db_node:
            db.delete(db_node)
            db.commit()
            return True
        return False

class PoolService:
    @staticmethod
    def get_pools(db: Session) -> List[Pool]:
        return db.query(Pool).all()
    
    @staticmethod
    def get_pool(db: Session, pool_id: int) -> Optional[Pool]:
        return db.query(Pool).filter(Pool.id == pool_id).first()
    
    @staticmethod
    def create_pool(db: Session, pool: PoolCreate) -> Pool:
        db_pool = Pool(**pool.dict())
        db.add(db_pool)
        db.commit()
        db.refresh(db_pool)
        return db_pool
    
    @staticmethod
    def update_pool(db: Session, pool_id: int, pool: PoolUpdate) -> Optional[Pool]:
        db_pool = db.query(Pool).filter(Pool.id == pool_id).first()
        if db_pool:
            update_data = pool.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(db_pool, field, value)
            db.commit()
            db.refresh(db_pool)
        return db_pool
    
    @staticmethod
    def delete_pool(db: Session, pool_id: int) -> bool:
        db_pool = db.query(Pool).filter(Pool.id == pool_id).first()
        if db_pool:
            db.delete(db_pool)
            db.commit()
            return True
        return False

class MetricService:
    @staticmethod
    def get_metrics(db: Session, node_id: Optional[int] = None) -> List[Metric]:
        query = db.query(Metric)
        if node_id:
            query = query.filter(Metric.node_id == node_id)
        return query.order_by(desc(Metric.timestamp)).limit(1000).all()
    
    @staticmethod
    def create_metric(db: Session, metric: MetricCreate) -> Metric:
        db_metric = Metric(**metric.dict())
        db.add(db_metric)
        db.commit()
        db.refresh(db_metric)
        return db_metric

class ScheduleService:
    @staticmethod
    def get_schedules(db: Session) -> List[Schedule]:
        return db.query(Schedule).all()
    
    @staticmethod
    def create_schedule(db: Session, schedule: ScheduleCreate) -> Schedule:
        db_schedule = Schedule(**schedule.dict())
        db.add(db_schedule)
        db.commit()
        db.refresh(db_schedule)
        return db_schedule
    
    @staticmethod
    def update_schedule(db: Session, schedule_id: int, schedule: ScheduleCreate) -> Optional[Schedule]:
        db_schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
        if db_schedule:
            update_data = schedule.dict()
            for field, value in update_data.items():
                setattr(db_schedule, field, value)
            db.commit()
            db.refresh(db_schedule)
        return db_schedule
    
    @staticmethod
    def delete_schedule(db: Session, schedule_id: int) -> bool:
        db_schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
        if db_schedule:
            db.delete(db_schedule)
            db.commit()
            return True
        return False
