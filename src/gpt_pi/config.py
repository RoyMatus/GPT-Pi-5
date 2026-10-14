"""No secrets and no implicit live cloud access in the scaffold."""
from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class Settings:
    port: int = 8765
    provider: str = "offline"

    def __post_init__(self):
        if not 1 <= self.port <= 65535:
            raise ValueError("GPT_PI_PORT must be between 1 and 65535")
        if self.provider != "offline":
            raise ValueError("Only the offline provider is implemented")

    @classmethod
    def from_env(cls, env: Mapping[str, str]):
        return cls(port=int(env.get("GPT_PI_PORT", "8765")),
                   provider=env.get("GPT_PI_PROVIDER", "offline"))
