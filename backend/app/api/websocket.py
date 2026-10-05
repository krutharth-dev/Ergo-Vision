import asyncio
import logging

from fastapi import WebSocket, WebSocketDisconnect

from ..config import WEBSOCKET_UPDATE_INTERVAL

logger = logging.getLogger(__name__)

active_connections: set[WebSocket] = set()
_lifecycle_lock = asyncio.Lock()


async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    from ..main import get_pipeline

    async with _lifecycle_lock:
        active_connections.add(websocket)
        pipeline = get_pipeline()
        if pipeline is not None and len(active_connections) == 1:
            await asyncio.to_thread(pipeline.activate_camera)

    try:
        while True:
            pipeline = get_pipeline()
            if pipeline is not None:
                await websocket.send_json(pipeline.get_current())
            await asyncio.sleep(WEBSOCKET_UPDATE_INTERVAL)
    except (WebSocketDisconnect, RuntimeError):
        pass
    except Exception:
        logger.exception("WebSocket error")
    finally:
        async with _lifecycle_lock:
            active_connections.discard(websocket)
            if not active_connections:
                pipeline = get_pipeline()
                if pipeline is not None and not pipeline.background_monitoring_enabled:
                    await asyncio.to_thread(pipeline.deactivate_camera)


async def broadcast(event: dict):
    if not active_connections:
        return

    dead: list[WebSocket] = []
    for ws in list(active_connections):
        try:
            await ws.send_json(event)
        except Exception:
            dead.append(ws)

    if dead:
        async with _lifecycle_lock:
            for ws in dead:
                active_connections.discard(ws)
            if not active_connections:
                from ..main import get_pipeline
                pipeline = get_pipeline()
                if pipeline is not None and not pipeline.background_monitoring_enabled:
                    await asyncio.to_thread(pipeline.deactivate_camera)
