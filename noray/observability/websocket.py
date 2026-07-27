from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from noray.observability.event_bus import event_bus

router = APIRouter()

@router.websocket("/stream")
async def stream_events(websocket: WebSocket):
    await websocket.accept()

    # Send historical events for replay on initial connection
    for event in event_bus.history:
        await websocket.send_json(event)

    queue = await event_bus.subscribe()
    try:
        while True:
            # Wait for new events from the bus
            event_dict = await queue.get()
            await websocket.send_json(event_dict)
    except WebSocketDisconnect:
        event_bus.unsubscribe(queue)
    except Exception as e:
        print(f"Websocket error: {e}")
        event_bus.unsubscribe(queue)
