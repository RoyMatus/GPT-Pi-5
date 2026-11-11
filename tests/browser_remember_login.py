"""Optional real-browser restart acceptance, using a synthetic cloud account."""
import os
from pathlib import Path
import socket
import sys
import tempfile
import threading
import time
from urllib.parse import parse_qs, urlencode, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import uvicorn
from playwright.sync_api import sync_playwright
from gpt_pi.config import Settings
from gpt_pi.webapp import create_app
from test_webapp import FakeCloud


class Server:
    def __init__(self, settings):
        self.settings = settings

    def start(self):
        self.app = create_app(self.settings, FakeCloud())
        self.server = uvicorn.Server(uvicorn.Config(self.app, host='127.0.0.1',
            port=self.settings.port, access_log=False, log_level='warning', timeout_graceful_shutdown=2, timeout_keep_alive=1))
        self.thread = threading.Thread(target=self.server.run, daemon=True)
        self.thread.start()
        deadline = time.monotonic() + 5
        while not self.server.started and time.monotonic() < deadline:
            time.sleep(.05)
        assert self.server.started

    def stop(self):
        self.server.should_exit = True
        self.thread.join(15)
        assert not self.thread.is_alive()


def check():
    with tempfile.TemporaryDirectory() as directory, sync_playwright() as p:
        with socket.socket() as listener:
            listener.bind(('127.0.0.1', 0))
            port = listener.getsockname()[1]
        settings = Settings(port=port, data_dir=Path(directory) / 'data')
        server = Server(settings)
        server.start()
        profile = str(Path(directory) / 'browser')
        context = p.chromium.launch_persistent_context(profile, channel=os.environ.get('GPT_PI_TEST_BROWSER_CHANNEL'))
        errors = []
        try:
            page = context.pages[0]
            page.on('pageerror', lambda error: errors.append(str(error)))
            captured = []
            def auth(route):
                captured.append(parse_qs(urlparse(route.request.url).query))
                route.fulfill(status=200, content_type="text/html", body="Synthetic OAuth")
            page.route('https://auth.openai.com/**', auth)
            page.goto(settings.origin)
            page.get_by_role('button', name='Continue with ChatGPT').click()
            for _ in range(60):
                if captured: break
                page.wait_for_timeout(50)
            assert captured, "OAuth navigation was not requested"
            page.wait_for_url("https://auth.openai.com/**")
            page.goto(settings.origin + '/auth/callback?' + urlencode({
                'code': 'synthetic-owner', 'state': captured[0]['state'][0],
                'client_id': 'oaiapp_owner'}))
            page.get_by_role('button', name='Завершить сеанс', exact=True).wait_for()
            # Expire the old 30-minute inactivity deadline without a wall-clock wait.
            for session in server.app.state.runtime.sessions.values():
                session.touched -= 3600
            page.reload()
            page.get_by_role('button', name='Завершить сеанс', exact=True).wait_for()
            server.stop()
            server.start()
            # Existing page detects new CSRF/session state without logging out.
            page.get_by_text('Приложение перезапустилось. Вход сохранён.', exact=True).wait_for(timeout=15000)
            page.get_by_role('button', name='Завершить сеанс', exact=True).wait_for()
            context.close()
            context = p.chromium.launch_persistent_context(profile, channel=os.environ.get('GPT_PI_TEST_BROWSER_CHANNEL'))
            page = context.pages[0]
            page.goto(settings.origin)
            page.get_by_role('button', name='Завершить сеанс', exact=True).wait_for()
            page.get_by_role('button', name='Завершить сеанс', exact=True).click()
            page.get_by_role('button', name='Continue with ChatGPT').wait_for()
            context.close()
            context = p.chromium.launch_persistent_context(profile, channel=os.environ.get('GPT_PI_TEST_BROWSER_CHANNEL'))
            page = context.pages[0]
            page.goto(settings.origin)
            page.get_by_role('button', name='Continue with ChatGPT').wait_for()
            assert not errors, errors
        finally:
            context.close()
            server.stop()
    print('PASS: idle, server restart, browser restart preserve login; explicit logout stays logged out')


if __name__ == '__main__':
    check()
