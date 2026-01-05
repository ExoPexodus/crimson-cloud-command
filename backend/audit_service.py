"""
Enterprise Audit Logging Service

Provides centralized audit logging for all user and system actions.
"""
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import json
import logging

from models import AuditLog, User

logger = logging.getLogger(__name__)


class AuditCategory:
    """Audit log categories"""
    AUTH = "AUTH"           # Login, logout, token refresh
    NODE = "NODE"           # Node CRUD operations
    POOL = "POOL"           # Pool operations
    USER = "USER"           # User management
    CONFIG = "CONFIG"       # Configuration changes
    SYSTEM = "SYSTEM"       # System events (heartbeats, scaling)
    ADMIN = "ADMIN"         # Admin operations


class AuditAction:
    """Standard audit action types"""
    # Auth actions
    LOGIN_SUCCESS = "LOGIN_SUCCESS"
    LOGIN_FAILED = "LOGIN_FAILED"
    LOGOUT = "LOGOUT"
    TOKEN_REFRESH = "TOKEN_REFRESH"
    KEYCLOAK_LOGIN = "KEYCLOAK_LOGIN"
    
    # User actions
    USER_CREATED = "USER_CREATED"
    USER_UPDATED = "USER_UPDATED"
    USER_DELETED = "USER_DELETED"
    USER_ROLE_CHANGED = "USER_ROLE_CHANGED"
    PROFILE_UPDATED = "PROFILE_UPDATED"
    PASSWORD_CHANGED = "PASSWORD_CHANGED"
    
    # Node actions
    NODE_REGISTERED = "NODE_REGISTERED"
    NODE_CREATED = "NODE_CREATED"
    NODE_UPDATED = "NODE_UPDATED"
    NODE_DELETED = "NODE_DELETED"
    NODE_WENT_OFFLINE = "NODE_WENT_OFFLINE"
    NODE_CAME_ONLINE = "NODE_CAME_ONLINE"
    
    # Config actions
    CONFIG_UPDATED = "CONFIG_UPDATED"
    CONFIG_VIEWED = "CONFIG_VIEWED"
    
    # Pool actions
    POOL_CREATED = "POOL_CREATED"
    POOL_UPDATED = "POOL_UPDATED"
    POOL_DELETED = "POOL_DELETED"
    
    # System actions
    HEARTBEAT_RECEIVED = "HEARTBEAT_RECEIVED"
    SCALING_EVENT = "SCALING_EVENT"
    SYSTEM_ERROR = "SYSTEM_ERROR"


class AuditService:
    """Enterprise audit logging service"""
    
    @staticmethod
    def log(
        db: Session,
        action: str,
        category: str,
        user: Optional[User] = None,
        user_id: Optional[int] = None,
        user_email: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        resource_name: Optional[str] = None,
        description: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        status: str = "SUCCESS",
        error_message: Optional[str] = None
    ) -> AuditLog:
        """
        Log an audit event
        
        Args:
            db: Database session
            action: The action being performed (use AuditAction constants)
            category: Category of the action (use AuditCategory constants)
            user: User object performing the action (optional)
            user_id: User ID if user object not available
            user_email: User email if user object not available
            resource_type: Type of resource being acted upon
            resource_id: ID of the resource
            resource_name: Human-readable name of the resource
            description: Brief description of the action
            details: Additional JSON details
            ip_address: Client IP address
            user_agent: Client user agent
            status: SUCCESS or FAILURE
            error_message: Error message if status is FAILURE
            
        Returns:
            The created AuditLog entry
        """
        try:
            # Extract user info from user object if provided
            if user:
                user_id = user.id
                user_email = user.email
                user_role = user.role.value if user.role else None
            else:
                user_role = None
            
            # Serialize details to JSON if provided
            details_json = json.dumps(details) if details else None
            
            audit_log = AuditLog(
                user_id=user_id,
                user_email=user_email,
                user_role=user_role,
                action=action,
                category=category,
                resource_type=resource_type,
                resource_id=str(resource_id) if resource_id else None,
                resource_name=resource_name,
                description=description,
                details=details_json,
                ip_address=ip_address,
                user_agent=user_agent,
                status=status,
                error_message=error_message,
                timestamp=datetime.utcnow()
            )
            
            db.add(audit_log)
            db.commit()
            db.refresh(audit_log)
            
            logger.debug(f"Audit log created: {action} by {user_email or 'system'}")
            return audit_log
            
        except Exception as e:
            logger.error(f"Failed to create audit log: {str(e)}")
            db.rollback()
            raise
    
    @staticmethod
    def log_auth_success(
        db: Session,
        user: User,
        action: str = AuditAction.LOGIN_SUCCESS,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> AuditLog:
        """Log successful authentication"""
        return AuditService.log(
            db=db,
            action=action,
            category=AuditCategory.AUTH,
            user=user,
            description=f"User {user.email} authenticated successfully",
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            status="SUCCESS"
        )
    
    @staticmethod
    def log_auth_failure(
        db: Session,
        email: str,
        reason: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        """Log failed authentication"""
        return AuditService.log(
            db=db,
            action=AuditAction.LOGIN_FAILED,
            category=AuditCategory.AUTH,
            user_email=email,
            description=f"Authentication failed for {email}",
            error_message=reason,
            ip_address=ip_address,
            user_agent=user_agent,
            status="FAILURE"
        )
    
    @staticmethod
    def log_node_action(
        db: Session,
        action: str,
        node_id: int,
        node_name: str,
        user: Optional[User] = None,
        description: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        triggered_by: str = "user"
    ) -> AuditLog:
        """Log node-related action"""
        return AuditService.log(
            db=db,
            action=action,
            category=AuditCategory.NODE,
            user=user,
            resource_type="node",
            resource_id=str(node_id),
            resource_name=node_name,
            description=description or f"{action} on node {node_name}",
            details={**(details or {}), "triggered_by": triggered_by}
        )
    
    @staticmethod
    def log_user_action(
        db: Session,
        action: str,
        target_user_id: int,
        target_user_email: str,
        acting_user: Optional[User] = None,
        description: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> AuditLog:
        """Log user management action"""
        return AuditService.log(
            db=db,
            action=action,
            category=AuditCategory.USER,
            user=acting_user,
            resource_type="user",
            resource_id=str(target_user_id),
            resource_name=target_user_email,
            description=description or f"{action} for user {target_user_email}",
            details=details
        )
    
    @staticmethod
    def log_config_change(
        db: Session,
        node_id: int,
        node_name: str,
        user: Optional[User] = None,
        old_hash: Optional[str] = None,
        new_hash: Optional[str] = None,
        description: Optional[str] = None
    ) -> AuditLog:
        """Log configuration change"""
        return AuditService.log(
            db=db,
            action=AuditAction.CONFIG_UPDATED,
            category=AuditCategory.CONFIG,
            user=user,
            resource_type="node_config",
            resource_id=str(node_id),
            resource_name=node_name,
            description=description or f"Configuration updated for node {node_name}",
            details={"old_hash": old_hash, "new_hash": new_hash}
        )
    
    @staticmethod
    def log_system_event(
        db: Session,
        action: str,
        description: str,
        details: Optional[Dict[str, Any]] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None
    ) -> AuditLog:
        """Log system event (not user-initiated)"""
        return AuditService.log(
            db=db,
            action=action,
            category=AuditCategory.SYSTEM,
            description=description,
            details=details,
            resource_type=resource_type,
            resource_id=resource_id
        )
    
    @staticmethod
    def get_audit_logs(
        db: Session,
        category: Optional[str] = None,
        action: Optional[str] = None,
        user_id: Optional[int] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        status: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        search: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[AuditLog]:
        """
        Query audit logs with filters
        
        Args:
            db: Database session
            category: Filter by category
            action: Filter by action type
            user_id: Filter by user ID
            resource_type: Filter by resource type
            resource_id: Filter by resource ID
            status: Filter by status (SUCCESS/FAILURE)
            start_date: Filter logs after this date
            end_date: Filter logs before this date
            search: Search in description, user_email, resource_name
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            List of AuditLog entries
        """
        query = db.query(AuditLog)
        
        if category:
            query = query.filter(AuditLog.category == category)
        
        if action:
            query = query.filter(AuditLog.action == action)
        
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        
        if resource_type:
            query = query.filter(AuditLog.resource_type == resource_type)
        
        if resource_id:
            query = query.filter(AuditLog.resource_id == resource_id)
        
        if status:
            query = query.filter(AuditLog.status == status)
        
        if start_date:
            query = query.filter(AuditLog.timestamp >= start_date)
        
        if end_date:
            query = query.filter(AuditLog.timestamp <= end_date)
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                (AuditLog.description.ilike(search_term)) |
                (AuditLog.user_email.ilike(search_term)) |
                (AuditLog.resource_name.ilike(search_term)) |
                (AuditLog.action.ilike(search_term))
            )
        
        return query.order_by(desc(AuditLog.timestamp)).offset(offset).limit(limit).all()
    
    @staticmethod
    def get_audit_log_count(
        db: Session,
        category: Optional[str] = None,
        action: Optional[str] = None,
        user_id: Optional[int] = None,
        status: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        search: Optional[str] = None
    ) -> int:
        """Get total count of audit logs matching filters"""
        query = db.query(AuditLog)
        
        if category:
            query = query.filter(AuditLog.category == category)
        if action:
            query = query.filter(AuditLog.action == action)
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        if status:
            query = query.filter(AuditLog.status == status)
        if start_date:
            query = query.filter(AuditLog.timestamp >= start_date)
        if end_date:
            query = query.filter(AuditLog.timestamp <= end_date)
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                (AuditLog.description.ilike(search_term)) |
                (AuditLog.user_email.ilike(search_term)) |
                (AuditLog.resource_name.ilike(search_term)) |
                (AuditLog.action.ilike(search_term))
            )
        
        return query.count()
    
    @staticmethod
    def get_audit_summary(
        db: Session,
        hours: int = 24
    ) -> Dict[str, Any]:
        """Get summary statistics for audit logs"""
        from sqlalchemy import func
        
        since = datetime.utcnow() - timedelta(hours=hours)
        
        # Count by category
        category_counts = db.query(
            AuditLog.category,
            func.count(AuditLog.id)
        ).filter(
            AuditLog.timestamp >= since
        ).group_by(AuditLog.category).all()
        
        # Count by status
        status_counts = db.query(
            AuditLog.status,
            func.count(AuditLog.id)
        ).filter(
            AuditLog.timestamp >= since
        ).group_by(AuditLog.status).all()
        
        # Recent failures
        recent_failures = db.query(AuditLog).filter(
            AuditLog.timestamp >= since,
            AuditLog.status == "FAILURE"
        ).order_by(desc(AuditLog.timestamp)).limit(10).all()
        
        return {
            "period_hours": hours,
            "category_counts": {cat: count for cat, count in category_counts},
            "status_counts": {status: count for status, count in status_counts},
            "total_events": sum(count for _, count in category_counts),
            "failure_count": next((count for status, count in status_counts if status == "FAILURE"), 0),
            "recent_failures": [
                {
                    "id": f.id,
                    "action": f.action,
                    "user_email": f.user_email,
                    "error_message": f.error_message,
                    "timestamp": f.timestamp.isoformat() if f.timestamp else None
                }
                for f in recent_failures
            ]
        }
