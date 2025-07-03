from os import getenv

import jwt
from dotenv import load_dotenv
from fastapi import Request, HTTPException
from keycloak.keycloak_openid import KeycloakOpenID
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

load_dotenv()


class KeycloakAuth:
    def __init__(self):
        self.keycloak = KeycloakOpenID(
            server_url=str(getenv("KEYCLOAK_URL")),
            client_id=str(getenv("KEYCLOAK_CLIENT_ID")),
            realm_name=str(getenv("KEYCLOAK_REALM")),
            client_secret_key=str(getenv("KEYCLOAK_CLIENT_SECRET"))
        )
        self._public_key = None

    def get_public_key(self):
        if not self._public_key:
            self._public_key = f"-----BEGIN PUBLIC KEY-----\n{self.keycloak.public_key()}\n-----END PUBLIC KEY-----"
        return self._public_key

    def verify_token(self, token: str):
        try:
            return jwt.decode(
                token,
                self.get_public_key(),
                algorithms=["RS256"],
                options={"verify_aud": False}
            )
        except Exception as e:
            raise HTTPException(status_code=401, detail=str(e))


class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.auth = KeycloakAuth()
        self.public_paths = {"/docs", "/openapi.json", "/redoc", "/v1/auth/signin"}

    async def dispatch(self, request: Request, call_next):
        if request.url.path in self.public_paths or request.method == "OPTIONS" or request.url.path.startswith("/frame"):
            return await call_next(request)

        try:
            auth_header = request.headers.get("Authorization")
            if not auth_header:
                raise HTTPException(status_code=401, detail="Missing authorization header")

            scheme, token = auth_header.split()
            if scheme.lower() != "bearer":
                raise HTTPException(status_code=401, detail="Invalid authentication scheme")

            token_data = self.auth.verify_token(token)
            request.state.user = {
                "id": token_data.get("sub"),
                "roles": token_data.get("realm_access", {}).get("roles", [])
            }

            return await call_next(request)

        except HTTPException as e:
            return JSONResponse(status_code=e.status_code, content={"detail": e.detail})


def require_roles(allowed_roles: list[str]):
    def dependency(request: Request):
        user_roles = request.state.user.get("roles", [])
        if not any(role in user_roles for role in allowed_roles):
            raise HTTPException(
                status_code=403,
                detail="Not enough permissions"
            )
        return True

    return dependency
