import importlib
import os
import unittest
from unittest.mock import patch


class _FakeSecretsManager:
    def __init__(self, secrets):
        self._secrets = secrets

    def get_secret_value(self, SecretId):  # noqa: N802 (AWS naming)
        return {"SecretString": self._secrets.get(SecretId, "{}")}


class ConfigTests(unittest.TestCase):
    def _reload_config(self, env, secrets):
        with patch.dict(os.environ, env, clear=False):
            with patch("boto3.client", return_value=_FakeSecretsManager(secrets)):
                import app.config

                return importlib.reload(app.config)

    def test_named_secret_only_fills_missing_values(self):
        env = {
            "SF_SECRET_NAME": "named-secret",
            "SF_USER": "existing-user",
            "SF_ACCOUNT_URL": "",
            "SF_SECRET_ID": "",
            "AWS_REGION": "ap-southeast-2",
        }
        secrets = {
            "named-secret": '{"SF_USER":"secret-user","SF_ACCOUNT_URL":"https://acct.snowflakecomputing.com"}'
        }

        config = self._reload_config(env, secrets)

        self.assertEqual(config.settings.sf_user, "existing-user")
        self.assertEqual(config.settings.sf_account_url, "https://acct.snowflakecomputing.com")

    def test_secret_id_hydration_does_not_override_existing(self):
        env = {
            "SF_SECRET_ID": "id-secret",
            "SF_SECRET_NAME": "",
            "SF_USER": "env-user",
            "SF_PRIVATE_KEY_PEM_B64": "ZXhpc3Rpbmcta2V5",
            "AWS_REGION": "ap-southeast-2",
        }
        secrets = {
            "id-secret": '{"SF_USER":"secret-user","SF_ACCOUNT_URL":"https://from-secret.snowflakecomputing.com"}'
        }

        config = self._reload_config(env, secrets)

        self.assertEqual(config.settings.sf_user, "env-user")

    def test_invalid_private_key_base64_raises(self):
        env = {
            "SF_SECRET_ID": "",
            "SF_SECRET_NAME": "",
            "SF_PRIVATE_KEY_PEM_PATH": "",
            "SF_PRIVATE_KEY_PEM_B64": "%%%invalid%%%",
        }
        config = self._reload_config(env, {})

        with self.assertRaises(RuntimeError):
            config.load_private_key_pem_bytes()


if __name__ == "__main__":
    unittest.main()
