---
id: adr-2605212100-etzhayyim-to-etzhayyim-migration-batch
title: "ADR-2605212100: etzhayyim→etzhayyim 60-apps migration batch (gov / law / legal scope)"
status: active
doc_type: adr
topic: etzhayyim-to-etzhayyim-migration
authoritative: true
last_verified: 2026-05-24
priority: 6.0
axis: migration
weight: 0.55
priority_note: "Referenced by DEPRECATED.md in source archive; back-authored 2026-05-24 to close the dangling reference."
authoritative_for:
  - etzhayyim-to-etzhayyim-60apps-batch
depends_on:
  - adr-2605172000-etzhayyim-rw-free-substrate
  - adr-2605172100-etzhayyim-payments-on-chain-only
  - adr-2605214000-etzhayyim-murakumo-mesh-no-vke-and-lexicon-port-rules
related:
  - adr-2605171900-yoro-migration-to-etzhayyim
  - adr-2605172800-geth-private-migration-to-etzhayyim
  - adr-2605202300-maps-etzhayyim-consumer-migration
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
supersedes: []
superseded_by: []
---

# ADR-2605212100: etzhayyim→etzhayyim 60-apps migration batch (gov / law / legal scope)

**Status**: active
**Date**: 2026-05-21 (batch executed) / 2026-05-24 (this ADR back-authored)
**Deciders**: Jun Kawasaki

# Context

On 2026-05-21, a batch migration moved a set of `60-apps/etzhayyim-project-*` directories from `etzhayyim-apps-etzhayyimcojp` to `etzhayyim/root/60-apps/`. The migration archive on the source side (`_archive/migrated-to-etzhayyim-2026-05-21/`) recorded the move and dropped a `DEPRECATED.md` in each migrated app.

Every DEPRECATED.md file cites this ADR (`ADR-2605212100-etzhayyim-to-etzhayyim-migration-batch.md`) as the migration record, but the ADR file itself was never authored. A 2026-05-24 audit triggered by the user question "この世の全ての政府機関、行政手続きの pregel, mcp の実装カバレッジ?" surfaced this gap, alongside three apps whose `appview/` and `wasm/` subtrees had been intentionally **excluded** from the copy because they rely on substrate primitives prohibited on the etzhayyim side (Kysely + HyperDrive Postgres, per ADR-2605172000).

The DEPRECATED.md authors were correct to skip the violating subtrees, but the deferral was never written down — leading the post-audit reader (the user) to perceive the religious-corp's gov / admin coverage as ~0% when in fact:

- `etzhayyim-project-cofog` (1229 files, 203 actor-bundles covering UN COFOG × country) is **fully migrated**.
- `etzhayyim-project-gov` (gov.etzhayyim.com public-services hub, 8 COFOG-aligned path-based DID sub-agents) had its `appview/gov-mcp-component/` (12 files) **deferred** due to Kysely/HyperDrive use.
- `etzhayyim-project-lawfirm-admin` (11 files) and `etzhayyim-project-legal-entity` (13 files) follow the same pattern.

# Decision

1. **Batch migration scope (2026-05-21, retroactively recorded here)**:
   - Apps moved fully: `etzhayyim-project-cofog` / `etzhayyim-project-government-body` / `etzhayyim-project-lawfirm` / `etzhayyim-project-lawyer`.
   - Apps moved with substrate-violating subtrees deferred: `etzhayyim-project-gov` / `etzhayyim-project-lawfirm-admin` / `etzhayyim-project-legal-entity`.
   - Apps added directly on etzhayyim side (no archive equivalent): `etzhayyim-project-legal-aid` / `etzhayyim-project-legal-corpus` / `etzhayyim-project-open-jpn-gov`.
   - Apps kept active on the etzhayyim side (not migration targets): `50-infra/cloudflare/workers/gov-fetch-proxy` (serves `*.etzhayyim.com` traffic; the religious-corp routing-around stance forbids etzhayyim depending on etzhayyim-side proxies).

2. **Deferred-subtree handling (2026-05-24 blind-copy wave)**:
   - The 36 files (12+11+13) previously deferred have been **blind-copied** to the etzhayyim side per user direction "blind copy して、後から修正".
   - Each restored app carries a `SUBSTRATE-PORT-PENDING.md` documenting the exact Kysely / HyperDrive call sites and the substrate-port checklist (Kysely → MST PUT via `@etzhayyim/sdk`, `did:web:*.etzhayyim.com` → `did:web:etzhayyim.com:*`, Lexicon `com.etzhayyim.apps.*` → `com.etzhayyim.*`, package `@etzhayyim/kotodama-*` → `@etzhayyim/kotodama-*`).
   - The substrate-port wave will execute as part of the ADR-2605214000 §3 atomic identifier cutover, gated on legal-registration completion of the etzhayyim → 宗教法人 transition.

3. **Authoritative audit record**: `60-apps/MIGRATION-NOTES-GOV-2026-05-24.md` is the single source of truth for the migration-gap matrix and per-app file counts as of 2026-05-24.

4. **Source-side DEPRECATED.md**: Left as-is on the etzhayyim side. Its reference to "ADR-2605212100" is now valid (this file).

# Consequences

- The religious-corp gov / admin coverage is no longer perceived as ~0%. The actual coverage is **9 apps under `60-apps/`** plus the `etzhayyim-project-cofog` 203-actor COFOG×country bundle.
- Pregel cells (`40-engine/kotoba/crates/kotoba-kotodama/cells/`) and MCP servers (`40-engine/kotoba/crates/kotoba-kotodama/mcp/`) remain **0 gov-specific** — by design. Gov coverage lives in the appview/worker layer, not the religious-corp Pregel cell catalog.
- A substrate-port wave is now formally on the backlog. Until it lands, the 3 restored apps **cannot be deployed on etzhayyim infra** without violating ADR-2605172000. Their presence in the repo is for git-history continuity and substrate-port reference only.
- The pattern of "DEPRECATED.md cites an ADR that doesn't exist" is closed; future migration batches should author the ADR **before** dropping deprecated markers.

# Alternatives Considered

1. **Author the ADR with `status: superseded` and write a new replacement ADR**: rejected. The batch did execute on 2026-05-21; the canonical date is 2026-05-21. Back-dating the ID matches the existing reference and the `_archive/migrated-to-etzhayyim-2026-05-21/` directory name.
2. **Hard-delete the dangling DEPRECATED.md references on the etzhayyim side**: rejected. The etzhayyim archive is part of the project's git history; rewriting it would propagate to multiple downstream consumers. The right fix is to author the missing ADR (this file).
3. **Substrate-port the 3 deferred apps now instead of blind-copying**: rejected per user direction "blind copy して、後から修正". Substrate-port is a non-trivial 36-file rewrite that requires test coverage + lefthook validation; deferring it to a focused wave is the better sequencing.

# References

- ADR-2605172000 (RW-free substrate boundary — the reason for deferral)
- ADR-2605172100 (substrate ladder)
- ADR-2605214000 §3 (atomic etzhayyim → etzhayyim identifier cutover)
- ADR-2605215000 (etzhayyim inference Murakumo-only)
- `60-apps/MIGRATION-NOTES-GOV-2026-05-24.md` (audit record)
- `60-apps/etzhayyim-project-gov/SUBSTRATE-PORT-PENDING.md`
- `60-apps/etzhayyim-project-lawfirm-admin/SUBSTRATE-PORT-PENDING.md`
- `60-apps/etzhayyim-project-legal-entity/SUBSTRATE-PORT-PENDING.md`
- Source archive root: `/Users/junkawasaki/github/etzhayyim-apps-etzhayyimcojp/_archive/migrated-to-etzhayyim-2026-05-21/60-apps/`
