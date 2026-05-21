# Workflows

This directory contains GitHub Actions CI workflows for the etzhayyim monorepo.

## test.yml

Runs on every PR and push to main.

**Jobs:**
- `vitest` — runs test suite for each of 25 canonical actors (`60-apps/ai-gftd-project-{actor}/rw-free`)
- `tsc --noEmit` — type-check core SDKs and tools (mock, auth, mst-projector, lexicon-to-openapi, integration-tests)
- `integration-tests` — Phase H cross-actor scenario tests

**Matrix:** fail-fast disabled; all jobs report in parallel.

## wrangler-validate.yml

Triggered by `deploy-preview` label on PRs.

**Job:**
- `dry-run` — runs `wrangler deploy --dry-run` for each actor's xrpc-adapter to validate CF Worker config before deployment

## Adding a new actor

1. Update the 25-actor matrix in both `test.yml` and `wrangler-validate.yml` (alphabetical order)
2. Verify actor has `60-apps/ai-gftd-project-{actor}/rw-free/package.json` with vitest config
3. Verify actor has `60-apps/ai-gftd-project-{actor}/xrpc-adapter/wrangler.jsonc`
4. Open a PR with the matrix update
