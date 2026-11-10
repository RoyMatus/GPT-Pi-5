# GPT-Pi 5

[Русский](README.md) | **English**

A desktop Raspberry Pi 5 assistant with a touchscreen and planned voice support.
An independent project by Roy Matus ([RoyMatus](https://github.com/RoyMatus)),
developed with ChatGPT; not an official OpenAI or Raspberry Pi device.

**Status: personal text prototype v0.2, not a finished multi-user voice assistant.**

## Included in the prototype

- Official **Microsoft Fluent 2 / Fluent UI React v9** components: light/dark themes,
  responsive sign-in, conversations, model selection and text chat.
- **Continue with ChatGPT** opens OpenAI's website. The app never receives your
  password. OAuth/PKCE, signed ID-token validation, token refresh and attempted
  session revocation on sign-out are implemented.
- Eligible ChatGPT plan usage through the documented Responses API, including
  streaming, cancellation, quota and network errors. No separately billed API fallback.
- Chats and tokens exist only in server-session memory. Restart/sign-out clears them;
  idle sessions expire after 30 minutes. HTTP access is scoped to the current session.
- Loopback-only server with Host, Origin and CSRF checks. Access logging is disabled.
  Disk storage contains only host/client registrations and hashed account identifiers
  used to validate returning sign-ins.
- A user-service and Wayland kiosk installer for Pi, without sudo.

Authentication and responses are covered by offline tests with a fake cloud transport.
A completed sign-in and real OpenAI response for a particular account still require
owner verification; an implemented button does not establish account/region eligibility.
Voice, persistent chats, memory, files and separate protected local profiles are not
implemented. App sign-out does not sign out the ordinary OpenAI browser session;
our kiosk launcher uses a separate private window.

## Run from source

Requires Python 3.11+ and Node.js 22+. Build the interface first. Node.js is not
needed on the device when installing a prebuilt wheel.

```sh
npm ci
npm run build
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\python.exe -m pip install .
.\.venv\Scripts\python.exe -m gpt_pi
```

Linux / Raspberry Pi:

```sh
.venv/bin/python -m pip install .
.venv/bin/python -m gpt_pi
```

Open http://127.0.0.1:8765 **on the server's machine**. To access Pi from another
computer, use SSH forwarding with the same local port; do not expose the service
to the LAN. The OAuth callback always uses `127.0.0.1`, not `localhost`.
The app makes no OpenAI requests until sign-in is explicitly started.

Settings: `GPT_PI_PORT`, `GPT_PI_PROVIDER=chatgpt|offline`, `GPT_PI_DATA_DIR`.
Registration metadata defaults to the user's application-data directory.
`.env` is not automatically loaded. API keys are not accepted.

## Checks and packaging

Inside the activated venv:

```sh
python -m unittest discover -s tests -v
python -m pip wheel . --no-deps -w dist
```

Wheel builds require the bundled interface. Generated JS/CSS are neither edited nor
committed; package-lock.json pins npm dependencies. Windows/Linux CI builds the UI,
runs offline tests without cloud credentials, and builds the wheel. This does not
replace physical Pi screen, audio or startup acceptance.

## Deployment and documentation

Supporting documents are currently in Russian:
[Install and rollback](deploy/README.md) · [Testing](TESTING.md) ·
[Current state](docs/AI_CONTEXT.md) · [Product](docs/PRODUCT.md) ·
[Architecture](docs/ARCHITECTURE.md) · [OpenAI](docs/OPENAI.md) ·
[Roadmap](docs/ROADMAP.md) · [Hardware](docs/HARDWARE.md) ·
[Enclosure](hardware/enclosure/BRIEF.md) · [AI workflow](docs/AI_WORKFLOW.md) ·
[GitHub tools](tools/README.md).

Public repository: https://github.com/RoyMatus/GPT-Pi-5.
A source license has not been selected. Public visibility does not by itself mean OSS.
See [CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md).
