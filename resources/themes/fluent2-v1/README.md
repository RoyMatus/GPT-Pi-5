# Exact theme resources — GPT-Pi 5 / Fluent 2 v1

This set transfers the implementation used for the 15 previews. It does not
propose another design. Start with [DESIGN_LOCK.md](DESIGN_LOCK.md), then use the
[Sol 6.1 implementation prompt](SOL-6.1-PROMPT.md).

Frozen implementation: `24946e1b69cb7ffabd5ea7e8777a8df6238c6bdc`.
Compatible comparison base: `06a5d709a9c0d1216ce7ec1fe65c8d70d287fa50`.

## Contents

- [Preview gallery](previews/index.html): 165 original screen/dialog PNGs plus
  15 contact sheets, copied unchanged from the chat delivery. GitHub may show
  HTML source; download the branch ZIP or open this file locally for the gallery.
- [Resource lock](resource-lock.json): SHA-256 for every frozen source, reference
  and compiled runtime file; original-to-target integration map.
- [Original render verification](previews/verification.json) and the new finite
  [responsive audit](responsive-report.json). Read actual failures and limits.
- [Actual font measurements](font-report.json): Segoe UI Semibold and Consolas
  on the Windows reference browser; these are system fonts, not bundled binaries.
- Source files remain in their real project paths at the frozen commit. No
  duplicate editable theme implementation is maintained in this folder.

The exported ZIP contains `source/` (complete frontend code/assets and pinned npm
dependencies, plus original UI test fixtures), `runtime/gpt_pi/web/` (ready-built
HTML/JS/CSS/illustration/worklet and legal notices), the preview set, a restricted
`integration.patch`, this contract, the starter prompt, validation tools and a
`MANIFEST.json` of all archive entries. Fonts, credentials, real chats, local
profiles and backend configuration are not included.

## Verify and export

In the resource branch, with its existing frontend build available:

```sh
python tools/package_theme_resources.py --verify-only
python tools/package_theme_resources.py
```

Output: `build/GPT-Pi-5-theme-resources-v1.zip`. The exporter uses Git blobs from
the pinned source commit. In a downloaded source ZIP without Git history, it
accepts only working-tree source bytes matching the frozen hashes. Changed/missing
reference or runtime bytes cause an error. It writes only the archive; it never
installs files, updates a device or changes the checkout.

If the runtime build is absent, build the **pinned implementation** in an isolated
checkout (`npm ci`, `npm run build`), then use its `src/gpt_pi/web/` outputs here.
Keep the source checkout at the pinned commit; do not build a redesigned frontend
and update the lock to accept it. The resource branch itself retains that frontend
unchanged. Node.js 22+ and the committed package-lock.json are required for building;
Node is not needed on Pi for the ready-built Python package.

## Transfer into the application

1. Read the target repository instructions and current state. Create a separate
   integration branch based on current main. Preserve unrelated changes.
2. Verify the lock. Compare target files with the recorded base, and use the
   `integration_files` list to scope the transfer. On the unchanged base, the
   supplied source files can be copied exactly. With later functional changes,
   merge the UI delta while keeping those changes.
3. `git apply --check integration.patch` is a preview, not an instruction to
   overwrite current logic. The patch is restricted to frontend/package/HTML
   paths; it intentionally excludes unrelated documentation deletions.
4. Include the original appearance tests and theme fixtures in the integration;
   use the resource branch's responsive audit. Build the frontend normally.
   Compiled JS/CSS are generated install artifacts, not editable source files.
5. Run the checks in the starter prompt, compare against the frozen PNGs and fix
   any demonstrated adaptive defects within the design lock. Update current
   documentation without replacing unrelated content. Prepare a PR and report
   outstanding hardware/font acceptance separately.

The runtime subtree may be staged into a compatible application's wheel build
instead of rebuilding it, preserving its relative paths and LEGAL file. Do not
overwrite a running installation or a different application version without
compatibility verification and a rollback package. The backend is not contained
in this theme ZIP; it is not a complete Pi image or automatic device installer.

## Verified handoff state

The 2026-11-11 Edge 157.0.4341.46 audit passed **3480/3480** cases: 15 themes,
29 configurations and eight states. Widths 320–3840 CSS px, 480/600/720/1024
breakpoints ±1 px, short 320/360 px windows, DPR 1/2/3 and 200% root text scaling
are covered. The scaling test is not browser zoom. No browser errors or external
requests were recorded. The report's app.js hash matches the ready-built runtime.

All 165 copied reference screenshots were compared with the chat-delivered set:
zero changed pixels. This verifies the handoff copies, not a new Pi rendering.
Five focused tooling tests passed, including rejection of changed resources,
unsafe archive paths, one-pixel changes and image-size changes. Rebuilding from
canonical source ZIP contents reproduced the locked runtime bytes, and exporting
without Git history was checked. Actual Pi/font/blur-performance acceptance remains
pending; frontend source and preview images were not changed by this handoff.

## What must be carried over

All 15 IDs: `fluent_light`, `fluent_dark`, `classic`, `monokai`, `gruvbox`, `vscode`,
`dracula`, `nord`, `solarized_light`, `solarized_dark`, `github_light`, `tokyo_night`,
`catppuccin`, `synthwave_84`, `green_phosphor`.

Keep `ThemePicker`, both Fluent providers, document-level variables used by
portals, storage/migration and storage-denied fallback. Transferring only palette
JSON is insufficient. Keep the six tab components, source CSS, standard icons and
the existing holiday-tree.png. Do not ship synthetic fixture responses as data.
