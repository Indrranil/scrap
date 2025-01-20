from fastapi import FastAPI
from database.connection import engine, Base
from auth.auth import KeycloakMiddleware
from fastapi.middleware.cors import CORSMiddleware

# ROUTERS 
from routers.product_upload import router as product_upload_router
from routers.device import router as device_router
from routers.users import router as user_router
from routers.property import router as property_router
from routers.pipeline_session import router as pipeline_session_router
from routers.application import router as application_router
from routers.pipeline_session_output import router as pipeline_session_output_router
from routers.pipeline_session_output_unit import router as pipeline_session_output_unit_router


app = FastAPI(title="Machine Management API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# app.add_middleware(KeycloakMiddleware)

app.include_router(pipeline_session_router)
app.include_router(pipeline_session_output_router)
app.include_router(pipeline_session_output_unit_router)
app.include_router(product_upload_router)
app.include_router(device_router)
app.include_router(user_router)
app.include_router(property_router)
app.include_router(application_router)


Base.metadata.create_all(bind=engine)

