from typing import Any, Dict, List, Optional

import requests

from app.config import settings
from app.snowflake_rest_auth import generate_snowflake_rest_jwt


def cortex_search_rest(
    database: str,
    schema: str,
    service_name: str,
    query: str,
    limit: int = 5,
    columns: Optional[List[str]] = None,
    filter_obj: Optional[Dict[str, Any]] = None,
    timeout_s: int = 20
) -> Dict[str, Any]:

    url = (
        f"{settings.sf_account_url}"
        f"/api/v2/databases/{database}/schemas/{schema}"
        f"/cortex-search-services/{service_name}:query"
    )

    headers = {
        "Authorization": f"Bearer {generate_snowflake_rest_jwt()}",
        "X-Snowflake-Authorization-Token-Type": "KEYPAIR_JWT",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    payload: Dict[str, Any] = {"query": query, "limit": int(min(max(limit, 1), 1000))}
    if columns:
        payload["columns"] = columns
    if filter_obj:
        payload["filter"] = filter_obj

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=timeout_s)
        response.raise_for_status()
    except requests.RequestException as exc:
        detail = ""
        if getattr(exc, "response", None) is not None:
            detail = (exc.response.text or "")[:500]
        raise RuntimeError(f"Cortex Search request failed: {exc}. {detail}") from exc

    return response.json()
