"""Decides which past messages go to the model.
 
Models have a limited context window and you pay per token, so instead of
"the last N messages" we keep the newest messages that fit a token budget.
"""
 
CHARS_PER_TOKEN = 4  # rough rule of thumb for English; cheap and good enough
MAX_CONTEXT_TOKENS = 6000
 
 
def estimate_tokens(text: str) -> int:
    return len(text) // CHARS_PER_TOKEN + 4  # +4 for per-message overhead
 
 
def trim_history(history: list[dict], max_tokens: int = MAX_CONTEXT_TOKENS) -> list[dict]:
    """history: oldest-first list of {"role", "content"}. Returns the newest
    messages that fit the budget, oldest-first, always starting with a user
    message (models expect that)."""
    kept: list[dict] = []
    total = 0
    for message in reversed(history):
        cost = estimate_tokens(message["content"])
        if kept and total + cost > max_tokens:
            break  # always keep at least the newest message
        kept.append(message)
        total += cost
    kept.reverse()
 
    while kept and kept[0]["role"] != "user":
        kept.pop(0)
    return kept