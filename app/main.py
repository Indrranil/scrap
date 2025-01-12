from fastapi import FastAPI
from database.connection import engine, Base
from auth.auth import KeycloakMiddleware
from fastapi.middleware.cors import CORSMiddleware

from routers.application_container import router as application_container_router
from routers.application_output_type import router as application_output_type_router
from routers.application_session_unit_output import router as application_session_unit_output_router
from routers.application_session_unit import router as application_session_unit_router
from routers.application_session import router as application_session_router
from routers.application import router as application_router
from routers.application_status_log import router as application_status_log_router
from routers.general_property import router as general_property_router
from routers.machine import router as machine_router
from routers.pipeline import router as pipeline_router
from routers.pipeline_input_referrer import router as pipeline_input_referrer_router
from routers.pipeline_input import router as pipeline_input_router
from routers.product_upload import router as product_upload_router
from routers.device import router as device_router



app = FastAPI(title="Machine Management API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# app.add_middleware(KeycloakMiddleware)

# ROUTERS
# app.include_router(application_container_router)
# app.include_router(application_output_type_router)
# app.include_router(application_session_unit_output_router)
# app.include_router(application_session_unit_router)
# app.include_router(application_session_router)
# app.include_router(application_router)
# app.include_router(application_status_log_router)
# app.include_router(general_property_router)
# app.include_router(machine_router)
# app.include_router(pipeline_router)
# app.include_router(pipeline_input_referrer_router)
# app.include_router(pipeline_input_router)

app.include_router(product_upload_router)
app.include_router(device_router)

Base.metadata.create_all(bind=engine)

