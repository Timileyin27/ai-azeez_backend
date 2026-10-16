from collections import defaultdict
 
from fastapi import WebSocket
 
 
class ConnectionManager:
    """Maps user_id -> open WebSocket connections (one user can have several tabs).
 
    In-memory only, so it works with a single server process. If you ever run
    multiple instances, replace this with Redis pub/sub.
    """
 
    def __init__(self) -> None:
        self._connections: dict[str, set[WebSocket]] = defaultdict(set)
 
    def connect(self, user_id: str, ws: WebSocket) -> None:
        self._connections[user_id].add(ws)
 
    def disconnect(self, user_id: str, ws: WebSocket) -> None:
        conns = self._connections.get(user_id)
        if not conns:
            return
        conns.discard(ws)
        if not conns:
            self._connections.pop(user_id, None)
 
    def is_online(self, user_id: str) -> bool:
        return user_id in self._connections
 
    async def send_to_user(self, user_id: str, payload: dict) -> None:
        for ws in list(self._connections.get(user_id, ())):
            try:
                await ws.send_json(payload)
            except Exception:
                # Dead socket: drop it so we stop sending to it.
                self.disconnect(user_id, ws)
 
 
manager = ConnectionManager()
 