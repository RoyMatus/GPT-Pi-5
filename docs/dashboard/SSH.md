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
| Windows | PowerShell/CIM CPU, RAM, system drive, summed network-interface rates | CPU frequency from CIM; GPU/temperature/fan unavailable | OpenSSH server, PowerShell and permitted CIM classes |

Memory/disk use bytes converted to GiB (2^30); network rates use bits/s converted to
Mbit/s (10^6). First Linux network sample and counter resets/reboots are unavailable,
never zero traffic. Network totals include available physical/virtual interfaces and
are not a selected physical-link speed. Up to 60 actual samples are retained in RAM.
Requests use one batched collector with a 12-second command deadline and 20-second
outer bound; connection/auth/banner/channel bounds are explicit. No daemon, agent,
startup collector, driver or sensor utility is installed by this implementation.

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
