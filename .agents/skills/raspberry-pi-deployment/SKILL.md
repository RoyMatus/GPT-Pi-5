---
name: raspberry-pi-deployment
description: Prepare or perform an explicitly requested GPT-Pi 5 deployment or device diagnostic.
---

# raspberry-pi-deployment

Read [deployment](../../../deploy/README.md) and [hardware](../../../docs/HARDWARE.md).
Identify the authorized target and current software/service before making changes.
Use `python tools/execution_profile.py --device` on the actual device for bounded
read-only diagnostics; Windows or x64 CI results do not establish Pi readiness.
Before installation, prepare exact package/version, rollback and protection of user
data. Use an unprivileged service, loopback binding and a locked startup screen.
Validate graphics/session autostart, audio permissions, restart, network loss and
power recovery on the target. Do not restart/reconfigure the device for a code review.
Deployment permission does not authorize deleting profiles, reinstalling the OS,
changing network/security access or printing device identifiers into public logs.
Report separately what was installed, what started and what was actually exercised.
