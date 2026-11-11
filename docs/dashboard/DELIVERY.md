# Epic 2 delivery

v0.3.2 is installed on the authorized Pi. All six dashboard screens and shared
contracts are implemented in codex/dashboard-integration, following child PRs
#11–#17. Delivery PR #18 targets codex/chatgpt-device-prototype; main/PR #1 and the
original root-worktree documentation edits are unchanged.

The dashboard runs at the full 720×1280 screen size. Native keyboard layering,
geometry/DPR handling, focused composer visibility, synthetic q input and blur
cleanup were checked on Pi. A real reboot verified automatic fullscreen startup
and the user-scoped keyboard module. Sign-in survives the application updates.

## Actual Windows source

Windows OpenSSH is installed with automatic service startup, a dedicated standard
account and key-only access from Pi. The Windows host key was generated locally
and pinned before connection. Telemetry private keys remain on the backend.
Firewall scope is the selected device/local interface; the broad rule is disabled.
The temporary performance-counter group was removed. No administrator membership
or photo-folder permission was added. The temporary host private-key copy in
build was deleted after verifying the protected server installation.

Actual SSH tests verified pinned-key authentication, the reviewed fixed collector
when a different command is requested, and denial of PTY, SFTP and TCP forwarding.
The authenticated application then obtained real CPU, memory, system disk and
network byte counters/rates, retained multiple history points, and populated both
Computer and Overview. Fullscreen and sign-in remained intact; diagnostic browser
debugging was removed after acceptance. No real chat text or cloud token was read.

CIM timed out for both network counters and CPU in the actual SSH context. Kernel
GetSystemTimes/GlobalMemoryStatusEx, DriveInfo and NetworkInterface avoid that
provider dependency. GetTickCount64 supplies monotonic elapsed time; first samples
and counter resets are unavailable instead of fabricated zero traffic. Failed
jobs preserve their cause and retain the 8-second limit/cleanup. Windows CPU
frequency, temperatures, fan and GPU are unsupported; CPU usage above 64 logical
processors is unavailable rather than reporting one group as the entire machine.

## Verification and remaining acceptance

Offline Windows/Linux CI, browser feature/lifecycle scenarios and 192 shell layout
cases passed on the implementation head. The Python suite now contains 113 tests,
including Windows native collector/provider-failure and job-cleanup regressions.
Prior installed ARM64 tests (109, 3 Windows-only skips) cover unchanged Python
runtime behavior; v0.3.2 packaging, source hashing and actual SSH/UI were checked
separately. CI and automated pointers do not establish physical touch/audio.

Real personal-photo SFTP confinement and physical touch/audio remain open gates.
The telemetry account intentionally cannot use SFTP. The browser's dedicated 0700
profile still uses the file store (no keyring cookie encryption). Windows restart
was not performed; automatic service configuration and service restart were checked.
See deploy/README.md and docs/dashboard/SSH.md for setup and limitations.
