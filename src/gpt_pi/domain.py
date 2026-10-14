"""In-memory ownership model, NOT authentication or a production data store.

Trusted application services must obtain Principal from a verified session.
Never construct it directly from a caller-supplied HTTP profile ID.
"""
from dataclasses import dataclass
from uuid import uuid4


@dataclass(frozen=True)
class Principal:
    profile_id: str


class LocalSession:
    def __init__(self, principal: Principal):
        self._principal = principal

    def require_principal(self) -> Principal:
        if self._principal is None:
            raise PermissionError("Session is locked")
        return self._principal

    def lock(self):
        self._principal = None


@dataclass(frozen=True)
class Conversation:
    id: str
    owner_id: str
    title: str


class ConversationStore:
    def __init__(self):
        self._items: dict[str, Conversation] = {}

    def create(self, session: LocalSession, title: str) -> Conversation:
        owner = session.require_principal()
        conversation = Conversation(uuid4().hex, owner.profile_id, title)
        self._items[conversation.id] = conversation
        return conversation

    def list_for(self, session: LocalSession) -> tuple[Conversation, ...]:
        owner = session.require_principal()
        return tuple(c for c in self._items.values() if c.owner_id == owner.profile_id)

    def get(self, session: LocalSession, conversation_id: str) -> Conversation:
        owner = session.require_principal()
        conversation = self._items.get(conversation_id)
        if conversation is None or conversation.owner_id != owner.profile_id:
            raise LookupError("Conversation not found")
        return conversation

    def delete(self, session: LocalSession, conversation_id: str):
        self.get(session, conversation_id)
        del self._items[conversation_id]
