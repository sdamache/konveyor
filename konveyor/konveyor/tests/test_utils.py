from django.test import TestCase
from konveyor.konveyor.settings.utils import get_secret

class UtilsTest(TestCase):
    def test_get_secret_from_env(self):
        # Must have
        secret_name = 'TEST_SECRET'
        secret_value = 'test_value'
        with self.settings(ENV={'TEST_SECRET': secret_value}):
            self.assertEqual(get_secret(secret_name), secret_value)

    def test_get_secret_from_key_vault(self):
        # Must have
        secret_name = 'TEST_SECRET'
        secret_value = 'test_value'
        with self.settings(AZURE_KEY_VAULT_URL='https://myvault.vault.azure.net/'):
            with patch('konveyor.konveyor.settings.utils.SecretClient') as MockSecretClient:
                mock_client = MockSecretClient.return_value
                mock_client.get_secret.return_value.value = secret_value
                self.assertEqual(get_secret(secret_name), secret_value)
