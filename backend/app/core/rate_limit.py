from fastapi import Request, Response
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])


def rate_limit_exceeded_handler(request: Request, exc: Exception) -> Response:
    """Same as slowapi's default handler, except the body uses `detail`
    (like every other error response in this API — HTTPException and
    Pydantic validation errors both do) instead of slowapi's own `error`
    key, which would otherwise be the one inconsistent error shape in the
    API and silently defeat the frontend's shared error-message parsing."""
    assert isinstance(exc, RateLimitExceeded)
    # slowapi's handler also calls the private limiter._inject_headers, but
    # that only writes X-RateLimit-* headers when headers_enabled is on,
    # which it isn't here -- so there's nothing to copy.
    return JSONResponse({"detail": f"Rate limit exceeded: {exc.detail}"}, status_code=429)
