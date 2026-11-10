"""ChatGPT plan OAuth and Responses. Contract checked 2026-11-10.

https://developers.openai.com/siwc/token-sharing-open-source
Authlib handles OAuth/PKCE; PyJWT verifies OIDC. No browser credential extraction.
"""
import asyncio
import json
import secrets
import time
from dataclasses import dataclass, field
from urllib.parse import urlparse

import httpx
import jwt
from authlib.integrations.httpx_client import AsyncOAuth2Client

ISSUER = 'https://auth.openai.com'
AUTHORIZE = ISSUER + '/api/accounts/authorize'
TOKEN = ISSUER + '/api/accounts/oauth/token'
RESOURCE = 'https://api.openai.com/v1'
SCOPE = 'openid profile email offline_access resource.invoke chatgpt.tokens.use.direct'


class CloudError(Exception):
    def __init__(self, code='connection', status=502):
        super().__init__(code)
        self.code, self.status = code, status


@dataclass
class Connection:
    client_id: str
    subject: str
    name: str
    token: dict = field(repr=False)
    refresh_lock: asyncio.Lock = field(default_factory=asyncio.Lock, repr=False)
    persist: object = field(default=None, repr=False)
    invalidate: object = field(default=None, repr=False)

    @property
    def sharing(self):
        return 'chatgpt.tokens.use.direct' in self.token.get('scope', '').split()


class ChatGPT:
    def __init__(self, transport=None):
        self.transport = transport

    def client(self):
        return httpx.AsyncClient(transport=self.transport, timeout=httpx.Timeout(30, connect=10),
                                 follow_redirects=False)

    def oauth(self, client_id, **kwargs):
        return AsyncOAuth2Client(client_id=client_id, token_endpoint_auth_method='none',
                                 code_challenge_method='S256', transport=self.transport,
                                 timeout=20, **kwargs)

    async def authorize(self, host_id, redirect_uri, client_id=None):
        pending = dict(state=secrets.token_urlsafe(32), nonce=secrets.token_urlsafe(32),
                       verifier=secrets.token_urlsafe(48), redirect_uri=redirect_uri,
                       client_id=client_id, created=time.monotonic())
        async with self.oauth(client_id or 'dynamic_agent_client', scope=SCOPE,
                              redirect_uri=redirect_uri) as client:
            extra = {'ext_agent_host_id': host_id, 'resource': RESOURCE, 'nonce': pending['nonce']}
            if not client_id:
                extra['agent_name_hint'] = 'GPT-Pi 5'
            url, _ = client.create_authorization_url(AUTHORIZE, state=pending['state'],
                                                    code_verifier=pending['verifier'], **extra)
        return url, pending

    async def exchange(self, pending, code, issued_client_id):
        client_id = pending.get('client_id') or issued_client_id
        if not isinstance(client_id, str) or not client_id.startswith('oaiapp_'):
            raise CloudError('invalid_login', 400)
        if issued_client_id and issued_client_id != client_id:
            raise CloudError('invalid_login', 400)
        try:
            async with self.oauth(client_id, redirect_uri=pending['redirect_uri']) as client:
                token = await client.fetch_token(TOKEN, code=code, code_verifier=pending['verifier'],
                                                 resource=RESOURCE, grant_type='authorization_code')
            async with self.client() as client:
                keys = await client.get(ISSUER + '/.well-known/jwks.json')
                keys.raise_for_status()
            header = jwt.get_unverified_header(token['id_token'])
            candidates = [k for k in keys.json()['keys'] if k.get('kid') == header.get('kid')]
            if len(candidates) != 1:
                raise CloudError('invalid_login', 400)
            key = jwt.PyJWK.from_dict(candidates[0], algorithm='RS256').key
            claims = jwt.decode(token['id_token'], key, algorithms=['RS256'], audience=client_id,
                                issuer=ISSUER, options={'require': ['exp', 'iat', 'sub', 'nonce', 'aud', 'iss']})
            if not secrets.compare_digest(str(claims['nonce']), pending['nonce']):
                raise CloudError('invalid_login', 400)
            if claims.get('azp', client_id) != client_id or not isinstance(claims['sub'], str) or not claims['sub']:
                raise CloudError('invalid_login', 400)
            if not token.get('access_token') or token.get('token_type', '').lower() != 'bearer':
                raise CloudError('invalid_login', 400)
            return Connection(client_id, claims['sub'], str(claims.get('name') or 'Мой аккаунт')[:80], dict(token))
        except CloudError:
            raise
        except (jwt.PyJWTError, KeyError, ValueError, TypeError):
            raise CloudError('invalid_login', 400) from None
        except Exception:
            raise CloudError('login_failed', 502) from None

    async def access_token(self, connection):
        async with connection.refresh_lock:
            token = connection.token
            if not token:
                raise CloudError('session_expired', 401)
            if token.get('expires_at', 0) > time.time() + 60:
                if connection.persist:
                    connection.persist()
                return token['access_token']
            if not token.get('refresh_token'):
                raise CloudError('session_expired', 401)
            try:
                async with self.oauth(connection.client_id) as client:
                    updated = await client.refresh_token(TOKEN, refresh_token=token['refresh_token'], resource=RESOURCE)
                if connection.token is not token:
                    raise CloudError('session_expired', 401)
                updated.setdefault('scope', token.get('scope', ''))
                updated.setdefault('refresh_token', token['refresh_token'])
                updated.setdefault('id_token', token.get('id_token'))
                if not updated.get('access_token'):
                    raise CloudError('connection', 502)
                connection.token = dict(updated)
                if connection.persist:
                    connection.persist()
                if not connection.sharing:
                    raise CloudError('plan_permission', 403)
                return updated['access_token']
            except CloudError:
                raise
            except Exception as exc:
                terminal = {'invalid_grant', 'invalid_refresh_token', 'token_expired',
                            'refresh_token_expired', 'refresh_token_invalidated', 'refresh_token_reused'}
                if getattr(exc, 'error', None) in terminal:
                    connection.token = {}
                    if connection.invalidate:
                        connection.invalidate()
                    raise CloudError('session_expired', 401) from None
                # A temporary network/server failure must not erase renewable credentials.
                raise CloudError('connection', 502) from None

    @staticmethod
    def check(response):
        if response.status_code >= 400:
            mapping = {401: ('access_rejected', 401), 403: ('access_denied', 403), 429: ('usage_limit', 429)}
            code, status = mapping.get(response.status_code, ('connection', 502))
            raise CloudError(code, status)

    async def models(self, connection):
        if not connection.sharing:
            raise CloudError('plan_permission', 403)
        token = await self.access_token(connection)
        try:
            async with self.client() as client:
                response = await client.get(RESOURCE + '/models', headers={'Authorization': f'Bearer {token}'})
                self.check(response)
                return [{'id': m['slug'], 'name': m.get('display_name', m['slug'])}
                        for m in response.json().get('models', [])
                        if m.get('visibility') == 'list' and isinstance(m.get('slug'), str)]
        except (httpx.HTTPError, ValueError, KeyError):
            raise CloudError() from None

    async def stream(self, connection, model, messages):
        if not connection.sharing:
            raise CloudError('plan_permission', 403)
        token = await self.access_token(connection)
        payload = {'model': model, 'input': messages, 'store': False, 'stream': True,
                   'instructions': 'Ты личный помощник. Отвечай ясно, на языке пользователя. '
                   'Не выдумывай факты. У тебя нет доступа к устройству или внешним инструментам.'}
        completed = False
        try:
            async with self.client() as client:
                async with client.stream('POST', RESOURCE + '/responses', json=payload,
                                         headers={'Authorization': f'Bearer {token}'}) as response:
                    self.check(response)
                    data = []
                    async for line in response.aiter_lines():
                        if len(line) > 1_000_000:
                            raise CloudError('invalid_response')
                        if line.startswith('data:'):
                            data.append(line[5:].lstrip())
                        elif not line and data:
                            raw, data = '\n'.join(data), []
                            if raw == '[DONE]':
                                continue
                            event = json.loads(raw)
                            kind = event.get('type')
                            if kind == 'response.output_text.delta':
                                yield event.get('delta', '')
                            elif kind == 'response.completed':
                                completed = True
                                break
                            elif kind in {'response.failed', 'response.incomplete', 'error'}:
                                error = event.get('response', {}).get('error') or event.get('error') or {}
                                code = error.get('code', '') if isinstance(error, dict) else ''
                                raise CloudError('usage_limit' if 'usage' in code or 'rate_limit' in code else 'incomplete')
            if not completed:
                raise CloudError('incomplete')
        except (httpx.HTTPError, ValueError, KeyError):
            raise CloudError('connection') from None

    async def revoke(self, connection):
        token, connection.token = connection.token, {}
        refresh = token.get('refresh_token')
        if not refresh:
            return True
        try:
            async with self.client() as client:
                metadata = await client.get(ISSUER + '/.well-known/openid-configuration', timeout=5)
                metadata.raise_for_status()
                endpoint = metadata.json().get('revocation_endpoint', '')
                parsed = urlparse(endpoint)
                if parsed.scheme != 'https' or parsed.netloc != 'auth.openai.com':
                    return False
                response = await client.post(endpoint, data={'token': refresh, 'token_type_hint': 'refresh_token',
                                                            'client_id': connection.client_id}, timeout=5)
                return response.status_code == 200
        except (httpx.HTTPError, ValueError):
            return False
