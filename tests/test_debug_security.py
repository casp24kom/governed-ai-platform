import importlib
import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient


class _FakeSecretsManager:
    def get_secret_value(self, SecretId):  # noqa: N802
        return {"SecretString": "{}"}


def _load_app_with_env(env):
    with patch.dict(os.environ, env, clear=False):
        with patch("boto3.client", return_value=_FakeSecretsManager()):
            import app.config
            import app.routers.security
            import app.main

            importlib.reload(app.config)
            importlib.reload(app.routers.security)
            main = importlib.reload(app.main)
            return main.app


class DebugSecurityTests(unittest.TestCase):
    def test_mask_value_masks_middle(self):
        from app.routers.helpers import mask_value

        self.assertEqual(mask_value("abcdef", keep_prefix=2, keep_suffix=2), "ab**ef")
        self.assertEqual(mask_value("abc", keep_prefix=2, keep_suffix=2), "***")

    def test_debug_disabled_outside_dev(self):
        app = _load_app_with_env(
            {
                "APP_ENV": "prod-demo",
                "SF_SECRET_ID": "",
                "SF_SECRET_NAME": "",
            }
        )
        client = TestClient(app)

        resp = client.get("/debug/env")
        self.assertEqual(resp.status_code, 404)

    def test_debug_token_required_when_configured(self):
        app = _load_app_with_env(
            {
                "APP_ENV": "dev",
                "DEBUG_API_TOKEN": "token-123",
                "SF_SECRET_ID": "",
                "SF_SECRET_NAME": "",
                "SF_ACCOUNT_IDENTIFIER": "account-id",
                "SF_ACCOUNT_URL": "https://test.snowflakecomputing.com",
                "SF_USER": "demo-user",
            }
        )
        client = TestClient(app)

        forbidden = client.get("/debug/env")
        allowed = client.get("/debug/env", headers={"X-Debug-Token": "token-123"})

        self.assertEqual(forbidden.status_code, 403)
        self.assertEqual(allowed.status_code, 200)


if __name__ == "__main__":
    unittest.main()
