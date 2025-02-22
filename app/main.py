from fastapi import FastAPI
from database.connection import engine, Base
from auth.auth import AuthMiddleware
from fastapi.middleware.cors import CORSMiddleware

# Import routers
from routers.pipeline_session import router as pipeline_session_router
from routers.signin import router as signin_router
from routers.pipeline_session_output import router as pipeline_session_output_router
from routers.pipeline_session_output_unit import router as pipeline_session_output_unit_router
from routers.application import router as application_router
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
app.include_router(pipeline_session_router)
app.include_router(signin_router)
app.include_router(pipeline_session_output_router)
app.include_router(pipeline_session_output_unit_router)
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