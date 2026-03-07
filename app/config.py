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


class Settings(BaseModel):
    app_env: str = os.getenv("APP_ENV", "prod-demo")
    data_dir: str = os.getenv("DATA_DIR", "/data")
    kb_chunks_table: str = os.getenv("KB_CHUNKS_TABLE", "BHP_PLATFORM_LAB.KB.SOP_CHUNKS_ENRICHED")
    topic_templates_table: str = os.getenv("TOPIC_TEMPLATES_TABLE", "BHP_PLATFORM_LAB.KB.TOPIC_TEMPLATES")
    sf_private_key_pem_path: str = os.getenv("SF_PRIVATE_KEY_PEM_PATH", "")
    sf_account_identifier: str = os.getenv("SF_ACCOUNT_IDENTIFIER", "")
    sf_account_url: str = os.getenv("SF_ACCOUNT_URL", "")
    sf_user: str = os.getenv("SF_USER", "")
    sf_role: str = os.getenv("SF_ROLE", "BHP_LAB_APP_ROLE")
    sf_warehouse: str = os.getenv("SF_WAREHOUSE", "BHP_LAB_WH")
    sf_database: str = os.getenv("SF_DATABASE", "BHP_PLATFORM_LAB")
    sf_schema: str = os.getenv("SF_SCHEMA", "KB")
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
