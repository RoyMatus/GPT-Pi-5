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

Pi installation is pending: SSH via the device hostname failed host-key
verification; trust was not bypassed. Segoe UI/Consolas are not bundled and their
actual Pi use is unverified. No fallback is approved as exact visual acceptance.
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
