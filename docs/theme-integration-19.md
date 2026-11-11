# Theme integration #19

Version 0.3.4 transfers the restricted frontend delta from implementation
`24946e1b69cb7ffabd5ea7e8777a8df6238c6bdc` onto its exact comparison base.
All 15 IDs, palettes, assets, components, providers and portal variables are
preserved. No live backend/provider has been replaced by a fixture.
Original references/checksums and older dashboard references are unchanged.

## Authorized platform typography

The owner explicitly approved out-of-box substitute fonts on 2026-11-11,
provided the layout is retained. This is an exception for platform typography
only; the original DESIGN_LOCK and PNGs remain immutable.
Windows retains Segoe UI/Consolas. Pi uses installed Cantarell and Noto Sans Mono
through local-only font faces. No font binaries are downloaded or redistributed.
Cantarell size-adjust 98.5% prevents the evidenced 720px overview network-detail
wrap (previously increasing the panel height by 28px). The Noto mono adjustment
91.63423% matches measured Consolas digit advance: 109.87 vs 109.96px for ten
digits at 20px. CDP confirms the actual target fonts. These are measured layout
substitutes, not a claim of identical glyphs or cross-platform pixels.

## Verification

Windows x64/Python 3.12/Node 24/Edge: 126 offline tests (one platform skip),
11 Node tests, five resource/comparison tests, 270 theme layout cases and
192 shell cases passed. Synthetic computer, markets, calendar, photos, voice
and remembered-login scenarios passed; wheel built. No paid API/microphone.
The separate overview runner reported PASS with a Windows shutdown warning.
The original resource exporter verified 248 locked files before the authorized
font adaptation. It remains an exporter for the original resource set, not
an assertion that the adapted application runtime has the old hash.

Strict Windows comparison: 165/165 screenshots match the frozen originals,
zero changed pixels, no masks/thresholds. Initial differences were not
reproducible in the normal Edge renderer; isolated GPU-mode probes produced
SVG-edge raster differences, while normal/default and sRGB probes matched.
The compositor-specific cause of that transient initial state is not proven.

Original Windows responsive audit: 3480/3480 cases, widths 320–3840 CSS px,
DPR 1/2/3, 200% root text. Root scaling is not browser zoom.
Pi ARM64/Python 3.13 source-checkout regression: 126 tests, 12 platform/optional
skips. Corrected an invalid UTF-8 report discovered during this run.
Pi browser matrix and installation results are recorded in the PR.
Actual renders/logs stay in ignored build/; original expected images never change.

## Deployment and limits

Target is verified Raspberry Pi 5 ARM64, Debian 13, Chromium 154, 720x1280.
Credentials and addresses are excluded from Git. Connections pin the observed
SSH key after the initial authorized connection. Separate synthetic browser
profiles keep real chats/account data out of screenshots and fixtures.
Physical audio/touch and physical power-cycle acceptance cannot be inferred
from automated rendering. Font substitutions intentionally differ from Windows
glyphs; strict cross-platform comparator differences are reported, not masked.

Rollback: revert integration changes and rebuild, or restore the retained
previous device release with deploy/rollback-user.sh. Preserve profile/data.
