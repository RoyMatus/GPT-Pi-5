# Dashboard foundation handoff (#10)

Base: d7a8e3f9255a9356cb22560517d53bdfceb93e64, freshly fetched prototype branch.
Coordinator: Codex root, sole writer. Branch/worktree: codex/issue-10-foundation,
build/worktrees/issue-10-foundation. Integration branch has the same initial base.
No merge or deployment performed. Existing root documentation edits are preserved.

The reserved namespaces in #2 are retained. Shared lease for this PR: frontend/app.jsx,
frontend/dashboard/shared/**, frontend/dashboard/shell/**,
frontend/dashboard/assets/shared/**, src/gpt_pi/dashboard/shared/**,
package.json, README.md, README.en.md, docs/AI_CONTEXT.md, docs/ROADMAP.md,
TESTING.md and tests/dashboard-foundation*.test.mjs. Lease ends at handoff;
subsequent edits require a new recorded lease. No other writer is active.

Public frontend exports: DashboardShell (shell/shell.jsx), ScreenLifecycle,
SourceStore, clockSnapshot (shared/contracts.mjs), useClock (shared/clock.jsx).
Presentation exports retain the supplied kit's names and approved navigation order.
The production entry /?dashboard exposes the foundation; / retains the existing
assistant controller. Relocation and real tab-transition cancellation belong to #8.
Foundation placeholders are explicitly unavailable, without invented metrics or events.

SourceStore owns one producer for all subscribers. Source selection increments its
generation; producers publish only using the generation captured before an operation.
Last unsubscribe stops the producer and invalidates outstanding results. A producer
must react to source changes and cancel its old transport; adapters must never obtain
a fresh generation for an old response. Samples carry source, state, value (null for
unknown), unit/currency, acquiredAt and updatedAt in UTC ISO 8601, supported, errorCode.
Staleness is adapter-defined, visible to consumers, and never turns missing into zero.

The single clock reads wall time, including after visibility/pageshow and timezone
changes. Locale is ru-RU; default timezone is the current OS zone. Selected IANA zones
are supported by clockSnapshot/useClock but no zone preference is persisted yet.
Calendar arithmetic belongs to #6. No network access is needed for time.

Backend public interfaces: dashboard.shared.contracts. SSHService has separate
telemetry and photo sessions, never arbitrary command execution. The actual host
trust, key management, fixed collectors, timeouts, and permissions implementation
belongs to #4; #7 consumes the photo session contract and independently authorized
grant. ForceCommand/SFTP compatibility requires server-side verification. No SSH
implementation, credential storage, or server confinement is claimed by these types.

Access decision: the public shell and clock are accessible before cloud login;
private computer/photos/events are unavailable until their authorization design is
implemented and accepted. The shell never equates cloud login with PC permission.
No new private persistence is introduced. Only the existing theme preference is stored
in localStorage. Reserved settings namespaces: computer (#4), markets (#5), calendar
(#6), photos (#7), overview (#3); assistant chats stay RAM-only. Future storage needs
a coordinator-reviewed interface and feature-scoped schema registration before use.
No global database/schema or migration machinery is selected in this foundation.

Every worktree uses its own node_modules/.venv and generated assets. Synthetic runtime
must use absolute build/synthetic-data, a verified free port and a private browser
profile under that worktree. Do not use saved personal credentials or real PC data.

Outstanding acceptance: full render comparison, actual hardware, backend SSH fixture
contracts and review/merge gate. This PR is a foundation increment, not completed #10
or epic acceptance. #8 and the downstream issues are not released by its existence.

Verified on Windows/Python 3.12/Node 24 with Edge: npm run build; npm test
(6 passed); Python unittest discovery (76 passed); browser_dashboard_foundation.py
--browser-channel msedge (192 layout cases passed). Screenshots: ignored
build/dashboard-evidence/. Compared the portrait shell with approved Overview;
this does not establish completed screen composition fidelity. Package installation
built a wheel successfully. No Pi, physical touch, or SSH/provider acceptance run.
