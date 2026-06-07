---
id: 2605142355-okaimono-unispsc-contract-boundary
title: Okaimono UNSPSC contract boundary uses proto, manifest, docs, and verifier tests
status: active
doc_type: adr
topic: okaimono-unispsc-contract
authoritative: true
last_verified: 2026-05-14
authoritative_for:
  - okaimono UNSPSC catalog contract ownership
  - okaimono UNSPSC verifier scope
  - okaimono WIT pruning
related:
  - 2604251700-wproto-wit-dead-path
  - adr-2604261110-wproto-wreactive-wit-retirement
supersedes: []
superseded_by: []
---

# Context

Okaimono needs to consume actual UNSPSC commodity items from the openUnispsc
MCP surface:

- `com.etzhayyim.apps.openUnispsc.syncCatalogItem`
- `com.etzhayyim.apps.openUnispsc.planCatalogPurchase`
- `com.etzhayyim.apps.openUnispsc.importSegmentCatalog`

The Okaimono side exposes those capabilities through shopping catalog/order
contracts, component manifest capabilities/subscriptions, and operator docs.
Keeping an additional Okaimono WIT tree active would duplicate the contract
source and conflict with the repository-wide WIT retirement policy.

# Decision

Okaimono UNSPSC integration is governed by these active sources:

- `60-apps/etzhayyim-project-okaimono/proto/v1/shopping.proto`
- `60-apps/etzhayyim-project-shopping/proto/v1/shopping.proto`
- `60-apps/etzhayyim-project-okaimono/appview/okaimono-shopping-mcp-component/kotodama.jsonld`
- `60-apps/etzhayyim-project-okaimono/CLAUDE.md`
- `60-apps/etzhayyim-project-okaimono/appview/okaimono-shopping-mcp-component/README.md`
- `60-apps/etzhayyim-project-okaimono/okaimono-etzhayyim-ai-ec-operating-spec.md`

The Okaimono WIT path is legacy and pruned. It must not be reintroduced as the
active contract source for this integration.

The contract gate is:

- `python3 -m unittest 60-apps/etzhayyim-project-okaimono/tests/test_verify_unispsc_contracts.py`
- `python3 60-apps/etzhayyim-project-okaimono/scripts/verify_unispsc_contracts.py --pretty`
- `.github/workflows/okaimono-unispsc-contracts.yml`

# Consequences

- Proto fields/RPCs are the API contract for catalog import/search and order
  UNSPSC references.
- The component manifest declares the runtime capability/subscription surface.
- Docs must name the user-facing commands and openUnispsc MCP handoff tools.
- The verifier and its unit tests are part of the contract, not optional smoke
  checks.
- WIT-specific checks, `wasm-tools`, and `wit/okaimono` paths are intentionally
  absent from the Okaimono UNSPSC gate.

# Alternatives Considered

1. Keep Okaimono WIT as a parallel contract source.
   - Rejected: this creates duplicate ownership and contradicts the WIT dead
     path ADRs.

2. Rely only on proto compilation.
   - Rejected: proto compilation does not cover docs, manifest capabilities, or
     openUnispsc MCP handoff naming.

3. Rely only on docs and manifest checks.
   - Rejected: the catalog/order API fields and RPCs must remain mechanically
     verified.

# References

- `60-apps/deps.toml`
- `60-apps/etzhayyim-project-okaimono/scripts/verify_unispsc_contracts.py`
- `60-apps/etzhayyim-project-okaimono/tests/test_verify_unispsc_contracts.py`
- `.github/workflows/okaimono-unispsc-contracts.yml`
- `90-docs/adr/2604251700-wproto-wit-dead-path.md`
