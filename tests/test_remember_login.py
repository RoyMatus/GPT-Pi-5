"""Remembered login uses only synthetic credentials and browser session cookies."""
import tempfile
import time
import unittest
import os
import httpx
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from starlette.testclient import TestClient
from gpt_pi.config import Settings
from gpt_pi.credentials import CredentialStore
from gpt_pi.webapp import COOKIE, create_app
from test_webapp import FakeCloud


def login(client, subject='synthetic-owner'):
    info = client.get('/api/session').json()
    response = client.post('/api/auth/start', json={}, headers={
        'Origin': 'http://127.0.0.1:8765', 'X-CSRF-Token': info['csrf']})
    state = parse_qs(urlparse(response.json()['url']).query)['state'][0]
    client.get('/auth/callback', params={'code': subject, 'state': state,
                                       'client_id': 'oaiapp_' + subject})
    return client.cookies.get(COOKIE)


class RememberLoginTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.settings = Settings(data_dir=Path(self.temp.name))

    def tearDown(self):
        self.temp.cleanup()

    def test_signed_in_owner_is_not_logged_out_after_half_an_hour(self):
        app = create_app(self.settings, FakeCloud())
        with TestClient(app, base_url=self.settings.origin) as client:
            key = login(client)
            app.state.runtime.sessions[key].touched -= 3600
            response = client.get('/api/session')
            self.assertTrue(response.json()['authenticated'])
            self.assertIn('Max-Age=', response.headers['set-cookie'])

    def test_restart_restores_only_cookie_owner_without_saving_chats(self):
        app = create_app(self.settings, FakeCloud())
        with TestClient(app, base_url=self.settings.origin) as client:
            key = login(client)
            current = app.state.runtime.sessions[key]
            current.chats['synthetic-private-chat'] = {'id': 'synthetic-private-chat', 'messages': []}
            connection = current.connection
        self.assertTrue(connection.token, 'normal shutdown must not revoke remembered credentials')
        restarted = create_app(self.settings, FakeCloud())
        with TestClient(restarted, base_url=self.settings.origin) as client:
            self.assertFalse(client.get('/api/session').json()['authenticated'])
            client.cookies.set(COOKIE, key)
            self.assertTrue(client.get('/api/session').json()['authenticated'])
            self.assertEqual([], client.get('/api/chats').json()['chats'])
            self.assertNotIn('synthetic-access', client.get('/api/session').text)
        files = list(Path(self.temp.name).rglob('*.json'))
        self.assertFalse(any('synthetic-private-chat' in path.read_text() for path in files))

    def test_logout_removes_saved_credentials_and_stale_cookie_cannot_restore(self):
        app = create_app(self.settings, FakeCloud())
        with TestClient(app, base_url=self.settings.origin) as client:
            key = login(client)
            info = client.get('/api/session').json()
            response = client.post('/api/logout', json={}, headers={
                'Origin': self.settings.origin, 'X-CSRF-Token': info['csrf']})
            self.assertEqual(200, response.status_code)
        with TestClient(create_app(self.settings, FakeCloud()), base_url=self.settings.origin) as client:
            client.cookies.set(COOKIE, key)
            self.assertFalse(client.get('/api/session').json()['authenticated'])
        self.assertFalse(any('synthetic-refresh' in path.read_text()
                             for path in Path(self.temp.name).rglob('*.json')))

    def test_rotated_token_is_saved_and_logout_cannot_be_undone_by_late_save(self):
        class RefreshCloud(FakeCloud):
            async def models(self, connection):
                await self.access_token(connection)
                return await super().models(connection)
        cloud = RefreshCloud()
        cloud.transport = httpx.MockTransport(lambda request: httpx.Response(200, json={
            'access_token': 'rotated-access', 'refresh_token': 'rotated-refresh',
            'token_type': 'Bearer', 'expires_in': 3600}))
        app = create_app(self.settings, cloud)
        with TestClient(app, base_url=self.settings.origin) as client:
            key = login(client)
            connection = app.state.runtime.sessions[key].connection
            connection.token['expires_at'] = 1
            self.assertEqual(200, client.get('/api/models').status_code)
            restored = app.state.runtime.credentials.load(key)
            self.assertEqual('rotated-refresh', restored.token['refresh_token'])
            path = app.state.runtime.credentials.path(key)
            if os.name == 'posix':
                self.assertEqual(0o600, path.stat().st_mode & 0o777)
            late_save = connection.persist
            info = client.get('/api/session').json()
            client.post('/api/logout', json={}, headers={
                'Origin': self.settings.origin, 'X-CSRF-Token': info['csrf']})
            late_save()
            self.assertIsNone(app.state.runtime.credentials.load(key))

    def test_saved_account_requires_matching_registration_identity(self):
        app = create_app(self.settings, FakeCloud())
        with TestClient(app, base_url=self.settings.origin) as client:
            key = login(client)
        restarted = create_app(self.settings, FakeCloud())
        restarted.state.runtime.registration['accounts'][0]['subject_hash'] = 'different-identity'
        with TestClient(restarted, base_url=self.settings.origin) as client:
            client.cookies.set(COOKIE, key)
            self.assertFalse(client.get('/api/session').json()['authenticated'])

    def test_second_server_cannot_rotate_same_saved_credentials(self):
        first = CredentialStore(self.temp.name)
        second = CredentialStore(self.temp.name)
        first.acquire()
        try:
            with self.assertRaises(RuntimeError):
                second.acquire()
        finally:
            first.release()
        second.acquire()
        second.release()

    def test_offline_mode_does_not_restore_cloud_access(self):
        with TestClient(create_app(self.settings, FakeCloud()), base_url=self.settings.origin) as client:
            key = login(client)
        offline = Settings(data_dir=self.settings.data_dir, provider='offline')
        with TestClient(create_app(offline, FakeCloud()), base_url=offline.origin) as client:
            client.cookies.set(COOKIE, key)
            self.assertFalse(client.get('/api/session').json()['authenticated'])
            self.assertEqual(401, client.get('/api/models').status_code)

    def test_rejected_refresh_removes_saved_access_but_network_failure_keeps_it(self):
        class RefreshCloud(FakeCloud):
            async def models(self, connection):
                await self.access_token(connection)
                return await super().models(connection)
        cloud = RefreshCloud()
        def unavailable(request):
            raise httpx.ConnectError('synthetic outage')
        cloud.transport = httpx.MockTransport(unavailable)
        app = create_app(self.settings, cloud)
        with TestClient(app, base_url=self.settings.origin) as client:
            key = login(client)
            app.state.runtime.sessions[key].connection.token['expires_at'] = 1
            self.assertEqual(502, client.get('/api/models').status_code)
            self.assertTrue(client.get('/api/session').json()['authenticated'])
            self.assertIsNotNone(app.state.runtime.credentials.load(key))
            cloud.transport = httpx.MockTransport(lambda request: httpx.Response(400, json={'error': 'invalid_grant'}))
            self.assertEqual(401, client.get('/api/models').status_code)
            self.assertIsNone(app.state.runtime.credentials.load(key))
            self.assertFalse(client.get('/api/session').json()['authenticated'])
