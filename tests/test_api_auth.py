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
            import app.auth
            import app.routers.security
            import app.main

            importlib.reload(app.config)
            importlib.reload(app.auth)
            importlib.reload(app.routers.security)
            main = importlib.reload(app.main)
            return main.app


class ApiAuthMiddlewareTests(unittest.TestCase):
    def test_prod_requires_bearer_token_on_non_exempt_route(self):
        app = _load_app_with_env(
            {
                "APP_ENV": "prod-demo",
                "API_AUTH_TOKEN": "api-token",
                "DEBUG_API_TOKEN": "debug-token",
                "SF_SECRET_ID": "",
                "SF_SECRET_NAME": "",
            }
        )
        client = TestClient(app, raise_server_exceptions=False)

        unauthorized = client.post("/rag/injection_test")
        forbidden = client.post("/rag/injection_test", headers={"Authorization": "Bearer wrong"})
        allowed = client.post("/rag/injection_test", headers={"Authorization": "Bearer api-token"})

        self.assertEqual(unauthorized.status_code, 401)
        self.assertEqual(forbidden.status_code, 403)
        self.assertNotIn(allowed.status_code, (401, 403))

    def test_dev_allows_when_token_not_configured(self):
        app = _load_app_with_env(
            {
                "APP_ENV": "dev",
                "API_AUTH_TOKEN": "",
                "SF_SECRET_ID": "",
                "SF_SECRET_NAME": "",
            }
        )
        client = TestClient(app, raise_server_exceptions=False)

        # route may fail internally due to missing infra, but middleware should not block it
        resp = client.post("/rag/injection_test")
        self.assertNotIn(resp.status_code, (401, 403))

    def test_exempt_paths_are_accessible_without_api_auth(self):
        app = _load_app_with_env(
            {
                "APP_ENV": "prod-demo",
                "API_AUTH_TOKEN": "api-token",
                "SF_SECRET_ID": "",
                "SF_SECRET_NAME": "",
            }
        )
        client = TestClient(app, raise_server_exceptions=False)

        health = client.get("/health")
        docs = client.get("/docs")

        self.assertEqual(health.status_code, 200)
        self.assertEqual(docs.status_code, 200)


if __name__ == "__main__":
    unittest.main()
