import asyncio
from typing import AsyncIterator
 
 
async def stream_reply(history: list[dict]) -> AsyncIterator[str]:
    """Yield the assistant reply in small chunks.
 
    PLACEHOLDER: fakes streaming so the WebSocket flow can be built and tested
    before the real AI wrapper exists. In Phase 3, replace the body with a call
    to Gemini's streaming API and `yield` each text chunk. Keep this signature
    so nothing else in the app has to change.
 
    `history` is a list of {"role": "user" | "assistant" | "system", "content": str},
    oldest first, and already ends with the user's latest message.
    """
    last_user_message = history[-1]["content"] if history else ""
    text = (
        f"(placeholder reply) You said: {last_user_message}. "
        "The real AI response will stream here."
    )
    for word in text.split(" "):
        await asyncio.sleep(0.05)
        yield word + " "