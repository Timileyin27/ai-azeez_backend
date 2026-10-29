import threading
import time
from collections import defaultdict, deque
 
from fastapi import HTTPException, Request, status
 
# (max attempts, window in seconds)
IP_SEND = (20, 3600)         # per IP, per hour (shared Wi-Fi networks exist, so generous)
EMAIL_SEND_COOLDOWN = (1, 60)  # one code per email per minute
EMAIL_SEND_HOURLY = (5, 3600)  # at most 5 codes per email per hour
IP_VERIFY = (30, 900)        # per IP, per 15 minutes
EMAIL_VERIFY = (5, 900)      # 5 tries per email per 15 minutes: stops brute-forcing a 6-digit code
 
_MAX_WINDOW = 3600  # longest window above; used to clean up idle keys
 
 
class SlidingWindowLimiter:
    def __init__(self) -> None:
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()  # sync routes run in a thread pool
        self._calls = 0
 
    def hit(self, key: str, limit: int, window: int) -> int:
        """Record an attempt. Returns 0 if allowed, otherwise the number of
        seconds until the caller may try again. Blocked attempts aren't recorded."""
        now = time.monotonic()
        with self._lock:
            self._calls += 1
            if self._calls % 500 == 0:
                self._sweep(now)
 
            q = self._hits[key]
            while q and now - q[0] >= window:
                q.popleft()
            if len(q) >= limit:
                return max(1, int(window - (now - q[0])) + 1)
            q.append(now)
            return 0
 
    def reset(self, key: str) -> None:
        with self._lock:
            self._hits.pop(key, None)
 
    def _sweep(self, now: float) -> None:
        """Drop keys with no recent activity so memory doesn't grow forever."""
        stale = [k for k, q in self._hits.items() if not q or now - q[-1] > _MAX_WINDOW]
        for k in stale:
            del self._hits[k]
 
 
limiter = SlidingWindowLimiter()
 
 
def _human(seconds: int) -> str:
    if seconds < 90:
        return f"{seconds} seconds"
    return f"{(seconds + 59) // 60} minutes"
 
 
def _enforce(key: str, rule: tuple[int, int], what: str) -> None:
    limit, window = rule
    retry_after = limiter.hit(key, limit, window)
    if retry_after:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"{what} Try again in {_human(retry_after)}.",
            headers={"Retry-After": str(retry_after)},
        )
 
 
def _client_ip(request: Request) -> str:
    # Uvicorn's proxy-headers handling already puts the real client IP here on Render.
    return request.client.host if request.client else "unknown"
 
 
def _norm(email: str) -> str:
    return email.strip().lower()
 
 
def check_send_otp(request: Request, email: str) -> None:
    """Call before generating and emailing a code. Applies to signup AND login."""
    email = _norm(email)
    _enforce(f"send:ip:{_client_ip(request)}", IP_SEND, "Too many requests from this network.")
    _enforce(f"send:cooldown:{email}", EMAIL_SEND_COOLDOWN, "Please wait before requesting another code.")
    _enforce(f"send:email:{email}", EMAIL_SEND_HOURLY, "Too many codes requested for this email.")
 
 
def check_verify_otp(request: Request, email: str) -> None:
    """Call before checking a submitted code. Counts every attempt."""
    email = _norm(email)
    _enforce(f"verify:ip:{_client_ip(request)}", IP_VERIFY, "Too many attempts from this network.")
    _enforce(f"verify:email:{email}", EMAIL_VERIFY, "Too many incorrect attempts.")
 
 
def clear_verify_otp(email: str) -> None:
    """Call after a successful verification so a legitimate user starts fresh."""
    limiter.reset(f"verify:email:{_norm(email)}")
 