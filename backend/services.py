from sqlalchemy.orm import Session
from sqlalchemy import desc, func, and_
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt

# Added imports for modules used below
import os
import json
import hashlib
import yaml
import logging

from models import (
    Node, Pool, Metric, Schedule, User, AuditLog, NodeConfiguration, 
    NodeHeartbeat, PoolAnalytics, SystemAnalytics, NodeStatus, PoolStatus,
    UserRole, AuthProvider, NodeLifecycleLog
)
from schemas import (
    NodeCreate, NodeUpdate, PoolCreate, PoolUpdate, 
    MetricCreate, ScheduleCreate, UserCreate, NodeHeartbeatData,
    PoolAnalyticsData, SystemAnalyticsResponse, NodeRegister, NodeRegisterResponse,
    UserRole as UserRoleSchema, AuthProvider as AuthProviderSchema
)
from auth_middleware import APIKeyAuth

# Password hashing
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    # Avoid raising on >72 bytes; bcrypt will effectively use first 72 bytes
    bcrypt__truncate_error=False,
)

# JWT settings
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

class AuthService:
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        if not hashed_password:
            return False
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except Exception as e:
            logging.getLogger(__name__).warning(f"Password verification error: {e}")
            return False
    
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
        logger = logging.getLogger(__name__)
        
        logger.info(f"🔍 verify_token called with token: {token[:20]}...")
        
        # First try Keycloak token validation
        try:
            from keycloak_service import keycloak_service
            
            if keycloak_service.is_enabled():
                keycloak_data = keycloak_service.validate_token(token)
                if keycloak_data:
                    logger.info("✅ Keycloak token validation successful")
                    return AuthService.handle_keycloak_user(db, keycloak_data, token)
        except Exception as e:
            logger.info(f"⚠️ Keycloak validation failed, trying local: {e}")
        
        # Fall back to local JWT validation
        try:
            logger.info(f"🔐 SECRET_KEY in use: {SECRET_KEY[:10]}...")
            logger.info(f"📊 ALGORITHM: {ALGORITHM}")
            
            # Decode without verification first to manually check expiration with UTC
            logger.info("🔓 Attempting to decode token...")
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], options={"verify_exp": False})
            logger.info(f"📦 Token payload decoded successfully: {payload}")
            
            # Manually validate expiration using UTC time
            exp = payload.get("exp")
            logger.info(f"⏰ Token expiration: {exp}")
            
            if exp is None:
                logger.warning("❌ No expiration found in token")
                return None
            
            # Check if token is expired using UTC time
            current_utc_timestamp = datetime.utcnow().timestamp()
            logger.info(f"🕐 Current UTC timestamp: {current_utc_timestamp}")
            logger.info(f"⏳ Token expires at: {exp}")
            logger.info(f"🔄 Time until expiration: {exp - current_utc_timestamp} seconds")
            
            if exp < current_utc_timestamp:
                logger.warning(f"❌ Token expired! Expired {current_utc_timestamp - exp} seconds ago")
                return None
            
            logger.info("✅ Token is not expired")
            
            email: str = payload.get("sub")
            logger.info(f"📧 Email from token: {email}")
            
            if email is None:
                logger.warning("❌ No email (sub) found in token")
                return None
            
            logger.info(f"🔍 Looking up user in database: {email}")
            user = db.query(User).filter(User.email == email).first()
            
            if user:
                logger.info(f"👤 User found in database: {user.email} (ID: {user.id})")
            else:
                logger.warning(f"❌ User not found in database: {email}")
            
            return user
            
        except JWTError as e:
            logger.error(f"❌ JWT Error: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"❌ Unexpected error in verify_token: {str(e)}")
            return None
    
    @staticmethod
    def handle_keycloak_user(db: Session, keycloak_data: dict, token: str):
        """Handle Keycloak user authentication and role mapping"""
        from keycloak_service import keycloak_service
        from role_service import RoleService
        
        logger = logging.getLogger(__name__)
        
        user_info = keycloak_data['user_info']
        token_info = keycloak_data.get('token_info', {})
        email = user_info.get('email')
        full_name = user_info.get('name', user_info.get('preferred_username', email))
        keycloak_user_id = user_info.get('sub')
        
        logger.info(f"🔍 KEYCLOAK ROLE DETECTION - Processing user: {email}")
        logger.info(f"📋 COMPLETE Keycloak user_info: {user_info}")
        logger.info(f"📋 COMPLETE Keycloak token_info: {token_info}")
        
        # Extract and log all possible role/group sources
        logger.info(f"🎭 TOKEN GROUPS: {token_info.get('groups', [])}")
        logger.info(f"🎭 TOKEN REALM ACCESS: {token_info.get('realm_access', {})}")
        logger.info(f"🎭 TOKEN RESOURCE ACCESS: {token_info.get('resource_access', {})}")
        logger.info(f"🎭 USER INFO GROUPS: {user_info.get('groups', [])}")
        logger.info(f"🎭 USER INFO ROLES: {user_info.get('roles', [])}")
        
        # Print to console for easy debugging
        print(f"\n=== KEYCLOAK LOGIN DEBUG INFO ===")
        print(f"User Email: {email}")
        print(f"User Name: {full_name}")
        print(f"Keycloak User ID: {keycloak_user_id}")
        print(f"Groups from token: {token_info.get('groups', [])}")
        print(f"Realm access: {token_info.get('realm_access', {})}")
        print(f"Resource access: {token_info.get('resource_access', {})}")
        print(f"Groups from user_info: {user_info.get('groups', [])}")
        print(f"Roles from user_info: {user_info.get('roles', [])}")
        print(f"================================\n")
        
        if not email or not keycloak_user_id:
            logger.error("Missing email or user ID from Keycloak")
            return None
        
        # Check if user already exists
        user = db.query(User).filter(
            (User.email == email) | (User.keycloak_user_id == keycloak_user_id)
        ).first()
        
        # Get user roles from Keycloak with verbose logging
        logger.info(f"🔐 Extracting roles from Keycloak for user: {email}")
        roles = keycloak_service.get_user_roles(token)
        logger.info(f"🎭 RAW KEYCLOAK ROLES/GROUPS DETECTED: {roles}")
        
        # Map to application role with verbose logging
        app_role = RoleService.map_keycloak_roles_to_app_role(roles)
        logger.info(f"🎯 MAPPED APPLICATION ROLE: {app_role}")
        logger.info(f"📊 Role mapping details - Input: {roles} -> Output: {app_role}")
        
        if user:
            # Update existing user
            old_role = user.role
            user.keycloak_user_id = keycloak_user_id
            user.auth_provider = AuthProvider.KEYCLOAK
            user.full_name = full_name
            
            # Only update role from Keycloak if role_override is False
            if not getattr(user, 'role_override', False):
                user.role = app_role
                logger.info(f"✅ Updated existing Keycloak user: {email}")
                logger.info(f"🔄 Role change: {old_role} -> {app_role}")
            else:
                logger.info(f"⚠️ Skipping role update for {email} - manual override in place (current role: {user.role})")
        else:
            # Create new user
            user = User(
                email=email,
                full_name=full_name,
                role=app_role,
                auth_provider=AuthProvider.KEYCLOAK,
                keycloak_user_id=keycloak_user_id,
                hashed_password=None  # No password for Keycloak users
            )
            db.add(user)
            logger.info(f"🆕 Created new Keycloak user: {email} with role: {app_role}")
        
        db.commit()
        db.refresh(user)
        logger.info(f"💾 User saved to database with final role: {user.role}")
        return user
    
    @staticmethod
    def create_keycloak_jwt(user: User) -> str:
        """Create a local JWT token for Keycloak users"""
        return AuthService.create_access_token(data={"sub": user.email})
    
    @staticmethod
    def authenticate_user(db: Session, email: str, password: str):
        logger = logging.getLogger(__name__)
        user = db.query(User).filter(User.email == email).first()
        if not user:
            logger.warning(f"Local login failed: user not found for {email}")
            return None
        # Only local users with a stored password can use local login
        if user.auth_provider != AuthProvider.LOCAL:
            logger.warning(f"Local login blocked for non-local user (provider={user.auth_provider})")
            return None
        if not user.hashed_password:
            logger.warning("Local login failed: no password set for user")
            return None
        if not AuthService.verify_password(password, user.hashed_password):
            logger.warning("Local login failed: invalid password")
            return None
        return user

class UserService:
    @staticmethod
    def create_user(db: Session, user: UserCreate):
        hashed_password = AuthService.get_password_hash(user.password)
        db_user = User(
            email=user.email,
            hashed_password=hashed_password,
            full_name=user.full_name,
            role=UserRole.USER,  # Default role
            auth_provider=AuthProvider.LOCAL
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    
    @staticmethod
    def get_all_users(db: Session) -> List[User]:
        """Get all users for admin management"""
        return db.query(User).all()
    
    @staticmethod
    def update_user_role(db: Session, user_id: int, new_role: UserRole, allow_keycloak_override: bool = True) -> Optional[User]:
        """Update user role (admin only). For Keycloak users, sets role_override flag."""
        logger = logging.getLogger(__name__)
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        # For Keycloak users, set the override flag
        if user.auth_provider != AuthProvider.LOCAL:
            if not allow_keycloak_override:
                raise ValueError("Cannot modify roles for non-local users without override permission")
            user.role_override = True  # Mark as manually overridden
            logger.info(f"🔄 Setting role override for Keycloak user {user.email}")
        
        old_role = user.role
        user.role = new_role
        db.commit()
        db.refresh(user)
        logger.info(f"✅ Updated user {user.email} role from {old_role} to {new_role}")
        return user
    
    @staticmethod
    def reset_role_override(db: Session, user_id: int) -> Optional[User]:
        """Reset role override for a Keycloak user, allowing Keycloak roles to take effect on next login"""
        logger = logging.getLogger(__name__)
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        if user.auth_provider != AuthProvider.KEYCLOAK:
            raise ValueError("Role override reset only applies to Keycloak users")
        
        user.role_override = False
        db.commit()
        db.refresh(user)
        logger.info(f"✅ Reset role override for Keycloak user {user.email}")
        return user
    
    @staticmethod
    def update_profile(db: Session, user_id: int, full_name: Optional[str] = None, 
                      email: Optional[str] = None, current_password: Optional[str] = None, 
                      new_password: Optional[str] = None) -> Optional[User]:
        """Update user profile (self-service for local users)"""
        logger = logging.getLogger(__name__)
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.warning(f"User not found: {user_id}")
            return None
        
        # Only allow profile updates for local users
        if user.auth_provider != AuthProvider.LOCAL:
            logger.warning(f"Profile update blocked for non-local user: {user.email}")
            raise ValueError("Cannot modify profile for non-local users")
        
        # Update full name if provided
        if full_name is not None:
            user.full_name = full_name
            logger.info(f"Updated full_name for user {user.email}")
        
        # Update email if provided and not already taken
        if email is not None and email != user.email:
            existing_user = db.query(User).filter(User.email == email).first()
            if existing_user:
                logger.warning(f"Email {email} already taken")
                raise ValueError("Email already exists")
            user.email = email
            logger.info(f"Updated email for user {user.id} to {email}")
        
        # Update password if provided
        if new_password is not None:
            # Verify current password
            if not current_password:
                logger.warning("Current password not provided for password change")
                raise ValueError("Current password is required to change password")
            
            if not user.hashed_password:
                logger.warning("User has no password set")
                raise ValueError("User has no password set")
            
            if not AuthService.verify_password(current_password, user.hashed_password):
                logger.warning("Current password incorrect")
                raise ValueError("Current password is incorrect")
            
            user.hashed_password = AuthService.get_password_hash(new_password)
            logger.info(f"Updated password for user {user.email}")
        
        db.commit()
        db.refresh(user)
        logger.info(f"Profile updated successfully for user {user.email}")
        return user

class NodeService:
    @staticmethod
    def get_nodes(db: Session) -> List[Node]:
        # Filter out OFFLINE nodes from the list
        nodes = db.query(Node).filter(Node.status != NodeStatus.OFFLINE).all()
        for node in nodes:
            node.has_api_key = bool(node.api_key_hash)
        return nodes
    
    @staticmethod
    def get_node(db: Session, node_id: int) -> Optional[Node]:
        node = db.query(Node).filter(Node.id == node_id).first()
        if node:
            node.has_api_key = bool(node.api_key_hash)
        return node
    
    @staticmethod
    def register_node(db: Session, node: NodeRegister) -> NodeRegisterResponse:
        """Register a new node and generate API key"""
        # Generate API key
        api_key = APIKeyAuth.generate_api_key()
        api_key_hash = APIKeyAuth.hash_api_key(api_key)
        
        # Create node
        db_node = Node(
            name=node.name,
            region=node.region,
            ip_address=node.ip_address,
            description=node.description,
            api_key_hash=api_key_hash,
            status=NodeStatus.INACTIVE
        )
        db.add(db_node)
        db.commit()
        db.refresh(db_node)
        
        return NodeRegisterResponse(
            node_id=db_node.id,
            api_key=api_key,
            name=db_node.name,
            region=db_node.region
        )
    
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
            # If node is inactive, permanently delete it
            # Otherwise, soft delete by setting status to OFFLINE
            if db_node.status == NodeStatus.INACTIVE:
                db.delete(db_node)
            else:
                previous_status = db_node.status.value if db_node.status else None
                db_node.status = NodeStatus.OFFLINE
                
                # Log lifecycle event
                NodeLifecycleService.log_event(
                    db=db,
                    node_id=node_id,
                    event_type="WENT_OFFLINE",
                    previous_status=previous_status,
                    new_status="OFFLINE",
                    reason="Node deleted by user",
                    triggered_by="manual"
                )
            db.commit()
            return True
        return False

class NodeConfigurationService:
    @staticmethod
    def get_node_config(db: Session, node_id: int) -> Optional[NodeConfiguration]:
        return db.query(NodeConfiguration).filter(
            and_(NodeConfiguration.node_id == node_id, NodeConfiguration.is_active == True)
        ).first()
    
    @staticmethod
    def update_node_config(db: Session, node_id: int, yaml_config: str) -> NodeConfiguration:
        # Deactivate old configs
        db.query(NodeConfiguration).filter(NodeConfiguration.node_id == node_id).update({
            "is_active": False
        })
        
        # Create new config
        config_hash = hashlib.sha256(yaml_config.encode()).hexdigest()
        db_config = NodeConfiguration(
            node_id=node_id,
            yaml_config=yaml_config,
            config_hash=config_hash,
            is_active=True
        )
        db.add(db_config)
        db.commit()
        db.refresh(db_config)
        return db_config

class NodeLifecycleService:
    """Service for tracking node lifecycle events (online/offline transitions)"""
    
    @staticmethod
    def log_event(
        db: Session,
        node_id: int,
        event_type: str,
        previous_status: Optional[str],
        new_status: str,
        reason: Optional[str] = None,
        triggered_by: Optional[str] = None,
        metadata_dict: Optional[Dict[str, Any]] = None
    ) -> NodeLifecycleLog:
        """Log a node lifecycle event"""
        metadata_json = json.dumps(metadata_dict) if metadata_dict else None
        
        log_entry = NodeLifecycleLog(
            node_id=node_id,
            event_type=event_type,
            previous_status=previous_status,
            new_status=new_status,
            reason=reason,
            triggered_by=triggered_by,
            extra_data=metadata_json
        )
        db.add(log_entry)
        return log_entry
    
    @staticmethod
    def get_logs(
        db: Session,
        node_id: Optional[int] = None,
        event_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get lifecycle logs with optional filtering"""
        query = db.query(NodeLifecycleLog, Node.name.label('node_name')).join(
            Node, NodeLifecycleLog.node_id == Node.id
        )
        
        if node_id:
            query = query.filter(NodeLifecycleLog.node_id == node_id)
        if event_type:
            query = query.filter(NodeLifecycleLog.event_type == event_type)
        
        results = query.order_by(desc(NodeLifecycleLog.timestamp)).limit(limit).all()
        
        return [
            {
                "id": log.id,
                "node_id": log.node_id,
                "node_name": node_name,
                "event_type": log.event_type,
                "previous_status": log.previous_status,
                "new_status": log.new_status,
                "reason": log.reason,
                "triggered_by": log.triggered_by,
                "metadata": log.extra_data,
                "timestamp": log.timestamp
            }
            for log, node_name in results
        ]


class HeartbeatService:
    @staticmethod
    def process_heartbeat(db: Session, node_id: int, heartbeat_data: NodeHeartbeatData) -> Dict[str, Any]:
        logger = logging.getLogger(__name__)
        
        # Update node status and last heartbeat
        node = db.query(Node).filter(Node.id == node_id).first()
        if not node:
            raise ValueError(f"Node {node_id} not found")
        
        previous_status = node.status.value if node.status else None
        node.last_heartbeat = datetime.utcnow()
        
        # Reactivate OFFLINE nodes automatically on heartbeat
        if node.status == NodeStatus.OFFLINE:
            logger.info(f"Reactivating offline node {node_id}")
            node.status = NodeStatus.ACTIVE
            
            # Log lifecycle event for coming back online
            NodeLifecycleService.log_event(
                db=db,
                node_id=node_id,
                event_type="CAME_ONLINE",
                previous_status=previous_status,
                new_status="ACTIVE",
                reason="Node sent heartbeat after being offline",
                triggered_by="heartbeat"
            )
        else:
            node.status = NodeStatus.ACTIVE
        
        # Convert metrics_data dict to JSON string for database storage
        metrics_data_json = json.dumps(heartbeat_data.metrics_data) if heartbeat_data.metrics_data else None
        
        # Store heartbeat record
        heartbeat = NodeHeartbeat(
            node_id=node_id,
            config_hash=heartbeat_data.config_hash,
            status=heartbeat_data.status,
            error_message=heartbeat_data.error_message,
            metrics_data=metrics_data_json  # Store as JSON string
        )
        db.add(heartbeat)
        
        # Process pool analytics if provided
        if heartbeat_data.pool_analytics:
            AnalyticsService.process_pool_analytics(db, node_id, heartbeat_data.pool_analytics)
        
        # Check for configuration drift
        current_config = NodeConfigurationService.get_node_config(db, node_id)
        config_update_needed = False
        
        if current_config and current_config.config_hash != heartbeat_data.config_hash:
            config_update_needed = True
        
        db.commit()
        
        response = {
            "status": "success",
            "config_update_needed": config_update_needed,
            "current_config_hash": current_config.config_hash if current_config else None
        }
        
        if config_update_needed and current_config:
            response["new_config"] = current_config.yaml_config
        
        return response

class AnalyticsService:
    @staticmethod
    def get_node_analytics(db: Session, node_id: int) -> Dict[str, Any]:
        """Get latest analytics for a specific node"""
        # Get the latest pool analytics for this node
        latest_analytics = db.query(PoolAnalytics).filter(
            PoolAnalytics.node_id == node_id
        ).order_by(desc(PoolAnalytics.timestamp)).first()
        
        if not latest_analytics:
            return {
                "avg_cpu_utilization": 0,
                "avg_memory_utilization": 0,
                "current_instances": 0,
                "max_instances": 0
            }
        
        # Get max_instances from node configuration instead of pool
        node_config = db.query(NodeConfiguration).filter(
            NodeConfiguration.node_id == node_id,
            NodeConfiguration.is_active == True
        ).first()
        
        max_instances = latest_analytics.current_instances  # fallback
        if node_config:
            try:
                import yaml
                config_data = yaml.safe_load(node_config.yaml_config)
                if 'pools' in config_data and len(config_data['pools']) > 0:
                    pool_config = config_data['pools'][0]  # Get first pool config
                    if 'scaling_limits' in pool_config:
                        max_instances = pool_config['scaling_limits'].get('max', latest_analytics.current_instances)
            except Exception:
                pass  # Use fallback if config parsing fails
        
        return {
            "avg_cpu_utilization": latest_analytics.avg_cpu_utilization,
            "avg_memory_utilization": latest_analytics.avg_memory_utilization,
            "current_instances": latest_analytics.current_instances,
            "max_instances": max_instances
        }
    
    @staticmethod
    def process_pool_analytics(db: Session, node_id: int, pool_analytics_list: List[PoolAnalyticsData]):
        logger = logging.getLogger(__name__)
        
        # Get node's configuration to sync scaling limits
        node_config = NodeConfigurationService.get_node_config(db, node_id)
        config_pools = {}
        if node_config and node_config.yaml_config:
            try:
                config_data = yaml.safe_load(node_config.yaml_config)
                for pool_cfg in config_data.get('pools', []):
                    pool_id = pool_cfg.get('instance_pool_id')
                    if pool_id:
                        config_pools[pool_id] = pool_cfg.get('scaling_limits', {})
            except Exception as e:
                logger.warning(f"Failed to parse YAML config for scaling limits sync: {e}")
        
        for pool_data in pool_analytics_list:
            # First, ensure the pool exists in the database
            pool = db.query(Pool).filter(Pool.oracle_pool_id == pool_data.oracle_pool_id).first()
            node = db.query(Node).filter(Node.id == node_id).first()
            
            # Get scaling limits from YAML config
            scaling_limits = config_pools.get(pool_data.oracle_pool_id, {})
            config_min = scaling_limits.get('min', 1)
            config_max = scaling_limits.get('max', pool_data.current_instances)
            
            if not pool:
                # Create the pool if it doesn't exist
                pool = Pool(
                    node_id=node_id,
                    oracle_pool_id=pool_data.oracle_pool_id,
                    name=node.name if node else f"Pool-{pool_data.oracle_pool_id[-8:]}",  # Use node name
                    region=node.region if node else "unknown",
                    min_instances=config_min,
                    max_instances=config_max,
                    current_instances=pool_data.current_instances,
                    status=PoolStatus.HEALTHY
                )
                db.add(pool)
                db.flush()  # Flush to get the ID
                logger.info(f"Created pool '{pool.name}' with min={config_min}, max={config_max}")
            else:
                # Sync pool name with node name
                if node and pool.name != node.name:
                    pool.name = node.name
                
                # Sync scaling limits from YAML config
                if pool.min_instances != config_min:
                    pool.min_instances = config_min
                if pool.max_instances != config_max:
                    pool.max_instances = config_max
            
            # Update pool's current instances if it has changed
            if pool.current_instances != pool_data.current_instances:
                pool.current_instances = pool_data.current_instances
            
            db.add(pool)
            
            # Now create the analytics record with the correct pool_id
            analytics = PoolAnalytics(
                pool_id=pool.id,  # Use the actual pool ID from database
                node_id=node_id,
                oracle_pool_id=pool_data.oracle_pool_id,
                current_instances=pool_data.current_instances,
                active_instances=pool_data.active_instances,
                avg_cpu_utilization=pool_data.avg_cpu_utilization,
                avg_memory_utilization=pool_data.avg_memory_utilization,
                max_cpu_utilization=pool_data.max_cpu_utilization,
                max_memory_utilization=pool_data.max_memory_utilization,
                pool_status=pool_data.pool_status,
                is_active=pool_data.is_active,
                scaling_event=pool_data.scaling_event,
                scaling_reason=pool_data.scaling_reason
            )
            db.add(analytics)
        
        # Calculate and update system analytics
        AnalyticsService.update_system_analytics(db)
    
    @staticmethod
    def update_system_analytics(db: Session):
        now = datetime.utcnow()
        
        # Get latest pool analytics (within last 5 minutes)
        recent_analytics = db.query(PoolAnalytics).filter(
            PoolAnalytics.timestamp >= now - timedelta(minutes=5)
        ).all()
        
        if not recent_analytics:
            return
        
        # Calculate current metrics - group by unique pools
        unique_pools = {}
        for analytics in recent_analytics:
            pool_key = f"{analytics.pool_id}"  # Assuming pool_id exists, or use node_id
            if pool_key not in unique_pools or analytics.timestamp > unique_pools[pool_key].timestamp:
                unique_pools[pool_key] = analytics
        
        active_pool_analytics = list(unique_pools.values())
        total_active_pools = len([a for a in active_pool_analytics if a.is_active])
        total_current_instances = sum(a.current_instances for a in active_pool_analytics)
        total_active_instances = sum(a.active_instances for a in active_pool_analytics)
        
        if active_pool_analytics:
            avg_cpu = sum(a.avg_cpu_utilization for a in active_pool_analytics) / len(active_pool_analytics)
            avg_memory = sum(a.avg_memory_utilization for a in active_pool_analytics) / len(active_pool_analytics)
            max_cpu = max(a.max_cpu_utilization or 0 for a in active_pool_analytics)
            max_memory = max(a.max_memory_utilization or 0 for a in active_pool_analytics)
        else:
            avg_cpu = avg_memory = max_cpu = max_memory = 0
        
        # Calculate 24h peaks - get the maximum instances that were running simultaneously
        yesterday = now - timedelta(hours=24)
        
        # Get hourly snapshots and find the maximum total instances across all pools
        hourly_totals = db.query(
            func.date_trunc('hour', PoolAnalytics.timestamp).label('hour'),
            func.sum(PoolAnalytics.current_instances).label('total_instances')
        ).filter(
            PoolAnalytics.timestamp >= yesterday
        ).group_by(func.date_trunc('hour', PoolAnalytics.timestamp)).all()
        
        peak_instances_24h = max((total.total_instances for total in hourly_totals), default=0)
        
        # Get maximum active pools in any hour in the last 24h
        hourly_pool_counts = db.query(
            func.date_trunc('hour', PoolAnalytics.timestamp).label('hour'),
            func.count(func.distinct(PoolAnalytics.id)).label('pool_count')
        ).filter(
            and_(PoolAnalytics.timestamp >= yesterday, PoolAnalytics.is_active == True)
        ).group_by(func.date_trunc('hour', PoolAnalytics.timestamp)).all()
        
        max_active_pools_24h = max((count.pool_count for count in hourly_pool_counts), default=0)
        
        # Count active nodes
        active_nodes = db.query(Node).filter(
            and_(
                Node.status == NodeStatus.ACTIVE,
                Node.last_heartbeat >= now - timedelta(minutes=2)
            )
        ).count()
        
        # Create system analytics record
        system_analytics = SystemAnalytics(
            total_active_pools=total_active_pools,
            total_current_instances=total_current_instances,
            total_active_instances=total_active_instances,
            avg_system_cpu=avg_cpu,
            avg_system_memory=avg_memory,
            max_system_cpu=max_cpu,
            max_system_memory=max_memory,
            peak_instances_24h=peak_instances_24h,
            max_active_pools_24h=max_active_pools_24h if isinstance(max_active_pools_24h, int) else 0,
            active_nodes=active_nodes
        )
        db.add(system_analytics)
        db.commit()
    
    @staticmethod
    def get_system_analytics(db: Session) -> SystemAnalyticsResponse:
        """
        Get real-time system analytics based on current node status.
        Now uses DashboardAnalyticsCalculator for accurate calculations.
        """
        try:
            from analytics_calculator import DashboardAnalyticsCalculator
            
            analytics_data = DashboardAnalyticsCalculator.get_complete_dashboard_analytics(db)
            
            return SystemAnalyticsResponse(
                total_active_pools=analytics_data["total_active_pools"],
                total_current_instances=analytics_data["total_current_instances"],
                peak_instances_24h=analytics_data["peak_instances_24h"],
                max_active_pools_24h=analytics_data["max_active_pools_24h"],
                avg_system_cpu=analytics_data["avg_system_cpu"],
                avg_system_memory=analytics_data["avg_system_memory"],
                active_nodes=analytics_data["active_nodes"],
                last_updated=analytics_data["last_updated"].isoformat()
            )
        except Exception as e:
            logger.error(f"Error in get_system_analytics: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # Return zeros on error
            now = datetime.utcnow()
            return SystemAnalyticsResponse(
                total_active_pools=0,
                total_current_instances=0,
                peak_instances_24h=0,
                max_active_pools_24h=0,
                avg_system_cpu=0.0,
                avg_system_memory=0.0,
                active_nodes=0,
                last_updated=now.isoformat()
            )

# ... keep existing code (PoolService, MetricService, ScheduleService classes remain unchanged)

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
