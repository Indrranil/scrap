# app/config/permissions.py
ROLE_PERMISSIONS = {
    "app_admin": [
        "create:pipeline",
        "read:pipeline",
        "update:pipeline",
        "delete:pipeline",
        "create:machine",
        "read:machine",
        "update:machine",
        "delete:machine",
        "create:application",
        "read:application",
        "update:application",
        "delete:application"
    ],
    "app_user": [
        "read:pipeline",
        "read:machine",
        "read:application",
        "create:pipeline_input",
        "update:pipeline_input"
    ]
}