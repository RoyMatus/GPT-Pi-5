"""Provider boundary. Live providers must declare verified capabilities."""
from dataclasses import asdict, dataclass
from typing import Protocol


@dataclass(frozen=True)
class Capabilities:
    text_chat: bool = False
    voice: bool = False
    image_generation: bool = False
    chatgpt_sign_in: bool = False
    private_profiles: bool = False

    def to_dict(self):
        return asdict(self)


class Provider(Protocol):
    capabilities: Capabilities

    def reply(self, text: str) -> str: ...


class OfflineProvider:
    capabilities = Capabilities()

    def reply(self, text: str) -> str:
        raise NotImplementedError("Cloud chat is not connected in this scaffold")
