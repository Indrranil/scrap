from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth.auth import AuthMiddleware
from app.database.connection import engine, Base
# Import routers
from app.routers.application import router as application_router
from app.routers.device import router as device_router
from app.routers.pipeline import router as pipeline_router
from app.routers.pipeline_session import router as pipeline_session_router
from app.routers.pipeline_session_output import router as pipeline_session_output_router
from app.routers.pipeline_session_output_unit import router as pipeline_session_output_unit_router
from app.routers.product import router as product_router
from app.routers.general_property import router as property_router
from app.routers.signin import router as signin_router
from app.routers.users import router as user_router
from app.routers.pipeline_input import router as pipeline_input_router

# ... other router imports ...

app = FastAPI(title="Machine Management API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auth middleware
app.add_middleware(AuthMiddleware)

# Include routers
app.include_router(application_router)
app.include_router(device_router)
app.include_router(pipeline_router)
app.include_router(pipeline_session_router)
app.include_router(pipeline_session_output_router)
app.include_router(pipeline_session_output_unit_router)
app.include_router(product_router)
app.include_router(property_router)
app.include_router(signin_router)
app.include_router(user_router)
app.include_router(pipeline_input_router)
# ... other routers ...

# Create database tables
Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
