# Epic 2 delivery

All seven implementation PRs #11–#17 have been integrated into
codex/dashboard-integration after exact-head successful Windows/Linux/browser CI.
The initial release was v0.3.0; the fullscreen follow-up is v0.3.1. Existing root-worktree documentation edits are preserved.
Coordinator root is the sole final integration/lease owner for metadata/docs/deployment
and cross-feature safety fixes. No other writer is active.

Final review found and reproduced a logout race while an SSH configuration request
body was still arriving: it could persist settings after the owning session ended.
All new dashboard mutations now recheck liveness after reading their body. A separate
regression rejects non-string empty calendar times. No arbitrary command API or
private-image persistence is introduced. Tests first observed both failures.

Actual-device installation/verification is recorded in deploy/README.md after execution.
CI and synthetic sources do not establish real-PC SSH/SFTP ACL readiness, physical
touch, microphone/speaker operation or millimetre/pixel-perfect visual acceptance.
The PC source is never silently replaced by the display Pi.

Final local verification: Windows/Python 3.12/Node 24/Edge, 103 Python tests,
7 Node tests, all seven synthetic feature/Assistant browser runners, 192 shell
geometry cases and wheel build passed. Existing root worktree modifications remain
limited to the original docs/AI_CONTEXT.md and docs/HARDWARE.md.

Final screenshot inspection reproduced countdown line-height overlap and insufficient
dark sign-in heading contrast. Geometry/contrast tests observed both failures, then
CSS restores readable line height and >=4.5 heading contrast without changing design.


On-device HTTP navigation initially hung before sending headers because the desktop
keyring remained locked under automatic login. A fresh-profile /health experiment
failed with the default store and passed with Chromium's file store. The dedicated
0700 application profile now uses that store, without disabling the sandbox or
network security. Cookies have no keyring encryption; see deploy/README.md.
The actual 720×1218 Chromium viewport loads all six tabs and survives a backend
restart. Its current profile is unauthenticated; backend credential records remain
untouched. Saved-login regression coverage uses synthetic credentials, not a claim
that this device profile is signed in. Real-PC/SFTP and physical audio/touch remain
acceptance gates; this delivery does not close Epic #2.

The first device screenshot also exposed a dark hardcoded gradient behind the
light-theme header/clock. A screenshot-pixel test failed before a light-theme
background/color-scheme override; the full geometry matrix then passed.


## Fullscreen and PC setup follow-up

The owner explicitly requested fullscreen and Windows SSH installation. The active
browser session on Pi is now authenticated. Its Computer profile was configured
through its normal CSRF-protected API for the actual Windows computer; a fresh
server host key was generated locally and pinned before any connection. Private
telemetry keys remain on Pi. Host addresses/keys/passwords are not in Git.

v0.3.1 uses Chromium kiosk and a user-scoped GTK module for squeekboard. The module
raises only namespace osk, publishes bounded physical-pixel geometry in private
runtime storage and observes no key/input text. The backend accepts only fresh
owner-only regular files. The shell converts physical pixels using DPR, reserves
space, keeps the focused field visible and defers layout changes during a click.
Actual-device checks first found the composer hidden by the keyboard, despite a
visible keyboard. Synthetic geometry/click/DPR coverage exercises this regression.
A separate GObject harness checks that unrelated applications/surfaces are unchanged.

Windows setup is a separate explicit administrator script, preview by default:
standard account, public-key-only authentication, forced bounded collector, no
interactive shell/SFTP/forwarding, and device-only firewall scope. At preparation
it was waiting for native UAC; this is not a claim that Windows SSH or actual PC
metrics have passed. The dashboard itself never requests elevation or installs it.
