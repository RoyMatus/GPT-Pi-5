---
name: code-quality-review
description: Review a concrete GPT-Pi 5 correctness, lifecycle or performance concern.
---

# code-quality-review

Trace the affected execution path before proposing a defect. Focus on observable
failures: late streamed replies after logout, uncancelled tasks, retained audio
buffers, resource leaks, duplicated state and blocking device I/O.
Explain the trigger, impact, source evidence and smallest correction. Label
unverified runtime risks as hypotheses; omit style-only findings and unrelated cleanup.
For an assigned fix, select focused checks using [TESTING.md](../../../TESTING.md).
Do not run the full suite again if valid results already cover unchanged inputs.
