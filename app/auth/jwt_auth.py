from datetime import datetime, timedelta, timezone
from os import getenv
from typing import Any, Dict, Optional

import bcrypt
from jose import JWTError, jwt

JWT_ALGORITHM = "HS256"


def _get_jwt_secret() -> str:
    return getenv("JWT_SECRET", "change-me-in-production")


def _get_expire_hours() -> int:
    return int(getenv("JWT_EXPIRE_HOURS", "24"))


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


def create_access_token(
    subject: str,
    role: str,
    plant_id: Optional[int] = None,
    scrapeyard_id: Optional[int] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(hours=_get_expire_hours())
    )
    payload: Dict[str, Any] = {
        "sub": subject,
        "role": role,
        "exp": int(expire.timestamp()),
    }
    if plant_id is not None:
        payload["plant_id"] = plant_id
    if scrapeyard_id is not None:
        payload["scrapeyard_id"] = scrapeyard_id
    return jwt.encode(payload, _get_jwt_secret(), algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> Dict[str, Any]:
    try:
        return jwt.decode(token, _get_jwt_secret(), algorithms=[JWT_ALGORITHM])
    except JWTError as e:
        raise ValueError(str(e)) from e
