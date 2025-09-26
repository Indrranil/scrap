import asyncio
import logging
from collections import defaultdict
from typing import Any, Callable, Coroutine, Dict, List

from starlette.websockets import WebSocket

logger = logging.getLogger(__name__)


class BroadcastController:
    def __init__(self, keep_alive_enabled: bool = True):
        self._topics: Dict[str, Any] = {}
        self._pub_lock: Dict[str, bool] = {}
        self._subscribers: Dict[
            str, List[Callable[[Any], Coroutine[Any, Any, None]]]
        ] = defaultdict(list)
        self._keep_alive_enabled = keep_alive_enabled

    def publish(self, topic: str, data: Any) -> None:
        if not self._pub_lock.get(topic, False):
            self._topics[topic] = data
            self._pub_lock[topic] = True
            loop = asyncio.get_event_loop()
            for callback in self._subscribers[topic]:
                loop.create_task(callback(data))
            self._pub_lock[topic] = False

    def subscribe(
        self, topic: str, callback: Callable[[Any], Coroutine[Any, Any, None]], keep_alive: bool = False
    ) -> bool:
        # Initialize topic if it doesn't exist and keep_alive is enabled
        if topic not in self._topics:
            if keep_alive and self._keep_alive_enabled:
                self._topics[topic] = None
                logger.info(f"Topic {topic} initialized for keep-alive subscriber")
            else:
                logger.warning(f"Topic {topic} not found and keep_alive disabled")
                return False

        self._subscribers[topic].append(callback)

        # Send latest data if available (not None)
        if self._topics[topic] is not None:
            loop = asyncio.get_event_loop()
            loop.create_task(callback(self._topics[topic]))

        return True

    def unsubscribe(
        self, topic: str, callback: Callable[[Any], Coroutine[Any, Any, None]]
    ) -> None:
        if topic in self._subscribers:
            self._subscribers[topic].remove(callback)

    def get_latest(self, topic: str) -> Any:
        return self._topics.get(topic, None)


class OutputStreamRouter:
    def __init__(self, keep_alive_enabled: bool = True):
        self._streamers: Dict[str, Dict[str, WebSocket]] = {}
        self._frames: Dict[str, str] = {}
        self._stream_lock = False
        self._is_broadcasting = False
        self._keep_alive_enabled = keep_alive_enabled

    def send_frame(self, cam: str, frame: str) -> None:
        if cam not in self._streamers:
            self._streamers[cam] = {}
        self._store_frame(cam, frame)

    def remove_cam(self, cam: str) -> None:
        """Remove camera completely - only use when no keep-alive subscribers exist"""
        self._streamers.pop(cam, None)
        self._frames.pop(cam, None)
        logger.info(f"Camera {cam} completely removed")
    
    def remove_publisher(self, cam: str) -> None:
        """Remove publisher but keep camera and subscribers if they exist"""
        if cam in self._frames:
            self._frames.pop(cam, None)
            logger.info(f"Publisher frames cleared for camera {cam}, but keeping subscribers")
        else:
            logger.info(f"No frames to clear for camera {cam}")
    
    def has_subscribers(self, cam: str) -> bool:
        """Check if camera has any subscribers"""
        return cam in self._streamers and len(self._streamers[cam]) > 0

    def add_subscriber(self, sid: str, cam: str, ws: WebSocket, keep_alive: bool = False) -> bool:
        """Add a subscriber to a camera stream.

        Args:
            sid: Subscriber ID
            cam: Camera ID
            ws: WebSocket connection
            keep_alive: If True, allows subscription even if camera doesn't exist

        Returns:
            bool: True if subscription successful, False otherwise
        """
        # Initialize camera if it doesn't exist and keep_alive is enabled
        if cam not in self._streamers:
            if keep_alive and self._keep_alive_enabled:
                self._streamers[cam] = {}
                logger.info(f"Camera {cam} initialized for keep-alive subscriber {sid}")
            else:
                logger.warning(f"Camera {cam} not found and keep_alive disabled")
                return False

        self._streamers[cam][sid] = ws
        logger.info(f"Subscriber {sid} added to camera {cam}")

        # Send latest frame if available
        if cam in self._frames:
            try:
                loop = asyncio.get_event_loop()
                loop.create_task(ws.send_text(self._frames[cam]))
            except Exception as e:
                logger.error(f"Error sending initial frame to subscriber {sid}: {e}")

        return True

    def remove_subscriber(self, sid: str, cam: str) -> None:
        if cam in self._streamers:
            if sid in self._streamers[cam]:
                self._streamers[cam].pop(sid)
                logger.info(f"Subscriber {sid} removed from camera {cam}")
                
                # If no subscribers left and no keep-alive, remove camera completely
                if len(self._streamers[cam]) == 0:
                    logger.info(f"No subscribers left for camera {cam}")
                    if not self._keep_alive_enabled:
                        self.remove_cam(cam)

    def _store_frame(self, cam: str, frame: str) -> None:
        self._frames[cam] = frame
        self._broadcast(cam)

    def _broadcast(self, cam: str) -> None:
        if self._stream_lock:
            return
        self._stream_lock = True

        if cam in self._streamers and cam in self._frames:
            subs = self._streamers[cam].copy().values()
            loop = asyncio.get_event_loop()
            frame = self._frames[cam]
            for ws in subs:
                try:
                    loop.create_task(ws.send_text(frame))
                except Exception as e:
                    logger.error(f"Error broadcasting frame to camera {cam}: {e}")

        self._stream_lock = False


output_stream_router = OutputStreamRouter()
broadcast_controller = BroadcastController()
