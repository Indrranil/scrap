from enum import Enum
from typing import Set, List, Dict
from fastapi import Request, Depends
from .auth import AuthorizationError, get_current_user
import logging

logger = logging.getLogger(__name__)

class Permission(str, Enum):
    # Pipeline Session permissions
    PIPELINE_SESSION_CREATE = "pipeline_session:create"
    PIPELINE_SESSION_READ = "pipeline_session:read"
    PIPELINE_SESSION_UPDATE = "pipeline_session:update"
    PIPELINE_SESSION_DELETE = "pipeline_session:delete"
    
    # Add other permissions as needed
    ALL = "all"

class RBACHandler:
    def __init__(self, role_permissions: Dict[str, Set[str]]):
        self.role_permissions = role_permissions

    def _has_permission(self, user_roles: List[str], required_permission: str) -> bool:
        """Check if user has the required permission based on their roles"""
        if not user_roles:
            return False

        user_permissions = set()
        for role in user_roles:
            role_perms = self.role_permissions.get(role, set())
            user_permissions.update(role_perms)
            
        return Permission.ALL.value in user_permissions or required_permission in user_permissions

    def require_permission(self, required_permission: str):
        """Dependency creator for permission-based access control"""
        async def permission_dependency(
            user: Dict = Depends(get_current_user)
        ) -> bool:
            user_roles = user.get("roles", [])
            
            if not self._has_permission(user_roles, required_permission):
                logger.warning(
                    f"Permission denied: User roles {user_roles} "
                    f"do not have required permission {required_permission}"
                )
                raise AuthorizationError(
                    f"Insufficient permissions. Required: {required_permission}"
                )
            return True
            
        return permission_dependency

# Initialize RBAC handler with role-permission mappings
def init_rbac(role_permissions: Dict[str, Set[str]]) -> RBACHandler:
    """Initialize RBAC handler with role-permission mappings"""
    return RBACHandler(role_permissions)