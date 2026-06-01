# ai-gftd-project-open-seiyaku — Pharmaceutical Manufacturing BPMN Platform

**Status**: Phase 1 scaffold (2026-04-23). Canonical implementation lives in
monorepo contracts and graph migrations; this project directory is the entry
point for the OSS-facing design surface.

## Scope

- **Runtime**: BPMN-as-actor only. No dedicated Worker for business logic.
- **Domain**: GMP-oriented batch manufacturing for drug substance / drug
  product release.
- **Core flows**:
  - `seiyaku_register_batch` — plant operator prepares the batch record and QA
    releases or rejects it
  - `seiyaku_amend_batch` — amendment / deviation / CAPA loop for an existing
    batch
  - `seiyaku_purge` — confidential payload retention purge
- **Contracts**:
  - BPMN: `00-contracts/bpmn/ai/gftd/open-seiyaku/`
  - Forms: `00-contracts/forms/ai/gftd/open-seiyaku/`
  - Lexicons: `00-contracts/lexicons/ai/gftd/apps/openSeiyaku/`
  - Graph schema: `30-graph/graph-schema/migrations/20260423190000_vertex_open_seiyaku.ts`

## XRPC Surface

| NSID | Type | Description |
|---|---|---|
| `app.etzhayyim.apps.openSeiyaku.startBatchRecord` | procedure | start a new manufacturing batch workflow |
| `app.etzhayyim.apps.openSeiyaku.submitBatchDraft` | procedure | save encrypted confidential batch draft |
| `app.etzhayyim.apps.openSeiyaku.amendBatchRecord` | procedure | raise amendment / deviation workflow |
| `app.etzhayyim.apps.openSeiyaku.reviewBatch` | procedure | QA verdict with checklist |
| `app.etzhayyim.apps.openSeiyaku.finalizeBatch` | procedure | mark the batch released / rejected |
| `app.etzhayyim.apps.openSeiyaku.getBatchRecord` | query | fetch one batch record (RBAC gated) |
| `app.etzhayyim.apps.openSeiyaku.listForPlant` | query | plant / org batch list |
| `app.etzhayyim.apps.openSeiyaku.purge` | procedure | retention purge for confidential payloads |

## Design Notes

- `ADR-0051` in this repo is a payroll/fuyou ADR dated 2026-04-23. This
  project reuses that **implementation pattern**:
  BPMN-as-actor + graph tier split + form contracts + lexicon routing.
- Tier split is adapted for manufacturing confidentiality:
  - `vertex_open_seiyaku_batch` = Tier 1 metadata + batch hash
  - `vertex_open_seiyaku_batch_confidential` = encrypted BMR / QC / deviation
    payloads
- Retention is modeled as a configurable confidential-record lifecycle with a
  Phase 1 default of 10 years.

## Deploy

The runtime depends on the shared BPMN watcher / LangServer dispatcher already
present in the monorepo. There is no per-project deploy command beyond the
standard graph migration + contract sync pipeline.
