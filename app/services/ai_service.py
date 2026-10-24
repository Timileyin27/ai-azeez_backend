from typing import AsyncIterator

from app.ai.client import AIError, stream_chat  # noqa: F401
from app.ai.context import trim_history
from app.ai.prompts import SUPPORT_SYSTEM_PROMPT


async def stream_reply(history: list[dict]) -> AsyncIterator[str]:
    context = trim_history(history)
    async for chunk in stream_chat(context, SUPPORT_SYSTEM_PROMPT):
        yield chunk