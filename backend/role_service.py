from sqlalchemy.orm import Session
from typing import List
from functools import wraps
from fastapi import HTTPException, status
import logging

from models import User, UserRole

logger = logging.getLogger(__name__)

class RoleService:
    
    @staticmethod
    def map_keycloak_roles_to_app_role(keycloak_roles: List[str]) -> UserRole:
        """Map Keycloak roles to application role"""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"🎭 ROLE MAPPING - Input roles: {keycloak_roles}")
        
        # Convert all roles to lowercase for case-insensitive comparison
        lower_roles = [role.lower() for role in keycloak_roles]
        logger.info(f"🔤 Lowercase roles: {lower_roles}")
        
        # Check for admin role first (highest priority)
        admin_matches = [role for role in lower_roles if role in ['admin', 'administrator']]
        if admin_matches:
            logger.info(f"👑 ADMIN role detected! Matching roles: {admin_matches}")
            return UserRole.ADMIN
        
        # Check for devops role
        devops_matches = [role for role in lower_roles if role in ['devops', 'dev-ops']]
        if devops_matches:
            logger.info(f"🛠️ DEVOPS role detected! Matching roles: {devops_matches}")
            return UserRole.DEVOPS
        
        # Default to user role for all other cases
        logger.info(f"👤 No special roles found, defaulting to USER role")
        return UserRole.USER
    
    @staticmethod
    def has_role(user: User, required_role: UserRole) -> bool:
        """Check if user has required role or higher"""
        role_hierarchy = {
            UserRole.USER: 1,
            UserRole.DEVOPS: 2,
            UserRole.ADMIN: 3
        }
        
        user_level = role_hierarchy.get(user.role, 0)
        required_level = role_hierarchy.get(required_role, 0)
        
        return user_level >= required_level
    
    @staticmethod
    def require_role(required_role: UserRole):
        """Decorator to require specific role for route access"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Extract current_user from kwargs
                current_user = kwargs.get('current_user')
                if not current_user:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Authentication required"
                    )
                
                if not RoleService.has_role(current_user, required_role):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Access denied. Required role: {required_role.value}"
                    )
                
                return func(*args, **kwargs)
            return wrapper
        return decorator
    
    @staticmethod
    def get_accessible_routes(user: User) -> List[str]:
        """Get list of routes accessible to user based on their role"""
        routes = {
            UserRole.USER: [
                "/",
                "/analytics/system",
                "/analytics/pools"
            ],
            UserRole.DEVOPS: [
                "/",
                "/nodes",
                "/analytics/system",
                "/analytics/pools",
                "/nodes/*",
                "/metrics"
            ],
            UserRole.ADMIN: [
                "/",
                "/nodes", 
                "/admin/*",
                "/analytics/system",
                "/analytics/pools",
                "/nodes/*",
                "/metrics",
                "/schedules"
            ]
        }
        
        accessible = []
        for role, role_routes in routes.items():
            if RoleService.has_role(user, role):
                accessible.extend(role_routes)
        
        return list(set(accessible))  # Remove duplicates

# Dependency functions for FastAPI
def require_admin():
    """Dependency to require admin role"""
    return RoleService.require_role(UserRole.ADMIN)

def require_devops():
    """Dependency to require devops role or higher"""
    return RoleService.require_role(UserRole.DEVOPS)

def require_user():
    """Dependency to require user role or higher (any authenticated user)"""
    return RoleService.require_role(UserRole.USER)