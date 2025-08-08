import logging
import os

import requests
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator

load_dotenv()

router = APIRouter(prefix="/v1/auth", tags=["authentication"])


class SignInRequest(BaseModel):
    username: str
    password: str

    @field_validator("username", "password")
    def validate_credentials(cls, v):
        if not v or not v.strip():
            raise ValueError("This field cannot be empty")
        return v


@router.post("/signin")
async def signin(credentials: SignInRequest):
    try:
        keycloak_url = os.getenv("KEYCLOAK_URL")
        if not keycloak_url:
            raise HTTPException(
                status_code=401,
                detail="Authentication failed: Keycloak URL not configured",
            )

        # Make request to Keycloak
        try:
            response = requests.post(
                f"{keycloak_url}/realms/{os.getenv('KEYCLOAK_REALM')}/protocol/openid-connect/token",
                data={
                    "client_id": os.getenv("KEYCLOAK_CLIENT_ID"),
                    "client_secret": os.getenv("KEYCLOAK_CLIENT_SECRET"),
                    "grant_type": "password",
                    "username": credentials.username,
                    "password": credentials.password,
                },
                timeout=10,
            )
        except Exception as e:
            raise HTTPException(
                status_code=401, detail=f"Authentication failed: {str(e)}"
            )

        if response.status_code == 500:
            raise HTTPException(
                status_code=401, detail="Authentication failed: Keycloak server error"
            )

        if response.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        token_data = response.json()
        return {
            "access_token": token_data["access_token"],
            "token_type": token_data["token_type"],
            "expires_in": token_data["expires_in"],
            "refresh_token": token_data["refresh_token"],
        }

    except ValueError as ve:
        # Validation errors from pydantic
        raise HTTPException(status_code=422, detail=str(ve))
    except HTTPException as he:
        raise he
    except Exception as e:
        logging.error(f"Login error: {str(e)}")
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")
