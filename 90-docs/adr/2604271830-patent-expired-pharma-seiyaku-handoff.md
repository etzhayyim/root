---
id: adr-2604271830-patent-expired-pharma-seiyaku-handoff
title: "Patent-expired pharmaceutical candidates hand off to open-seiyaku through auditable BPMN workers"
status: accepted
doc_type: adr
topic: patent-expired-pharma
authoritative: true
last_verified: 2026-04-27
authoritative_for:
  - patent-expired-pharma-bpmn-coverage
  - patent-to-open-seiyaku-handoff
  - expired-patent-worker-boundary
related:
  - 60-apps/etzhayyim-project-patent/magatama.toml
  - 60-apps/etzhayyim-project-patent/worker/python/patent_expiry_worker.py
  - 70-tools/config/bpmn-coverage-manifest.json
  - 30-graph/graph-schema/migrations/20260427075000_open_patent_expired_pharma_bpmn_worker.ts
  - adr-2604251024-patent-bulk-ingest-and-blob-cid
  - 90-docs/adr/0056-bpmn-as-actor.md
supersedes: []
superseded_by: []
---

# Context

The patent actor already covers public patent ingest and registry behavior.
The new pharmaceutical use case is narrower: find already-expired drug patent
candidates and connect them to `open-seiyaku` manufacturing workflows.

That path cannot be a direct "patent expired therefore manufacture" rule. A
patent term may be expired while regulatory exclusivity, litigation stays,
secondary patents, or missing plant/product batch context still block action.

# Decision

Expired pharmaceutical patent processing is modeled as an auditable BPMN worker
chain under `patent-expired-pharma`, not as a legal freedom-to-operate decision.

The chain is:

1. Collect estimated-expired pharmaceutical patent backlog.
2. Screen patent expiry and blockers.
3. Record explicit regulatory / litigation / secondary-patent blockers.
4. Create generic, biosimilar, or API-source manufacturing candidates.
5. Hand candidates to `open-seiyaku`.
6. Prepare an `openSeiyaku.startBatchRecord` draft.
7. Validate required batch-start fields.
8. Queue the `openSeiyaku.startBatchRecord` request.
9. Acknowledge open-seiyaku acceptance / start / rejection.
10. Summarize queued, accepted, started, or rejected progress.

The handoff target is fixed:

- NSID: `com.etzhayyim.apps.openSeiyaku.startBatchRecord`
- BPMN process: `seiyaku_register_batch`

# Worker Boundary

The Python worker in `60-apps/etzhayyim-project-patent/worker/python` is a
deterministic bridge worker for this pharma handoff path. It does not replace
the broader patent actor's shared-executor model.

The worker may:

- derive review candidates using explicit expiry dates or `filed_at + 20 years`
- persist auditable graph rows for candidate, blocker, handoff, draft,
  validation, queue, acknowledgement, and progress
- produce a start request payload for open-seiyaku

The worker must not:

- assert legal freedom to operate
- bypass regulatory blocker review
- start manufacturing directly
- write confidential open-seiyaku batch records directly

# Consequences

`60-apps/etzhayyim-project-patent/magatama.toml` is the local wiring manifest for
this handoff. Coverage is enforced by `70-tools/config/bpmn-coverage-manifest.json`
under area `patent-expired-pharma`.

The graph tables created by
`20260427075000_open_patent_expired_pharma_bpmn_worker.ts` provide the audit
trail:

- `vertex_open_patent_expiry_backlog_run`
- `vertex_open_patent_drug_expiry`
- `vertex_open_patent_regulatory_blocker`
- `vertex_open_patent_generic_candidate`
- `vertex_open_patent_seiyaku_handoff`
- `vertex_open_patent_seiyaku_batch_draft`
- `vertex_open_patent_seiyaku_batch_validation`
- `vertex_open_patent_seiyaku_start_request`
- `vertex_open_patent_seiyaku_start_ack`
- `vertex_open_patent_seiyaku_progress`

This keeps patent review, regulatory blockers, and manufacturing batch
execution separated while still giving operators a durable end-to-end trail.
