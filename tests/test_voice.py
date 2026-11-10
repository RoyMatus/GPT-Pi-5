"""Voice transport uses synthetic PCM and fake local engines, never a microphone."""
import asyncio
import io
from pathlib import Path
import tempfile
import threading
import unittest
from urllib.parse import parse_qs, urlparse
import wave
from unittest.mock import AsyncMock, patch

from starlette.testclient import TestClient
from gpt_pi.config import Settings
from gpt_pi.webapp import create_app
from gpt_pi.voice import LocalVoice, VoiceError
from test_webapp import FakeCloud


def wav_bytes(rate=16000, channels=1, seconds=1):
    output = io.BytesIO()
    with wave.open(output, 'wb') as wav:
        wav.setparams((channels, 2, rate, 0, 'NONE', 'not compressed'))
        wav.writeframes(b'\0\0' * rate * channels * seconds)
    return output.getvalue()


class FakeVoice:
    def __init__(self):
        self.calls = []
        self.started = threading.Event()
        self.stopped = threading.Event()
        self.wait = False

    def available(self):
        return True

    async def transcribe(self, audio):
        self.calls.append('transcribe')
        self.started.set()
        try:
            if self.wait:
                await asyncio.sleep(30)
            return 'Синтетический вопрос'
        finally:
            self.stopped.set()

    async def speak(self, text):
        self.calls.append(text)
        return wav_bytes()


class VoiceHTTPTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.settings = Settings(data_dir=Path(self.temp.name))
        self.app = create_app(self.settings, FakeCloud())
        self.voice = FakeVoice()
        self.app.state.runtime.voice = self.voice
        self.client = TestClient(self.app, base_url=self.settings.origin).__enter__()
        self.csrf = self.client.get('/api/session').json()['csrf']

    def tearDown(self):
        self.client.__exit__(None, None, None)
        self.temp.cleanup()

    def headers(self):
        return {'Origin': self.settings.origin, 'X-CSRF-Token': self.csrf}

    def login(self):
        response = self.client.post('/api/auth/start', json={}, headers=self.headers())
        state = parse_qs(urlparse(response.json()['url']).query)['state'][0]
        self.client.get('/auth/callback', params={'code': 'synthetic', 'state': state,
                                                'client_id': 'oaiapp_synthetic'})
        self.csrf = self.client.get('/api/session').json()['csrf']

    def transcribe(self, audio=None, **headers):
        return self.client.post('/api/voice/transcribe', content=wav_bytes() if audio is None else audio,
                                headers={**self.headers(), 'Content-Type': 'audio/wav', **headers})

    def test_local_transcription_and_speech_require_current_session(self):
        self.assertEqual(401, self.transcribe().status_code)
        self.login()
        self.assertEqual({'text': 'Синтетический вопрос'}, self.transcribe().json())
        response = self.client.post('/api/voice/speak', json={'text': 'Синтетический ответ'}, headers=self.headers())
        self.assertEqual(200, response.status_code)
        self.assertEqual('audio/wav', response.headers['content-type'])
        self.assertEqual(wav_bytes(), response.content)
        self.assertEqual('no-store', response.headers['cache-control'])
        self.assertEqual(['transcribe', 'Синтетический ответ'], self.voice.calls)

    def test_voice_boundary_and_malformed_audio(self):
        self.login()
        self.assertEqual(403, self.transcribe(**{'X-CSRF-Token': 'wrong'}).status_code)
        self.assertEqual(403, self.transcribe(**{'Origin': 'https://evil.invalid'}).status_code)
        self.assertEqual(415, self.transcribe(**{'Content-Type': 'audio/webm'}).status_code)
        for audio in (b'bad', wav_bytes(rate=8000), wav_bytes(channels=2), wav_bytes()[:-20]):
            self.assertEqual(400, self.transcribe(audio).status_code)
        self.assertEqual(413, self.transcribe(b'x' * 1000001).status_code)
        self.assertEqual([], self.voice.calls)

    def test_logout_cancels_transcription_and_drops_result(self):
        self.login()
        self.voice.wait = True
        responses = []
        thread = threading.Thread(target=lambda: responses.append(self.transcribe()))
        thread.start()
        self.assertTrue(self.voice.started.wait(2))
        self.client.post('/api/logout', json={}, headers=self.headers())
        thread.join(3)
        self.assertFalse(thread.is_alive())
        self.assertTrue(self.voice.stopped.is_set())
        self.assertNotIn('Синтетический вопрос', responses[0].text)
        self.assertEqual(401, responses[0].status_code)

    def test_microphone_is_limited_to_same_origin(self):
        response = self.client.get('/')
        self.assertIn('microphone=(self)', response.headers['permissions-policy'])
        self.assertIn("media-src 'self' blob:", response.headers['content-security-policy'])

    def test_audio_device_status_is_available_before_cloud_login(self):
        response = self.client.get('/api/audio/devices')
        self.assertEqual(200, response.status_code)
        self.assertEqual({'microphone', 'speaker'}, set(response.json()))
        self.assertEqual(403, self.client.get('/api/audio/devices', headers={
            'Sec-Fetch-Site': 'cross-site'}).status_code)

    def test_cancel_and_text_limits_do_not_send_audio_or_call_cloud(self):
        self.login()
        for text in ('', 'x' * 2501, 123):
            response = self.client.post('/api/voice/speak', json={'text': text}, headers=self.headers())
            self.assertEqual(400, response.status_code)
        self.assertEqual([], self.voice.calls)
        self.voice.wait = True
        responses = []
        thread = threading.Thread(target=lambda: responses.append(self.transcribe()))
        thread.start()
        self.assertTrue(self.voice.started.wait(2))
        self.assertEqual(409, self.transcribe().status_code)
        self.client.post('/api/cancel', json={}, headers=self.headers())
        thread.join(3)
        self.assertFalse(thread.is_alive())
        self.assertEqual(409, responses[0].status_code)
        self.assertNotIn('Синтетический вопрос', responses[0].text)


class WorkerTests(unittest.IsolatedAsyncioTestCase):
    async def test_cancel_kills_worker_and_releases_resource_lock(self):
        started = asyncio.Event()
        class Process:
            returncode = None
            killed = False
            async def communicate(self, payload):
                started.set()
                await asyncio.sleep(30)
            def kill(self):
                self.killed = True
                self.returncode = -9
            async def wait(self):
                return self.returncode
        process = Process()
        voice = LocalVoice(Path('unused'))
        with patch.object(voice, 'available', return_value=True), patch(
                'asyncio.create_subprocess_exec', AsyncMock(return_value=process)):
            task = asyncio.create_task(voice.speak('Синтетический текст'))
            await asyncio.wait_for(started.wait(), 1)
            with self.assertRaises(VoiceError) as error:
                await voice.speak('busy')
            self.assertEqual('busy', error.exception.code)
            task.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await task
        self.assertTrue(process.killed)
        self.assertFalse(voice.lock.locked())
