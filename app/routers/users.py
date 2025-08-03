from io import StringIO
from os import getenv
from typing import Any, Dict, List

import pandas as pd
from dotenv import load_dotenv
from fastapi import APIRouter, File, HTTPException, UploadFile

from app.schemas.user import UserCreate, UserResponse, UsersListResponse, UserUpdate
from keycloak import KeycloakAdmin  # type: ignore

router = APIRouter(prefix="/v1/users", tags=["users"])

load_dotenv()

# Initialize Keycloak Admin
keycloak_admin = KeycloakAdmin(
    server_url=str(getenv("KEYCLOAK_URL")),
    username="admin",
    password=str(getenv("KEYCLOAK_PASSWORD")),
    realm_name="master",
    verify=True,
)

keycloak_admin.realm_name = "app-realm"  # type: ignore


@router.post("/")
async def create_user(user_data: UserCreate):
    try:
        # Create user without roles first
        existing_users = keycloak_admin.get_users({"username": user_data.username})
        if existing_users:
            raise HTTPException(
                status_code=409,
                detail=f"Username '{user_data.username}' already exists",
            )

        # Check if email already exists
        existing_email_users = keycloak_admin.get_users({"email": user_data.email})
        if existing_email_users:
            raise HTTPException(
                status_code=409, detail=f"Email '{user_data.email}' already exists"
            )
        user = {
            "username": user_data.username,
            "email": user_data.email,
            "enabled": True,
            "firstName": user_data.firstName,
            "lastName": user_data.lastName,
            "credentials": [
                {"type": "password", "value": user_data.password, "temporary": False}
            ],
        }

        # Create user
        user_id = keycloak_admin.create_user(user)

        # Add roles if specified
        if user_data.roles and len(user_data.roles) > 0:
            try:
                # Get available roles
                available_roles = keycloak_admin.get_realm_roles()
                role_dict = {role["name"]: role for role in available_roles}

                # Filter and assign existing roles
                roles_to_assign = []
                for role_name in user_data.roles:
                    if role_name in role_dict:
                        roles_to_assign.append(role_dict[role_name])

                if roles_to_assign:
                    keycloak_admin.assign_realm_roles(
                        user_id=user_id, roles=roles_to_assign
                    )

            except Exception as role_error:
                print(f"Error assigning roles: {str(role_error)}")
                # Continue even if role assignment fails

        return {"message": "User created successfully", "user_id": user_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/bulk")
async def bulk_create_users(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        df = pd.read_csv(StringIO(contents.decode("utf-8")))

        # Validate required columns
        required_columns = ["username", "email", "firstName", "lastName", "password"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required columns: {', '.join(missing_columns)}",
            )

        results: Dict[str, List[Dict[str, Any]]] = {"successful": [], "failed": []}

        for _, row in df.iterrows():
            try:
                # Validate each row using Pydantic model
                user_data = UserCreate(
                    username=row["username"],
                    email=row["email"],
                    firstName=row["firstName"],
                    lastName=row["lastName"],
                    password=row["password"],
                )

                user = {
                    "username": user_data.username,
                    "email": user_data.email,
                    "firstName": user_data.firstName,
                    "lastName": user_data.lastName,
                    "enabled": True,
                    "credentials": [
                        {
                            "type": "password",
                            "value": user_data.password,
                            "temporary": False,
                        }
                    ],
                }

                user_id = keycloak_admin.create_user(user)
                results["successful"].append(
                    {"username": user_data.username, "id": user_id}
                )

            except Exception as e:
                results["failed"].append(
                    {"username": row.get("username", "Unknown"), "error": str(e)}
                )

        return results
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/all", response_model=UsersListResponse)
async def get_all_users():
    try:
        users = keycloak_admin.get_users({})

        # Format user data according to response model
        formatted_users = [
            UserResponse(
                id=user.get("id", ""),
                username=user.get("username", ""),
                firstName=user.get("firstName", ""),
                lastName=user.get("lastName", ""),
                email=user.get("email", ""),
                enabled=user.get("enabled", True),
            )
            for user in users
            if user.get("username") != "admin"  # Exclude admin user
        ]

        return {"total": len(formatted_users), "users": formatted_users}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{username}", response_model=UserResponse)
async def get_user_by_username(username: str):
    try:
        # Get user by username
        users = keycloak_admin.get_users({"username": username})

        if not users:
            raise HTTPException(status_code=404, detail=f"User '{username}' not found")

        user = users[0]  # Get first user since username is unique

        return UserResponse(
            id=user.get("id", ""),
            username=user.get("username", ""),
            firstName=user.get("firstName", ""),
            lastName=user.get("lastName", ""),
            email=user.get("email", ""),
            enabled=user.get("enabled", True),
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{username}")
async def update_user_by_username(username: str, user_data: UserUpdate):
    try:
        # Get user by username
        users = keycloak_admin.get_users({"username": username})

        if not users:
            raise HTTPException(status_code=404, detail=f"User '{username}' not found")

        user_id = users[0]["id"]  # Get ID of the user to update

        # Check if new username already exists (if username is being updated)
        if user_data.username and user_data.username != username:
            existing_users = keycloak_admin.get_users({"username": user_data.username})
            if existing_users:
                raise HTTPException(
                    status_code=409,
                    detail=f"Username '{user_data.username}' already exists",
                )

        # Prepare update payload
        update_payload = {}

        if user_data.username is not None:
            update_payload["username"] = user_data.username
        if user_data.email is not None:
            # Check if new email already exists
            if user_data.email != users[0].get("email"):
                existing_email_users = keycloak_admin.get_users(
                    {"email": user_data.email}
                )
                if existing_email_users:
                    raise HTTPException(
                        status_code=409,
                        detail=f"Email '{user_data.email}' already exists",
                    )
            update_payload["email"] = user_data.email
        if user_data.firstName is not None:
            update_payload["firstName"] = user_data.firstName
        if user_data.lastName is not None:
            update_payload["lastName"] = user_data.lastName

        # Update password if provided
        if user_data.password:
            update_payload["credentials"] = [  # type: ignore
                {"type": "password", "value": user_data.password, "temporary": False}
            ]

        # Update user details
        keycloak_admin.update_user(user_id=user_id, payload=update_payload)

        # Handle role updates if provided
        if user_data.roles:
            try:
                # Get current user roles
                current_roles = keycloak_admin.get_realm_roles_of_user(user_id=user_id)
                current_role_names = [role["name"] for role in current_roles]

                # Get all available realm roles
                available_roles = keycloak_admin.get_realm_roles()
                available_role_dict = {role["name"]: role for role in available_roles}

                # Determine roles to add and remove
                roles_to_add = []
                invalid_roles = []
                for role_name in user_data.roles:
                    if role_name not in current_role_names:
                        if role_name in available_role_dict:
                            roles_to_add.append(available_role_dict[role_name])
                        else:
                            invalid_roles.append(role_name)

                roles_to_remove = []
                for role_name in current_role_names:
                    if (
                        role_name not in user_data.roles
                        and role_name in available_role_dict
                    ):
                        roles_to_remove.append(available_role_dict[role_name])

                # Remove old roles
                if roles_to_remove:
                    keycloak_admin.delete_realm_roles_of_user(
                        user_id=user_id, roles=roles_to_remove
                    )

                # Add new roles
                if roles_to_add:
                    keycloak_admin.assign_realm_roles(
                        user_id=user_id, roles=roles_to_add
                    )

                if invalid_roles:
                    print(
                        f"Warning: Following roles do not exist: {', '.join(invalid_roles)}"
                    )

            except Exception as role_error:
                print(f"Error updating roles: {str(role_error)}")

        # Get updated user details
        updated_user = keycloak_admin.get_user(user_id)
        updated_roles = keycloak_admin.get_realm_roles_of_user(user_id=user_id)

        return {
            "message": "User updated successfully",
            "user": {
                "id": user_id,
                "username": updated_user.get("username"),
                "email": updated_user.get("email"),
                "firstName": updated_user.get("firstName"),
                "lastName": updated_user.get("lastName"),
                "roles": [role["name"] for role in updated_roles],
            },
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{username}")
async def delete_user_by_username(username: str):
    try:
        # Get user by username
        users = keycloak_admin.get_users({"username": username})

        if not users:
            raise HTTPException(status_code=404, detail=f"User '{username}' not found")

        user_id = users[0]["id"]  # Get ID of the user to delete

        # Delete user
        keycloak_admin.delete_user(user_id=user_id)

        return {"message": f"User '{username}' deleted successfully"}

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
