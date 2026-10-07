# Test Strategy

## Testing layers

### Unit

Test:

- formatting
- chart transformations
- filter logic
- status mapping
- API parsing

### Backend integration

Test:

- project update → monitoring
- snapshot/change
- prediction
- event creation
- investigation trigger
- approval
- outbox
- analytics aggregations

### Agent tests

Preserve the existing agent behavioral suite.

Add explicit quality benchmarks separate from software behavior tests.

## Agent quality benchmark

Cases should include known scenarios:

- financial/progress mismatch
- schedule delay
- reporting discrepancy
- approval/clearance bottleneck
- multiple possible causes
- conflicting sources
- insufficient evidence

Measure:

- hypothesis quality
- unsupported causal claims
- tool choice quality
- evidence sufficiency
- premature termination
- recommendation quality

## E2E frontend

Test:

- login
- route navigation
- portfolio filtering
- analytics cross-filter
- project drilldown
- investigation flow
- approval permissions
- alert acknowledgement
- theme toggle

## Visual regression

Capture key screens in:

- dark mode
- light mode

Specifically test the known light-mode interaction issue around filters/dropdowns/popovers.

## Accessibility

Run automated accessibility checks plus keyboard/manual checks.

## Performance

Check:

- initial route load
- analytics route load
- chart rendering
- large table behavior
