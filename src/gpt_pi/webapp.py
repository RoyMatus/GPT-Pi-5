"""Loopback-only personal prototype with remembered login and RAM-only chats."""
import asyncio
import contextlib
import hashlib
import json
import os
import secrets
import time
from dataclasses import dataclass, field
from importlib.resources import files
from pathlib import Path
from uuid import uuid4

from starlette.applications import Starlette
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse, Response, StreamingResponse
from starlette.routing import Route

from . import __version__
from .cloud import ChatGPT, CloudError
from .config import Settings
from .voice import LocalVoice, VoiceError, MAX_AUDIO, MAX_SPEECH_TEXT, validate_audio
from .audio_devices import AudioDevices
from .credentials import CredentialStore
from .dashboard.markets import routes as market_routes

COOKIE = 'gpt_pi_session'


@dataclass
class Session:
    dashboard: dict = field(default_factory=dict, repr=False)
    csrf: str = field(default_factory=lambda: secrets.token_urlsafe(32))
    touched: float = field(default_factory=time.monotonic)
    alive: bool = True
    connection: object = field(default=None, repr=False)
    pending: dict | None = field(default=None, repr=False)
    chats: dict = field(default_factory=dict, repr=False)
    models: list = field(default_factory=list)
    tasks: set = field(default_factory=set, repr=False)
    saved_token: object = field(default=None, repr=False)

    def stop(self):
        self.alive = False
        self.pending = None
        self.chats.clear()
        self.dashboard.clear()
        self.models.clear()
        for task in list(self.tasks):
            task.cancel()


class Runtime:
    def __init__(self, settings, cloud):
        self.settings, self.cloud = settings, cloud
        self.voice = LocalVoice(settings.data_dir)
        self.audio_devices = AudioDevices()
        self.sessions = {}
        self.background = set()
        self.path = Path(settings.data_dir) / 'registration.json'
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        if self.path.exists():
            self.registration = json.loads(self.path.read_text('utf-8'))
        else:
            self.registration = {'host_id': 'urn:uuid:' + str(uuid4()), 'accounts': []}
            self.save_registration()
        self.credentials = CredentialStore(settings.data_dir) if settings.remember_login else None

    def remember(self, key, session):
        if (not self.credentials or not session.alive or not session.connection
                or self.sessions.get(key) is not session):
            return
        if session.saved_token is session.connection.token:
            return
        try:
            self.credentials.save(key, session.connection)
            session.saved_token = session.connection.token
        except OSError:
            raise CloudError('session_storage', 503) from None

    def attach(self, key, session):
        if self.credentials:
            session.connection.persist = lambda: self.remember(key, session)
        session.connection.invalidate = lambda: self.forget(key, session)

    def forget(self, key, session):
        if self.credentials:
            try:
                self.credentials.delete(key)
            except OSError:
                raise CloudError('session_storage', 503) from None
        session.stop()
        self.sessions.pop(key, None)

    def save_registration(self):
        temp = self.path.with_suffix('.tmp')
        fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, 'w', encoding='utf-8') as output:
            json.dump(self.registration, output)
        os.replace(temp, self.path)

    def defer_revoke(self, session):
        if session.connection:
            connection, session.connection = session.connection, None
            task = asyncio.create_task(self.cloud.revoke(connection))
            self.background.add(task)
            task.add_done_callback(self.background.discard)

    def prune(self):
        for key, session in list(self.sessions.items()):
            if self.credentials and session.connection:
                continue
            if time.monotonic() - session.touched > self.settings.idle_seconds:
                session.stop()
                self.defer_revoke(session)
                del self.sessions[key]

    def session(self, request, authenticated=False):
        self.prune()
        key = request.cookies.get(COOKIE)
        session = self.sessions.get(key)
        if session is None and self.credentials and self.settings.provider == 'chatgpt':
            connection = self.credentials.load(key)
            if connection:
                identity = hashlib.sha256(connection.subject.encode()).hexdigest()
                if any(a['client_id'] == connection.client_id and a.get('subject_hash') == identity
                       for a in self.registration['accounts']):
                    session = Session(connection=connection, saved_token=connection.token)
                    self.sessions[key] = session
                    self.attach(key, session)
        if not session or not session.alive or (authenticated and not session.connection):
            raise HTTPException(401, 'session_expired')
        return key, session

    def mutation(self, request, authenticated=False):
        key, session = self.session(request, authenticated)
        if request.headers.get('origin') != self.settings.origin or not secrets.compare_digest(
                request.headers.get('x-csrf-token', ''), session.csrf):
            raise HTTPException(403, 'forbidden')
        session.touched = time.monotonic()
        return key, session

    def new(self):
        self.prune()
        if len(self.sessions) >= 16:
            raise HTTPException(429, 'too_many_sessions')
        key, session = secrets.token_urlsafe(32), Session()
        self.sessions[key] = session
        return key, session


def cookie(response, key, remembered=False):
    response.set_cookie(COOKIE, key, httponly=True, samesite='lax', path='/',
                        max_age=400 * 86400 if remembered else None)
    return response


async def body(request):
    if request.headers.get('content-type', '').split(';')[0] != 'application/json':
        raise HTTPException(415, 'json_required')
    data = bytearray()
    async for chunk in request.stream():
        data.extend(chunk)
        if len(data) > 32000:
            raise HTTPException(413, 'too_large')
    try:
        result = json.loads(data)
        if not isinstance(result, dict):
            raise ValueError()
        return result
    except ValueError:
        raise HTTPException(400, 'invalid_request') from None


def event(kind, **data):
    return 'data: ' + json.dumps({'type': kind, **data}, ensure_ascii=False) + '\n\n'


class LocalBoundary:
    def __init__(self, app, settings):
        self.app, self.settings = app, settings

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)
        headers = dict(scope['headers'])
        host = headers.get(b'host', b'').decode()
        valid = {f'127.0.0.1:{self.settings.port}', f'localhost:{self.settings.port}'}
        site = headers.get(b'sec-fetch-site', b'').decode()
        # OAuth redirects retain cross-site Fetch Metadata through the landing
        # navigation. Only the inert app shell may load as a top-level document;
        # API reads/writes and embedded documents remain blocked.
        landing = (scope['path'] == '/' and scope['method'] == 'GET'
                   and headers.get(b'sec-fetch-mode') == b'navigate'
                   and headers.get(b'sec-fetch-dest') == b'document')
        if host not in valid or (site == 'cross-site'
                                 and scope['path'] != '/auth/callback' and not landing):
            return await Response('Forbidden', status_code=403)(scope, receive, send)

        async def secure_send(message):
            if message['type'] == 'http.response.start':
                message['headers'] += [(b'cache-control', b'no-store'), (b'x-content-type-options', b'nosniff'),
                    (b'x-frame-options', b'DENY'), (b'referrer-policy', b'no-referrer'),
                    (b'permissions-policy', b'microphone=(self), camera=()'),
                    (b'content-security-policy', b"default-src 'none'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
                     b"img-src 'self' data:; connect-src 'self'; media-src 'self' blob:; worker-src 'self'; font-src 'self'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'")]
            await send(message)
        await self.app(scope, receive, secure_send)


def create_app(settings=None, cloud=None):
    settings = settings or Settings.from_env(os.environ)
    runtime = Runtime(settings, cloud or ChatGPT())

    @contextlib.asynccontextmanager
    async def lifespan(app):
        if runtime.credentials:
            runtime.credentials.acquire()
        async def reap():
            while True:
                await asyncio.sleep(5)
                runtime.prune()
        reaper = asyncio.create_task(reap())
        try:
            yield
        finally:
            reaper.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await reaper
            try:
                for session in list(runtime.sessions.values()):
                    session.stop()
                    if not runtime.credentials or session.saved_token is None:
                        runtime.defer_revoke(session)
                if runtime.background:
                    await asyncio.gather(*runtime.background, return_exceptions=True)
            finally:
                if runtime.credentials:
                    runtime.credentials.release()

    async def home(request):
        if request.url.hostname == 'localhost':
            return RedirectResponse(settings.origin)
        return Response(files('gpt_pi').joinpath('web/index.html').read_bytes(), media_type='text/html')

    async def asset(request):
        name = request.path_params['name']
        if name not in {'app.js', 'app.css', 'app.js.LEGAL.txt', 'recorder-worklet.js'}:
            raise HTTPException(404)
        path = files('gpt_pi').joinpath('web/assets/' + name)
        if not path.is_file():
            return Response('Build the interface: npm ci && npm run build', status_code=503)
        content_type = 'text/javascript' if name.endswith('.js') else 'text/css' if name.endswith('.css') else 'text/plain'
        return Response(path.read_bytes(), media_type=content_type)

    async def health(request):
        return JSONResponse({'status': 'ok', 'mode': settings.provider, 'version': __version__})

    async def capabilities(request):
        return JSONResponse({'text_chat': settings.provider == 'chatgpt', 'chatgpt_sign_in': settings.provider == 'chatgpt',
                             'voice': runtime.voice.available(), 'voice_mode': 'local',
                             'image_generation': False, 'private_profiles': False})

    async def audio_devices(request):
        return JSONResponse(await runtime.audio_devices.status())

    async def session_info(request):
        try:
            key, session = runtime.session(request)
        except HTTPException:
            key, session = runtime.new()
        conn = session.connection
        data = {'authenticated': bool(conn), 'csrf': session.csrf, 'provider': settings.provider,
                'account': {'name': conn.name, 'sharing': conn.sharing} if conn else None,
                'registrations': [{'id': a['client_id'], 'name': f'Подключение {i + 1}'}
                                  for i, a in enumerate(runtime.registration['accounts'])]}
        data['remember_login'] = settings.remember_login
        return cookie(JSONResponse(data), key, bool(conn) and settings.remember_login)

    async def auth_start(request):
        _, session = runtime.mutation(request)
        if settings.provider != 'chatgpt':
            raise HTTPException(409, 'offline_mode')
        if session.connection:
            raise HTTPException(409, 'already_connected')
        data = await body(request)
        client_id = data.get('registration')
        account = next((a for a in runtime.registration['accounts'] if a['client_id'] == client_id), None)
        if client_id and not account:
            raise HTTPException(400, 'invalid_request')
        url, pending = await runtime.cloud.authorize(runtime.registration['host_id'], settings.origin + '/auth/callback', client_id)
        pending['subject_hash'] = account.get('subject_hash') if account else None
        if not session.alive:
            raise HTTPException(401, 'session_expired')
        session.pending = pending
        return JSONResponse({'url': url})

    async def callback(request):
        try:
            old_key, session = runtime.session(request)
            pending = session.pending
            state = request.query_params.get('state', '')
            if not pending or not secrets.compare_digest(state, pending['state']):
                raise CloudError('invalid_login', 400)
            session.pending = None  # Single use, even if the exchange fails.
            if time.monotonic() - pending['created'] > 600:
                raise CloudError('login_expired', 400)
            if request.query_params.get('error'):
                raise CloudError('login_cancelled', 400)
            code = request.query_params.get('code')
            if not code or len(code) > 8192:
                raise CloudError('invalid_login', 400)
            conn = await runtime.cloud.exchange(pending, code, request.query_params.get('client_id'))
            subject_hash = hashlib.sha256(conn.subject.encode()).hexdigest()
            if not session.alive or (pending.get('subject_hash') and pending['subject_hash'] != subject_hash):
                await runtime.cloud.revoke(conn)
                raise CloudError('invalid_login', 400)
            accounts = runtime.registration['accounts']
            if not any(a['client_id'] == conn.client_id for a in accounts):
                accounts.append({'client_id': conn.client_id, 'subject_hash': subject_hash})
                runtime.save_registration()
            session.stop()
            del runtime.sessions[old_key]
            key, replacement = runtime.new()
            replacement.connection = conn
            runtime.attach(key, replacement)
            try:
                runtime.remember(key, replacement)
            except CloudError:
                runtime.forget(key, replacement)
                await runtime.cloud.revoke(conn)
                raise
            return cookie(RedirectResponse('/?connected=1', status_code=303), key, settings.remember_login)
        except (CloudError, HTTPException) as exc:
            error = exc.code if isinstance(exc, CloudError) else 'login_expired'
            return RedirectResponse('/?error=' + error, status_code=303)

    async def logout(request):
        key, session = runtime.mutation(request)
        runtime.forget(key, session)
        revoked = True
        if session.connection:
            revoked = await runtime.cloud.revoke(session.connection)
            session.connection = None
        result = JSONResponse({'signed_out': True, 'revocation_confirmed': revoked})
        result.delete_cookie(COOKIE, path='/')
        return result

    async def models(request):
        _, session = runtime.session(request, True)
        result = await runtime.cloud.models(session.connection)
        if not session.alive:
            raise HTTPException(401, 'session_expired')
        session.models = result
        return JSONResponse({'models': result})

    async def chats(request):
        if request.method == 'GET':
            _, session = runtime.session(request, True)
            return JSONResponse({'chats': [{'id': c['id'], 'title': c['title']} for c in session.chats.values()]})
        _, session = runtime.mutation(request, True)
        if len(session.chats) >= 25:
            raise HTTPException(409, 'chat_limit')
        chat = {'id': uuid4().hex, 'title': 'Новый разговор', 'messages': []}
        session.chats[chat['id']] = chat
        return JSONResponse(chat, status_code=201)

    async def chat(request):
        _, session = runtime.session(request, True)
        item = session.chats.get(request.path_params['chat_id'])
        if item is None:
            raise HTTPException(404, 'not_found')
        return JSONResponse(item)

    async def cancel(request):
        _, session = runtime.mutation(request, True)
        for task in list(session.tasks):
            task.cancel()
        return JSONResponse({'cancelled': True})

    async def voice_request(request):
        _, session = runtime.mutation(request, True)
        if session.tasks:
            raise HTTPException(409, 'busy')

        async def work():
            async with asyncio.timeout(100):
                if request.url.path.endswith('/transcribe'):
                    if request.headers.get('content-type', '').split(';')[0] != 'audio/wav':
                        raise HTTPException(415, 'wav_required')
                    data = bytearray()
                    async for chunk in request.stream():
                        if len(data) + len(chunk) > MAX_AUDIO:
                            raise HTTPException(413, 'too_large')
                        data.extend(chunk)
                    validate_audio(data)
                    text = await runtime.voice.transcribe(bytes(data))
                    return JSONResponse({'text': text})
                data = await body(request)
                text = data.get('text')
                if not isinstance(text, str) or not 1 <= len(text.strip()) <= MAX_SPEECH_TEXT:
                    raise HTTPException(400, 'speech_text_limit')
                audio = await runtime.voice.speak(text.strip())
                return Response(audio, media_type='audio/wav')

        task = asyncio.create_task(work())
        session.tasks.add(task)
        try:
            response = await task
            if not session.alive:
                raise HTTPException(401, 'session_expired')
            return response
        except asyncio.CancelledError:
            raise HTTPException(409 if session.alive else 401,
                                'cancelled' if session.alive else 'session_expired') from None
        except TimeoutError:
            raise VoiceError('voice_timeout', 504) from None
        finally:
            task.cancel()
            session.tasks.discard(task)

    async def message(request):
        _, session = runtime.mutation(request, True)
        data = await body(request)
        item = session.chats.get(request.path_params['chat_id'])
        if item is None:
            raise HTTPException(404, 'not_found')
        text = data.get('text')
        if not isinstance(text, str) or not text.strip() or len(text) > 8000:
            raise HTTPException(400, 'invalid_message')
        if session.tasks:
            raise HTTPException(409, 'busy')
        if data.get('model') not in {m['id'] for m in session.models}:
            raise HTTPException(400, 'select_model')
        if len(item['messages']) >= 100 or sum(len(m['content']) for m in item['messages']) + len(text) > 60000:
            raise HTTPException(409, 'conversation_limit')
        history = [{'role': m['role'], 'content': m['content']} for m in item['messages'] if not m.get('incomplete')]
        history.append({'role': 'user', 'content': text.strip()})
        item['messages'].append(history[-1])
        if len(item['messages']) == 1:
            item['title'] = text.strip()[:60]
        answer = {'role': 'assistant', 'content': '', 'incomplete': True}
        item['messages'].append(answer)
        queue = asyncio.Queue(maxsize=32)

        async def generate():
            try:
                async with asyncio.timeout(180):
                    async for delta in runtime.cloud.stream(session.connection, data['model'], history):
                        if not session.alive:
                            return
                        if len(answer['content']) + len(delta) > 100000:
                            raise CloudError('response_limit')
                        answer['content'] += delta
                        await queue.put(event('delta', text=delta))
                    if session.alive:
                        answer['incomplete'] = False
                        await queue.put(event('done'))
            except asyncio.CancelledError:
                if session.alive:
                    with contextlib.suppress(asyncio.QueueFull):
                        queue.put_nowait(event('cancelled'))
            except (CloudError, TimeoutError) as exc:
                if session.alive:
                    await queue.put(event('error', code=exc.code if isinstance(exc, CloudError) else 'timeout'))
            except Exception:
                if session.alive:
                    await queue.put(event('error', code='connection'))
            finally:
                session.tasks.discard(asyncio.current_task())

        task = asyncio.create_task(generate())
        session.tasks.add(task)

        async def output():
            try:
                while session.alive:
                    try:
                        chunk = await asyncio.wait_for(queue.get(), timeout=.25)
                        if session.alive:
                            yield chunk
                    except TimeoutError:
                        if task.done() and queue.empty():
                            break
            finally:
                task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await task
        return StreamingResponse(output(), media_type='text/event-stream', headers={'X-Accel-Buffering': 'no'})

    async def errors(request, exc):
        if isinstance(exc, CloudError) and exc.code == 'session_expired':
            with contextlib.suppress(HTTPException):
                key, session = runtime.session(request)
                runtime.forget(key, session)
                session.connection = None
        return JSONResponse({'error': exc.code if isinstance(exc, (CloudError, VoiceError)) else str(exc.detail)},
                            status_code=exc.status if isinstance(exc, (CloudError, VoiceError)) else exc.status_code)

    app = Starlette(lifespan=lifespan, routes=[
        Route('/', home), Route('/assets/{name}', asset), Route('/health', health),
        Route('/api/audio/devices', audio_devices),
        Route('/api/capabilities', capabilities), Route('/api/session', session_info),
        Route('/api/auth/start', auth_start, methods=['POST']), Route('/auth/callback', callback),
        Route('/api/logout', logout, methods=['POST']), Route('/api/models', models),
        Route('/api/chats', chats, methods=['GET', 'POST']), Route('/api/chats/{chat_id}', chat),
        Route('/api/chats/{chat_id}/messages', message, methods=['POST']),
        Route('/api/voice/transcribe', voice_request, methods=['POST']),
        Route('/api/voice/speak', voice_request, methods=['POST']),
        Route('/api/cancel', cancel, methods=['POST'])] + market_routes(runtime, body),
        exception_handlers={HTTPException: errors, CloudError: errors, VoiceError: errors})
    app.state.runtime = runtime
    app.add_middleware(LocalBoundary, settings=settings)
    return app
