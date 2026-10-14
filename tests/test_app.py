import http.client
import json
import threading
import unittest

from gpt_pi.app import create_server
from gpt_pi.config import Settings
from gpt_pi.providers import OfflineProvider


class ConfigTests(unittest.TestCase):
    def test_invalid_ports(self):
        for value in ("0", "65536", "invalid"):
            with self.assertRaises(ValueError):
                Settings.from_env({"GPT_PI_PORT": value})

    def test_live_provider_rejected(self):
        with self.assertRaises(ValueError):
            Settings.from_env({"GPT_PI_PROVIDER": "openai"})

    def test_no_fake_chat(self):
        with self.assertRaises(NotImplementedError):
            OfflineProvider().reply("Synthetic input")


class HttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = create_server(0)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def request(self, path, method="GET", headers=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=3)
        try:
            connection.request(method, path, headers=headers or {})
            response = connection.getresponse()
            return response.status, dict(response.getheaders()), response.read()
        finally:
            connection.close()

    def test_health(self):
        status, headers, body = self.request("/health")
        self.assertEqual(200, status)
        self.assertEqual("offline", json.loads(body)["mode"])
        self.assertEqual("no-store", headers["Cache-Control"])

    def test_home(self):
        status, _, body = self.request("/")
        self.assertEqual(200, status)
        self.assertIn("GPT-Pi 5", body.decode())

    def test_capabilities_are_honest(self):
        status, _, body = self.request("/api/capabilities")
        self.assertEqual(200, status)
        self.assertFalse(any(json.loads(body).values()))

    def test_paths_do_not_expose_files_or_conversations(self):
        for path in ("/../.env", "/AGENTS.md", "/api/chats", "/data/chats.db"):
            self.assertEqual(404, self.request(path)[0])

    def test_untrusted_host_rejected(self):
        self.assertEqual(403, self.request("/", headers={"Host": "evil.example"})[0])

    def test_mutation_not_supported(self):
        self.assertEqual(501, self.request("/api/chats", method="POST")[0])
