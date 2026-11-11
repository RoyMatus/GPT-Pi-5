# GPT-Pi 5

[Русский](README.md) | **English**

A desktop Raspberry Pi 5 assistant with a touchscreen and local speech input.
An independent project by Roy Matus ([RoyMatus](https://github.com/RoyMatus)),
developed with ChatGPT; not an official OpenAI or Raspberry Pi device.

**Status: personal prototype v0.2. Physical microphone/speaker acceptance is not complete.**

## Included in the prototype

- Official **Microsoft Fluent 2 / Fluent UI React v9** components: light/dark themes,
  responsive sign-in, conversations, model selection and text chat.
- **Continue with ChatGPT** opens OpenAI's website. The app never receives your
  password. OAuth/PKCE, signed ID-token validation, token refresh and attempted
  session revocation on sign-out are implemented.
- Eligible ChatGPT plan usage through the documented Responses API, including
  streaming, cancellation, quota and network errors. No separately billed API fallback.
- Personal-device sign-in survives restarts and does not expire after 30 idle minutes.
  Sign-out removes saved access. Chats remain in RAM; HTTP access is session-scoped.
- Loopback-only server with Host, Origin and CSRF checks. Access logging is disabled.
  Registrations and tokens stay in the backend user's data directory; Linux token
  files have 0600 permissions. Disk encryption is not implemented.
- A user-service and Wayland app-window installer for Pi, without sudo.
  The maximized window supports the desktop's squeekboard on-screen keyboard.
- Optional local Russian speech: button-controlled recording up to 30 seconds,
  Vosk transcription, editable text before sending, and Piper speech output.
  Audio is never stored or uploaded to the cloud. Cancel, sign-out and leaving
  the page stop recording/playback. Replies up to 2500 characters can be read aloud.
- “Проверить звук” is available before sign-in and in chat: five-second recording
  with a level meter, recording playback and a speaker signal. Checks stay local,
  never enumerate cameras or pin a USB port. On Pi, missing audio output is
  distinguished from virtual Dummy Output.

Authentication and responses are covered by offline tests with a fake cloud transport.
On 2026-11-10, the owner's real sign-in, model discovery and an OpenAI response using
the connected ChatGPT plan were verified on Pi. This confirms one account and its
current connection, not eligibility for other accounts or regions.
Persistent chats, memory, files and separate protected local profiles are not
implemented. App sign-out does not sign out the ordinary OpenAI browser session;
our kiosk launcher uses a separate persistent browser profile.

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
Without a remembered login, the app makes no OpenAI requests until sign-in is started.

Settings: `GPT_PI_PORT`, `GPT_PI_PROVIDER=chatgpt|offline`, `GPT_PI_DATA_DIR`,
`GPT_PI_REMEMBER_LOGIN=1` (default). Set `0` for RAM-only sign-in with a 30-minute
idle timeout. Data defaults to the user's application-data directory.
Remembered login does not override OpenAI's credential expiry or revocation.
`.env` is not automatically loaded. API keys are not accepted.

For local voice on Linux/Pi, run `python3 tools/install_voice.py` as the app user,
then reload the page. It downloads SHA-256-verified Russian models and creates a
separate environment in data-dir/voice; no sudo or extra cloud API is required.
If `GPT_PI_DATA_DIR` is set, pass the same directory through `--data-dir`.
Press “Говорить”, allow microphone access, speak, then press “Закончить запись”.
Review the transcription and send it with the arrow. Voice input enables spoken
replies; disable them in Settings. This is a turn-based local voice interface,
not ChatGPT's built-in Voice Mode. Synthetic speech has been checked on Pi;
real capture and audible playback still need hardware acceptance.

## Checks and packaging

Inside the activated venv:

```sh
python -m unittest discover -s tests -v
node --test tests/voice.test.mjs
python -m pip wheel . --no-deps -w dist
```

Wheel builds require the bundled interface. Generated JS/CSS are neither edited nor
committed; package-lock.json pins npm dependencies. Windows/Linux CI builds the UI,
runs offline tests without cloud credentials, and builds the wheel. A separate
Chromium check on Ubuntu covers remembered sign-in, sign-out and voice controls
with a synthetic cloud and microphone; commands are in [TESTING.md](TESTING.md).
This does not replace physical Pi screen, audio or startup acceptance.

## Deployment and documentation

Upcoming device dashboard: [design and tasks](https://github.com/RoyMatus/GPT-Pi-5/issues/2) ·
[development board](https://github.com/users/RoyMatus/projects/8). Dashboard features are not implemented yet.

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

The dashboard foundation is available at `/?dashboard`: six destinations and a local system clock. Data sources are not connected yet; the existing Assistant remains at `/`. Epic #2 is not complete.

Assistant is integrated into the dashboard tab. Leaving the tab cancels voice and active generation while retaining login and the RAM-only conversation.
