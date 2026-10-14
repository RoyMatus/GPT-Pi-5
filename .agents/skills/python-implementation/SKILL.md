---
name: python-implementation
description: Implement assigned GPT-Pi 5 Python behavior with focused regression tests.
---

# python-implementation

Find the existing state owner and service/provider boundary before editing.
Keep domain logic testable without hardware, credentials or network. Never expose
the in-memory Principal constructor as client-controlled authentication.
For new testable behavior or a reproducible defect, follow the small test-first
cycle and exceptions in [TESTING.md](../../../TESTING.md). Use fake clocks/transport
for expiry, retries and cancellation; do not test paid APIs in CI.
Keep network/device timeouts bounded and cancellation tied to the current session.
Add dependencies only for an actual requirement; use maintained libraries instead
of inventing OAuth validation or cryptography. Finish with relevant checks and docs.
