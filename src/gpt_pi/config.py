"""Explicit local configuration. No implicit dotenv or paid API fallback."""
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping


@dataclass(frozen=True)
class Settings:
    port: int = 8765
    provider: str = "chatgpt"
    data_dir: Path = Path.home() / '.local' / 'share' / 'gpt-pi'
    idle_seconds: int = 1800

    def __post_init__(self):
        if not 1 <= self.port <= 65535:
            raise ValueError("GPT_PI_PORT must be between 1 and 65535")
        if self.provider not in {'offline', 'chatgpt'}:
            raise ValueError('Supported providers: offline, chatgpt')

    @property
    def origin(self):
        return f'http://127.0.0.1:{self.port}'

    @classmethod
    def from_env(cls, env: Mapping[str, str]):
        return cls(port=int(env.get("GPT_PI_PORT", "8765")),
                   provider=env.get("GPT_PI_PROVIDER", "chatgpt"),
                   data_dir=Path(env.get('GPT_PI_DATA_DIR') or
                                 Path(env.get('LOCALAPPDATA') or env.get('XDG_DATA_HOME') or
                                      Path.home() / '.local' / 'share') / 'gpt-pi'))
