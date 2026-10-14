---
name: profile-isolation
description: Design or change GPT-Pi 5 local authentication, profile data ownership or session switching.
---

# profile-isolation

Read the identity and threat boundaries in [architecture](../../../docs/ARCHITECTURE.md).
Derive the local principal from a verified session, never an arbitrary client ID.
Apply ownership checks to chats, files, memory, search, exports and tool credentials.
Unknown and foreign IDs must not leak another user's existence/content.
On lock/logout/switch, invalidate access and stop capture, playback and provider work.
Recheck session/generation ownership before every delayed UI/audio delivery.
Test user B guessing A's IDs, stale sessions, pending stream after switch, export,
reconnect and restart. Do not claim isolation from in-memory ownership tests alone;
test the actual HTTP/storage boundaries when implemented. State limits against root,
physical access, backups and audio audible to nearby people.
