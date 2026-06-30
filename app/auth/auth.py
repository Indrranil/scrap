from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.auth.jwt_auth import decode_access_token


class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.public_paths = {
            "/",
            "/docs",
            "/openapi.json",
            "/redoc",
            "/v1/auth/login",
        }

    async def dispatch(self, request: Request, call_next):
        if (
            request.url.path in self.public_paths
            or request.method == "OPTIONS"
        ):
            return await call_next(request)

        try:
            auth_header = request.headers.get("Authorization")
            if not auth_header:
                raise HTTPException(
                    status_code=401, detail="Missing authorization header"
                )

            scheme, token = auth_header.split()
            if scheme.lower() != "bearer":
                raise HTTPException(
                    status_code=401, detail="Invalid authentication scheme"
                )

            token_data = decode_access_token(token)
            request.state.user = {
                "id": token_data.get("sub"),
                "role": token_data.get("role"),
                "plant_id": token_data.get("plant_id"),
                "scrapeyard_id": token_data.get("scrapeyard_id"),
                "gso_id": token_data.get("gso_id"),
                "security_id": token_data.get("security_id"),
            }
            return await call_next(request)

        except HTTPException as e:
            return JSONResponse(status_code=e.status_code, content={"detail": e.detail})
        except ValueError as e:
            return JSONResponse(status_code=401, content={"detail": str(e)})
