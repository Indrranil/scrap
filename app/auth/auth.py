from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer
from keycloak import KeycloakOpenID
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from functools import wraps
import jwt

class KeycloakAuth:
    def __init__(self):
        self.keycloak = KeycloakOpenID(
            server_url="http://localhost:8080/",
            client_id="fastapi-client",
            realm_name="app-realm",
            client_secret_key="IRK0F8WoiZgBvOQtKHdXLG9Q9AjB602g"
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
        self.public_paths = {"/docs", "/openapi.json", "/redoc","/v1/auth/signin"}

    async def dispatch(self, request: Request, call_next):
        if request.url.path in self.public_paths:
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
        except Exception as e:
            return JSONResponse(status_code=401, content={"detail": str(e)})

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