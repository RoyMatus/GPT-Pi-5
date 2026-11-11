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
