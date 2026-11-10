"""Optional browser acceptance with a synthetic account, microphone and speech."""
from pathlib import Path
import socket
import sys
import tempfile
import threading
import time
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import uvicorn
from gpt_pi.config import Settings
from gpt_pi.webapp import create_app
from test_webapp import FakeCloud
from test_voice import FakeVoice

def check(origin):
    from urllib.parse import urlparse, parse_qs, urlencode
    from playwright.sync_api import sync_playwright, expect

    with sync_playwright() as p:
        browser = p.chromium.launch(args=['--use-fake-device-for-media-stream', '--use-fake-ui-for-media-stream'])
        page = browser.new_page(viewport={'width': 720, 'height': 1280})
        page.add_init_script("""window.testTracks = [];
            if (navigator.mediaDevices) {
            navigator.mediaDevices.enumerateDevices = async () => { throw new Error('Camera enumeration is forbidden'); };
            const getMedia = navigator.mediaDevices.getUserMedia.bind(navigator.mediaDevices);
            navigator.mediaDevices.getUserMedia = async options => {
                const stream = await getMedia(options);
                window.testTracks.push(...stream.getTracks()); return stream;
            }; }""")
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.route('**/api/audio/devices', lambda route: route.fulfill(json={'microphone': True, 'speaker': True}))
        page.goto(origin)
        # Device checks must work before ChatGPT sign-in and stay local.
        device_requests = []
        page.on('request', lambda request: device_requests.append(request.url) if '/api/voice/' in request.url else None)
        page.get_by_role('button', name='Проверить звук', exact=True).click(timeout=2500)
        panel = page.get_by_role('dialog', name='Микрофон и динамик')
        panel.get_by_role('button', name='Проверить микрофон', exact=True).click()
        panel.get_by_text('Идёт запись · 5 секунд', exact=True).wait_for()
        panel.get_by_role('button', name='Прослушать запись', exact=True).wait_for()
        panel.get_by_role('button', name='Прослушать запись', exact=True).click()
        panel.get_by_text('Воспроизвожу запись…', exact=True).wait_for()
        panel.get_by_role('button', name='Остановить проверку', exact=True).click()
        panel.get_by_role('button', name='Проверить динамик', exact=True).click()
        panel.get_by_text('Воспроизвожу тестовый сигнал…', exact=True).wait_for()
        panel.get_by_role('button', name='Закрыть проверку', exact=True).click()
        page.get_by_role('button', name='Проверить звук', exact=True).click()
        panel.get_by_role('button', name='Проверить микрофон', exact=True).click()
        panel.get_by_text('Идёт запись · 5 секунд', exact=True).wait_for()
        page.evaluate("Object.defineProperty(document, 'hidden', {configurable:true, get:()=>true}); document.dispatchEvent(new Event('visibilitychange'))")
        panel.get_by_text('Проверка остановлена, запись удалена.', exact=True).wait_for()
        assert page.evaluate("testTracks.every(track => track.readyState === 'ended')")
        assert panel.get_by_role('button', name='Прослушать запись', exact=True).count() == 0
        page.evaluate("delete document.hidden")
        panel.get_by_role('button', name='Проверить микрофон', exact=True).click()
        panel.get_by_text('Идёт запись · 5 секунд', exact=True).wait_for()
        panel.get_by_role('button', name='Закрыть проверку', exact=True).click()
        assert page.evaluate("testTracks.every(track => track.readyState === 'ended')")
        assert not device_requests, 'guest device checks must not send audio to the backend'
        absent = browser.new_page(viewport={'width': 720, 'height': 1280})
        absent.route('**/api/audio/devices', lambda route: route.fulfill(json={'microphone': False, 'speaker': False}))
        absent.add_init_script("navigator.mediaDevices.getUserMedia = async () => { throw new DOMException('No device', 'NotFoundError'); };")
        absent.goto(origin)
        absent.get_by_role('button', name='Проверить звук', exact=True).click()
        absent.get_by_role('button', name='Проверить микрофон', exact=True).click()
        absent.get_by_text('Микрофон не найден системой.', exact=True).wait_for()
        absent.get_by_role('button', name='Проверить динамик', exact=True).click()
        absent.get_by_text('Динамик не найден системой. Тестовый сигнал не запущен.', exact=True).wait_for()
        absent.close()
        captured = []
        def auth(route):
            captured.append(parse_qs(urlparse(route.request.url).query))
            route.abort()
        page.route('https://auth.openai.com/**', auth)
        page.get_by_role('button', name='Continue with ChatGPT').click()
        page.wait_for_timeout(300)
        page.goto(origin + '/auth/callback?' + urlencode({
            'code': 'synthetic-voice', 'state': captured[0]['state'][0], 'client_id': 'oaiapp_voice'}))
        page.get_by_role('button', name='Говорить', exact=True).click()
        page.get_by_text('● Микрофон включён', exact=True).wait_for()
        page.wait_for_timeout(1200)
        page.get_by_role('button', name='Закончить запись', exact=True).click()
        field = page.get_by_role('textbox', name='Сообщение')
        expect(field).to_have_value('Синтетический вопрос')
        page.get_by_role('button', name='Отправить сообщение', exact=True).click()
        page.get_by_text('Synthetic answer', exact=True).wait_for()
        page.get_by_text('Читаю ответ…', exact=True).wait_for()
        page.get_by_text('Русский · до 30 секунд', exact=True).wait_for()
        voice_requests = []
        page.on('request', lambda request: voice_requests.append(request.url) if request.url.endswith('/api/voice/speak') else None)
        page.evaluate("Object.defineProperty(document, 'hidden', {configurable:true, get:()=>true}); document.dispatchEvent(new Event('visibilitychange'))")
        page.get_by_role('button', name='Прослушать', exact=True).click()
        page.wait_for_timeout(500)
        assert not voice_requests, 'hidden page must not start speech'
        page.evaluate("delete document.hidden")
        page.get_by_role('button', name='Говорить', exact=True).click()
        page.get_by_text('● Микрофон включён', exact=True).wait_for()
        page.get_by_role('button', name='Завершить сеанс', exact=True).click()
        page.get_by_role('button', name='Continue with ChatGPT').wait_for()
        assert page.get_by_text('Микрофон выключен', exact=True).count() == 1
        assert not errors, errors
        browser.close()
    print('PASS: guest audio checks, no microphone error, close/hide cleanup, local voice chat; no browser errors')

if __name__ == '__main__':
    with tempfile.TemporaryDirectory() as directory, socket.socket() as listener:
        listener.bind(('127.0.0.1', 0))
        settings = Settings(port=listener.getsockname()[1], data_dir=Path(directory))
        app = create_app(settings, FakeCloud())
        app.state.runtime.voice = FakeVoice()
        server = uvicorn.Server(uvicorn.Config(app, access_log=False, log_level='warning'))
        thread = threading.Thread(target=lambda: server.run(sockets=[listener]), daemon=True)
        thread.start()
        try:
            deadline = time.monotonic() + 5
            while not server.started and time.monotonic() < deadline:
                time.sleep(.05)
            assert server.started
            check(settings.origin)
        finally:
            server.should_exit = True
            thread.join(5)
