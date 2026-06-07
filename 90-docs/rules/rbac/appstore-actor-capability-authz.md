# AppStore Actor Capability AuthZ Rules

This rule set defines authorization for the app review and publish workflow using `actor_nanoid + capability`, not coarse role checks.

## Core Principles

1. Subject identity MUST be `actor_nanoid` resolved by authn (Clerk/JWT + mesh identity), not a client-trusted free-form field.
2. Authorization MUST evaluate action + resource + capability, not role names.
3. UI visibility controls are advisory only. Final enforcement MUST happen in provider APIs (`etzhayyim:appstore`, `etzhayyim:review`).
4. Every allow/deny decision MUST emit an immutable audit log entry.

## Required Input For Policy Decision

- `subject_actor_nanoid`
- `action` (for example `submit-version`, `publish-app`, `assign-reviewer`, `submit-review`)
- `resource_id` (for example `app_id`, `submission_id`)
- `resource_owner_actor_nanoid` and/or `resource_owner_org_id` when applicable
- `effective_capabilities` for subject at decision time
- request timestamp (`decide_at_unix_ms`)

## Mandatory Capability Gates

1. `submit-version` requires capability scoped to target app: `app.submit:<app_id>` or wildcard grant.
2. `assign-reviewer` requires `review.assign` capability.
3. `submit-review` requires `review.decide:<submission_id>` and reviewer assignment match.
4. `publish-app` requires `app.publish:<app_id>` and prior approved review summary.
5. `emergency-revoke` requires privileged platform capability (no app-owner self-grant path).

## Assignment and Ownership Constraints

1. A review decision MUST be accepted only if `subject_actor_nanoid == assigned_reviewer_nanoid`.
2. Reviewer assignment changes MUST be versioned and auditable (who changed, old/new assignee, timestamp).
3. Capability grants MUST include grantor nanoid and optional expiry.
4. Self-grant for privileged capabilities MUST be denied.

## Workflow Safety Constraints

1. Publish transition is allowed only from approved state with valid signature and supply-chain checks.
2. Re-review requirement (`needs-information`) MUST block publish until a new approved decision exists.
3. Idempotency key is REQUIRED for mutating actions (assign, decide, publish, revoke).

## Audit Log Minimum Fields

- `decision_id`
- `subject_actor_nanoid`
- `action`
- `resource_id`
- `allowed`
- `matched_capability_id` (if allowed)
- `reason`
- `request_id`
- `decide_at_unix_ms`

## WIT Enforcement

- **Policy check**: `governance.check-policy(action, subject_actor_nanoid, org_id)` → allow/pending-approval/denied
- **Permission check**: `governance.check-permission(subject_actor_nanoid, org_id, capability_id)` → allowed + matched-role
- **Audit trail**: `audit-trail.emit(authz, action, resource_id, outcome, details)` → immutable seq
- **Risk gate**: `governance.list-risks(open)` for supply-chain checks before publish

## Implementation Note

These rules are enforced by the `kotodama:agent/governance` WIT host (RBAC + RACI policy) and the `kotodama:observability/audit-trail` WIT host. BPMN orchestrates sequence; governance WIT gates transitions.
