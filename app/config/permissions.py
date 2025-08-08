from typing import Dict, Set

# Dictionary mapping user roles to their permissions
ROLE_PERMISSIONS = {
    "app_admin": {
        # Pipeline Session Permissions
        "pipeline_session:create",
        "pipeline_session:read",
        "pipeline_session:update",
        "pipeline_session:delete",
        # Pipeline Session Output Permissions
        "pipeline_session_output:create",
        "pipeline_session_output:read",
        "pipeline_session_output:update",
        "pipeline_session_output:delete",
        # Pipeline Session Output Unit Permissions
        "pipeline_session_output_unit:create",
        "pipeline_session_output_unit:read",
        "pipeline_session_output_unit:update",
        "pipeline_session_output_unit:delete",
        # Device Permissions
        "device:create",
        "device:read",
        "device:update",
        "device:delete",
        # Property Permissions
        "property:create",
        "property:read",
        "property:update",
        "property:delete",
        # Application Permissions
        "application:create",
        "application:read",
        "application:update",
        "application:delete",
        # Product Upload Permissions
        "product:upload",
        "product:read",
        "product:update",
        "product:delete",
        # User Management
        "user:create",
        "user:read",
        "user:update",
        "user:delete",
    },
    "app_user": {
        # Pipeline Session Permissions
        "pipeline_session:read",
        # Pipeline Session Output Permissions
        "pipeline_session_output:read",
        # Pipeline Session Output Unit Permissions
        "pipeline_session_output_unit:read",
        # Device Permissions
        "device:read",
        # Property Permissions
        "property:read",
        # Application Permissions
        "application:read",
        # Product Permissions
        "product:read",
    },
}

# Permission descriptions for documentation
PERMISSION_DESCRIPTIONS = {
    "pipeline_session:create": "Create new pipeline sessions",
    "pipeline_session:read": "View pipeline sessions",
    "pipeline_session:update": "Update existing pipeline sessions",
    "pipeline_session:delete": "Delete pipeline sessions",
    "pipeline_session_output:create": "Create new pipeline session outputs",
    "pipeline_session_output:read": "View pipeline session outputs",
    "pipeline_session_output:update": "Update existing pipeline session outputs",
    "pipeline_session_output:delete": "Delete pipeline session outputs",
    "pipeline_session_output_unit:create": "Create new pipeline session output units",
    "pipeline_session_output_unit:read": "View pipeline session output units",
    "pipeline_session_output_unit:update": "Update existing pipeline session output units",
    "pipeline_session_output_unit:delete": "Delete pipeline session output units",
    "device:create": "Create new devices",
    "device:read": "View devices",
    "device:update": "Update existing devices",
    "device:delete": "Delete devices",
    "property:create": "Create new properties",
    "property:read": "View properties",
    "property:update": "Update existing properties",
    "property:delete": "Delete properties",
    "application:create": "Create new applications",
    "application:read": "View applications",
    "application:update": "Update existing applications",
    "application:delete": "Delete applications",
    "product:upload": "Upload new products",
    "product:read": "View products",
    "product:update": "Update existing products",
    "product:delete": "Delete products",
    "user:create": "Create new users",
    "user:read": "View users",
    "user:update": "Update existing users",
    "user:delete": "Delete users",
}


# Helper function to check if a user has a specific permission
def has_permission(user_roles: list, required_permission: str) -> bool:
    user_permissions = set()
    for role in user_roles:
        user_permissions.update(ROLE_PERMISSIONS.get(role, set()))
    return required_permission in user_permissions


# Helper function to get all permissions for a role
def get_role_permissions(role: str) -> set:
    return ROLE_PERMISSIONS.get(role, set())


# Helper function to get roles that have a specific permission
def get_roles_with_permission(permission: str) -> list:
    return [
        role
        for role, permissions in ROLE_PERMISSIONS.items()
        if permission in permissions
    ]
