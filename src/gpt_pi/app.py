"""Read-only loopback demo. Not a production HTTP server."""
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib.resources import files

from . import __version__
from .config import Settings
from .providers import OfflineProvider


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Do not log URLs or potentially sensitive request content.
        pass

    def send_body(self, status: int, body: bytes, content_type: str):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy",
                         "default-src 'none'; style-src 'unsafe-inline'; "
                         "frame-ancestors 'none'; base-uri 'none'; form-action 'none'")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        port = self.server.server_port
        if self.headers.get("Host") not in {f"127.0.0.1:{port}", f"localhost:{port}"}:
            self.send_body(403, b"Forbidden host", "text/plain")
            return
        if self.path == "/":
            self.send_body(200, files("gpt_pi").joinpath("web/index.html").read_bytes(),
                           "text/html; charset=utf-8")
        elif self.path in {"/health", "/api/capabilities"}:
            data = ({"status": "ok", "mode": "offline", "version": __version__}
                    if self.path == "/health" else OfflineProvider.capabilities.to_dict())
            self.send_body(200, json.dumps(data).encode(), "application/json")
        else:
            self.send_body(404, b"Not found", "text/plain")


def create_server(port: int = 8765):
    # Port zero is intentionally supported for isolated tests.
    return ThreadingHTTPServer(("127.0.0.1", port), Handler)


def main():
    settings = Settings.from_env(os.environ)
    with create_server(settings.port) as server:
        print(f"GPT-Pi 5 offline scaffold: http://127.0.0.1:{server.server_port}")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
