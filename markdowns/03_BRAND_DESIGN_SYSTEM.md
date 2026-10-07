# Brand + Design System

## Visual direction

Desired character:

- premium
- institutional
- technical
- calm
- data-dense but readable
- modern without looking like a consumer crypto dashboard

Reference feeling: a high-end national infrastructure command center.

## Theme model

### Dark theme

Primary surfaces should use very dark navy/charcoal rather than flat pure black everywhere.

Use:
- deep background
- elevated dark surfaces
- translucent but readable overlays
- white/high-contrast text
- blue/cyan for active intelligence
- green for healthy outcomes
- amber/orange for attention
- red only for critical state
- purple for agentic/analytical context

### Light theme

Use:
- warm/cool off-white page background
- white elevated surfaces
- dark charcoal foreground
- subtle gray borders
- restrained accent usage

Every surface must explicitly define both foreground and background. Do not depend on inherited colors for dropdowns/popovers/menus.

## Semantic color system

```text
healthy       → green
attention     → amber
high risk     → orange
critical      → red
informational → blue
agentic       → purple
neutral       → slate/gray
```

Colors are semantic, not decorative.

## Typography

Use a modern variable sans family available in the existing stack. Prefer a single primary family plus a mono face only for IDs, timestamps, model/version labels and technical traces.

Hierarchy:

- Display: bold, tight tracking, large
- Page title: strong but restrained
- Section heading: semibold
- Metric: large, tabular numerals
- Body: readable 14–16px equivalent
- Dense metadata: 12–13px equivalent

Do not use overly futuristic fonts.

## Surfaces

Recommended tiers:

1. page background
2. primary panel
3. elevated panel
4. inset panel
5. popover/modal

Cards should have enough opacity/contrast to remain readable over any map/image background.

## Borders

Prefer subtle 1px borders over heavy shadows.

## Radius

Use a consistent radius scale. Avoid mixing many unrelated border radii.

## Charts

Plotly must inherit the application theme dynamically.

Dark mode charts:
- dark plot area
- light axis/legend text
- subtle grid

Light mode charts:
- light plot area
- dark axis/legend text
- subtle grid

Hover labels must always maintain contrast.

## Component states

Every interactive component must define:

- default
- hover
- focus-visible
- active
- selected
- disabled
- loading
- error

No state should unexpectedly become black in light mode.

## Data density

Use whitespace around strategic groups, but don't create giant empty hero-like gaps in operational screens.

## Icons

Use one coherent icon library already compatible with the project. Do not mix multiple visual icon styles without a reason.
