---
id: adr-2606074000-apps-maturity-enhancement
title: "ADR-2606074000: Apps Store Appview Testing Baseline and Maturity Enhancement"
status: approved
doc_type: adr
topic: testing-maturity
authoritative: true
last_verified: 2026-06-07
priority: 5.0
axis: quality
weight: 0.50
priority_note: "Ensures baseline test coverage across 73 Apps Store apps."
authoritative_for:
  - 60-apps
depends_on: []
related: []
supersedes: []
superseded_by: []
---

# ADR-2606074000: Apps Store Appview Testing Baseline and Maturity Enhancement

**Status**: approved
**Date**: 2026-06-07
**Deciders**: Jun Kawasaki

# Context
We identified that out of the 73 core apps listed in the Apps Store UI (e.g., `kiyome`, `gmail`, `docs`, `harai`, etc.), a significant portion (41 apps) lacked a testing harness, while others had tests but either lacked complete coverage or failed due to underlying SDK mismatches. Ensuring that all apps have a baseline testing standard is crucial for maintaining platform stability, avoiding regressions, and facilitating safer refactors when upgrading substrate components like `kotoba-kotodama` or `@etzhayyim/sdk`.

# Decision
1. **SDK Dependency Fix**: We downgraded `@noble/hashes` from `2.2.0` to `1.8.0` in `@etzhayyim/sdk` and fixed corresponding module export references, successfully repairing the test failures for `yadoya` and `shopping` apps.
2. **Core Coverage Expansion**: We extended integration test suites for existing mature apps (`manga`, `anime`, `narou`) to push their Line and Statement test coverage beyond 80%, providing a golden standard for test coverage across the ecosystem.
3. **Vitest Scaffolding**: We programmatically scaffolded `vitest.config.ts` and baseline test facades (e.g., checking `/health` endpoint and routing behavior) for all 41 previously untested apps.
4. **Workspace Harmonization**: We updated the `pnpm-workspace.yaml` manifest to include all scaffolded `appview/*/svelte` directories, removed broken or unresolved local dependencies (e.g., `@etzhayyim/kotodama-host-sdk`, `@etzhayyimcojp/design-system`), and synchronized SvelteKit TSConfigs.

# Consequences
- **Positive**: All 73 apps listed in the Apps Store now feature at least basic continuous integration coverage (`Coverage > 0%` and `PASS`). The testing pipeline ensures the edge-level facades correctly route `xrpc` actions, respond to `/health`, and return properly scoped `did:web:` actor values.
- **Positive**: The workspace has been thoroughly synchronized with `svelte-kit sync`, alleviating TSConfig inference issues.
- **Neutral**: The test facades for some of the scaffolded apps mock `fetch` deeply, which means end-to-end BP/langserver orchestration still relies on upstream integration tests.

# Alternatives Considered
- Skipping baseline scaffolding and addressing tests case-by-case during feature implementation. This was rejected because the volume of apps would cause tests to lag significantly, masking latent routing bugs or uncompilable TS syntax over time.

# References
- `deps.toml` updated to reflect the completion of the 260607 Apps Maturity wave.
