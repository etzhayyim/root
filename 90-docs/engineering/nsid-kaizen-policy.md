# NSID Kaizen Policy

## Canonical Command Naming
- Canonical command namespace: `app.etzhayyim.apps.<app>.<method>`
- `<method>` must be `lowerCamelCase`
- Legacy names (`snake_case`, plain, `UpperCamelCase`) are compatibility aliases only

## Baseline And Guard
- Baseline file: `80-data/80-data/80-data/reports/nsid-rule-violations-2026-04-01.csv`
- CI guard: `70-tools/70-tools/70-tools/70-tools/70-tools/70-tools/scripts/lint/nsid-regression-guard.mjs`
- Entry point: `gftd lint nsid-regression` (Go CLI launches Node lint script)
- Hook: `lefthook` pre-push command `lint-nsid-regression`

## Hook Rule
- Existing baseline violations are tolerated temporarily
- New violations (path + method not present in baseline) fail pre-push
- Removed violations are allowed and expected

## PDS Namespace Migration (2026-04-03)
- Canonical:
  - `app.etzhayyim.pds.listHeartbeatApps`
  - `app.etzhayyim.pds.registerSyncApp`
- Removed alias (no longer accepted by PDS as of 2026-04-03):
  - `app.etzhayyim.apps.pds.listHeartbeatApps`
  - `app.etzhayyim.apps.pds.registerSyncApp`
- Enforcement:
  - callers must use canonical NSIDs only
  - alias calls return method-not-found at dispatch layer

## Update Procedure
1. Migrate commands to canonical NSID form
2. Keep legacy aliases during rollout
3. Verify clients use NSID endpoints
4. Regenerate baseline only when intentionally re-baselining
