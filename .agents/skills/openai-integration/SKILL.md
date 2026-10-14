---
name: openai-integration
description: Implement or troubleshoot GPT-Pi 5 OpenAI providers, OAuth, streaming or capability detection.
---

# openai-integration

Read [the integration notes](../../../docs/OPENAI.md), then verify the affected
current API/auth contract in official OpenAI documentation. Record source/date;
do not assume a previous model, scope, subscription entitlement or endpoint still applies.
Keep ChatGPT sign-in, plan-based inference and API-key billing separate. Establish
eligibility and supported operations before implementing an adapter; no undocumented
token extraction, shared browser cookies or silent paid fallback.
Secrets remain backend-only. Validate OAuth state, nonce, PKCE, token issuer/audience
using suitable libraries; use minimum scopes and handle refresh/revocation errors.
Declare only demonstrated capabilities. Mock transport for streaming, expired auth,
rate limits, interruption and profile changes. Real paid calls need task authorization
and an explicit budget. A documented feature is not proof this account can access it.
