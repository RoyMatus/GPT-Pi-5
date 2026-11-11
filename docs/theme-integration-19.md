# Theme integration #19

Transferred the restricted frontend delta from frozen implementation
`24946e1b69cb7ffabd5ea7e8777a8df6238c6bdc` onto its exact base
`06a5d709a9c0d1216ce7ec1fe65c8d70d287fa50`. No backend/provider changes.
All archive manifest SHA-256 values verified. Frozen originals remain unchanged.
`package_theme_resources.py --verify-only` verified 248 files after rebuilding.
Both providers, portal variables, legacy migration and denied-storage handling
are supplied unchanged. Existing design references are preserved.

Validation: Windows x64, Python 3.12.14, Node 24.22.1, Edge.
126 offline tests passed (one platform skip); 11 Node tests passed; five resource
and pixel-comparator tests passed. npm ci/build succeeded.
Theme browser: 270 layout cases, 165 renders, all 15 schemes/persistence passed.
Computer, markets, calendar, photos, voice and remembered-login browser runners
passed with synthetic providers. No paid cloud calls or real microphone used.
Additional matrix/comparison results are recorded in the PR.

Pi access restored on 2026-11-11 using owner-supplied credentials and resolved
device address (not published). ARM64 Raspberry Pi 5, Python 3.13.5 and active
service confirmed. Initial host trust was accepted in memory for the new address;
subsequent connections pinned its SHA-256 key. No credentials were persisted.
Fontconfig selects Cantarell for Segoe UI and DejaVu Sans Mono for Consolas.
These are unapproved substitutes, so target visual acceptance remains blocked. No fallback is approved as exact visual acceptance.
Physical touch/audio, blur performance, browser zoom and target OSK acceptance
remain pending. Root font scaling tests do not establish browser zoom support.

Rollback: revert the integration commit and rebuild; for a later device install,
retain the previous release and use deploy/rollback-user.sh. Preserve profiles,
credentials and unrelated local changes. Actual captures/logs belong in ignored
build/, never over the originals.

Strict comparison: all 165 captures differ (zero threshold, no masks).
The current browser matches the recorded Edge 157.0.4341.46. CDP confirms
Segoe UI Semibold for the sampled overview heading and clock, matching the
recorded measurements. Runtime bytes reproduce the frozen SHA-256 values.
This narrows the investigation but does not prove rasterization is the sole
cause. Pixel fidelity is unresolved and must not be declared accepted.
192 shell layout cases passed. Wheel build succeeded.

Responsive audit completed: 3480/3480 cases passed (15 themes, 29
configurations, eight states), widths 320–3840 CSS px, DPR 1/2/3 and
200% root text size. No browser errors or external requests. Original report
and actual renders/diffs are retained under ignored build/. See the committed
comparison JSON for all 165 pixel counts and current sampled font measurements.
Overview fixture also reported PASS; its Windows server shutdown emitted a
WinError 10022 warning, so it is not reported as a clean log.

ARM64 source-checkout regression: 126 tests, OK with 12 platform/optional skips.
The first run found invalid UTF-8 in this integration report; corrected to UTF-8
and rerun successfully. Guidance/link validation passed locally. A wheel and
synthetic tests were staged in the user cache; active release/service, browser
profile and credentials were not changed. Device activation awaits design/font
acceptance and successful CI of the corrected commit.

Microsoft's font redistribution FAQ does not grant copying Windows font binaries
to this Linux device. Segoe UI licensing is available separately; no font purchase,
redistribution or fallback acceptance has been performed:
https://learn.microsoft.com/en-us/typography/fonts/font-faq
