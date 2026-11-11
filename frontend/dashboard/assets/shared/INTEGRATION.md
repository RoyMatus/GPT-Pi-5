# Copy-ready UI resources

These files are presentation resources, **not implemented monitoring, weather,
market, calendar, photo-sharing or assistant integrations**. The approved renders
remain the mandatory visual reference. There is no permission to redesign them.
The constants are inferred from the images; they are not exact Figma measurements
and must be calibrated against screenshots before visual acceptance.

## Copy and import

Copy `ui/` into the implementation's frontend source tree. Keep `icons.jsx`,
`components.jsx` and `tokens.css` together. Existing project dependencies provide
React, Fluent UI React v9 and Fluent icons; no new package or font download is needed.

```jsx
import { DashboardProvider, DashboardFrame, MetricCard, Sparkline } from "./ui/components.jsx";
import { dashboardIcons } from "./ui/icons.jsx";

<DashboardProvider className="dashboard-viewport">
  <DashboardFrame title="Компьютер" activeTab="computer"
    onNavigate={navigate} onSettings={openSettings}
    connected={connection.connected} connectionLabel={connection.label}>
    <MetricCard label="CPU" value={telemetry.cpuLabel}
      detail={telemetry.cpuTemperatureLabel} icon={dashboardIcons.cpu}>
      <Sparkline values={telemetry.cpuSamples} min={0} max={100}
        label="Загрузка процессора за последнюю минуту" />
    </MetricCard>
  </DashboardFrame>
</DashboardProvider>
```

The enclosing container must have a resolved height. Use `dashboard-viewport` for
a full app view or supply a parent height when embedding in a larger shell.
Never include the pictured metal bezel or stand in the application viewport.

## Components and responsibilities

| Resource | Caller supplies |
| --- | --- |
| `DashboardFrame` | Current title/tab, real connection state, navigation/settings callbacks, optional footer; `fullscreen` omits shell chrome |
| `DashboardNavigation` | `activeTab` and required `onNavigate(id)`; six fixed approved labels/order |
| `Panel`, `MetricCard` | Labels and formatted, unit-bearing values; unknown metrics use null/explicit unavailable text |
| `Sparkline` | Finite sample array, accessible label, optional real axis range; it does not fetch or invent samples |
| `ProgressMeter` | Percentage and accessible label; unknown is not converted to zero |
| `ClockHero`, `CountdownCard` | Already formatted time/date/count; no timezone or countdown arithmetic is hidden in these widgets |
| `MonthCalendar` | Monday-first cells and all date/navigation callbacks; no persistence, recurrence or date arithmetic |
| `Agenda` | Event list and optional add callback |
| `Suggestion`, `Composer` | Explicit actions; a suggestion may populate a draft, never silently send device data |
| `PhotoFrame` | Approved image URL, alt, cover/contain choice, disclosure state, controls and image error handling |

`MonthCalendar` cells are `{key, day, dateTime, selected, today, hasEvent}` or `null`;
`today` marks the current date semantically, while `selected` controls selection.
Do not mislabel a selected future date as the current date. Calendar callbacks, image intervals, cache rules, providers,
authentication and request cancellation belong to the screen-logic tickets.

## Different devices, panels and resolutions

- 720 × 1280 is the approved portrait **comparison viewport**, not the only supported panel.
- Use CSS pixels and the platform's viewport/DPI. Do not derive text or touch sizes
  from the panel's physical resolution and do not scale a whole screenshot/canvas.
- Layout fills the provided viewport. Text uses `rem`/`clamp`; cards use flexible
  columns. Main content scrolls independently of the navigation.
- At widths below 480 CSS px the metric grid becomes one column. The six labelled
  navigation items remain at least 92 CSS px wide in a horizontally scrollable row;
  do not truncate or replace labels. Keyboard focus scrolls focused items into view.
- At widths of at least 1024 CSS px the example screen groups use two columns in
  their existing reading order. This adapts geometry, not palette or hierarchy.
- Interactive controls have a baseline 44 CSS px minimum height; inspect actual
  physical finger use separately. The compact month grid scrolls inside its own
  card when enlarged text would make seven touchable columns exceed the width.
- Check portrait and landscape, DPR 1/2, 200% text zoom, reduced motion, and on-screen
  keyboard/visual-viewport changes. `100dvh` alone does not prove keyboard behavior
  on every OS; integrate the existing device keyboard behavior and verify it there.
- Segoe is used when installed. Linux/system fallback changes glyph metrics.
  No proprietary font files are redistributed. If exact font matching requires
  licensing/provisioning, resolve that before claiming visual equivalence.

## Example harness

`examples/ScreenExamples.jsx` offers all six visual fixture screens with **synthetic**
data. It is a resource-usage example, not a replacement for the application.

`examples/BundledPreview.jsx` shows direct imports of the supplied resources:
`assets/holiday-tree.png` and `assets/demo-alpine-lake.png`. Use the bundler's PNG
file loader (for esbuild, `loader: { '.png': 'file' }`) and retain its emitted asset
files. The PNGs are implementation resources derived from the approved reference;
if any image detail differs, the original render remains authoritative.

```jsx
import { ScreenExamples } from "./examples/ScreenExamples.jsx";
// URLs can come from imports handled by the app's bundler:
<ScreenExamples calendarArtwork={calendarImageUrl} photoUrl={samplePhotoUrl}
  initialTab="calendar" actions={screenCallbacks} />
```

Photo examples are edge-to-edge. A tap reveals navigation; the runtime must wire
slideshow intervals/pause/next/previous and a reliable exit. `fit="cover"` crops
edges to fill a panel; `fit="contain"` preserves the entire photo with unused space.
The product choice must be explicit for images whose aspect differs from the screen.

The `beforeNavigate` callback is a notification, not an asynchronous navigation guard.
The integration must cancel capture/playback and handle active streaming before
switching to a sensitive view. There is no microphone, token, file or network API in
this kit. Header connection state must come from actual PC pairing, not OpenAI login.

## Acceptance

Compare the live app screenshot's screen content against the reference at 720 × 1280,
then verify responsive adaptations on other devices. Check typography, relative card
sizes, gaps, icon mapping, blue selection, chart colors, nav order and photo immersion.
Do not call compilation or these demo fixtures a pixel-perfect visual acceptance,
hardware acceptance, or proof that any screen's data logic works.

## Optional local verification

Build the portable preview with `node examples/build-preview.mjs` from the kit
directory after copying it into the repository. The generated `examples/.preview/`
is an offline visual preview and can be omitted from the resource archive.
For geometry smoke checks, use the existing development Python environment with
Playwright: `python examples/check-layout.py --browser-channel msedge` on a machine
with Edge, or omit the channel for an already installed Playwright Chromium.
This does not require installing a browser or adding runtime dependencies.
