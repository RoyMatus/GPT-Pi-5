import asyncio
import json
import time
import unittest
from urllib.parse import parse_qs
import httpx
import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from gpt_pi.cloud import ChatGPT, CloudError, Connection, ISSUER


class CloudTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        cls.key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        cls.jwk = json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(cls.key.public_key()))
        cls.jwk['kid'] = 'synthetic-key'

    def setUp(self):
        self.claims = {'iss': ISSUER, 'aud': 'oaiapp_test', 'sub': 'synthetic-user', 'nonce': 'synthetic-nonce',
                       'iat': int(time.time()), 'exp': int(time.time()) + 300}
        self.scope = 'openid chatgpt.tokens.use.direct'
        self.requests = []

    def transport(self, request):
        self.requests.append(request)
        if request.url.path.endswith('/token'):
            return httpx.Response(200, json={'access_token': 'synthetic-access', 'refresh_token': 'synthetic-refresh',
                'token_type': 'Bearer', 'expires_in': 3600, 'scope': self.scope,
                'id_token': jwt.encode(self.claims, self.key, algorithm='RS256', headers={'kid': 'synthetic-key'})})
        if request.url.path.endswith('jwks.json'):
            return httpx.Response(200, json={'keys': [self.jwk]})
        return httpx.Response(404)

    async def exchange(self):
        cloud = ChatGPT(httpx.MockTransport(self.transport))
        _, pending = await cloud.authorize('urn:uuid:synthetic', 'http://127.0.0.1:8765/auth/callback')
        pending['nonce'] = 'synthetic-nonce'
        return await cloud.exchange(pending, 'synthetic-code', 'oaiapp_test')

    async def test_valid_signed_identity_and_exact_pkce_exchange(self):
        conn = await self.exchange()
        self.assertEqual('synthetic-user', conn.subject)
        self.assertTrue(conn.sharing)
        form = parse_qs(self.requests[0].content.decode())
        self.assertEqual(['oaiapp_test'], form['client_id'])
        self.assertEqual(['http://127.0.0.1:8765/auth/callback'], form['redirect_uri'])
        self.assertGreater(len(form['code_verifier'][0]), 42)
        self.assertNotIn('client_secret', form)

    async def test_wrong_issuer_audience_nonce_expiry_rejected(self):
        for name, value in [('iss', 'https://evil.invalid'), ('aud', 'different-app'),
                            ('nonce', 'different-nonce'), ('exp', 1), ('azp', 'different-app')]:
            original = dict(self.claims)
            self.claims[name] = value
            with self.subTest(name=name), self.assertRaises(CloudError):
                await self.exchange()
            self.claims = original

    async def test_identity_only_does_not_enable_inference(self):
        self.scope = 'openid email'
        conn = await self.exchange()
        self.assertFalse(conn.sharing)
        with self.assertRaises(CloudError) as caught:
            await ChatGPT(httpx.MockTransport(self.transport)).models(conn)
        self.assertEqual('plan_permission', caught.exception.code)

    async def test_models_use_documented_catalog_and_stream_requires_completion(self):
        recorded = []
        def transport(request):
            recorded.append(request)
            if request.method == 'GET':
                return httpx.Response(200, json={'models': [
                    {'slug': 'synthetic-model', 'display_name': 'Synthetic', 'visibility': 'list'},
                    {'slug': 'hidden', 'visibility': 'hidden'}]})
            return httpx.Response(200, text='data: {"type":"response.output_text.delta","delta":"partial"}\n\n',
                                  headers={'Content-Type': 'text/event-stream'})
        cloud = ChatGPT(httpx.MockTransport(transport))
        conn = Connection('oaiapp_test', 'synthetic', 'Test', {'scope': self.scope,
                          'access_token': 'synthetic-access', 'expires_at': time.time() + 3600})
        self.assertEqual([{'id': 'synthetic-model', 'name': 'Synthetic'}], await cloud.models(conn))
        parts = []
        with self.assertRaises(CloudError) as caught:
            async for part in cloud.stream(conn, 'synthetic-model', [{'role': 'user', 'content': 'Synthetic'}]):
                parts.append(part)
        self.assertEqual(['partial'], parts)
        self.assertEqual('incomplete', caught.exception.code)
        payload = json.loads(recorded[-1].content)
        self.assertFalse(payload['store'])
        self.assertTrue(payload['stream'])
        self.assertNotIn('previous_response_id', payload)

    async def test_refresh_serialized_and_revocation_endpoint_pinned(self):
        counter = []
        async def transport(request):
            counter.append(request)
            if request.url.path.endswith('/token'):
                await asyncio.sleep(.01)
                return httpx.Response(200, json={'access_token': 'synthetic-new', 'refresh_token': 'rotated',
                    'token_type': 'Bearer', 'expires_in': 3600})
            return httpx.Response(200, json={'revocation_endpoint': 'https://evil.invalid/steal'})
        cloud = ChatGPT(httpx.MockTransport(transport))
        conn = Connection('oaiapp_test', 'synthetic', 'Test', {'scope': self.scope,
                          'access_token': 'synthetic-old', 'refresh_token': 'synthetic-refresh', 'expires_at': 1})
        result = await asyncio.gather(cloud.access_token(conn), cloud.access_token(conn))
        self.assertEqual(['synthetic-new', 'synthetic-new'], result)
        self.assertEqual(1, len(counter))
        self.assertFalse(await cloud.revoke(conn))
        self.assertEqual({}, conn.token)
        self.assertFalse(any(r.url.host == 'evil.invalid' for r in counter))

    async def test_temporary_refresh_failure_preserves_credentials(self):
        def transport(request):
            raise httpx.ConnectError('synthetic network outage', request=request)
        cloud = ChatGPT(httpx.MockTransport(transport))
        conn = Connection('oaiapp_test', 'synthetic', 'Test', {'scope': self.scope,
                          'access_token': 'old', 'refresh_token': 'retained', 'expires_at': 1})
        with self.assertRaises(CloudError) as error:
            await cloud.access_token(conn)
        self.assertEqual('connection', error.exception.code)
        self.assertEqual(502, error.exception.status)
        self.assertEqual('retained', conn.token['refresh_token'])

    async def test_terminal_refresh_failure_requires_sign_in(self):
        cloud = ChatGPT(httpx.MockTransport(lambda request:
            httpx.Response(400, json={'error': 'invalid_grant'})))
        conn = Connection('oaiapp_test', 'synthetic', 'Test', {'scope': self.scope,
                          'access_token': 'old', 'refresh_token': 'expired', 'expires_at': 1})
        with self.assertRaises(CloudError) as error:
            await cloud.access_token(conn)
        self.assertEqual('session_expired', error.exception.code)
