# Calendar policy

Dates are YYYY-MM-DD; optional HH:mm is a floating local wall time, not an instant.
DST skipped/repeated wall times are displayed as entered and never scheduled or
converted silently. No notifications, UTC instant or timezone migration is claimed.
Countdown counts calendar days excluding today, floored at zero for past targets.
The shared clock supplies the current date in the OS zone; dates do not shift when
the zone changes. Selection differs from today.

Events are scoped to the authenticated backend session, never a client owner ID.
They live only in RAM (128 events max), clear at logout/expiry/restart and have no
disk backups. This is explicit in the UI. There is no private-data database.

Base 6150fc199b5189eb6349f8ba472d8be025fe9c3a. Coordinator root has the exclusive
lease for webapp Session/route and asset allowlist, frontend registry/build, npm test
script, CI calendar runner and shared docs in this worktree until PR handoff.
Validation: model/date tests observed failing behavior before implementation; API
negative tests cover authentication, CSRF, foreign event IDs and logout cleanup.
Node month tests and synthetic browser CRUD pass. 192 shell geometry cases pass.
Physical touch and full epic screen comparison are separate acceptance evidence.
