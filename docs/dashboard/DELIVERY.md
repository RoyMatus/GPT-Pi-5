# Epic 2 delivery

All seven implementation PRs #11–#17 have been integrated into
codex/dashboard-integration after exact-head successful Windows/Linux/browser CI.
This release is v0.3.0. Existing root-worktree documentation edits are preserved.
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
