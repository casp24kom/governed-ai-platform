import hmac
from typing import Final

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.config import settings

DEV_ENVS: Final[set[str]] = {"local", "dev", "development", "test"}
EXACT_EXEMPT_PATHS: Final[set[str]] = {
    "/",
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
}
EXEMPT_PREFIXES: Final[tuple[str, ...]] = ("/static", "/debug")


def _is_exempt_path(path: str) -> bool:
    if path in EXACT_EXEMPT_PATHS:
        return True
    return path.startswith(EXEMPT_PREFIXES)


class ApiAuthMiddleware(BaseHTTPMiddleware):
    """
    Security-sensitive: protects non-debug API routes using bearer token auth.

    Behavior:
    - In local/dev/test-like environments, auth is bypassed for all non-exempt routes.
    - In non-dev environments, auth is required for non-exempt paths.
    - If API_AUTH_TOKEN is set, every non-exempt request must present matching bearer token.
    """

    async def dispatch(self, request: Request, call_next):
        path = request.url.path or "/"
        if _is_exempt_path(path):
            return await call_next(request)

        env = settings.app_env.strip().lower()
        configured_token = settings.api_auth_token.strip()

        if env in DEV_ENVS:
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "").strip()
        if not auth_header.lower().startswith("bearer "):
            return JSONResponse(status_code=401, content={"detail": "Unauthorized"})

        provided_token = auth_header[7:].strip()
        if not configured_token or not hmac.compare_digest(provided_token, configured_token):
            return JSONResponse(status_code=403, content={"detail": "Forbidden"})

        return await call_next(request)
