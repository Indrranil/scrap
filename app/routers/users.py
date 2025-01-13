from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from keycloak import KeycloakAdmin
import pandas as pd
from io import StringIO
import json
from schemas.user import UserCreate,UsersListResponse,UserResponse

router = APIRouter(prefix="/v1/users", tags=["users"])

# Initialize Keycloak Admin
keycloak_admin = KeycloakAdmin(
    server_url="http://localhost:8080",
    username="admin",
    password="admin",
    realm_name="master",
    verify=True
)

keycloak_admin.realm_name = "app-realm"

@router.post("/")
async def create_user(user_data: UserCreate):
    try:
        # Create user without roles first
        user = {
            "username": user_data["username"],
            "email": user_data["email"],
            "enabled": True,
            "firstName": user_data["firstName"],
            "lastName": user_data["lastName"],
            "credentials": [{
                "type": "password",
                "value": user_data["password"],
                "temporary": False
            }]
        }
        
        # Create user
        user_id = keycloak_admin.create_user(user)
        
        # Add roles if specified
        if "roles" in user_data and user_data["roles"]:
            try:
                # Get available roles
                available_roles = keycloak_admin.get_realm_roles()
                role_dict = {role['name']: role for role in available_roles}
                
                # Filter and assign existing roles
                roles_to_assign = []
                for role_name in user_data["roles"]:
                    if role_name in role_dict:
                        roles_to_assign.append(role_dict[role_name])
                
                if roles_to_assign:
                    keycloak_admin.assign_realm_roles(user_id=user_id, roles=roles_to_assign)
            
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
        df = pd.read_csv(StringIO(contents.decode('utf-8')))
        
        # Validate required columns
        required_columns = ['username', 'email', 'firstName', 'lastName', 'password']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise HTTPException(
                status_code=400, 
                detail=f"Missing required columns: {', '.join(missing_columns)}"
            )
        
        results = {
            "successful": [],
            "failed": []
        }
        
        for _, row in df.iterrows():
            try:
                # Validate each row using Pydantic model
                user_data = UserCreate(
                    username=row['username'],
                    email=row['email'],
                    firstName=row['firstName'],
                    lastName=row['lastName'],
                    password=row['password']
                )
                
                user = {
                    "username": user_data.username,
                    "email": user_data.email,
                    "firstName": user_data.firstName,
                    "lastName": user_data.lastName,
                    "enabled": True,
                    "credentials": [{
                        "type": "password",
                        "value": user_data.password,
                        "temporary": False
                    }]
                }
                
                user_id = keycloak_admin.create_user(user)
                results["successful"].append({
                    "username": user_data.username, 
                    "id": user_id
                })
                
            except Exception as e:
                results["failed"].append({
                    "username": row.get('username', 'Unknown'),
                    "error": str(e)
                })
                
        return results
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=UsersListResponse)
async def get_all_users():
    try:
        users = keycloak_admin.get_users()
        
        # Format user data according to response model
        formatted_users = [
            UserResponse(
                username=user.get('username', ''),
                firstName=user.get('firstName', ''),
                lastName=user.get('lastName', '')
            )
            for user in users
            if user.get('username') != 'admin'
        ]
        
        return {
            "total": len(formatted_users),
            "users": formatted_users
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))