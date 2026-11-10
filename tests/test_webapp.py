import asyncio
import json
from pathlib import Path
import tempfile
import threading
import time
import unittest
from urllib.parse import parse_qs, urlparse

from starlette.testclient import TestClient
from gpt_pi.cloud import ChatGPT, CloudError, Connection
from gpt_pi.config import Settings
from gpt_pi.webapp import COOKIE, create_app


class FakeCloud(ChatGPT):
    def __init__(self):
        super().__init__()
        self.calls = []
        self.started = threading.Event()
        self.stopped = threading.Event()
        self.wait = False
        self.fail = False

    async def exchange(self, pending, code, issued_client_id):
        self.calls.append('exchange')
        return Connection(issued_client_id or pending['client_id'], code, 'Synthetic account',
                          {'access_token': 'synthetic-access', 'refresh_token': 'synthetic-refresh',
                           'scope': 'chatgpt.tokens.use.direct', 'expires_at': time.time() + 3600})

    async def models(self, connection):
        return [{'id': 'synthetic-model', 'name': 'Test model'}]

    async def stream(self, connection, model, messages):
        self.calls.append(messages)
        self.started.set()
        try:
            yield 'Synthetic '
            if self.wait:
                await asyncio.sleep(30)
            if self.fail:
                raise CloudError('usage_limit')
            yield 'answer'
        finally:
            self.stopped.set()

    async def revoke(self, connection):
        connection.token = {}
        return True


class WebTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.settings = Settings(data_dir=Path(self.temp.name))
        self.cloud = FakeCloud()
        self.app = create_app(self.settings, self.cloud)
        self.client = TestClient(self.app, base_url=self.settings.origin).__enter__()
        self.info = self.client.get('/api/session').json()

    def tearDown(self):
        self.client.__exit__(None, None, None)
        self.temp.cleanup()

    def post(self, path, data=None, client=None):
        client = client or self.client
        info = client.get('/api/session').json()
        return client.post(path, json=data or {}, headers={'Origin': self.settings.origin, 'X-CSRF-Token': info['csrf']})

    def login(self, subject='synthetic-A', client=None, registration=None):
        client = client or self.client
        result = self.post('/api/auth/start', {'registration': registration}, client)
        self.assertEqual(200, result.status_code)
        params = parse_qs(urlparse(result.json()['url']).query)
        callback = client.get('/auth/callback', params={'code': subject, 'state': params['state'][0],
                                                       'client_id': registration or 'oaiapp_synthetic'}, follow_redirects=False)
        self.assertEqual('/?connected=1', callback.headers['location'])
        self.assertTrue(client.get('/api/session').json()['authenticated'])
        client.get('/api/models')
        return params

    def test_boot_anonymous_and_headers(self):
        self.assertFalse(self.info['authenticated'])
        response = self.client.get('/')
        self.assertEqual(200, response.status_code)
        self.assertIn('GPT-Pi 5', response.text)
        self.assertEqual('no-store', response.headers['cache-control'])
        self.assertIn("script-src 'self'", response.headers['content-security-policy'])
        self.assertEqual(401, self.client.get('/api/chats').status_code)

    def test_callback_expiry_and_denied_consent_do_not_exchange_code(self):
        for expired in (True, False):
            result = self.post('/api/auth/start').json()
            params = parse_qs(urlparse(result['url']).query)
            session = self.app.state.runtime.sessions[self.client.cookies.get(COOKIE)]
            if expired:
                session.pending['created'] -= 601
            response = self.client.get('/auth/callback', params={
                'state': params['state'][0], 'error': 'access_denied'}, follow_redirects=False)
            self.assertIn('login_expired' if expired else 'login_cancelled', response.headers['location'])
            self.assertIsNone(session.pending)
        self.assertEqual([], self.cloud.calls)

    def test_model_and_body_limits_are_enforced_before_upstream(self):
        self.login()
        chat = self.post('/api/chats').json()
        url = '/api/chats/' + chat['id'] + '/messages'
        for payload in ({'text': 'Synthetic', 'model': 'unavailable'},
                        {'text': 'x' * 8001, 'model': 'synthetic-model'},
                        {'text': {'nested': 'bad'}, 'model': 'synthetic-model'}):
            self.assertEqual(400, self.post(url, payload).status_code)
        self.assertEqual(413, self.post(url, {'text': 'x' * 40000}).status_code)
        self.assertEqual([], self.client.get('/api/chats/' + chat['id']).json()['messages'])

    def test_host_origin_and_csrf_boundaries(self):
        self.assertEqual(403, self.client.get('/', headers={'Host': 'evil.invalid'}).status_code)
        self.assertEqual(403, self.client.get('/api/session', headers={'Sec-Fetch-Site': 'cross-site'}).status_code)
        self.assertEqual(403, self.client.post('/api/auth/start', json={}).status_code)
        self.assertEqual(403, self.client.post('/api/auth/start', json={}, headers={
            'Origin': 'https://evil.invalid', 'X-CSRF-Token': self.info['csrf']}).status_code)
        self.assertEqual(307, self.client.get('/', headers={'Host': 'localhost:8765'}, follow_redirects=False).status_code)

    def test_pkce_no_credentials_and_callback_requires_state(self):
        result = self.post('/api/auth/start').json()
        params = parse_qs(urlparse(result['url']).query)
        self.assertEqual('S256', params['code_challenge_method'][0])
        self.assertEqual('dynamic_agent_client', params['client_id'][0])
        self.assertEqual(self.settings.origin + '/auth/callback', params['redirect_uri'][0])
        self.assertNotIn('code_verifier', params)
        result = self.client.get('/auth/callback?code=fake&state=wrong', follow_redirects=False)
        self.assertIn('invalid_login', result.headers['location'])
        self.assertEqual([], self.cloud.calls)

    def test_login_rotates_session_and_callback_is_single_use(self):
        old_cookie = self.client.cookies.get(COOKIE)
        params = self.login()
        self.assertNotEqual(old_cookie, self.client.cookies.get(COOKIE))
        self.assertNotIn('synthetic-access', self.client.get('/api/session').text)
        replay = self.client.get('/auth/callback', params={'code': 'synthetic-A', 'state': params['state'][0],
                                                         'client_id': 'oaiapp_synthetic'}, follow_redirects=False)
        self.assertNotIn('connected=1', replay.headers['location'])
        self.assertEqual(1, self.cloud.calls.count('exchange'))

    def test_text_stream_and_session_scoped_history(self):
        self.login()
        chat = self.post('/api/chats').json()
        response = self.post('/api/chats/' + chat['id'] + '/messages', {'text': 'Synthetic question', 'model': 'synthetic-model'})
        self.assertIn('"type": "done"', response.text)
        item = self.client.get('/api/chats/' + chat['id']).json()
        self.assertEqual('Synthetic answer', item['messages'][1]['content'])
        self.assertFalse(item['messages'][1]['incomplete'])
        other = TestClient(self.app, base_url=self.settings.origin)
        other.get('/api/session')
        self.login('synthetic-B', other)
        self.assertEqual([], other.get('/api/chats').json()['chats'])
        for target in (chat['id'], 'unknown'):
            self.assertEqual(404, other.get('/api/chats/' + target).status_code)
            self.assertEqual(404, self.post('/api/chats/' + target + '/messages',
                {'text': 'Synthetic', 'model': 'synthetic-model'}, other).status_code)

    def test_provider_failure_keeps_incomplete_marker(self):
        self.login()
        self.cloud.fail = True
        chat = self.post('/api/chats').json()
        response = self.post('/api/chats/' + chat['id'] + '/messages', {'text': 'Synthetic', 'model': 'synthetic-model'})
        self.assertIn('usage_limit', response.text)
        self.assertNotIn('"type": "done"', response.text)
        self.assertTrue(self.client.get('/api/chats/' + chat['id']).json()['messages'][-1]['incomplete'])

    def test_logout_cancels_upstream_and_drops_late_response(self):
        self.login()
        self.cloud.wait = True
        chat = self.post('/api/chats').json()
        response = []
        worker = threading.Thread(target=lambda: response.append(self.post('/api/chats/' + chat['id'] + '/messages',
            {'text': 'Synthetic', 'model': 'synthetic-model'})))
        worker.start()
        self.assertTrue(self.cloud.started.wait(3))
        result = self.post('/api/logout')
        worker.join(3)
        self.assertFalse(worker.is_alive())
        self.assertTrue(self.cloud.stopped.wait(1))
        self.assertEqual(200, result.status_code)
        self.assertNotIn('answer', response[0].text)
        self.assertEqual(401, self.client.get('/api/chats/' + chat['id']).status_code)

    def test_expiry_and_restart_do_not_restore_tokens_or_chats(self):
        self.login()
        chat = self.post('/api/chats').json()
        active = self.app.state.runtime.sessions[self.client.cookies.get(COOKIE)]
        active.touched -= 1900
        self.assertEqual(401, self.client.get('/api/chats/' + chat['id']).status_code)
        saved = self.app.state.runtime.path.read_text()
        self.assertNotIn('synthetic-access', saved)
        self.assertNotIn('synthetic-refresh', saved)
        self.assertNotIn('synthetic-A', saved)
        with TestClient(create_app(self.settings, self.cloud), base_url=self.settings.origin) as restarted:
            self.assertFalse(restarted.get('/api/session').json()['authenticated'])

    def test_returning_registration_cannot_switch_identity(self):
        self.login()
        self.post('/api/logout')
        result = self.post('/api/auth/start', {'registration': 'oaiapp_synthetic'}).json()
        params = parse_qs(urlparse(result['url']).query)
        result = self.client.get('/auth/callback', params={'code': 'synthetic-B', 'state': params['state'][0]}, follow_redirects=False)
        self.assertIn('invalid_login', result.headers['location'])
        self.assertFalse(self.client.get('/api/session').json()['authenticated'])
