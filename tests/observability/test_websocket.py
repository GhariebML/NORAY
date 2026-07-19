import pytest
import asyncio
from fastapi import FastAPI
from fastapi.testclient import TestClient
from noray.observability.websocket import router
from noray.observability.event_bus import event_bus
from noray.observability.events import BaseEvent

app = FastAPI()
app.include_router(router)

@pytest.mark.asyncio
async def test_event_bus_publish():
    # Test the core event bus queue mechanics
    queue = await event_bus.subscribe()
    
    event = BaseEvent(event_type="TestEvent", metadata={"key": "value"})
    await event_bus.publish(event)
    
    # Verify it hits history
    assert len(event_bus.history) > 0
    assert event_bus.history[-1]["event_type"] == "TestEvent"
    
    # Verify it hits queue
    queued_event = await queue.get()
    assert queued_event["event_type"] == "TestEvent"
    assert queued_event["metadata"]["key"] == "value"
    
    event_bus.unsubscribe(queue)

def test_websocket_stream():
    client = TestClient(app)
    
    # We use the context manager to connect to the websocket
    with client.websocket_connect("/stream") as websocket:
        # Publish an event while connected
        event = BaseEvent(event_type="WSTestEvent", metadata={"foo": "bar"})
        # We need to run the async publish in the test's event loop
        # Since TestClient is sync, we use a small trick:
        asyncio.run(event_bus.publish(event))
        
        # We should receive it
        data = websocket.receive_json()
        
        # It might receive historical events first, so we loop until we find WSTestEvent
        found = False
        for _ in range(10):
            if data["event_type"] == "WSTestEvent":
                found = True
                assert data["metadata"]["foo"] == "bar"
                break
            try:
                data = websocket.receive_json()
            except:
                break
                
        assert found
