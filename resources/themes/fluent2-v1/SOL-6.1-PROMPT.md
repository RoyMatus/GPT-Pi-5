# Starter prompt for Sol 6.1 in IDEA

You are implementing the existing GPT-Pi 5 theme design, not designing a new one.
Work only in RoyMatus/GPT-Pi-5 and the supplied resource set. Read AGENTS.md,
README.md, docs/AI_CONTEXT.md, TESTING.md and tools/README.md first. Preserve other
local changes. Do not deploy to Pi or merge unless separately authorized.

## Mandatory design lock

Read `resources/themes/fluent2-v1/DESIGN_LOCK.md` in full. Strictly reproduce the
approved preview design by transferring the supplied resources. Do not invent,
redesign, approximate, regenerate assets, replace fonts/icons or "improve" any
colors, spacing, typography, materials, shapes, layout hierarchy or interaction.
Do not regenerate expected images to make changed UI pass. The source of truth
is the supplied implementation plus the immutable original PNGs and their hashes.
If something is unclear or unavailable, report the concrete gap instead of
silently inventing a substitute.

## Source of truth and acquisition

- Resource branch: `codex/swypetris-visual-themes`; the issue links an immutable
  resource commit. Fetch it and use those exact files, not a moving branch tip.
- Frozen UI implementation: `24946e1b69cb7ffabd5ea7e8777a8df6238c6bdc`.
- Comparison base: `06a5d709a9c0d1216ce7ec1fe65c8d70d287fa50`.
- Handoff: `resources/themes/fluent2-v1/README.md`, `DESIGN_LOCK.md`,
  `resource-lock.json`, `previews/manifest.json`, `previews/verification.json`,
  `responsive-report.json` and this prompt.
- 165 full-size references and 15 contact sheets are in `previews/`; reference
  viewport is 720 × 1280 CSS px. Open original PNGs, not just contact sheets.
- Run `python tools/package_theme_resources.py --verify-only` in the resource
  checkout with the pinned frontend built. Export the transferable ZIP with the
  same command without `--verify-only` if needed. Do not change lock checksums.

## Implementation sequence

1. Create an integration branch from current main and inspect its changes against
   the comparison base. Never replace another person's edits. The entire branch
   diff includes unrelated historical reference deletions: do NOT apply it.
2. Copy the ready-made theme modules, CSS, components and unchanged dependencies
   listed by `integration_files` in the resource lock. Preserve later functional
   changes in app.jsx and other touched files. Use the restricted integration
   patch only after inspection and `git apply --check`. Do not rewrite the design
   from screenshots or substitute a new CSS/component system.
3. Wire all 15 themes into both dashboard and Assistant settings, including portal
   dialogs, storage persistence, legacy light/dark migration and denied-storage
   behavior. Preserve all chat/voice/account/data operations and six tabs.
4. Read every failed responsive case in the audit. Fix proven adaptation defects
   with the smallest responsive rules; preserve all theme tokens and the approved
   720 × 1280 layout. Keep controls reachable at all supported viewport sizes,
   orientation changes, dense screens and 200% text. Do not remove controls or
   shrink touch targets to make a test pass. Preserve fullscreen photos and
   on-screen-keyboard input visibility. Do not report a finite matrix as proof of
   every possible display.
5. Verify which fonts are actually used on Linux/Pi. Font binaries are not in the
   package. Do not accept an unapproved fallback as preview fidelity; resolve
   lawful access to the preview font or ask the owner about the specific conflict.
6. Build and run the checks below. Keep the immutable reference directory intact.
   Actual captures belong in build/, never over the frozen references.
7. Prepare a PR with exact transferred resources, tests, comparison results,
   remaining platform/device limitations and rollback instructions. Update both
   READMEs, AI_CONTEXT and roadmap to the actual state. Do not claim installation
   or hardware acceptance from a Windows browser test.

## Required checks and acceptance

Use synthetic fixtures, never paid APIs, real tokens/chats or a live microphone.
Install the project's existing dependencies and optional Playwright as described
in TESTING.md; do not add runtime dependencies for screenshots.

```sh
npm ci
npm run build
npm test
python -m unittest tests.test_theme_resources tests.test_theme_preview_comparison -v
node tests/browser-themes.mjs
node tests/browser-theme-responsive.mjs
python tools/compare_theme_previews.py --actual build/fluent-theme-renders
python tests/browser_dashboard_foundation.py
python tests/browser_dashboard_computer.py
python tests/browser_dashboard_markets.py
python tests/browser_dashboard_calendar.py
python tests/browser_dashboard_photos.py
python tests/browser_voice.py
python tests/browser_remember_login.py
```

Set `PYTHONPATH=src` and the supported Playwright browser channel as needed.
The responsive audit and its report are part of this handoff; transfer the tools
and required tests into the integration branch before running their commands.
The comparison script must report every changed pixel; do not add blanket masks
or thresholds. Investigate browser/font/OS rasterization separately from actual
design differences and keep the owner's visual acceptance explicit.

Done means all 15 options switch and persist correctly; no lost functionality;
all required adaptive cases and regression scenarios pass; approved reference
geometry/materials/assets match; no unresolved font substitution is hidden; and
any unavailable device acceptance is listed as pending rather than completed.
