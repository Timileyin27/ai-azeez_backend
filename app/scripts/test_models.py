"""Times how long each candidate model takes to return its first token.
 
Run from the project root:   python scripts/test_models.py
Pick a primary and a fallback from the results, then set them in Settings or env.
"""
import asyncio
import sys
import time
from pathlib import Path
 
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
 
from google import genai  # noqa: E402
 
from app.config import settings  # noqa: E402
 
MODELS = [
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
]
 
 
async def try_model(client: genai.Client, model: str) -> None:
    start = time.perf_counter()
    try:
        stream = await client.aio.models.generate_content_stream(
            model=model,
            contents="Reply with one short friendly sentence.",
        )
        async for chunk in stream:
            if chunk.text:
                elapsed = time.perf_counter() - start
                print(f"OK     {model:<24} first token in {elapsed:5.1f}s  {chunk.text.strip()[:50]!r}")
                return
        print(f"EMPTY  {model:<24} stream ended with no text")
    except Exception as e:  # noqa: BLE001
        elapsed = time.perf_counter() - start
        print(f"FAIL   {model:<24} after {elapsed:5.1f}s  {type(e).__name__}: {str(e)[:100]}")
 
 
async def main() -> None:
    client = genai.Client(api_key=settings.gemini_api_key)
    for model in MODELS:
        await try_model(client, model)
 
 
asyncio.run(main())