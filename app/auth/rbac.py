from functools import wraps
from fastapi import HTTPException, Request, Depends
from config.permissions import ROLE_PERMISSIONS

def has_permission(user_roles: list, required_permission: str) -> bool:
    user_permissions = []
    for role in user_roles:
        user_permissions.extend(ROLE_PERMISSIONS.get(role, []))
    return (required_permission in user_permissions) or ('all' in user_permissions)

def require_permission(required_permission: str):
    def dependency(request: Request):
        user_roles = getattr(request.state, "user_roles", [])
        if not has_permission(user_roles, required_permission):
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient permissions. Required: {required_permission}"
            )
        return True
    return dependency