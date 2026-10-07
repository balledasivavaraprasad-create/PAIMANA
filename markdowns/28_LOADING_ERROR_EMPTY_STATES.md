# Loading, Error and Empty States

## Principle

The product should fail gracefully and explain what is missing.

## Loading

Use skeletons that preserve final layout geometry.

Don't show full-page spinners for every chart.

## Partial failure

One failed chart must show:

`Analytics unavailable`

with retry.

Other sections remain usable.

## Empty analytics

Examples:

- “No historical snapshots available yet.”
- “No comparable projects meet the peer-quality threshold.”
- “No intervention outcomes have been recorded.”

## Stale data

Use a persistent but compact banner:

`Data last synchronized 9 days ago. Some analytics may be incomplete.`

## Investigation unavailable

Show:

- trigger
- available facts
- reason investigation could not complete
- retry option when appropriate

## Model unavailable

Do not display invented metrics.

Use:

`Prediction unavailable`

and show model/system status.

## Light-mode safety

Every empty/error/loading component must be tested in both themes.
