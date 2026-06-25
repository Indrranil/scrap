from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.auth import LoginRequest, LoginResponse
from app.services.auth import auth_service

router = APIRouter(prefix="/v1/auth", tags=["authentication"])


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate plant or admin user and return JWT."""
    return auth_service.login(db, request)


@router.post("/logout")
def logout():
    """Client-side token discard."""
    return {"message": "Logged out successfully"}
