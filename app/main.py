import time
import uuid

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette import status
from starlette.websockets import WebSocket, WebSocketDisconnect

from app.auth.auth import AuthMiddleware
from app.database.connection import Base, engine
from app.routers.admin import router as admin_router
from app.routers.analytics import router as analytics_router
# Import routers
from app.routers.application import router as application_router
from app.routers.device import router as device_router
from app.routers.general_property import router as property_router
from app.routers.images import router as images_router
from app.routers.pipeline import router as pipeline_router
from app.routers.pipeline_input import router as pipeline_input_router
from app.routers.pipeline_session import router as pipeline_session_router
from app.routers.pipeline_session_output import router as pipeline_session_output_router
from app.routers.pipeline_session_output_unit import (
    router as pipeline_session_output_unit_router,
)
from app.routers.product import router as product_router
from app.routers.signin import router as signin_router
from app.routers.users import router as user_router
from app.routers.external import router as external_router
from app.routers.controller import router as controller_router
from app.routers.ws_router import broadcast_controller, output_stream_router

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
app.include_router(images_router)
app.include_router(pipeline_router)
app.include_router(pipeline_session_router)
app.include_router(pipeline_session_output_router)
app.include_router(pipeline_session_output_unit_router)
app.include_router(product_router)
app.include_router(admin_router)
app.include_router(property_router)
app.include_router(signin_router)
app.include_router(user_router)
app.include_router(pipeline_input_router)
app.include_router(analytics_router)
app.include_router(external_router)
app.include_router(controller_router)

# Create database tables
Base.metadata.create_all(bind=engine)


@app.get("/", status_code=status.HTTP_200_OK)
def is_running():
    return "Server is up and running :)"


@app.websocket("/pub/{topic}")
async def broadcast_pub(websocket: WebSocket, topic: str):
    await websocket.accept()
    while True:
        try:
            f = None
            message = await websocket.receive()
            if "text" in message:
                f = message.get("text")
            elif "bytes" in message:
                f = message.get("bytes")
            if f is not None:
                broadcast_controller.publish(topic, f)
            time.sleep(0.02)
        except WebSocketDisconnect:
            print("Websocket disconnected :)")
            break
        except RuntimeError:
            print("Websocket disconnected early:)")
            break
        except KeyboardInterrupt:
            break


@app.websocket("/sub/{topic}")
async def broadcast_sub(websocket: WebSocket, topic: str, keep_alive: bool = False):
    async def wrapper(data):
        if isinstance(data, str):
            await websocket.send_text(data)
        if isinstance(data, dict):
            await websocket.send_json(data)
        elif isinstance(data, bytes):
            await websocket.send_bytes(data)

    await websocket.accept()
    sub_status = broadcast_controller.subscribe(topic, wrapper, keep_alive=keep_alive)
    if not sub_status:
        await websocket.close()
        return
    while True:
        try:
            await websocket.receive()
            time.sleep(0.02)
        except WebSocketDisconnect:
            print("Websocket disconnected :)")
            break
        except KeyboardInterrupt:
            break
        except RuntimeError:
            print("Websocket disconnected :)")
            break
    broadcast_controller.unsubscribe(topic, wrapper)


@app.websocket("/frame/{cam}/post")
async def websocket_post_endpoint(websocket: WebSocket, cam: str):
    await websocket.accept()
    output_stream_router.send_frame(cam, "")
    while True:
        try:
            f = await websocket.receive_text()
            output_stream_router.send_frame(cam, f)
            time.sleep(0.02)
        except WebSocketDisconnect as err:
            print(err)
            print("Websocket disconnected :)")
            break
        except KeyboardInterrupt:
            break
    # Only clear publisher frames, keep subscribers alive for reconnection
    output_stream_router.remove_publisher(cam)


@app.websocket("/frame/{cam}/get")
async def websocket_get_endpoint(websocket: WebSocket, cam: str, keep_alive: bool = False):
    await websocket.accept()
    sid = str(uuid.uuid4())
    s = output_stream_router.add_subscriber(sid, cam, websocket, keep_alive=keep_alive)
    if not s:
        await websocket.close()
        return
    while True:
        try:
            await websocket.receive_text()
            time.sleep(0.02)
        except WebSocketDisconnect:
            print("Websocket disconnected")
            break
        except KeyboardInterrupt:
            break
    output_stream_router.remove_subscriber(sid, cam)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",  # nosec B104
        port=8000,
        reload=True,
        log_level="info",
    )
