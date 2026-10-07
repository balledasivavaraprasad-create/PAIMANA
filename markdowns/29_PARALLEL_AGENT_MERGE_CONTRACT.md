# Parallel Agent Merge Contract

## Goal

Allow multiple coding agents to work simultaneously without repeatedly touching the same files.

## Ownership principle

Each workstream owns a set of directories/components.

Agents must not casually rewrite files owned by another workstream.

## Shared contracts first

Before implementation, the following documents are treated as stable contracts:

- design system
- route map
- API contract
- data model
- analytics data contracts
- agent integration contract

If a contract needs changing, record the change explicitly rather than silently diverging.

## Recommended worktree boundaries

Possible ownership:

```text
frontend/landing/
frontend/app-shell/
frontend/analytics/
frontend/project/
frontend/investigation/
backend/api/
backend/analytics/
backend/automation/
backend/integration/
agent/peer/
agent/investigation/
```

Actual paths must follow the repository.

## Shared-file rule

Files like:

- global routing
- package.json
- global CSS
- shared types
- root config

should have a designated owner or be changed through small coordinated commits.

## Commit convention

Use narrow commits:

```text
feat(landing): build hero and proof strip
feat(analytics): add risk matrix
feat(agent): add peer deviation contract
fix(theme): correct light-mode popover tokens
```

## Merge order

1. design tokens/shared primitives
2. backend contracts/types
3. application shell/routing
4. feature pages
5. integration wiring
6. tests
7. polish/motion

## Conflict policy

When behavior conflicts with a contract, do not “make it work” by duplicating logic. Resolve at the owning layer.

## No cross-workstream redesign

An agent asked to build Analytics should not redesign the landing page.

An agent asked to build the agent integration should not rewrite project cards.
