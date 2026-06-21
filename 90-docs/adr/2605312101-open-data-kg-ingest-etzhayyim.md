---
id: adr-2605312101-open-data-kg-ingest-etzhayyim
renumbered_from: "2605312100"
title: "ADR-2605312101: Open-data KG ingest (public-internet sources) on the etzhayyim kotoba substrate"
status: active
doc_type: adr
topic: open-data-kg-ingest-etzhayyim
authoritative: true
last_verified: 2026-05-31
priority: 5.0
axis: architecture
weight: 0.50
priority_note: ""
authoritative_for:
  - open-data KG ingest worker (etzhayyim) — wikidata + crossref
  - vendor kg_ingest deletion = post-cutover step (NOT done)
depends_on:
  - adr-2605312000-ndl-oai-ingest-etzhayyim
related:
  - adr-2605172000-etzhayyim-kotoba-substrate
  - adr-2605172400-etzhayyim-vendor-three-axis-split-rule
supersedes: []
superseded_by: []
---

# ADR-2605312101: Open-data KG ingest (public-internet sources) on the etzhayyim kotoba substrate

**Status**: active
**Date**: 2026-05-31
**Deciders**: Jun Kawasaki

# Context

Continues ADR-2605312000 (NDL). The vendor yatabase KG ingest
(`etzhayyimcojp:…/lg_yatabase/graphs/kg_ingest.py` `_SOURCES`) harvests 7 sources from
the public internet: wikidata, crossref, japan_company_registry (gBiz),
openstreetmap, egov_laws, hf_rebel, hf_conceptnet. User direction (2026-05-31):
migrate the open-data / public / net-ingest family to kotoba; vendor removal is
authorised "once migrated". Same kotoba constraint (ADR-2605172000) → re-build
on the open substrate, with the RW→kotoba-datomic refactor performed kotoba-side.

# Decision

Add an etzhayyim open-data KG ingest worker — `ingest/kg_open.py` +
`kg_open_worker_main.py` + `test_kg_open_worker.py` — registry-driven, same
canonical flat entity shape the kotoba datomic writer consumes.

**This slice ships the live-grounded clean-public sources:**
- **wikidata** (SPARQL, CC0), **crossref** (REST, CC0), **openstreetmap**
  (Overpass, ODbL). All three fetch→extract→persist paths verified end-to-end
  against the live endpoints 2026-05-31 (wikidata 5/5, crossref 3/3, osm 5/5 —
  real ward names 目黒区/東京都/…; real fixtures captured into the test so it is
  not circular; PII screen drops records carrying
  email/phone/SSN/マイナンバー/postal).

**Deliberately excluded:**
- `hf_rebel` / `hf_conceptnet` — already covered by the existing
  `ingest.hf_dataset` (don't duplicate).
- `egov_laws` (e-Gov) — **excluded as redundant + broken**, not deferred. (1) The
  e-Gov laws source is already ingested by `ingest.houbun` (EGOV `api/2` → full
  statute + article corpus); a KG-legislation node should derive from houbun, not
  re-fetch e-Gov. (2) The vendor adapter is broken vs the live API: it GETs
  `/api/1/lawdata` and `json.loads()` it, but the live e-Gov v1 API returns
  **XML** (verified 2026-05-31); the working JSON surface is v2 (`/api/2/laws`,
  which houbun uses).
- `japan_company_registry` (gBiz) — **out of scope** per user direction
  (2026-05-31); not migrated. (It is token-gated open data — gBizINFO requires a
  registered API token, 500 without / 401 with an invalid one, probed 2026-05-31
  — and the user chose to exclude it.) The earlier ready-but-gated port was
  removed from `kg_open.py`.

Persistence: spine (run/cursor) via best-effort `ingest.core` (`_spine`);
canonical entities in worker-local kotoba `ingest_kg_open.db`. **Kotoba handoff
= single `_persist_entities` seam** → swap for
`com.etzhayyim.apps.kotoba.datomic.transact` into an etzhayyim-owned graph (never
vendor `kotobase-kg-v1`); the kotoba datomic client is not ported here.

**Vendor removal is NOT done — it is the post-cutover step.** Unlike NDL's
standalone `ndl_ingest.py`, these adapters are entries in one `_SOURCES` registry
inside `kg_ingest.py`, consumed by the live commercial yatabase/kotobase product
(`server.py` scheduler + `kg_handlers` reads). Removing them darks a running
product, and `MIGRATION-rw-to-kotoba-datomic.md` is explicit: "NOT a cutover …
RW is not retired until the 7-step sovereign cutover gate passes." So `git rm` in
etzhayyimcojp waits on that cutover (disable scheduler / redirect reads first), not
this port.

# Consequences

- wikidata + crossref + openstreetmap open-data harvest runs kotoba on etzhayyim
  today, live-verified; the datomic write is the isolated kotoba-side follow-up.
- **The kotoba datomic write is NOT verifiable here** (in-cluster + gated on its
  scaling fix, vendor ADR-2605302130) — gate-ready, not running.
- Worker registration (`kg_open_worker_main.py`) is syntax-compiled but its Zeebe
  imports are not import-resolved here (first in-cluster start is the check).
- Vendor kg_ingest is **untouched and still live**; deletion is deferred to the
  documented cutover, not done in this turn.

# Alternatives Considered

- **Delete the migrated adapters from vendor now** → rejected: not a coherent
  per-adapter file delete (shared `_SOURCES` registry), breaks the live product,
  and gated by `MIGRATION-rw-to-kotoba-datomic.md`.
- **Batch-build all remaining adapters blind** → rejected (the NDL lesson:
  vendor assumptions can diverge from real feeds — confirmed again here: the
  vendor egov_laws adapter is broken against the live e-Gov API). One adapter
  grounded live at a time; egov dropped as redundant-with-houbun, gBiz staged.
- **Per-source files (wikidata.py, crossref.py)** → folded into one registry
  worker since they share extract/normalize/persist + the kotoba seam (mirrors
  the vendor `_SOURCES` design being migrated).

# References

- `90-docs/2605312200-open-data-ingest-vendor-cutover-runbook.md` (staged vendor removal + gates G1–G3 + kotoba handoff status)
- `90-docs/adr/2605312000-ndl-oai-ingest-etzhayyim.md`
- vendor `…/lg_yatabase/graphs/kg_ingest.py` `_SOURCES` (source-fetch origin)
- vendor `…/docs/MIGRATION-rw-to-kotoba-datomic.md` (deletion gate)
- vendor `90-docs/adr/2605302130-yatabase-rw-to-kotoba-datomic-…md` (kotoba-side refactor target)
