from fastapi import FastAPI, Depends, HTTPException, status, Form, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import uvicorn
import logging
import os

from database import engine, get_db, SessionLocal
import models
from models import Base
from schemas import (
    NodeCreate, NodeResponse, NodeUpdate, NodeConfigurationCreate, NodeConfigurationResponse,
    PoolCreate, PoolResponse, PoolUpdate,
    MetricCreate, MetricResponse,
    ScheduleCreate, ScheduleResponse,
    UserCreate, UserResponse, UserListResponse, UserUpdateRole, UserProfileUpdate,
    Token, AuthResponse, KeycloakLoginRequest, NodeHeartbeatData, HeartbeatResponse,
    SystemAnalyticsResponse, PoolAnalyticsResponse, NodeLifecycleLogResponse,
    NodeRegister, NodeRegisterResponse, UserRole, AuditLogResponse, AuditLogSummaryResponse
)
from services import (
    NodeService, PoolService, MetricService, 
    ScheduleService, UserService, AuthService,
    NodeConfigurationService, HeartbeatService, AnalyticsService,
    NodeLifecycleService
)
from audit_service import AuditService, AuditAction, AuditCategory
from auth_middleware import get_node_from_api_key
from role_service import RoleService, require_admin, require_devops, require_user
from keycloak_service import keycloak_service
from seed_data import seed_initial_data
from migration_manager import initialize_database

# Configure logging
logging.basicConfig(
    level=logging.DEBUG, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
    ]
)
logger = logging.getLogger(__name__)

# Configure uvicorn logging
logging.getLogger("uvicorn").setLevel(logging.DEBUG)
logging.getLogger("uvicorn.access").setLevel(logging.DEBUG)

app = FastAPI(
    title="Oracle Cloud Autoscaling Management API",
    description="Central management system for Oracle Cloud instance pool autoscaling",
    version="1.0.0"
)

# CORS middleware - must be added before other middleware
cors_origins = os.getenv("CORS_ORIGINS", "*")
if cors_origins == "*":
    allow_origins = ["*"]
else:
    allow_origins = [origin.strip() for origin in cors_origins.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Initialize database and run migrations with reset if needed
logger.info("Initializing database...")
try:
    if initialize_database(force_reset=False):
        logger.info("Database initialization completed successfully")
        
        # Seed initial data
        logger.info("Running database seeding...")
        db = SessionLocal()
        try:
            from seed_data import seed_initial_data
            seed_initial_data(db)
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
    logger.info(f"🔐 get_current_user called")
    logger.info(f"🔑 Token received (first 20 chars): {credentials.credentials[:20]}...")
    
    result = AuthService.verify_token(credentials.credentials, db)
    logger.info(f"✅ Token verification result: {result is not None}")
    if result:
        logger.info(f"👤 User authenticated: {result.email}")
    else:
        logger.warning("❌ Token verification failed - returning None")
    
    return result

# Health check - no auth required
@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "Oracle Cloud Autoscaling Management API is running"}

# Public runtime config - expose non-sensitive settings for frontend
@app.get("/config")
async def public_config():
    try:
        cfg = {
            "keycloak_enabled": bool(os.getenv("KEYCLOAK_SERVER_URL") and os.getenv("KEYCLOAK_REALM") and os.getenv("KEYCLOAK_CLIENT_ID")),
            "keycloak_url": os.getenv("KEYCLOAK_SERVER_URL") or "",
            "keycloak_realm": os.getenv("KEYCLOAK_REALM") or "",
            "keycloak_client_id": os.getenv("KEYCLOAK_CLIENT_ID") or "",
            # Optionally expose API base for the SPA to know backend base
            "api_base_url": os.getenv("VITE_API_BASE_URL") or ""
        }
        logger.info(
            f"Serving public config: enabled={cfg['keycloak_enabled']}, url={cfg['keycloak_url']}, realm={cfg['keycloak_realm']}, client_id_set={'yes' if cfg['keycloak_client_id'] else 'no'}"
        )
        return cfg
    except Exception as e:
        logger.error(f"Failed to serve public config: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to load configuration")

# Authentication endpoints
@app.post("/auth/register", response_model=UserResponse)
async def register(user: UserCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """Register new user (admin only)"""
    try:
        if not RoleService.has_role(current_user, UserRole.ADMIN):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Admin role required."
            )
        logger.info(f"Admin {current_user.email} creating new user: {user.email}")
        new_user = UserService.create_user(db, user)
        
        # Log user creation
        AuditService.log_user_action(
            db, AuditAction.USER_CREATED,
            new_user.id, new_user.email,
            acting_user=current_user,
            description=f"Admin {current_user.email} created user {new_user.email}"
        )
        
        return new_user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@app.post("/auth/login", response_model=AuthResponse)
async def login(email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    try:
        user = AuthService.authenticate_user(db, email, password)
        if not user:
            # Log failed authentication
            AuditService.log_auth_failure(db, email, "Incorrect email or password")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        access_token = AuthService.create_access_token(data={"sub": user.email})
        
        # Log successful authentication
        AuditService.log_auth_success(db, user, AuditAction.LOGIN_SUCCESS)
        
        return {
            "access_token": access_token, 
            "token_type": "bearer",
            "user": user
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

@app.post("/auth/keycloak/login", response_model=AuthResponse)
async def keycloak_login(login_request: KeycloakLoginRequest, db: Session = Depends(get_db)):
    """Login using Keycloak authorization code"""
    import traceback
    try:
        logger.info("=" * 80)
        logger.info("🔐 KEYCLOAK LOGIN ENDPOINT CALLED")
        logger.info("=" * 80)
        logger.info(f"📋 Authorization Code: {login_request.code[:20]}...{login_request.code[-10:] if len(login_request.code) > 30 else login_request.code}")
        logger.info(f"↩️  Redirect URI: {login_request.redirect_uri}")
        logger.info("=" * 80)
        
        if not keycloak_service.is_enabled():
            logger.error("❌ Keycloak service not enabled")
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Keycloak authentication is not configured"
            )
        
        logger.info("🔄 Attempting to exchange code for token...")
        
        # Exchange code for token
        token_data = keycloak_service.exchange_code_for_token(
            login_request.code, 
            login_request.redirect_uri
        )
        
        if not token_data:
            logger.error("❌ Token exchange returned None")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to exchange authorization code"
            )
        
        logger.info("✅ Token exchange successful")
        logger.info("🔄 Validating token...")
        
        # Validate token and get/create user
        keycloak_data = keycloak_service.validate_token(token_data['access_token'])
        if not keycloak_data:
            logger.error("❌ Token validation failed")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Keycloak token"
            )
        
        logger.info("✅ Token validated successfully")
        logger.info(f"👤 User email: {keycloak_data.get('user_info', {}).get('email', 'N/A')}")
        
        user = AuthService.handle_keycloak_user(db, keycloak_data, token_data['access_token'])
        if not user:
            logger.error("❌ Failed to handle Keycloak user")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to authenticate user"
            )
        
        logger.info("✅ User authenticated successfully")
        
        # Create local JWT token
        local_token = AuthService.create_keycloak_jwt(user)
        
        # Get user roles from Keycloak
        user_roles = keycloak_service.get_user_roles(token_data['access_token'])
        
        logger.info("✅ Keycloak login complete")
        logger.info("=" * 80)
        
        # Log successful Keycloak authentication
        AuditService.log_auth_success(
            db, user, 
            AuditAction.KEYCLOAK_LOGIN,
            details={"provider": "keycloak", "roles": user_roles}
        )
        
        return {
            "access_token": local_token,
            "token_type": "bearer", 
            "user": user,
            "keycloak_data": keycloak_data,
            "token_data": token_data,
            "roles": user_roles,
            "groups": keycloak_data.get('groups', [])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("=" * 80)
        logger.error(f"❌ Keycloak login error: {str(e)}")
        logger.error(f"📚 Traceback:\n{traceback.format_exc()}")
        logger.error("=" * 80)
        raise HTTPException(status_code=500, detail=f"Keycloak login failed: {str(e)}")

@app.put("/auth/profile", response_model=UserResponse)
async def update_profile(
    update_data: UserProfileUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update user profile (authenticated users only)"""
    try:
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated"
            )
        
        updated_user = UserService.update_profile(
            db=db,
            user_id=current_user.id,
            full_name=update_data.full_name,
            email=update_data.email,
            current_password=update_data.current_password,
            new_password=update_data.new_password
        )
        
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Log profile update
        changes = []
        if update_data.full_name:
            changes.append("name")
        if update_data.email:
            changes.append("email")
        if update_data.new_password:
            changes.append("password")
        
        AuditService.log_user_action(
            db, AuditAction.PROFILE_UPDATED,
            current_user.id, current_user.email,
            acting_user=current_user,
            description=f"User {current_user.email} updated their profile",
            details={"fields_changed": changes}
        )
        
        logger.info(f"Profile updated for user: {updated_user.email}")
        return updated_user
        
    except ValueError as e:
        logger.warning(f"Profile update validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Profile update error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Profile update failed: {str(e)}")

# Node registration endpoint (for autoscaling nodes)
@app.post("/nodes/register", response_model=NodeRegisterResponse)
async def register_node(node: NodeRegister, db: Session = Depends(get_db)):
    """Register a new autoscaling node and generate API key"""
    try:
        result = NodeService.register_node(db, node)
        
        # Log node registration
        AuditService.log_node_action(
            db, AuditAction.NODE_REGISTERED,
            result.node_id, node.name,
            description=f"Node '{node.name}' registered in region {node.region}",
            details={"region": node.region, "ip_address": node.ip_address},
            triggered_by="system"
        )
        
        return result
    except Exception as e:
        logger.error(f"Node registration error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Node registration failed: {str(e)}")

# Node management endpoints (require devops or admin role)
@app.get("/nodes", response_model=List[NodeResponse])
async def get_nodes(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    try:
        # Check role permissions
        if not RoleService.has_role(current_user, UserRole.DEVOPS):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Devops role required."
            )
        return NodeService.get_nodes(db)
    except Exception as e:
        logger.error(f"Get nodes error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get nodes: {str(e)}")

@app.post("/nodes", response_model=NodeResponse)
async def create_node(node: NodeCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    try:
        if not RoleService.has_role(current_user, UserRole.DEVOPS):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Devops role required."
            )
        result = NodeService.create_node(db, node)
        
        # Log node creation
        AuditService.log_node_action(
            db, AuditAction.NODE_CREATED,
            result.id, result.name,
            user=current_user,
            description=f"Node '{result.name}' created by {current_user.email}"
        )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create node error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create node: {str(e)}")

@app.get("/nodes/{node_id}", response_model=NodeResponse)
async def get_node(node_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    try:
        if not RoleService.has_role(current_user, UserRole.DEVOPS):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Devops role required."
            )
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
        if not RoleService.has_role(current_user, UserRole.DEVOPS):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Devops role required."
            )
        result = NodeService.update_node(db, node_id, node)
        if not result:
            raise HTTPException(status_code=404, detail="Node not found")
        
        # Log node update
        AuditService.log_node_action(
            db, AuditAction.NODE_UPDATED,
            result.id, result.name,
            user=current_user,
            description=f"Node '{result.name}' updated by {current_user.email}"
        )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update node error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update node: {str(e)}")

@app.get("/nodes/{node_id}/analytics")
async def get_node_analytics(node_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """Get analytics for a specific node"""
    try:
        node = NodeService.get_node(db, node_id)
        if not node:
            raise HTTPException(status_code=404, detail="Node not found")
        
        return AnalyticsService.get_node_analytics(db, node_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get node analytics error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get node analytics: {str(e)}")

@app.get("/nodes/{node_id}/config")
async def get_node_config(
    node_id: int,
    db: Session = Depends(get_db),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    authorization: Optional[str] = Header(None)
):
    """Get the current configuration for a node - supports both API key and user authentication"""
    try:
        # Try API key authentication first (for autoscaling nodes)
        if x_api_key:
            try:
                from auth_middleware import APIKeyAuth
                hashed_key = APIKeyAuth.hash_api_key(x_api_key)
                node = db.query(models.Node).filter(models.Node.api_key_hash == hashed_key).first()
                
                if not node:
                    raise HTTPException(status_code=401, detail="Invalid API key")
                
                if node.id != node_id:
                    raise HTTPException(status_code=403, detail="Node ID mismatch")
                
                config = NodeConfigurationService.get_node_config(db, node_id)
                if not config:
                    return {"yaml_config": "# No configuration set yet\n"}
                return {"yaml_config": config.yaml_config}
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"API key auth failed: {str(e)}")
                raise HTTPException(status_code=403, detail="Invalid API key")
        
        # Fall back to user authentication (for web app)
        elif authorization and authorization.startswith("Bearer "):
            try:
                token = authorization.replace("Bearer ", "")
                logger.info(f"🌐 Web app authentication - Bearer token received: {token[:20]}...")
                
                # Try to decode token to see what's inside
                try:
                    from jose import jwt
                    import time
                    payload = jwt.decode(token, verify=False)  # Don't verify to see content
                    logger.info(f"📦 Raw token payload: {payload}")
                    
                    # Check if token is expired
                    exp = payload.get('exp')
                    current_time = time.time()
                    logger.info(f"⏰ Token expiry: {exp}, Current time: {current_time}")
                    logger.info(f"⏳ Token expired: {exp < current_time if exp else 'No exp field'}")
                    
                except Exception as e:
                    logger.error(f"❌ Failed to decode token for inspection: {e}")
                
                logger.info("🔄 Calling AuthService.verify_token...")
                current_user = AuthService.verify_token(token, db)
                logger.info(f"✅ AuthService.verify_token result: {current_user is not None}")
                
                if not current_user:
                    logger.error("❌ Token verification failed - raising 401")
                    raise HTTPException(status_code=401, detail="Invalid or expired token")
                
                logger.info(f"👤 User authenticated successfully: {current_user.email}")
                logger.info(f"🔍 Looking up node {node_id}...")
                
                node = NodeService.get_node(db, node_id)
                if not node:
                    logger.error(f"❌ Node {node_id} not found")
                    raise HTTPException(status_code=404, detail="Node not found")
                
                logger.info(f"✅ Node {node_id} found: {node.name}")
                logger.info(f"🔧 Fetching config for node {node_id}...")
                    
                config = NodeConfigurationService.get_node_config(db, node_id)
                if not config:
                    logger.info(f"⚠️ No config found for node {node_id}, returning default")
                    return {"yaml_config": "# No configuration set yet\n"}
                
                logger.info(f"✅ Config found for node {node_id}, returning YAML")
                return {"yaml_config": config.yaml_config}
                
            except HTTPException:
                logger.error("❌ HTTPException in Bearer token auth - re-raising")
                raise
            except Exception as e:
                logger.error(f"❌ Unexpected error in Bearer token auth: {str(e)}")
                raise HTTPException(status_code=401, detail="Invalid authentication")
        
        else:
            raise HTTPException(status_code=401, detail="Authentication required")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching config for node {node_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch configuration")

@app.put("/nodes/{node_id}/config")
async def update_node_config(
    node_id: int,
    config_data: NodeConfigurationCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update the configuration for a node"""
    try:
        # Verify node exists
        node = NodeService.get_node(db, node_id)
        if not node:
            raise HTTPException(status_code=404, detail="Node not found")
        
        # Get old config hash for audit
        old_config = NodeConfigurationService.get_node_config(db, node_id)
        old_hash = old_config.config_hash if old_config else None
        
        # Update configuration
        updated_config = NodeConfigurationService.update_node_config(
            db, node_id, config_data.yaml_config
        )
        
        # Log configuration update
        AuditService.log_config_change(
            db, node_id, node.name,
            user=current_user,
            old_hash=old_hash,
            new_hash=updated_config.config_hash,
            description=f"Configuration updated for node '{node.name}' by {current_user.email}"
        )
        
        return {
            "status": "success",
            "message": "Configuration updated successfully",
            "config_hash": updated_config.config_hash
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating config for node {node_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update configuration")

@app.delete("/nodes/{node_id}")
async def delete_node(node_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    try:
        # Get node info before deletion for audit
        node = NodeService.get_node(db, node_id)
        if not node:
            raise HTTPException(status_code=404, detail="Node not found")
        
        node_name = node.name
        success = NodeService.delete_node(db, node_id)
        if not success:
            raise HTTPException(status_code=404, detail="Node not found")
        
        # Log node deletion
        AuditService.log_node_action(
            db, AuditAction.NODE_DELETED,
            node_id, node_name,
            user=current_user,
            description=f"Node '{node_name}' deleted by {current_user.email}"
        )
        
        return {"message": "Node deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete node error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete node: {str(e)}")

# Node Configuration endpoint for autoscaling nodes (API key auth)
@app.get("/nodes/{node_id}/config/fetch", response_model=NodeConfigurationResponse)
async def fetch_node_config(node_id: int, node: models.Node = Depends(get_node_from_api_key), db: Session = Depends(get_db)):
    """Get current configuration for a node - used by autoscaling nodes with API key"""
    try:
        # Verify the node_id matches the authenticated node
        if node.id != node_id:
            raise HTTPException(status_code=403, detail="Node ID mismatch")
        
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
                created_at="1970-01-01T00:00:00Z"
            )
        return config
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get node config error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get node config: {str(e)}")

# Alternative approach: Create separate endpoints for API key auth
@app.put("/nodes/{node_id}/config/push", response_model=NodeConfigurationResponse)
async def push_node_config(
    node_id: int, 
    config: NodeConfigurationCreate, 
    node: models.Node = Depends(get_node_from_api_key), 
    db: Session = Depends(get_db)
):
    """Push node configuration using API key authentication - used by autoscaling nodes"""
    try:
        # Verify the node_id matches the authenticated node
        if node.id != node_id:
            raise HTTPException(status_code=403, detail="Node ID mismatch")
            
        return NodeConfigurationService.update_node_config(db, node_id, config.yaml_config)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Push node config error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to push node config: {str(e)}")

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

# Analytics endpoints
@app.get("/analytics/system", response_model=SystemAnalyticsResponse)
async def get_system_analytics(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """Get system-wide analytics and metrics"""
    try:
        return AnalyticsService.get_system_analytics(db)
    except Exception as e:
        logger.error(f"Get system analytics error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get system analytics: {str(e)}")

@app.get("/analytics/pools")
async def get_pool_analytics(node_id: Optional[int] = None, hours: int = 24, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """Get pool analytics for the specified time period with node names"""
    try:
        from datetime import datetime, timedelta
        from models import PoolAnalytics, Node
        
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Join with nodes table to get node name
        query = db.query(
            PoolAnalytics,
            Node.name.label('node_name')
        ).outerjoin(
            Node, PoolAnalytics.node_id == Node.id
        ).filter(PoolAnalytics.timestamp >= cutoff_time)
        
        if node_id:
            query = query.filter(PoolAnalytics.node_id == node_id)
        
        results = query.order_by(PoolAnalytics.timestamp.desc()).limit(1000).all()
        
        # Convert to response format with node_name
        response = []
        for analytics, node_name in results:
            item = {
                "id": analytics.id,
                "pool_id": analytics.pool_id,
                "node_id": analytics.node_id,
                "oracle_pool_id": analytics.oracle_pool_id,
                "timestamp": analytics.timestamp.isoformat() if analytics.timestamp else None,
                "current_instances": analytics.current_instances,
                "active_instances": analytics.active_instances,
                "avg_cpu_utilization": analytics.avg_cpu_utilization,
                "avg_memory_utilization": analytics.avg_memory_utilization,
                "max_cpu_utilization": analytics.max_cpu_utilization,
                "max_memory_utilization": analytics.max_memory_utilization,
                "pool_status": analytics.pool_status,
                "is_active": analytics.is_active,
                "scaling_event": analytics.scaling_event,
                "scaling_reason": analytics.scaling_reason,
                "node_name": node_name
            }
            response.append(item)
        
        return response
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
        result = PoolService.create_pool(db, pool)
        
        # Log pool creation
        AuditService.log_pool_action(
            db, AuditAction.POOL_CREATED,
            result.id, result.name,
            user=current_user,
            description=f"Pool '{result.name}' created by {current_user.email}"
        )
        
        return result
    except HTTPException:
        raise
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
        
        # Log pool update
        AuditService.log_pool_action(
            db, AuditAction.POOL_UPDATED,
            result.id, result.name,
            user=current_user,
            description=f"Pool '{result.name}' updated by {current_user.email}"
        )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update pool error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update pool: {str(e)}")

@app.delete("/pools/{pool_id}")
async def delete_pool(pool_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    try:
        # Get pool info before deletion for audit
        pool = PoolService.get_pool(db, pool_id)
        if not pool:
            raise HTTPException(status_code=404, detail="Pool not found")
        
        pool_name = pool.name
        success = PoolService.delete_pool(db, pool_id)
        if not success:
            raise HTTPException(status_code=404, detail="Pool not found")
        
        # Log pool deletion
        AuditService.log_pool_action(
            db, AuditAction.POOL_DELETED,
            pool_id, pool_name,
            user=current_user,
            description=f"Pool '{pool_name}' deleted by {current_user.email}"
        )
        
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
        result = ScheduleService.create_schedule(db, schedule)
        
        # Log schedule creation
        AuditService.log_schedule_action(
            db, AuditAction.SCHEDULE_CREATED,
            result.id, result.name,
            user=current_user,
            description=f"Schedule '{result.name}' created by {current_user.email}"
        )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create schedule error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create schedule: {str(e)}")

@app.put("/schedules/{schedule_id}", response_model=ScheduleResponse)
async def update_schedule(schedule_id: int, schedule: ScheduleCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    try:
        result = ScheduleService.update_schedule(db, schedule_id, schedule)
        if not result:
            raise HTTPException(status_code=404, detail="Schedule not found")
        
        # Log schedule update
        AuditService.log_schedule_action(
            db, AuditAction.SCHEDULE_UPDATED,
            result.id, result.name,
            user=current_user,
            description=f"Schedule '{result.name}' updated by {current_user.email}"
        )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update schedule error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update schedule: {str(e)}")

@app.delete("/schedules/{schedule_id}")
async def delete_schedule(schedule_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    try:
        # Get schedule info before deletion for audit
        existing = ScheduleService.get_schedule(db, schedule_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Schedule not found")
        
        schedule_name = existing.name
        success = ScheduleService.delete_schedule(db, schedule_id)
        if not success:
            raise HTTPException(status_code=404, detail="Schedule not found")
        
        # Log schedule deletion
        AuditService.log_schedule_action(
            db, AuditAction.SCHEDULE_DELETED,
            schedule_id, schedule_name,
            user=current_user,
            description=f"Schedule '{schedule_name}' deleted by {current_user.email}"
        )
        
        return {"message": "Schedule deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete schedule error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete schedule: {str(e)}")

# Admin endpoints (require admin role)
@app.get("/admin/users", response_model=List[UserListResponse])
async def get_all_users(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """Get all users for admin management"""
    try:
        if not RoleService.has_role(current_user, UserRole.ADMIN):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Admin role required."
            )
        return UserService.get_all_users(db)
    except Exception as e:
        logger.error(f"Get all users error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get users: {str(e)}")

@app.put("/admin/users/{user_id}/role", response_model=UserResponse)
async def update_user_role(user_id: int, role_update: UserUpdateRole, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """Update user role (admin only, local users only)"""
    try:
        if not RoleService.has_role(current_user, UserRole.ADMIN):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Admin role required."
            )
        
        # Get old role for audit
        target_user = db.query(models.User).filter(models.User.id == user_id).first()
        old_role = target_user.role.value if target_user and target_user.role else None
        
        logger.info(f"Admin {current_user.email} updating user {user_id} role to {role_update.role}")
        
        try:
            updated_user = UserService.update_user_role(db, user_id, role_update.role)
            if not updated_user:
                raise HTTPException(status_code=404, detail="User not found")
            
            # Log role change
            AuditService.log_user_action(
                db, AuditAction.USER_ROLE_CHANGED,
                user_id, updated_user.email,
                acting_user=current_user,
                description=f"Admin {current_user.email} changed role for {updated_user.email} from {old_role} to {role_update.role}",
                details={"old_role": old_role, "new_role": role_update.role}
            )
            
            logger.info(f"Successfully updated user {user_id} role to {role_update.role}")
            return updated_user
        except ValueError as e:
            logger.warning(f"Role update validation error for user {user_id}: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update user role error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update user role: {str(e)}")

@app.get("/admin/users/{user_id}", response_model=UserResponse)
async def get_user_details(user_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """Get detailed user information (admin only)"""
    try:
        if not RoleService.has_role(current_user, UserRole.ADMIN):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Admin role required."
            )
        
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
        
    except Exception as e:
        logger.error(f"Get user details error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get user details: {str(e)}")


# Node Lifecycle Audit Log endpoints
@app.get("/nodes/lifecycle-logs", response_model=List[NodeLifecycleLogResponse])
async def get_lifecycle_logs(
    node_id: Optional[int] = None,
    event_type: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get node lifecycle audit logs (online/offline transitions)"""
    try:
        if not RoleService.has_role(current_user, UserRole.DEVOPS):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Devops role required."
            )
        return NodeLifecycleService.get_logs(db, node_id=node_id, event_type=event_type, limit=limit)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get lifecycle logs error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get lifecycle logs: {str(e)}")


@app.get("/nodes/{node_id}/lifecycle-logs", response_model=List[NodeLifecycleLogResponse])
async def get_node_lifecycle_logs(
    node_id: int,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get lifecycle logs for a specific node"""
    try:
        if not RoleService.has_role(current_user, UserRole.DEVOPS):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Devops role required."
            )
        
        node = NodeService.get_node(db, node_id)
        if not node:
            raise HTTPException(status_code=404, detail="Node not found")
        
        return NodeLifecycleService.get_logs(db, node_id=node_id, limit=limit)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get node lifecycle logs error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get node lifecycle logs: {str(e)}")


# ============================================================================
# AUDIT LOG ENDPOINTS (Admin only)
# ============================================================================

@app.get("/admin/audit-logs", response_model=List[AuditLogResponse])
async def get_audit_logs(
    category: Optional[str] = None,
    action: Optional[str] = None,
    user_id: Optional[int] = None,
    resource_type: Optional[str] = None,
    status: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get audit logs (admin only)"""
    try:
        if not RoleService.has_role(current_user, UserRole.ADMIN):
            raise HTTPException(
                status_code=status_code.HTTP_403_FORBIDDEN,
                detail="Access denied. Admin role required."
            )
        
        # Parse dates if provided
        start_dt = None
        end_dt = None
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid start_date format")
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid end_date format")
        
        return AuditService.get_audit_logs(
            db=db,
            category=category,
            action=action,
            user_id=user_id,
            resource_type=resource_type,
            status=status,
            start_date=start_dt,
            end_date=end_dt,
            search=search,
            limit=limit,
            offset=offset
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get audit logs error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get audit logs: {str(e)}")


@app.get("/admin/audit-logs/summary", response_model=AuditLogSummaryResponse)
async def get_audit_log_summary(
    hours: int = 24,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get audit log summary statistics (admin only)"""
    try:
        if not RoleService.has_role(current_user, UserRole.ADMIN):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Admin role required."
            )
        
        return AuditService.get_audit_summary(db, hours=hours)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get audit summary error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get audit summary: {str(e)}")


@app.get("/admin/audit-logs/categories")
async def get_audit_categories(
    current_user = Depends(get_current_user)
):
    """Get available audit log categories and actions"""
    try:
        if not RoleService.has_role(current_user, UserRole.ADMIN):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Admin role required."
            )
        
        return {
            "categories": [
                {"value": "AUTH", "label": "Authentication"},
                {"value": "NODE", "label": "Node Operations"},
                {"value": "POOL", "label": "Pool Operations"},
                {"value": "USER", "label": "User Management"},
                {"value": "CONFIG", "label": "Configuration"},
                {"value": "SYSTEM", "label": "System Events"},
                {"value": "ADMIN", "label": "Admin Operations"}
            ],
            "actions": [
                {"value": "LOGIN_SUCCESS", "label": "Login Success", "category": "AUTH"},
                {"value": "LOGIN_FAILED", "label": "Login Failed", "category": "AUTH"},
                {"value": "LOGOUT", "label": "Logout", "category": "AUTH"},
                {"value": "KEYCLOAK_LOGIN", "label": "Keycloak Login", "category": "AUTH"},
                {"value": "USER_CREATED", "label": "User Created", "category": "USER"},
                {"value": "USER_ROLE_CHANGED", "label": "Role Changed", "category": "USER"},
                {"value": "PROFILE_UPDATED", "label": "Profile Updated", "category": "USER"},
                {"value": "NODE_REGISTERED", "label": "Node Registered", "category": "NODE"},
                {"value": "NODE_CREATED", "label": "Node Created", "category": "NODE"},
                {"value": "NODE_UPDATED", "label": "Node Updated", "category": "NODE"},
                {"value": "NODE_DELETED", "label": "Node Deleted", "category": "NODE"},
                {"value": "POOL_CREATED", "label": "Pool Created", "category": "POOL"},
                {"value": "POOL_UPDATED", "label": "Pool Updated", "category": "POOL"},
                {"value": "POOL_DELETED", "label": "Pool Deleted", "category": "POOL"},
                {"value": "SCHEDULE_CREATED", "label": "Schedule Created", "category": "CONFIG"},
                {"value": "SCHEDULE_UPDATED", "label": "Schedule Updated", "category": "CONFIG"},
                {"value": "SCHEDULE_DELETED", "label": "Schedule Deleted", "category": "CONFIG"},
                {"value": "CONFIG_UPDATED", "label": "Config Updated", "category": "CONFIG"},
                {"value": "HEARTBEAT_RECEIVED", "label": "Heartbeat", "category": "SYSTEM"}
            ],
            "statuses": [
                {"value": "SUCCESS", "label": "Success"},
                {"value": "FAILURE", "label": "Failure"}
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get audit categories error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get audit categories: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
