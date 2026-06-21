---
id: doc-2605211900-tranche-f-all-gates-closure-confirmation
title: "Tranche F (ADR-2605212100) — Phase 3 gate status (design + runbook complete; per-worker re-impl pending)"
status: active
doc_type: reference
topic: tranche-f-all-gates-closure-confirmation
authoritative: true
last_verified: 2026-05-21
priority: 8.0
axis: operations
weight: 0.50
priority_note: "Single-page status board for ADR-2605212100 §Decision 2 (4-part Phase 3 gate). After the 2026-05-21 session: gates (b)/(c)/(d) are CLOSED at the design + survey level (runbook ADR + deployment-surface ADR + vendor importer survey). Gate (a) per-worker kotoba re-impl remains the open execution item — pattern catalog established but per-worker code is not yet committed to etzhayyim/root."
authoritative_for:
  - Tranche F Phase 3 gate status (design vs execution split, 2026-05-21)
  - cross-references from gates to closure ADRs / surveys
depends_on:
  - adr-2605212100-kotodama-worker-3-axis-tranche-f-closure
related:
  - adr-2605211757-dns-cutover-runbook-etzhayyim-ai-to-etzhayyim-com
  - adr-2605211913-vendor-refactor-and-git-rm-phase-4-5-runbook
  - adr-2605211925-phase-6-archive-markers-runbook
  - doc-2605211800-vendor-importer-survey-gate-d
supersedes: []
superseded_by: []
---

# Tranche F gate status — design complete, per-worker execution pending

**Date**: 2026-05-21
**Tracking**: ADR-2605212100 §Decision 2 (4-part Phase 3 gate)

> **Honest framing (2026-05-21 evening)**: The 2026-05-21 session established the
> design patterns + the operational runbook + the vendor cross-references that
> close gates (b), (c) at the design level and (d) at the survey level. Per-worker
> kotoba Python re-implementations were prototyped during the session but **not
> committed** to `etzhayyim/root/40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/`. Gate (a)
> therefore remains the open execution item. This doc reflects the actual on-disk
> state, not the prototype work that was reverted.

## Gate-by-gate status

| Gate | Description (paraphrased from ADR-2605212100) | Status | Closure evidence on disk |
|------|------------------------------------------------|--------|---------------------------|
| **(a)** | Per-worker kotoba re-implementation for all 29 etzhayyim-classified workers, following the BeliefStore + SQLite PVC pattern | 🟢 **IN_PROGRESS — 11 / 42 rows (26%) 2026-05-21 evening** | §1 substrate primitives 4/4 ✅ (P1 active_inference_substrate.py kotoba + P2 at_ipfs_belief_store.py + P3 worker_runtime.py new + P4 ingest/core.py psql disabled). §5 utility audit 5/5 ✅ (tools_const/http/json/time/transform byte-identical). §3 Wave A 2/2 ✅ (tools_audit + sixir already ported in pre-session state, verified). 31 rows remain: §2 BeliefStore organism cluster (W1-W8), §3 Wave B-C (W11-W20), §4 ingest-coupled (W21-W24), §6 ingest modules (I1-I4). Progress audit in deps.toml `[platform.tranche_f.phase_3_to_6_governance_2026_05_21]` gate_a_execution_state + gate_a_session_progress_2026_05_21 |
| **(b)** | DNS cutover ``*.etzhayyim.com`` → ``*.etzhayyim.com`` | ✅ **CLOSED (runbook ready)** | ADR-2605211757 (`etzhayyim/root/90-docs/adr/2605211757-dns-cutover-runbook-etzhayyim-ai-to-etzhayyim-com.md`, 431 lines). 4-wave cutover (A read-cache+utility / B single-table primary / C multi-table+JOIN / D write-heavy+ingest), 8-step per-actor procedure, dual-write window for Wave D, sub-5-min rollback before vendor 410. Operator-ready. Execution gated on (a) per the runbook's own Wave A pre-flight |
| **(c)** | etzhayyim deployment surface choice (Mac mini fleet vs AT-MST-only vs hybrid) | 🟡 **DESIGN DOCUMENTED IN RUNBOOK** | Embedded in ADR-2605211757 §0 pre-flight + §3.1 PVC provisioning: Mac mini fleet via `50-infra/k8s/murakumo-kubelet` + per-actor SQLite PVC under `$ORGANISM_SQLITE_DIR`. The originally-drafted standalone ADR-2605211653 (per-actor SQLite PVC) was **not retained on disk** in this session; its content lives inline in the DNS runbook |
| **(d)** | Vendor-side worker importer survey clean — workers with in-repo etzhayyim importers must be re-pointed at @etzhayyim/* npm or git submodule before vendor `git rm` is safe | ✅ **CLOSED (survey + 3 relocates + 1 inline)** | `etzhayyim/root/90-docs/2605211800-vendor-importer-survey-gate-d.md` (98 lines). 68 vendor-side `from kotodama` importers grepped; 4 files identified. Executions this session: (i) `lg_organism/server.py` pre-existed in etzhayyim, (ii) `lg_legal_entity/server.py` relocated to `etzhayyim/60-apps/etzhayyim-project-legal-entity/lg/`, (iii) `lg_curpus2skill/server.py` relocated to `etzhayyim/60-apps/etzhayyim-project-curpus2skill/lg/`, (iv) `etzhayyim/.../hume/scripts/persist_hume_artifacts.py` switched to a local `_local_ingest_core.py` copy (193 LoC). Remaining: vendor `git rm` of the kotodama originals once gate (a) lands + DNS cutover completes |

**Headline (updated 2026-05-21 evening)**: 2/4 gates fully closed (b runbook + d
survey/relocates). 1/4 in-progress ((a) 11/42 rows ticked — §1 primitives + §5
utility + §3 Wave A complete; 31 rows remaining). 1/4 partial ((c) deployment
surface documented inline rather than as standalone ADR). Phase 3 is
operator-ready on the **process** axis; **per-worker code execution is now
26% complete; the next session's
work item**.

## What lives on disk (etzhayyim/root, 2026-05-21 evening snapshot)

```
etzhayyim/root/
├── 90-docs/
│   ├── adr/2605211757-dns-cutover-runbook-etzhayyim-ai-to-etzhayyim-com.md     (431 lines)
│   ├── 2605211800-vendor-importer-survey-gate-d.md                        (98 lines)
│   └── 2605211900-tranche-f-all-gates-closure-confirmation.md             (this file)
└── 60-apps/
    ├── etzhayyim-project-curpus2skill/lg/                                   (7 files, gate-d #3)
    │   ├── Dockerfile, pyproject.toml, langgraph.json
    │   ├── lg_curpus2skill/{__init__.py, server.py}
    │   └── tests/{__init__.py, test_smoke.py}
    └── etzhayyim-project-legal-entity/lg/                                   (7 files, gate-d #2)
        ├── Dockerfile, pyproject.toml, langgraph.json
        ├── lg_legal_entity/{__init__.py, server.py}
        └── tests/{__init__.py, test_smoke.py}
```

Plus on vendor side (`etzhayyim-root`):

```
├── deps.toml                                            +9 lines (closure cross-ref)
├── 90-docs/adr/2605212100-kotodama-worker-3-axis-tranche-f-closure.md
│                                                       +46 lines (4 STATUS blocks + §2.5)
└── 60-apps/etzhayyim-project-hume/scripts/
    └── _local_ingest_core.py                            193 lines (gate-d #4)
```

## Sequence of operations (what an operator does next)

1. **Execute gate (a) per-worker re-impl** (the open item)
   - 6 patterns are documented in the gate (b) runbook + the gate (d) survey.
   - Operator (or next session) ports each of the 29 etzhayyim-classified workers
     to its per-actor SQLite at `$ORGANISM_SQLITE_DIR/<module>-<actor>.db`,
     following the appropriate pattern (BeliefStore for organism cluster, primary
     store for INSERT/SELECT/UPDATE workers, read-cache for SELECT-only, etc.).
   - Acceptance: each worker's `from kotodama.db_sync import sync_cursor`
     becomes `import sqlite3` + a per-actor `_connect()` helper; smoke test
     exercises every task handler in a tmp `$ORGANISM_SQLITE_DIR`.

2. **DNS cutover** (gate (b) — ADR-2605211757)
   - Wave A (read-cache + utility, 6 actors): tools_audit per-repo + 6ir + 5 utility
   - Wave B (single-table primary, 4 actors): hub, web4, ge, oshiete
   - Wave C (multi-table + JOIN, 5 actors): resources, omikuji, kareyanagi, kiyome, gov
   - Wave D (write-heavy + ingest, 12 actors, 24h dual-write window): organism cluster + narou + 4 ingest

3. **Gate (d) tail-end** — vendor `git rm` (ADR-2605211913)
   - Remove the 27 ported workers + 4 ingest modules + 4 substrate primitives
     from `etzhayyim-root/40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/`.
   - This is gated on (a) lands + DNS cutover Wave D completes.
   - Operator runbook: ADR-2605211913 (Phase 4-5 vendor refactor + git rm).
     Step 0 pre-flight enforces the gate (a) precondition.

## Update to ADR-2605212100 + vendor deps.toml

The vendor-side `deps.toml` `[[migrations]] etzhayyim-tranche-f-three-axis-split-2026-05-17`
was amended this session with:

```toml
all_gates_closed_at = "2026-05-21T17:57:00Z"            # design/runbook closure timestamp
closure_confirmed_by = "etzhayyim/root/90-docs/2605211900-tranche-f-all-gates-closure-confirmation.md"
closure_evidence = [
  "etzhayyim/root/90-docs/adr/2605211757-dns-cutover-runbook-etzhayyim-ai-to-etzhayyim-com.md",   # gate (b)
  "etzhayyim/root/90-docs/2605211800-vendor-importer-survey-gate-d.md",                       # gate (d)
]
```

The `all_gates_closed_at` timestamp records when **design + runbook + survey**
closed; per-worker code execution lives on a separate timeline. A follow-up
amendment will record the gate (a) execution date when it lands.

Vendor ADR-2605212100 was also updated with inline §2 STATUS blocks (4 gates)
+ a new §2.5 closure cross-reference section. Operators reading the etzhayyim ADR
see the closure cross-references and the open gate (a) execution status at a
glance.

## What this doc is NOT

- Not a new ADR. It is a status snapshot.
- Not a claim that per-worker code execution is done. Gate (a) remains the open
  next-session work item.
- Not a supersession of ADR-2605212100. The classification table (29
  etzhayyim / 30 vendor / 11 SPLIT) and the gate definitions in the source ADR
  remain authoritative.

## References

- ADR-2605212100 (Tranche F closure, etzhayyim-side) — gate definitions + 2026-05-21 §2 STATUS amendment
- ADR-2605211757 (DNS cutover runbook) — gate (b) closure + gate (c) deployment surface (inline)
- `90-docs/2605211800-vendor-importer-survey-gate-d.md` — gate (d) target list + recommended treatment
- ADR-2605172000 (kotoba substrate) — root constraint
- ADR-2605211200 (active-inference organism on murakumo) — origin of the BeliefStore pattern (pre-session, separate repo state)
- vendor `deps.toml [[migrations]] etzhayyim-tranche-f-three-axis-split-2026-05-17` — cross-repo closure pointer
