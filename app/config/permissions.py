from typing import Set, Dict

ROLE_PERMISSIONS: Dict[str, Set[str]] = {
    "app_admin": {"all"},
    "app_user": {
        "pipeline_session:read",
        "pipeline_session:create"
    }
}