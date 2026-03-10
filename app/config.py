import base64
import binascii
import json
import os
from typing import Final

import boto3
from dotenv import load_dotenv
from pydantic import BaseModel

from app.aws_secrets import hydrate_env_from_secrets_manager

load_dotenv()

DEFAULT_AWS_REGION: Final[str] = "ap-southeast-2"
SF_SECRET_KEYS: Final[tuple[str, ...]] = (
    "SF_PRIVATE_KEY_PEM_B64",
    "SF_ACCOUNT_IDENTIFIER",
    "SF_ACCOUNT_URL",
    "SF_USER",
    "SF_PUBLIC_KEY_FP",
)


def _split_fqn(value: str) -> tuple[str, str, str]:
    """
    Split OBJECT names like DB.SCHEMA.NAME.
    Returns empty strings when parts are missing.
    """
    parts = [p.strip() for p in (value or "").split(".") if p.strip()]
    if len(parts) >= 3:
        return parts[-3], parts[-2], parts[-1]
    if len(parts) == 2:
        return "", parts[0], parts[1]
    if len(parts) == 1:
        return "", "", parts[0]
    return "", "", ""


def _resolve_aws_region() -> str:
    return (
        os.getenv("AWS_REGION")
        or os.getenv("AWS_DEFAULT_REGION")
        or os.getenv("AGENTCORE_REGION")
        or DEFAULT_AWS_REGION
    )


def _load_secret_json(secret_id: str) -> dict:
    sm = boto3.client("secretsmanager", region_name=_resolve_aws_region())
    resp = sm.get_secret_value(SecretId=secret_id)
    return json.loads(resp.get("SecretString") or "{}")


def _hydrate_from_named_secret() -> None:
    """
    Backward-compatible support for SF_SECRET_NAME.
    Values are only set when currently missing.
    """
    secret_name = os.getenv("SF_SECRET_NAME", "").strip()
    if not secret_name:
        return

    for key, value in _load_secret_json(secret_name).items():
        if value is None or os.getenv(key):
            continue
        os.environ[key] = str(value)


def _hydrate_from_secret_id_if_needed() -> None:
    """
    Legacy fallback for SF_SECRET_ID when private-key fields are absent.
    This keeps startup behavior compatible with earlier deployments.
    """
    secret_id = os.getenv("SF_SECRET_ID", "").strip()
    if not secret_id:
        return
    if os.getenv("SF_PRIVATE_KEY_PEM_B64") or os.getenv("SF_PRIVATE_KEY_PEM_PATH"):
        return

    data = _load_secret_json(secret_id)
    for key in SF_SECRET_KEYS:
        value = data.get(key)
        if value and not os.getenv(key):
            os.environ[key] = str(value)


hydrate_env_from_secrets_manager()
_hydrate_from_secret_id_if_needed()
_hydrate_from_named_secret()

_DEFAULT_KB_CHUNKS_TABLE = os.getenv(
    "KB_CHUNKS_TABLE",
    "GOV_AI_PLATFORM.KB.SOP_CHUNKS_ENRICHED",
)
_DEFAULT_DB_FROM_KB, _DEFAULT_SCHEMA_FROM_KB, _ = _split_fqn(_DEFAULT_KB_CHUNKS_TABLE)
if not _DEFAULT_DB_FROM_KB:
    _DEFAULT_DB_FROM_KB = "GOV_AI_PLATFORM"
if not _DEFAULT_SCHEMA_FROM_KB:
    _DEFAULT_SCHEMA_FROM_KB = "KB"

_DEFAULT_TOPIC_TEMPLATES_TABLE = os.getenv(
    "TOPIC_TEMPLATES_TABLE",
    f"{_DEFAULT_DB_FROM_KB}.{_DEFAULT_SCHEMA_FROM_KB}.TOPIC_TEMPLATES",
)


class Settings(BaseModel):
    app_env: str = os.getenv("APP_ENV", "prod-demo")
    data_dir: str = os.getenv("DATA_DIR", "/data")
    kb_chunks_table: str = _DEFAULT_KB_CHUNKS_TABLE
    topic_templates_table: str = _DEFAULT_TOPIC_TEMPLATES_TABLE
    sf_private_key_pem_path: str = os.getenv("SF_PRIVATE_KEY_PEM_PATH", "")
    sf_account_identifier: str = os.getenv("SF_ACCOUNT_IDENTIFIER", "")
    sf_account_url: str = os.getenv("SF_ACCOUNT_URL", "")
    sf_user: str = os.getenv("SF_USER", "")
    sf_role: str = os.getenv("SF_ROLE", "GOV_AI_APP_ROLE")
    sf_warehouse: str = os.getenv("SF_WAREHOUSE", "GOV_AI_WH")
    sf_database: str = os.getenv("SF_DATABASE", _DEFAULT_DB_FROM_KB)
    sf_schema: str = os.getenv("SF_SCHEMA", _DEFAULT_SCHEMA_FROM_KB)
    sf_audit_schema: str = os.getenv("SF_AUDIT_SCHEMA", "AUDIT")
    cortex_search_service: str = os.getenv(
        "CORTEX_SEARCH_SERVICE",
        os.getenv("SF_CORTEX_SEARCH_SERVICE", "SOP_SEARCH"),
    )
    sf_private_key_pem_b64: str = os.getenv("SF_PRIVATE_KEY_PEM_B64", "")
    sf_public_key_fp: str = os.getenv("SF_PUBLIC_KEY_FP", "")
    agentcore_region: str = os.getenv("AGENTCORE_REGION", DEFAULT_AWS_REGION)
    agentcore_endpoint: str = os.getenv(
        "AGENTCORE_ENDPOINT",
        "https://bedrock-agentcore.ap-southeast-2.amazonaws.com",
    )
    agentcore_agent_id: str = os.getenv("AGENTCORE_AGENT_ID", "")
    api_auth_token: str = os.getenv("API_AUTH_TOKEN", "")
    debug_api_token: str = os.getenv("DEBUG_API_TOKEN", "")


settings = Settings()


def load_private_key_pem_bytes() -> bytes:
    """
    Return private key PEM bytes from file path first, then base64 env fallback.
    """
    path = settings.sf_private_key_pem_path.strip()
    if path and os.path.exists(path):
        with open(path, "rb") as handle:
            return handle.read()

    b64_value = settings.sf_private_key_pem_b64.strip()
    if b64_value:
        try:
            return base64.b64decode(b64_value)
        except (binascii.Error, ValueError) as exc:
            raise RuntimeError("SF_PRIVATE_KEY_PEM_B64 is not valid base64") from exc

    raise RuntimeError("Missing SF_PRIVATE_KEY_PEM_PATH (file) or SF_PRIVATE_KEY_PEM_B64")
