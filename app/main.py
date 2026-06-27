from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from starlette import status

from app.auth.auth import AuthMiddleware
from app.routers.auth import router as auth_router
from app.routers.employees import router as employees_router
from app.routers.images import router as images_router
from app.routers.items import router as items_router
from app.routers.plants import router as plants_router
from app.routers.reporting import router as reporting_router
from app.routers.sales import router as sales_router
from app.routers.scrapeyard_admin import router as scrapeyard_admin_router
from app.routers.scrapeyard import router as scrapeyard_router
from app.routers.shopfloor import router as shopfloor_router
from app.routers.transfers import router as transfers_router
from app.routers.vendors import router as vendors_router

app = FastAPI(
    title="DigiScrapyard API",
    description="Backend API for DigiScrapyard scrap management",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(AuthMiddleware)

app.include_router(auth_router)
app.include_router(employees_router)
app.include_router(transfers_router)
app.include_router(shopfloor_router)
app.include_router(scrapeyard_router)
app.include_router(scrapeyard_admin_router)
app.include_router(plants_router)
app.include_router(items_router)
app.include_router(vendors_router)
app.include_router(reporting_router)
app.include_router(sales_router)
app.include_router(images_router)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    openapi_schema.setdefault("components", {}).setdefault("securitySchemes", {})[
        "BearerAuth"
    ] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
    }
    for path in openapi_schema.get("paths", {}).values():
        for method in path.values():
            if isinstance(method, dict) and method.get("operationId"):
                if "/auth/login" not in str(method):
                    method.setdefault("security", [{"BearerAuth": []}])
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


@app.get("/", status_code=status.HTTP_200_OK)
def is_running():
    return {"status": "DigiScrapyard API is running"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",  # nosec B104
        port=8000,
        reload=True,
        log_level="info",
    )
