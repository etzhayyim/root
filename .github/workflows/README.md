# Workflows

This directory contains GitHub Actions CI workflows for the etzhayyim monorepo.

> **tree-guard** (#1680-class tree wipes / orphan submodule pins / pin regressions) is a **local lefthook `pre-push` hook**, not a workflow — see `lefthook.yml` + `70-tools/scripts/lint/tree-guard.sh` (operator direction 2026-06-12: guard before the push leaves the machine; the server-side gate is the required-review ruleset on `main`). A short-lived `tree-guard.yml` workflow (#1684) was relocated there.

## ci.yml

Runs on every PR and push to main. Invokes the local lefthook pre-commit hook stack against the PR diff so contributors who skipped local hooks (`--no-verify`, lefthook not installed) still get caught.

**Jobs:**
- `lint-and-test` — `lefthook run pre-commit` (lint + e7m verify + secret scan + no-two-stage-etzhayyim-domains + paywall-warn + …)
- `Substrate-boundary backstop` — PR-diff scan against `origin/{base_ref}` for substrate-boundary violations (ADR-2605191648)

## test.yml

Runs on every PR and push to main.

**Jobs:**
- `vitest` — runs test suite for each of 25 canonical actors (`60-apps/etzhayyim-project-{actor}/kotoba`)
- `tsc --noEmit` — type-check core SDKs and tools (mock, auth, mst-projector, lexicon-to-openapi, integration-tests)
- `integration-tests` — Phase H cross-actor scenario tests

**Matrix:** fail-fast disabled; all jobs report in parallel.

## wrangler-validate.yml

Triggered by `deploy-preview` label on PRs.

**Job:**
- `dry-run` — runs `wrangler deploy --dry-run` for each actor's xrpc-adapter to validate CF Worker config before deployment

**Purpose:** regression-test the SDK build chain + cyber-drill consumer integration. Mirrors the local lefthook `pre-push` hook so contributors who push without local hooks still get caught.

**See also:** ADR-2605264300 (SDK three.js-free cutover) + ADR-2605265200 (20-actors duplicate retirement). Both ADRs' "CI regression-test addendum" §refers to this workflow.

## audit-health.yml

Triggered on **push to main + PR to main + manual `workflow_dispatch`** when `.github/dependabot.yml`, `.github/workflows/audit-health.yml`, `70-tools/scripts/audit/**`, the SDK's `package.json`, or any `.gitrepo` file changes.

**Job:**
- `monorepo-health` — runs `bash 70-tools/scripts/audit/all.sh` (the 4-script aggregator from iter-30/31/32 of /loop). Reports total findings vs. the documented baseline of 25 (0 dependabot + 0 SDK exports/dist + 7 stale subrepo URLs + 18 kotoba escape-symlinks). Non-strict by default — known-deferred findings (ADR-2605211845 + ADR-2605262130) don't fail PRs; new drift surfaces in the job summary for reviewer attention.

**Purpose:** structural drift detection. When the documented findings are resolved (kotoba upstream symlink coordination + per-app `.gitrepo` decision), the workflow's strict-mode flag can be enabled to gate against re-introduction.

## council-nomination-watch.yml

Watches PRs for Bootstrap Council Seat 2-5 nomination updates per ADR-2605192300. Adds a check that the 30-day public objection period is honored before merge of Council Lv7+ amendments.

## openot-gate-c.yml

Open-OT (`60-apps/etzhayyim-project-open-ot/`) Gate C deployment validation per the open-ot ADR series.

## kotodama-image.yml

Builds the `kotodama` container image when changes land under `40-engine/kotoba/crates/kotoba-kotodama/py/`.

## yorishiro-audit.yml

Auditing for the yorishiro generator (`70-tools/etzhayyim-cli/yorishiro/`) emitted MCP servers (ADR-2605211900).

## Adding a new actor

1. Update the 25-actor matrix in both `test.yml` and `wrangler-validate.yml` (alphabetical order)
2. Verify actor has `60-apps/etzhayyim-project-{actor}/kotoba/package.json` with vitest config
3. Verify actor has `60-apps/etzhayyim-project-{actor}/xrpc-adapter/wrangler.jsonc`
4. Open a PR with the matrix update

## Adding a new path-triggered workflow

For SDK / engine / app-specific regression coverage that doesn't fit the per-actor matrix, follow the `kami-engine-sdk.yml` pattern:

1. Define `on.push.branches: [main]` + `on.pull_request.branches: [main]` + `on.workflow_dispatch: {}` (manual trigger for stale-branch audit)
2. Add `paths:` filters under `push` and `pull_request` so unrelated commits don't trigger
3. Mirror the workflow with a `pre-push` block in `lefthook.yml` if local pre-flight is worth the wall-clock (typically <10s)
4. Cross-reference the workflow from the relevant ADR's "CI regression-test addendum" §
