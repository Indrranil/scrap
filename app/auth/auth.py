# app/middleware/auth.py
from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from keycloak import KeycloakOpenID
import jwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

class KeycloakMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.keycloak_openid = KeycloakOpenID(
            server_url="http://localhost:8080/",
            client_id="fastapi-client",
            realm_name="app-realm",
            client_secret_key="lBgpLiCu6PoJTSjExg4GGu0fUGOPDV3a"
        )
        self.bearer = HTTPBearer()

    async def dispatch(self, request: Request, call_next):
        try:
            if request.url.path in ["/docs", "/openapi.json"]:  # Skip auth for docs
                return await call_next(request)

            auth_header = request.headers.get("Authorization")
            if not auth_header:
                return JSONResponse(
                    status_code=401,
                    content={"detail": "No authorization header"}
                )

            scheme, token = auth_header.split()
            if scheme.lower() != "bearer":
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Invalid authentication scheme"}
                )

            token_info = self.keycloak_openid.introspect(token)
            if not token_info.get("active", False):
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Invalid token"}
                )

            # Store user info in request state
            request.state.user_roles = token_info.get("realm_access", {}).get("roles", [])
            request.state.user_id = token_info.get("sub")

            return await call_next(request)

        except Exception as e:
            return JSONResponse(
                status_code=401,
                content={"detail": f"Authentication failed: {str(e)}"}
            )