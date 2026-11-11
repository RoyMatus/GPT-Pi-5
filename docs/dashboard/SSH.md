# SSH computer source

The display never becomes the selected computer implicitly. Configure a source in the
Computer tab after login: host/port, telemetry username, optional distinct photo username,
Linux/Windows platform, label and externally verified SHA256 server fingerprint.
Unknown/changed host identity blocks use. There is no AutoAddPolicy or password input.
Only fixed bundled collectors are executable; the model/browser cannot submit commands.

Supported matrix:
| Source | Baseline | Optional | Requirements |
| --- | --- | --- | --- |
| Linux | /proc CPU, RAM, root filesystem, sum of non-loopback interface counters | readable CPU thermal/frequency/fan sysfs; installed nvidia-smi GPU | OpenSSH and Python 3; existing filesystem permissions |
| Windows | kernel CPU times, physical RAM, system-drive capacity, summed interface byte counters | NVIDIA GPU via nvidia-smi; CPU clock/temperature via explicitly installed CPU sensor task; fan unavailable | OpenSSH server and Windows PowerShell 5.1+; optional setup below |

Memory/disk use bytes converted to GiB (2^30); network rates use bits/s converted to
Mbit/s (10^6). First Linux network sample and counter resets/reboots are unavailable,
never zero traffic. Network totals include available physical/virtual interfaces and
are not a selected physical-link speed. Up to 60 actual samples are retained in RAM.
Requests use one batched collector with a 12-second command deadline and 20-second
outer bound; connection/auth/banner/channel bounds are explicit. The dashboard does
not install host software. The separately invoked administrator sensor setup installs
the pinned CPU library/driver and an on-demand task, without a network listener or periodic collector.

Profiles and separate Ed25519 telemetry/photo keys are backend-only, indexed by the
SHA256 of the subject from the live validated cloud connection. Linux directories
are 0700 and atomic files 0600; Windows uses the OS user's data-directory ACLs.
Generated keys are unencrypted for unattended use; protection from root/stolen disk
is not claimed. Key import/passphrase UI is not implemented. Configure/edit, disable,
rotate and remove are explicit actions. Logout closes owned connections/tasks but
retains the account's settings. Removing local keys does not revoke authorized_keys
on the PC; remove those entries on the PC separately. Rotation requires installing
new public keys there. No cloud token or real host information is stored in Git.

## Server enforcement

Application command restrictions do not confine a stolen key. Use a dedicated
least-privilege telemetry account and a separately restricted SFTP account/key.
On Linux an owner-reviewed, root/admin-owned copy of the fixed collector can be
used as an authorized_keys forced command with restrict/no PTY/no forwarding. The
client's requested inline command is then ignored by OpenSSH; output schema must
remain the reviewed version. This is a one-shot script, not an installed daemon.
Do not give that account interactive/admin access or install optional tools silently.

For photos, configure server-enforced read-only SFTP confinement to the chosen
library (e.g. internal-sftp -R with an appropriately owned ChrootDirectory and readonly
ACLs). A telemetry forced command also intercepts SFTP subsystem requests: do not
reuse it by weakening the policy. The product uses the separate photo key/user.
Windows ChrootDirectory is SFTP-only and does not confine an ordinary SSH shell.
Verify ACLs, the installed Windows OpenSSH capabilities and subsystem policy; no
universal Linux configuration is silently applied to Windows. Unsupported restrictions
are a setup gate, not permission to grant a general shell. Product connection setup
never configures the PC's sshd, firewall or elevated system policy automatically.

References: https://docs.paramiko.org/en/stable/api/client.html ;
https://man.openbsd.org/sshd_config ;
https://learn.microsoft.com/en-us/windows-server/administration/openssh/openssh-server-configuration

## Ownership and verification

Started at 6150fc199b5189eb6349f8ba472d8be025fe9c3a. Coordinator root owns feature
modules and the exclusive shared Session/resources/routes, manifest, shell/registry,
fixture/CI/docs lease until PR handoff. SFTP contract requires a live session-owned
photo grant and current source generation, independent of telemetry consent. Separate
connections prevent photo I/O holding the telemetry collection lock.

Offline tests cover trust, independent photo identity/grant, typed metrics/profile,
unit conversion/reset, owner isolation, no arbitrary operation, revoke/late sample.
Synthetic browser checks cover setup, explicit trust, changed key and disable.
Both fixed collectors were run separately on actual Windows and authorized Linux ARM64;
this validates schema/capability extraction, not a configured end-user PC or server ACLs.
No PC profile is auto-filled with the display device's credentials.

Collector lifetime: Linux also sets a 10-second process alarm. Windows uses an
ephemeral PowerShell job with an 8-second wait deadline and forced job cleanup,
with forced cleanup. NVIDIA has a 1.2-second process bound; CPU cache waiting is
bounded to 2.5 seconds. The SYSTEM CPU task has a five-second execution limit and
IgnoreNew instance policy. Neither creates periodic background monitoring.


Windows network collection now uses NetworkInterface.GetIPStatistics byte totals
(excluding loopback), with GetTickCount64 uptime and shared backend rate/reset
handling. No performance-counter group is required. An actual local reproduction
showed the previous optional WMI network query timing out and discarding all core
metrics. Failed jobs now expose their underlying failure to the bounded SSH reader,
which maps it to a generic state and does not log raw stderr. The 8-second worker
lifetime/cleanup remains. Optional CPU/GPU sensors are described below.


Final Windows implementation avoids CIM entirely: GetSystemTimes over 250 ms for
CPU usage, GlobalMemoryStatusEx for physical memory, DriveInfo for the system disk,
and NetworkInterface for IP byte counters. Source uptime uses GetTickCount64, so
wall-clock adjustments do not distort rates. GetSystemTimes on >64 logical CPUs
covers only one processor group; the collector reports CPU unavailable there.
Fan RPM remains unavailable on Windows. The SSH
role also reproduced a Win32_Processor CIM timeout; widening group permissions did
not resolve it. The temporary counter-read group is removed during this repair.

## Optional Windows hardware sensors (v0.3.3)

NVIDIA reads the first physical NVIDIA GPU (`--id=0`) through the fixed absolute
System32/nvidia-smi.exe path. Intel/virtual adapters are not mixed into its values.
CSV parsing uses invariant numbers; MiB becomes bytes (2^20); W and degrees C are
unchanged. N/A, invalid ranges, multiple rows, timeout or provider errors remain
null and do not discard CPU/RAM/disk/network. GPU ordering is not a persistent
adapter selection contract on computers with multiple NVIDIA devices.

The separate administrator setup pins LibreHardwareMonitor 0.9.6 and signed official
PawnIO 2.2.0 to release SHA256 values. It enables CPU sensors only. Frequency is the
mean of available CPU core clocks in GHz, not the processor's advertised base clock.
Temperature is the maximum CPU Package value, falling back to maximum core temperature.
Unsupported physical hardware still returns null; no synthetic fallback is used.

Only the fixed, argument-free `\GPT-Pi\CpuSensors` task runs as SYSTEM. The standard
SSH role receives read/execute on the task and protected sensor files, without
write/delete/change-owner rights, administrator membership or direct driver access.
Task action/path/working directory contain no Run argument substitutions. CPU code
and dependency DLLs are administrator-owned; result publication is atomic. Cache
schema/size/numeric ranges are checked, with a five-second maximum age; future and
malformed data are ignored. Task invocation remains on demand, with no periodic
trigger. A task failure leaves core and NVIDIA metrics usable. The driver and task
remain installed across reboots; no security/blocklist setting is disabled.

Official release checksums: [LHM 0.9.6](https://github.com/LibreHardwareMonitor/LibreHardwareMonitor/releases/expanded_assets/v0.9.6),
[PawnIO 2.2.0](https://github.com/namazso/PawnIO.Setup/releases/expanded_assets/2.2.0).
Task permissions follow [Microsoft task security](https://learn.microsoft.com/en-us/windows/win32/taskschd/security-contexts-for-running-tasks).
