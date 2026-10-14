---
name: ci-policy
description: Change GPT-Pi 5 CI checks, merge validation or verification tooling.
---

# ci-policy

Read [TESTING.md](../../../TESTING.md) and [tool contracts](../../../tools/README.md).
GitHub Actions is allowed for offline checks. Keep cloud credentials and device
access out of CI; do not confuse Windows/Linux x64 with physical Pi acceptance.
When changing CI job names, update the required names in tools/github_api.py and
verify merge rejection for missing, failed, pending, wrong-source or stale results.
The merge helper checks the current head and main base, then uses GitHub's expected
head SHA. It cannot atomically lock main; branch protection must enforce server-side
policy. Do not change repository settings or weaken checks without authorization.
Tool changes need offline contract tests. No release, permission expansion or live
test issue creation is implied by changing the tooling.
