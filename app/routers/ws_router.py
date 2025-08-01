import asyncio
from collections import defaultdict
from typing import Any, Callable, Coroutine, Dict, List

from starlette.websockets import WebSocket


class BroadcastController:
    def __init__(self):
        self._topics: Dict[str, Any] = {}
        self._pub_lock: Dict[str, bool] = {}
        self._subscribers: Dict[
            str, List[Callable[[Any], Coroutine[Any, Any, None]]]
        ] = defaultdict(list)

    def publish(self, topic: str, data: Any) -> None:
        if not self._pub_lock.get(topic, False):
            self._topics[topic] = data
            self._pub_lock[topic] = True
            loop = asyncio.get_event_loop()
            for callback in self._subscribers[topic]:
                loop.create_task(callback(data))
            self._pub_lock[topic] = False

    def subscribe(
        self, topic: str, callback: Callable[[Any], Coroutine[Any, Any, None]]
    ) -> bool:
        if topic not in self._topics:
            return False

        self._subscribers[topic].append(callback)
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
    def __init__(self):
        self.__streamer: Dict[str, Dict[str, WebSocket]] = {}
        self.__frames: Dict[str, List[str]] = {}
        self.__stream_lock = False
        self.__is_broadcasting = False

    def send_frame(self, cam: str, frame: str) -> None:
        if cam not in self.__streamer:
            self.__streamer[cam] = {}
            return
        self.__store_frame(cam, frame)

    def remove_cam(self, cam: str) -> None:
        self.__streamer.pop(cam, None)

    def add_subscriber(self, sid: str, cam: str, ws: WebSocket) -> bool:
        if cam not in self.__streamer:
            return False
        self.__streamer[cam][sid] = ws
        return True

    def remove_subscriber(self, sid: str, cam: str) -> None:
        if cam in self.__streamer:
            if sid in self.__streamer[cam]:
                self.__streamer[cam].pop(sid)

    def __store_frame(self, cam: str, frame: str) -> None:
        if cam not in self.__frames:
            self.__frames[cam] = []
        if self.__frames[cam]:
            self.__frames[cam][0] = frame
        else:
            self.__frames[cam].append(frame)
        self.__broadcast(cam)

    def __broadcast(self, cam: str) -> None:
        if self.__stream_lock:
            return
        self.__stream_lock = True
        subs = self.__streamer[cam].copy().values()
        loop = asyncio.get_event_loop()
        frame = self.__frames[cam][0]
        for ws in subs:
            loop.create_task(ws.send_text(frame))
        self.__stream_lock = False


output_stream_router = OutputStreamRouter()
broadcast_controller = BroadcastController()
