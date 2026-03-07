import hmac

from fastapi import Header, HTTPException

from app.config import settings

DEBUG_ALLOWED_ENVS = {"local", "dev", "development", "test"}


def require_debug_access(x_debug_token: str | None = Header(default=None)) -> None:
    """
    Security-sensitive: debug endpoints are disabled outside dev/test-like environments.
    If DEBUG_API_TOKEN is configured, callers must provide matching `X-Debug-Token`.
    """
    if settings.app_env.strip().lower() not in DEBUG_ALLOWED_ENVS:
        raise HTTPException(status_code=404, detail="Not found")

    expected_token = settings.debug_api_token.strip()
    if not expected_token:
        return

    provided_token = (x_debug_token or "").strip()
    if not hmac.compare_digest(provided_token, expected_token):
        raise HTTPException(status_code=403, detail="Forbidden")
