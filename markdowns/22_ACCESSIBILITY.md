# Accessibility

## Core requirements

- keyboard navigation
- visible focus state
- sufficient contrast
- semantic headings
- accessible form labels
- accessible tables
- accessible dialogs/drawers
- reduced-motion support

## Charts

Plotly charts must not rely on color alone.

Provide:

- readable labels
- hover/focus details
- textual summary where practical

## Status

Do not communicate status only by red/green color.

Use:

- icon
- text
- color

## Reduced motion

Honor `prefers-reduced-motion`.

Disable/limit:

- large hero transitions
- background particle movement
- chart entrance animations
- cursor effects

## Light theme

Check every component state under both themes, particularly:

- select menus
- popovers
- command palette
- tooltips
- active filter chips
- data table rows
