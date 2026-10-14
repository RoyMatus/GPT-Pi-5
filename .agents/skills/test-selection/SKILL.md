---
name: test-selection
description: Select proportionate GPT-Pi 5 checks for a code, tooling, documentation or device change.
---

# test-selection

Use the matrix in [TESTING.md](../../../TESTING.md); it owns commands and coverage.
Map the changed behavior to plausible failure modes. Use offline Python tests for
logic/API contracts, mock cloud transport, and reserve physical-device checks for
Linux/ARM64, audio, touchscreen, thermal/resource and boot behavior.
Documentation-only changes need diff/link/consistency review; tool changes need
tool tests rather than an unrelated app run. Extend scope for coupled behavior or failures.
Reuse applicable completed results; coordinate device ownership. Record actual
platform, command, result and omissions. CI success on x64 is not Pi acceptance.
