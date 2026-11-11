# Photos: server permission and cache policy

Photos use the shared SSH profile/trust service and a separate photo key/user. A live
session must explicitly grant a root and confirm server-enforced read-only confinement.
Telemetry consent is insufficient. The application never silently changes server ACLs,
ForceCommand, chroot or forwarding policy to make SFTP work. A server administrator
must verify confinement/ACLs: an application allowlist or checkbox is not server proof.
SFTP v3 pathname checks cannot eliminate every rename/symlink race on an untrusted,
concurrently writable server; read-only confinement to the actual library remains a
prerequisite. This limitation is explicit in the device setup and SSH policy.

Registration canonicalizes the chosen absolute root and rejects symlink aliases.
Only registered opaque file IDs are accepted for reads. Every listing/read checks
canonical root/path, non-symlink regular-file type, size and metadata before/after
open/read. Reads use rb only. Root/grant/source generation and live-session ownership
are rechecked before delivery. Source/profile removal and logout invalidate old grants.
Windows drive-qualified paths are normalized conservatively; actual Win32 SFTP/ACL
acceptance is separate from synthetic path fixtures. Unsupported aliases fail closed.

Limits: no recursion (one explicitly granted folder); first 512 directory entries;
JPEG/PNG/WebP, max input 8 MiB, max decoded 12 million pixels, one decoding/transfer
worker at a time. EXIF orientation is applied, metadata stripped and output reduced to
1920x1920 max / 2 MiB JPEG. No disk image cache or demo library fallback. A canceled
worker retains its semaphore until it actually finishes; SSH I/O is bounded and closed
on cancellation, preventing a second decoder from overlapping the old worker.

Browser keeps one current object URL; change/leave/hide/logout aborts transfer and
revokes it. Slideshow starts with all chrome hidden, click reveals controls/navigation;
Escape exits, arrows step, Space pauses. Cover cropping and contain are explicit choices;
no stretching. Interval 2..300 seconds, sorted/random order, one timer. Rendering uses
img blob URLs; CSP allows blobs only for images/media, never executable scripts.

Base 3049fb98501167fd347fcb6974c16a0bea7fe357. Coordinator root owns Photos and the
exclusive app private-clear event, shared frame/fullscreen/shell/registry/routes/CSP,
Pillow dependency, fixture/CI/docs lease until handoff. No concurrent writers.
Validation: observed path/orientation failures before implementation; synthetic SFTP
rejects traversal/links/unregistered IDs/stale generations, image limits and EXIF cleanup
pass. API auth/CSRF/separate permission and browser fullscreen/reveal/next/Escape/
hidden-page object-URL cleanup pass. Real owner-folder/server ACL and physical touch
acceptance cannot be inferred from those synthetic checks.
