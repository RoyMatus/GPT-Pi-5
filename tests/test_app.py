import unittest
from gpt_pi.config import Settings
from gpt_pi.providers import OfflineProvider

class ConfigTests(unittest.TestCase):
    def test_invalid_ports(self):
        for value in ('0', '65536', 'invalid'):
            with self.assertRaises(ValueError):
                Settings.from_env({'GPT_PI_PORT': value})

    def test_paid_provider_rejected(self):
        with self.assertRaises(ValueError):
            Settings.from_env({'GPT_PI_PROVIDER': 'openai'})

    def test_no_fake_chat(self):
        with self.assertRaises(NotImplementedError):
            OfflineProvider().reply('Synthetic input')
