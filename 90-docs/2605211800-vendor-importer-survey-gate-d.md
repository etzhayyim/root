---
id: doc-2605211800-vendor-importer-survey-gate-d
title: "Vendor importer survey — Phase 3 gate (d) closure scope"
status: active
doc_type: reference
topic: vendor-importer-survey-gate-d
authoritative: true
last_verified: 2026-05-21
priority: 7.0
axis: operations
weight: 0.40
priority_note: "Closes the Phase 3 gate (d) survey requirement from ADR-2605212100. Identifies the 4 vendor-side files that import etzhayyim-ported worker / ingest / primitive code and must be re-pointed before vendor open-scope deletion is safe."
authoritative_for:
  - gate (d) target file list
  - per-file recommended treatment (relocate vs re-import via @etzhayyim/*)
depends_on:
  - adr-2605212100-magatama-worker-3-axis-tranche-f-closure
  - adr-2605211757-dns-cutover-runbook-etzhayyim-ai-to-etzhayyim-com
  # adr-2605211653 (per-actor SQLite PVC) was drafted but not retained on disk; content lives inline in the DNS cutover runbook
related: []
supersedes: []
superseded_by: []
---

# Vendor importer survey — Phase 3 gate (d) closure scope

**Date**: 2026-05-21
**Scope**: etzhayyim repo (`/Users/junkawasaki/github/etzhayyim-root`), excluding `_archive/`, `20-actors/magatama/py/src/pymagatama/` (internal), and `**/tests/`.

## Headline

Of the **68 vendor-side files** that `from pymagatama` something, only **4 files** import code that is in the etzhayyim-ported scope per gate (a) — i.e. the 29 etzhayyim-classified workers + 4 ingest modules + 4 substrate primitives that gate (a) **targets** (whether or not those ports are currently committed to `etzhayyim/root` on disk). Those 4 are the entire gate (d) closure scope.

The remaining 64 importers reference pymagatama modules outside the ported scope (vendor-only agents like `outlook_*`, vendor-only primitives like `lawfirm_*`, vendor-only graph workers, defense, etc.). They are NOT gate (d) blockers and stay as-is.

> **Execution note (2026-05-21 evening)**: gate (d) executable steps were done in this session — #2 + #3 lg subtree relocates ✅, #4 hume inline copy ✅, #1 lg_organism pre-existing in etzhayyim ✅. The vendor `git rm` of the ported pymagatama originals is gated on the per-worker re-impl actually landing in `etzhayyim/root/20-actors/magatama/py/src/pymagatama/` first (gate (a) open execution).

## Gate (d) closure targets (4 files)

| # | File | Imports (ported scope) | Recommended treatment |
|---|------|------------------------|------------------------|
| 1 | `60-apps/etzhayyim-project-ki/lg/lg_organism/server.py` | `from pymagatama.{hakkou,kabi,ki,kinoko,kobo,koke,saikin}_worker_main import ...` (7 organism worker modules) | **Relocate to etzhayyim**. lg_organism IS the organism runtime — conceptually it moves with the worker code per ADR-2605211200. New home: `etzhayyim/root/60-apps/etzhayyim-project-ki/lg/lg_organism/` |
| 2 | `60-apps/etzhayyim-project-legal-entity/lg/lg_legal_entity/server.py` | `from pymagatama.primitives.legal_entity import ...` (16 tasks) | **Relocate to etzhayyim**. legal-entity is etzhayyim per ADR-2605212100 §1 ("legal-entity (implied by ge)"). Move the lg server + primitive together |
| 3 | `60-apps/etzhayyim-project-curpus2skill/lg/lg_curpus2skill/server.py` | `from pymagatama.ingest.curpus2skill import task_curpus2skill_extract_evidence` | **Relocate to etzhayyim**. curpus2skill ingest is etzhayyim per gate (a). Move the lg server with it |
| 4 | `60-apps/etzhayyim-project-hume/scripts/persist_hume_artifacts.py` | `from pymagatama.ingest.core import ...` (artifact / cursor / run helpers) | **Re-import via @etzhayyim/* (or local copy)**. hume is vendor (PII / paid SaaS); only needs the ingest.core helper shape. Either inline the ~50 LoC it actually uses or import via `@etzhayyim/magatama-ingest-core` npm package after publish |

## Non-targets (64 files, summarized)

For posterity, the 64 importers that touch pymagatama but not the ported scope:

| Cluster | Count | Why not gate (d) |
|---------|-------|------------------|
| `_working/*.py` | 13 | Scratch / migration scripts; stays etzhayyim-side |
| `20-actors/magatama/py/{scripts,alembic}/*.py` | 11 | etzhayyim-side scripts for vendor RW alembic migrations + dry-run drivers — needed for vendor ops |
| `20-actors/defense/py/src/pydefense/*` | 9 | Defense actor (etzhayyim per ADR-2605172400 §1.12 "Transparent Religious Force" but **port not yet started** — separate Wave) |
| `60-apps/etzhayyim-project-animeka/` | 8 | vendor C-group lexicon split per ADR-2605212100; production workflow stays vendor |
| `60-apps/etzhayyim-project-{shinshi,mangaka}/` | 4+4 | same C-group treatment |
| `50-infra/vultr/*` | 3 | vendor cluster scripts (RW maintenance / VKE) |
| `60-apps/etzhayyim-project-patent/` | 2 | vendor primitive + LangGraph workflow |
| `70-tools/scripts/*` | 2 | etzhayyim CLI helpers |
| Individual root scripts (`check_quality.py`, `test_ollama.py`) | 2 | etzhayyim CI / dev |
| `60-apps/etzhayyim-project-pregel` | 1 | imports `pymagatama.agents.outlook_*` + projector/pregel — mixed scope, projector etzhayyim but outlook vendor (PII); split-treatment ADR follow-up |
| `60-apps/etzhayyim-project-{media-gamers,kenkyusha,karma,dougaka,webmk}/lg/.../*.py` | 1 each | each pulls a single vendor pymagatama primitive (no ported-scope hit) |

## Treatment summary

**Phase 3 gate (d) closes when**:

1. The 3 "Relocate to etzhayyim" files (#1-3) are moved to `etzhayyim/root/60-apps/<project>/lg/<server>/` together with their actor projects. **DONE 2026-05-21**: #1 `lg_organism` pre-existing in etzhayyim, #2 `lg_legal_entity` relocated (7 files), #3 `lg_curpus2skill` relocated (7 files).
2. The 1 "Re-import" file (#4) gets either:
   - A local copy of the 4 ingest.core functions it needs (low effort, ~50 LoC)
   - An `@etzhayyim/magatama-ingest-core` npm package + import switch (higher effort, durable)

   **DONE 2026-05-21 (local copy path)**: `60-apps/etzhayyim-project-hume/scripts/_local_ingest_core.py` (193 LoC, vendor-RW write semantics retained); `persist_hume_artifacts.py` import switched to the local module.

After these 4 changes, the vendor repo will be able to `git rm` the etzhayyim-side worker / ingest / primitive files without breaking vendor builds — once those originals are actually copied to `etzhayyim/root/20-actors/magatama/py/src/pymagatama/` (gate (a) open execution; the prototype ports from this session were not retained on disk).

## Order of operations vs DNS cutover (ADR-2605211757)

Both ordering is OK in principle, but the practical sequence is:

1. **DNS cutover first** (ADR-2605211757 Wave A-D) — gets etzhayyim deploys live, gate (b) done.
2. **Then gate (d) file moves** (this survey's 4 files) — once etzhayyim deploys are validated, the vendor importers can be re-pointed without coordination risk.
3. **Then vendor `git rm`** — the 27 worker files / 4 ingest modules / 4 primitives can be removed from etzhayyim repo. The 410 Gone in the vendor routing-gateway already tells external callers the route is gone.

Doing gate (d) before gate (b) (DNS cutover) creates a window where vendor builds fail (no source for the relocated modules) while etzhayyim deploys aren't yet serving traffic — operationally fragile. ADR-2605211757 is the safer ordering.

## References

- ADR-2605212100 (Tranche F closure — defines the 4-part gate; gate (d) is this survey)
- ADR-2605211757 (DNS cutover runbook — gate (b); gate (c) deployment surface documented inline)
- (gate (c) standalone ADR-2605211653 was drafted but not retained — see DNS runbook §0 + §3.1)
- `deps.toml [[migrations]] etzhayyim-tranche-f-three-axis-split-2026-05-17` (cutover log target — extend with gate (d) per-file move log)
- Grep command (reproduce this survey):

  ```bash
  cd /Users/junkawasaki/github/etzhayyim-root
  grep -rln "from pymagatama" --include="*.py" \
    | grep -v _archive \
    | grep -v "20-actors/magatama/py/src/pymagatama/" \
    | grep -v "/tests/"
  ```
