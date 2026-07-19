"""
NORAY — Observability Logger
Intercepts standard logging and bridges it to the event bus.
"""

from noray.observability.event_bus import event_bus
from noray.observability.events import BaseEvent

class Logger:
    @staticmethod
    async def log(message: str, severity: str = "info", **kwargs):
        event = BaseEvent(
            event_type="LogEmitted",
            severity=severity,
            metadata={"message": message, **kwargs}
        )
        await event_bus.publish(event)
