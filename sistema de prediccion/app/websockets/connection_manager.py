import asyncio
import json

from fastapi import WebSocket


class ConnectionManager:

    def __init__(self) -> None:
        self._connections: dict[int, set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, user_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections.setdefault(user_id, set()).add(websocket)

    async def disconnect(self, user_id: int, websocket: WebSocket) -> None:
        async with self._lock:
            sockets = self._connections.get(user_id)
            if sockets and websocket in sockets:
                sockets.remove(websocket)
                if not sockets:
                    self._connections.pop(user_id, None)

    async def send_to_user(self, user_id: int, message: dict) -> None:
        async with self._lock:
            sockets = list(self._connections.get(user_id, set()))

        payload = json.dumps(message, default=str)

        for socket in sockets:
            try:
                await socket.send_text(payload)
            except Exception:
                await self.disconnect(user_id, socket)

    async def send_to_users(self, user_ids: list[int], message: dict) -> None:
        for user_id in set(user_ids):
            await self.send_to_user(user_id, message)


manager = ConnectionManager()