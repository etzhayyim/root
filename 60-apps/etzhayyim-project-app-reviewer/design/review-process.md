# App Reviewer Process Design

## Roles
- Developer: submits app package and metadata.
- Reviewer: executes manual review and final decision.
- Admin: handles emergency revoke and policy overrides.

## Inputs required at submission
- app identity: `app_id`, `version`, `developer_id`, `org_id`
- package identity: `oci_ref`, `wasm_digest`, optional signature bundle
- capability declaration: outbound hosts, storage bindings, privileged operations
- policy declaration: data collection, retention, and third-party sharing

## Automated checks (blocking)
- Artifact integrity
  - digest match
  - signature verification
- Security
  - known CVE check in dependencies
  - static rule checks for dangerous calls
- Runtime
  - sandbox smoke run
  - panic/timeout/memory guard
- Policy
  - declared capabilities vs observed behavior diff

If any check is `critical` or `high` failure, status becomes `auto_failed`.

## Manual review checklist
- Functional correctness
  - main user flow works
  - no crash in normal operation
- Safety and abuse prevention
  - no fraud/scam flow
  - no hidden data exfiltration route
- Policy and compliance
  - metadata and actual behavior match
  - no prohibited content category

## Finding severity
- `critical`: exploit, data exfiltration, malware-like behavior
- `high`: severe auth/risk/policy issue
- `medium`: major bug or misleading behavior
- `low`: minor quality issue

## Decision policy
- Approve: no unresolved critical/high findings.
- Request changes: fixable findings remain.
- Reject: severe policy or security violation.
- Emergency revoke: post-release critical incident.

## SLA baseline
- automated checks: within 15 min
- manual review: within 24h (business day target)
- re-review after changes: within 12h
