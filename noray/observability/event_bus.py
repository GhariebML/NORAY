import asyncio
from typing import Callable, List, Dict
from noray.observability.events import BaseEvent
import json

class EventBus:
    def __init__(self):
        self._subscribers: List[asyncio.Queue] = []
        self.history: List[Dict] = []  # Keep a small buffer for replay

    async def subscribe(self) -> asyncio.Queue:
        queue = asyncio.Queue()
        self._subscribers.append(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue):
        if queue in self._subscribers:
            self._subscribers.remove(queue)

    async def publish(self, event: BaseEvent):
        """Publish event to all active websocket queues and store in history."""
        event_dict = event.model_dump()
        self.history.append(event_dict)
        if len(self.history) > 1000:
            self.history.pop(0) # Keep last 1000 events

        for queue in self._subscribers:
            await queue.put(event_dict)

# Global singleton event bus
event_bus = EventBus()
