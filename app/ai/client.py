"""The only module that talks to Gemini. Everything else calls stream_chat().
 
Swapping providers later means rewriting this one file.
"""
import asyncio
import logging
from typing import AsyncIterator
 
from google import genai
from google.genai import errors, types
 
from app.config import settings
 
logger = logging.getLogger(__name__)
 
# Set GEMINI_MODEL in your env to change it without touching code.
MODEL = getattr(settings, "gemini_model", None) or "gemini-3.5-flash"
# Used when the primary model is overloaded or too slow. Pick one that passes
# your own timing test (see the test script), not just one that appears in models.list().
FALLBACK_MODEL = getattr(settings, "gemini_fallback_model", None) or "gemini-3.1-flash-lite"
 
FIRST_CHUNK_TIMEOUT = 20.0  # seconds to wait for the first token
IDLE_TIMEOUT = 20.0         # max silence between tokens
TOTAL_TIMEOUT = 90.0        # hard cap for one reply
MAX_ATTEMPTS = 2  # attempt 1: primary model, attempt 2: fallback model
RETRYABLE_CODES = {429, 500, 502, 503, 504}
 
 
class AIError(Exception):
    """Anything that went wrong while generating a reply."""
 
 
_client: genai.Client | None = None
 
 
def _get_client() -> genai.Client:
    global _client
    if _client is None:
        if not settings.gemini_api_key:
            raise AIError("GEMINI_API_KEY is not configured")
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client
 
 
def _to_contents(history: list[dict]) -> list[types.Content]:
    """Convert [{"role","content"}] to Gemini's format. Gemini calls the
    assistant "model" and takes system text separately (system_instruction)."""
    contents = []
    for m in history:
        if m["role"] == "system":
            continue
        role = "user" if m["role"] == "user" else "model"
        contents.append(
            types.Content(role=role, parts=[types.Part.from_text(text=m["content"])])
        )
    return contents
 
 
async def stream_chat(history: list[dict], system_prompt: str) -> AsyncIterator[str]:
    contents = _to_contents(history)
    if not contents:
        raise AIError("empty conversation")
 
    config = types.GenerateContentConfig(
        system_instruction=system_prompt,
        temperature=0.4,
        max_output_tokens=2048,
    )
    client = _get_client()
    loop = asyncio.get_running_loop()
    last_error: Exception | None = None
 
    for attempt in range(1, MAX_ATTEMPTS + 1):
        started = False  # once a token has been sent we can't retry cleanly
        model = MODEL if attempt == 1 else FALLBACK_MODEL
        deadline = loop.time() + TOTAL_TIMEOUT
        try:
            stream = await client.aio.models.generate_content_stream(
                model=model, contents=contents, config=config
            )
            iterator = stream.__aiter__()
            wait = FIRST_CHUNK_TIMEOUT
            while True:
                remaining = deadline - loop.time()
                if remaining <= 0:
                    raise asyncio.TimeoutError()
                try:
                    chunk = await asyncio.wait_for(
                        iterator.__anext__(), timeout=min(wait, remaining)
                    )
                except StopAsyncIteration:
                    return
                wait = IDLE_TIMEOUT
                text = chunk.text  # None for non-text chunks (e.g. a safety stop)
                if text:
                    started = True
                    yield text
 
        except asyncio.TimeoutError as e:
            last_error = e
            logger.warning("Gemini timeout on %s (attempt %s/%s)", model, attempt, MAX_ATTEMPTS)
            if started:
                raise AIError("reply timed out mid-stream") from e
        except errors.APIError as e:
            last_error = e
            code = getattr(e, "code", None)
            logger.warning("Gemini API error %s on %s (attempt %s/%s)", code, model, attempt, MAX_ATTEMPTS)
            if started or code not in RETRYABLE_CODES:
                raise AIError(f"Gemini error {code}") from e
        except AIError:
            raise
        except Exception as e:  # network errors, SDK bugs
            last_error = e
            logger.exception("Unexpected Gemini failure")
            if started:
                raise AIError("unexpected failure mid-stream") from e
 
        if attempt < MAX_ATTEMPTS:
            await asyncio.sleep(0.5 * 2 ** attempt)  # 1s, then 2s
 
    raise AIError("Gemini unavailable after retries") from last_error
 