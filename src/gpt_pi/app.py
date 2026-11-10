"""Run the loopback-only ASGI prototype."""
import os
import uvicorn
from .config import Settings
from .webapp import create_app


def main():
    settings = Settings.from_env(os.environ)
    print(f'GPT-Pi 5: {settings.origin}', flush=True)
    uvicorn.run(create_app(settings), host='127.0.0.1', port=settings.port,
                access_log=False, log_level='warning', proxy_headers=False)
