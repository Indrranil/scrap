from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging
from dotenv import load_dotenv
import os
import requests

load_dotenv()

router = APIRouter(prefix="/v1/auth", tags=["authentication"])

class SignInRequest(BaseModel):
    username: str
    password: str

@router.post("/signin")
async def signin(credentials: SignInRequest):
    try:
        # Direct token request to Keycloak
        response = requests.post(
            f"{os.getenv('KEYCLOAK_URL')}realms/app-realm/protocol/openid-connect/token",
            data={
                "client_id": os.getenv("KEYCLOAK_CLIENT_ID"),
                "client_secret": os.getenv("KEYCLOAK_CLIENT_SECRET"),
                "grant_type": "password",
                "username": credentials.username,
                "password": credentials.password
            }
        )
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=401,
                detail="Invalid credentials"
            )
            
        token_data = response.json()
        return {
            "access_token": token_data["access_token"],
            "token_type": token_data["token_type"],
            "expires_in": token_data["expires_in"],
            "refresh_token": token_data["refresh_token"]
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logging.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=401,
            detail=f"Authentication failed: {str(e)}"
        )