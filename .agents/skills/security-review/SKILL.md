---
name: security-review
description: Investigate a specific GPT-Pi 5 trust boundary or security finding, and fix it only when assigned.
---

# security-review

Identify the asset, attacker-controlled input, reachable path and trust boundary.
Relevant boundaries include OAuth callback → backend credentials, local session →
profile data, browser → loopback server, model output → tool execution and Linux permissions.
Confirm reachability and impact; distinguish exploitable defects from hardening
opportunities. A scanner finding alone is not proof. Do not upload secrets or code
to a new external service, broaden permissions or inspect unrelated accounts.
Use synthetic data and negative tests. For cross-profile concerns also read
[profile-isolation](../profile-isolation/SKILL.md). Report residual uncertainty,
including admin/physical access outside the documented threat model.
