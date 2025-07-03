import asyncio
from collections import defaultdict
from typing import Dict, List, Callable

from starlette.websockets import WebSocket


class BroadcastController:
    def __init__(self):
        self._topics: Dict[str, any] = {}  # Stores the latest data for each topic
        self._pub_lock: Dict[str, bool] = {}
        self._subscribers: Dict[str, List[Callable[[any], None]]] = defaultdict(list)

    def publish(self, topic: str, data: any):
        """Publishes data to a topic and notifies all subscribers."""
        if not self._pub_lock.get(topic, False):
            self._topics[topic] = data
            self._pub_lock[topic] = True
            loop = asyncio.get_event_loop()
            for callback in self._subscribers[topic]:
                loop.create_task(callback(data))
            self._pub_lock[topic] = False

    def subscribe(self, topic: str, callback: Callable[[any], None]):
        """Subscribes to a topic if it has been published at least once."""
        if topic not in self._topics:
            return False

        self._subscribers[topic].append(callback)
        loop = asyncio.get_event_loop()
        loop.create_task(callback(self._topics[topic]))
        return True  # Send the latest data immediately

    def unsubscribe(self, topic: str, callback: Callable[[any], None]):
        """Unsubscribes a callback from a topic."""
        if topic in self._subscribers:
            self._subscribers[topic].remove(callback)

    def get_latest(self, topic: str):
        """Returns the latest data for a topic if available."""
        return self._topics.get(topic, None)


class OutputStreamRouter:
    def __init__(self):
        self.__streamer: dict[str, dict[str, WebSocket]] = {}
        self.__frames = {}
        self.__stream_lock = False
        self.__is_broadcasting = False

    def send_frame(self, cam: str, frame):
        if cam not in self.__streamer.keys():
            self.__streamer[cam] = {}
            return
        self.__store_frame(cam, frame)

    def remove_cam(self, cam):
        self.__streamer.pop(cam, None)

    def add_subscriber(self, sid, cam, ws) -> bool:
        if cam not in self.__streamer.keys():
            return False
        self.__streamer[cam][sid] = ws
        return True

    def remove_subscriber(self, sid, cam):
        cams = self.__streamer.keys()
        if cam in cams:
            subs = self.__streamer[cam].keys()
            if sid in subs:
                self.__streamer[cam].pop(sid)

    def __store_frame(self, cam: str, frame):
        if cam not in self.__frames.keys():
            self.__frames[cam] = []
        if len(self.__frames[cam]) > 0:
            self.__frames[cam][0] = frame
        else:
            self.__frames[cam].append(frame)
        self.__broadcast(cam)

    def __broadcast(self, cam):
        if self.__stream_lock:
            return
        self.__stream_lock = True
        sub = self.__streamer[cam].copy().values()
        loop = asyncio.get_event_loop()
        frame = self.__frames[cam].copy()[0]
        for s in sub:
            loop.create_task(s.send_text(frame))
        self.__stream_lock = False


output_stream_router = OutputStreamRouter()
broadcast_controller = BroadcastController()
