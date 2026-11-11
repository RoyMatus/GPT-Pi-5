# Hard design lock — Fluent 2 themes v1

## Non-negotiable instruction

**This is an implementation/transfer task, not a design task. Copy and integrate
the supplied resources. Do not redesign, reinterpret, approximate, regenerate or
"improve" the approved previews. Do not invent substitute assets.**

The implementation source is commit `24946e1b69cb7ffabd5ea7e8777a8df6238c6bdc`.
The visual references are the 165 original PNGs in `previews/`, identified by
`resource-lock.json` and `previews/manifest.json`. They are the same bytes delivered
in the chat, not a new rendering. The 15 contact sheets are navigation aids;
use the original 720 × 1280 PNGs for comparison.

Copy the existing theme data, CSS, React components, icons and illustration.
Keep all 15 scheme IDs, palettes, gradients, opacity, blur, shadows, radii,
outlines, spacing, typography, hierarchy, labels, icon shapes and control states.
Keep the position and behavior of the navigation and dialogs. Do not redraw
screens from PNGs, embed screenshots as UI, substitute a component library,
change the default scheme, or flatten the themes into unrelated color presets.

Do not edit, regenerate or replace the frozen previews, their checksums or this
design lock to make a different implementation pass. Never change expected
images to match actual output. Any intended change of the design requires an
explicit new user decision and a separate version of the reference set.

## Responsive behavior is required, not a redesign exemption

At 720 × 1280 CSS pixels the geometry must match the reference. At other sizes,
reuse the supplied fluid layouts, wrapping, scroll containers and breakpoints.
Only an evidenced adaptation defect may justify a targeted responsive-rule fix.
Such a fix must retain the reference viewport and the same visual hierarchy;
compare all affected reference screenshots again. Record the before/after
failure and affected viewport. Do not change tokens or remove functions to hide
overflow. Do not scale the whole application as a bitmap or shrink text/targets
until the layout fits.

All content and controls must remain reachable at narrow, short, wide and dense
viewports, with text enlargement and rotation. Intended local scrolling of the
navigation/content is allowed; uncontrolled page overflow, unreachable dialogs,
clipped submit/stop/close controls and overlay occlusion are not. Fullscreen
photos must fill the viewport without shell padding or a reserved scrollbar gap.
Keep explicit recording/error labels and monochrome semantics in Green Phosphor.
Keep reduced-motion, reduced-transparency and forced-colors behavior.

The finite matrix in `responsive-report.json` is evidence for those cases only.
It is not proof of every possible resolution. Failed cases remain blocking
acceptance items; never describe them as passed. Check additional sizes encountered
on the actual target, including its browser zoom and on-screen keyboard.

## Typography and cross-platform comparison

The original CSS uses Segoe UI Variable / Segoe UI / system-ui, and Consolas /
Cascadia Mono / monospace for phosphor metrics. Font binaries are not supplied.
Do not silently substitute or redistribute fonts. Record the actual font used
by the target browser. If the preview font is unavailable, resolve its lawful
provisioning or request the owner's decision before accepting a replacement.
An unapproved fallback is not exact visual acceptance.

For the same browser, fonts, viewport, DPR and deterministic fixtures, compare
pixels without masks or a permissive blanket threshold. Across platforms, document
any font-rasterization differences separately; they do not justify layout drift,
changed assets, a different palette or changed typography metrics. Never claim
pixel identity from identical CSS alone.

## Functional and repository boundaries

Preserve chat, voice, history, model selection, login/logout, telemetry, market
controls, calendar CRUD, countdown, SFTP/photo controls and all notices. Preserve
session ownership, request cancellation, microphone cleanup and backend APIs.
The preview fixtures are demonstration data; never ship them as live providers.

Compare each replaced file with the `base_commit` before copying. If current
application logic has changed, merge only the theme/UI changes and preserve that
logic. Do not blindly overwrite `frontend/app.jsx` or apply an unrestricted branch
diff. Do not delete the existing `docs/design/dashboard-2026-11-10/` references.
Do not overwrite unrelated local changes, including AI_CONTEXT/HARDWARE edits.
The historical `frontend/dashboard/assets/shared/INTEGRATION.md` is not the contract
for this resource set.

Do not deploy, merge or alter device services merely because the resources can
be built. Prepare a reviewable integration and the prescribed checks; device
installation follows an explicit deployment request. Roll back by reverting the
integration commit or restoring the backed-up package, never by destroying other
work with `reset --hard`.
