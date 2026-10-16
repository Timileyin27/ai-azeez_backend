import asyncio
import json
import logging
import uuid
 
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.sql import func
 
from app.ai.stream import stream_reply
from app.database import SessionLocal                          # ADJUST: your session factory
from app.models.chat import Conversation, Message, MessageRole  # ADJUST: your models path
from app.ws.manager import manager
 
logger = logging.getLogger(__name__)
router = APIRouter()
 
AUTH_TIMEOUT_SECONDS = 10
HISTORY_LIMIT = 20
MAX_MESSAGE_LENGTH = 4000
 
 
# --------------------------------------------------------------------------
# Auth
# --------------------------------------------------------------------------
def user_id_from_token(token: str) -> str:
    """Return the user id for a valid access token, or raise.
 
    ADJUST: call the same function your HTTP `get_current_user` dependency uses
    to decode and validate the JWT (signature, expiry, token type). Example:
 
        from app.oauth2 import verify_access_token
        return str(verify_access_token(token).id)
    """
    raise NotImplementedError("Hook this up to your existing JWT verification")
 
 
async def authenticate(ws: WebSocket) -> str | None:
    """Browsers can't set headers on WebSockets, and tokens in the URL end up in
    server logs, so the client sends {"type": "auth", "token": "..."} as its
    first message instead."""
    try:
        raw = await asyncio.wait_for(ws.receive_text(), timeout=AUTH_TIMEOUT_SECONDS)
        data = json.loads(raw)
        if not isinstance(data, dict) or data.get("type") != "auth":
            return None
        return user_id_from_token(data["token"])
    except Exception:
        return None
 
 
# --------------------------------------------------------------------------
# Database helpers (sync SQLAlchemy, so they run in a worker thread)
# --------------------------------------------------------------------------
def _serialize(msg: Message) -> dict:
    return {
        "id": str(msg.id),
        "conversation_id": str(msg.conversation_id),
        "role": msg.role.value,
        "content": msg.content,
        "created_at": msg.created_at.isoformat() if msg.created_at else None,
    }
 
 
def _save_user_message(user_id: uuid.UUID, conversation_id: uuid.UUID, content: str):
    """Owner check + save. Returns (saved_message, history) or None if the
    conversation doesn't exist or doesn't belong to this user."""
    with SessionLocal() as db:
        convo = (
            db.query(Conversation)
            .filter(Conversation.id == conversation_id, Conversation.user_id == user_id)
            .first()
        )
        if convo is None:
            return None
 
        msg = Message(conversation_id=convo.id, role=MessageRole.user, content=content)
        db.add(msg)
        convo.updated_at = func.now()
        db.commit()
        db.refresh(msg)
 
        rows = (
            db.query(Message)
            .filter(Message.conversation_id == convo.id)
            .order_by(Message.created_at.desc())
            .limit(HISTORY_LIMIT)
            .all()
        )
        history = [{"role": m.role.value, "content": m.content} for m in reversed(rows)]
        return _serialize(msg), history
 
 
def _save_assistant_message(conversation_id: uuid.UUID, content: str) -> dict:
    with SessionLocal() as db:
        msg = Message(
            conversation_id=conversation_id, role=MessageRole.assistant, content=content
        )
        db.add(msg)
        db.query(Conversation).filter(Conversation.id == conversation_id).update(
            {"updated_at": func.now()}
        )
        db.commit()
        db.refresh(msg)
        return _serialize(msg)
 
 
# --------------------------------------------------------------------------
# Message flow
# --------------------------------------------------------------------------
async def _handle_message(user_id: str, data: dict) -> None:
    send = lambda payload: manager.send_to_user(user_id, payload)  # noqa: E731
 
    try:
        conversation_id = uuid.UUID(str(data.get("conversation_id", "")))
    except ValueError:
        await send({"type": "error", "code": "bad_conversation_id"})
        return
 
    content = (data.get("content") or "").strip()
    if not content or len(content) > MAX_MESSAGE_LENGTH:
        await send({"type": "error", "code": "invalid_content",
                    "detail": f"1 to {MAX_MESSAGE_LENGTH} characters"})
        return
 
    result = await asyncio.to_thread(
        _save_user_message, uuid.UUID(user_id), conversation_id, content
    )
    if result is None:
        # Same response whether it doesn't exist or isn't theirs.
        await send({"type": "error", "code": "conversation_not_found"})
        return
 
    saved, history = result
    cid = str(conversation_id)
    await send({"type": "message_saved", "message": saved})
    await send({"type": "ai_typing", "conversation_id": cid, "typing": True})
 
    try:
        parts: list[str] = []
        async for token in stream_reply(history):
            parts.append(token)
            await send({"type": "ai_token", "conversation_id": cid, "token": token})
 
        reply = "".join(parts).strip()
        if not reply:
            raise ValueError("empty AI reply")
 
        ai_message = await asyncio.to_thread(_save_assistant_message, conversation_id, reply)
        await send({"type": "ai_done", "message": ai_message})
    except asyncio.CancelledError:
        raise  # client disconnected mid-stream
    except Exception:
        logger.exception("AI reply failed")
        await send({"type": "error", "code": "ai_failed", "conversation_id": cid})
    finally:
        await send({"type": "ai_typing", "conversation_id": cid, "typing": False})
 
 
# --------------------------------------------------------------------------
# Endpoint
# --------------------------------------------------------------------------
@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
 
    user_id = await authenticate(ws)
    if user_id is None:
        await ws.close(code=4401)  # app-defined "unauthorized"
        return
 
    manager.connect(user_id, ws)
    await ws.send_json({"type": "connected"})
 
    in_flight: set[asyncio.Task] = set()
    try:
        while True:
            try:
                data = json.loads(await ws.receive_text())
                if not isinstance(data, dict):
                    raise ValueError
            except ValueError:
                await ws.send_json({"type": "error", "code": "invalid_json"})
                continue
 
            kind = data.get("type")
            if kind == "ping":
                await ws.send_json({"type": "pong"})
            elif kind == "message":
                if in_flight:
                    # One AI reply at a time per connection: avoids overlapping
                    # replies and runaway API cost.
                    await ws.send_json({"type": "error", "code": "ai_busy"})
                    continue
                task = asyncio.create_task(_handle_message(user_id, data))
                in_flight.add(task)
                task.add_done_callback(in_flight.discard)
            else:
                await ws.send_json({"type": "error", "code": "unknown_type"})
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(user_id, ws)
        for task in in_flight:
            task.cancel()
 