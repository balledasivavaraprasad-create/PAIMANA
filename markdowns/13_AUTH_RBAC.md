# Authentication and RBAC

## Roles

Suggested roles:

### Viewer
Can inspect portfolio, analytics and project intelligence.

### Analyst
Viewer plus exports and detailed analytical views.

### Investigator
Analyst plus investigation review and evidence detail.

### Approver
Can approve/reject recommendations assigned to the role.

### Administrator
Can manage users, thresholds, integrations, monitoring settings and system health.

## Principle

UI hiding is not authorization. Backend APIs must enforce permissions.

## Sensitive actions

Require authorization for:

- project mutation
- threshold changes
- recommendation approval
- intervention execution
- integration settings
- webhook configuration
- user/role management

## Audit

Record:

- actor
- action
- target
- timestamp
- old value/new value where relevant
- approval reason if applicable

## Session behavior

Use the existing auth provider if the main application already has one. Do not create parallel auth unless required.

## Frontend rules

Do not render a sensitive action merely because the user knows the route. Also rely on server-side denial.
