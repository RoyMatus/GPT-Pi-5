# GPT-Pi 5

[Русский](README.md) | **English**

A desktop voice assistant built around Raspberry Pi 5, with a touchscreen,
microphone, speaker, and a custom 3D-printed enclosure.

**Status: a development scaffold, not a finished voice assistant.**
An independent project; not an official OpenAI or Raspberry Pi device.

## Developer

Created and developed by **Roy Matus ([RoyMatus](https://github.com/RoyMatus))**.
This project is written with the help of **ChatGPT**, which assists with
design, coding, documentation, and checks.

## What is included

- A runnable local status page with large elements suitable for a touchscreen.
- A Python service bound to loopback, `/health`, `/api/capabilities`, and an offline provider.
- A model of separate local profiles and in-memory conversation ownership checks.
  This does not replace authentication and is not connected to HTTP yet.
- Tests for access boundaries, configuration, and HTTP; CI for Windows and Linux.
- Product requirements, architecture, a roadmap, and an enclosure design brief.
- Instructions for Codex, Claude Code, GitHub Copilot, and other AI agents.
- Examples of systemd and UI autostart configuration; deployment to the device has not been performed.

## Run on your computer

Requires Python 3.11+. Run from the repository root:

```powershell
# Windows PowerShell
$env:PYTHONPATH = 'src'
python -m gpt_pi
```

```sh
# Linux / Raspberry Pi
PYTHONPATH=src python3 -m gpt_pi
```

Open http://127.0.0.1:8765. Press Ctrl+C to stop.
The demo requires no API keys, makes no OpenAI requests, records no audio, and stores no chats.
Set `GPT_PI_PORT` to use a different port. `.env.example` is a configuration reference;
the `.env` file is NOT loaded automatically.

Run checks:

```powershell
$env:PYTHONPATH = 'src'
python -m unittest discover -s tests -v
```

```sh
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

## Planned experience

After the operating system boots, the device will display a locked local profile selector.
After authenticating, each person will have access only to their own chats, memory,
and generated files. The owner will configure one active cloud connection for the device.
Voice conversations and tools will be added in stages. Availability will depend on
the actual permissions of the selected connection, rather than the subscription name alone.

Signing in with ChatGPT, using a subscription, using a separately billed API,
and isolating local users are distinct tasks. The idea of sharing one subscription
among several people remains a requested feature; its eligibility and availability
have not been confirmed. Full ChatGPT feature parity through the API cannot be promised.
See the [research notes](docs/OPENAI.md).

## Repository map

The supporting project documents are currently in Russian.

| Path | Purpose |
| --- | --- |
| `src/gpt_pi/` | Application, domain model, providers, and local UI |
| `tests/` | Offline tests without API access or hardware |
| `docs/PRODUCT.md` | Requirements and acceptance criteria |
| `docs/ARCHITECTURE.md` | Architecture and trust boundaries |
| `docs/ROADMAP.md` | Development roadmap |
| `docs/OPENAI.md` | Verified limitations and sources |
| `docs/HARDWARE.md` | Components and specifications still to be confirmed |
| `hardware/enclosure/BRIEF.md` | Enclosure design brief |
| `deploy/` | Autostart examples |
| `AGENTS.md` | Main instructions for AI agents |
| `docs/AI_CONTEXT.md` | Current state and next steps |

GitHub: https://github.com/RoyMatus/GPT-Pi-5

## Contributions and rights

The repository is public; direct write access is granted separately by the owner.
Other users can open issues and submit pull requests, but cannot merge them.
A license for using or redistributing the source code has not been selected yet.
A public repository is not automatically a licensed open-source project.
See [CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md).
