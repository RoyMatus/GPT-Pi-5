"""Backend-only SSH interfaces. No HTTP client can supply shell commands."""
from dataclasses import dataclass
from typing import Literal, Protocol

SourceState = Literal['not_configured', 'loading', 'ready', 'stale', 'unavailable',
                      'verification_required', 'host_key_changed', 'authentication_failed',
                      'permission_denied', 'unreachable', 'error']

@dataclass(frozen=True)
class SourceIdentity:
    id: str
    generation: int

@dataclass(frozen=True)
class Sample:
    source: SourceIdentity
    state: SourceState
    value: float | None
    unit: str
    acquired_at: str | None
    updated_at: str | None
    supported: bool
    error_code: str | None = None

@dataclass(frozen=True)
class SSHProfile:
    """Backend settings, never serialized to the browser; independent identities allowed."""
    id: str
    host: str
    port: int
    user: str
    telemetry_key_ref: str | None
    photo_key_ref: str | None
    trusted_fingerprint: str | None

class SecretStore(Protocol):
    """Authorization uses the live backend session, never a browser owner ID."""
    def resolve(self, session: object, namespace: str, reference: str) -> bytes: ...
    def delete(self, session: object, namespace: str, reference: str) -> None: ...
    def rotate(self, session: object, namespace: str, reference: str, secret: bytes) -> str: ...

class TelemetrySession(Protocol):
    source: SourceIdentity
    async def collect(self, *, timeout: float) -> tuple[Sample, ...]: ...
    async def close(self) -> None: ...

class PhotoSession(Protocol):
    source: SourceIdentity
    async def list_images(self, *, timeout: float) -> tuple[str, ...]: ...
    async def read_image(self, name: str, *, max_bytes: int, timeout: float) -> bytes: ...
    async def close(self) -> None: ...

class SSHService(Protocol):
    """Implementations must check pinned host identity before authentication/use.

    Session cancellation closes transports. Source generation changes reject late
    results. Fixed collectors only: deliberately no exec(command) method.
    Photo grants are separately authorized and server restrictions must be verified.
    """
    async def telemetry(self, session: object, profile_id: str, *, timeout: float) -> TelemetrySession: ...
    async def photos(self, session: object, profile_id: str, grant_id: str, *, timeout: float) -> PhotoSession: ...
    async def revoke(self, session: object, profile_id: str) -> None: ...
