---
id: adr-2605312000-ndl-oai-ingest-etzhayyim
title: "ADR-2605312000: NDL (国立国会図書館) OAI-PMH metadata ingest on the etzhayyim kotoba substrate"
status: active
doc_type: adr
topic: ndl-oai-ingest-etzhayyim
authoritative: true
last_verified: 2026-05-31
priority: 5.0
axis: architecture
weight: 0.50
priority_note: ""
authoritative_for:
  - ndl open-data ingest worker (etzhayyim)
  - ndl persistence seam → kotoba datomic refactor handoff
depends_on: []
related:
  - adr-2605172000-etzhayyim-kotoba-substrate
  - adr-2605172400-etzhayyim-vendor-three-axis-split-rule
supersedes: []
superseded_by: []
---

# ADR-2605312000: NDL (国立国会図書館) OAI-PMH metadata ingest on the etzhayyim kotoba substrate

**Status**: active
**Date**: 2026-05-31
**Deciders**: Jun Kawasaki

# Context

The National Diet Library (国立国会図書館 / NDL) ingest existed only in the
**vendor** repo (`etzhayyimcojp:60-apps/etzhayyim-project-yatabase/lg/lg_yatabase/ndl_ingest.py`)
as a `kg_adapter` inside the commercial yatabase/kotobase Universal Knowledge
Graph. It was Kotoba/Datomic-backed (`vertex_ndl_*`, ~620k rows). The vendor RW
adapter **stays in place** — this ADR does not move or delete it.

NDL bibliographic metadata is public-domain library data (3-axis test: Custody
clean — public; no Settlement, no Liability), so an open-data harvest of it is a
legitimate etzhayyim open-data source alongside arxiv / common-crawl / houbun.
The substrate constraint is that etzhayyim is **kotoba** (ADR-2605172000):
AT MST + IPFS only, no Kotoba/Datomic. So this is a **re-build on the open
substrate**, not a file move of the RW adapter.

User direction (2026-05-31): "移行を進めて … refactor は kotoba 側が行います" —
land the migration now; the RW→kotoba-datomic persistence refactor is performed
**kotoba-side**, not as part of this migration.

# Decision

Add NDL as an etzhayyim open-data ingest worker, **slice 1 = OAI-PMH metadata
only**, following the houbun / site_common_crawl pattern.

- `40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/ingest/ndl.py` — fetch + parse, 7 Zeebe
  tasks (createRun / oai.plan / acquireCursor / oai.fetchWindow /
  verifyVisibility / advanceCursor / completeRun). The parse logic was
  **re-grounded against the real feed** (the vendor adapter's set/PID assumptions
  did not hold on `ndlsearch.ndl.go.jp/api/oaipmh`):
  - Online filter = setSpec `ndl-dl-open` (digitised + freely available),
    env-overridable via `NDL_OAI_SETS`. The vendor's `ndl-dl-online` / `B00000` /
    `jpro-*` labels do **not** appear on this feed — filtering on them would drop
    every record.
  - Stable id (`ndl_id`) = the OAI header identifier (`R100000039-I{n}`), a
    catalogue key. It is **NOT** a digital PID: a `digital_pid` + IIIF
    `manifest_url` are populated **only** when a genuine `dl.ndl.go.jp/pid/{n}`
    URL is present (absent on the oai_dc feed — those records are bib-level
    metadata). Synthesising a manifest from the bib id is explicitly avoided.
  - Domain table = `vertex_ndl_bib_item` (bib-level metadata; collection
    `com.etzhayyim.apps.ndl.bibItem`).
- `40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/ndl_worker_main.py` — dedicated Zeebe
  worker registration.
- `test_ndl_worker.py` — offline test whose fixtures are **real NDL records**
  captured 2026-05-31 (so the test is not circular); green with **no network and
  no RW** (resumptionToken paging + `ndl-dl-open` filtering + bib-id-is-not-a-PID
  + resume idempotency).

**Persistence model:**
- Resumable OAI checkpoint + domain facts (`vertex_ndl_digital_item`) live in the
  worker's own kotoba `ingest_ndl.db` SQLite. Resumption depends only on this.
- The cross-domain orchestration spine (`ingest.core` run/cursor/artifact) is
  called **best-effort** (`_spine(...)`): it is still RW-coupled via
  `db_sync.sync_cursor` (the spine's own kotoba migration is incomplete), so a
  missing `KOTOBA_URL` degrades to a logged warning and never aborts an ingest.

**The kotoba handoff (single seam):** domain-fact writes go through exactly one
function — `ingest.ndl._persist_items`. The RW→kotoba-datomic refactor
(ADR-2605302130) swaps that function body for a kotoba
`com.etzhayyim.apps.kotoba.datomic.transact` of the same item dicts, into an
**etzhayyim-owned graph** (never the vendor `kotobase-kg-v1`). No other code in
the module touches the domain write path, so the swap is a single reviewable
edit performed kotoba-side. The kotoba datomic client is **intentionally not
ported here** per the user's split of responsibilities.

# Consequences

- NDL open-data harvest runs on the kotoba substrate today; the datomic write is
  a clean, isolated follow-up owned by kotoba.
- **Fetch + parse + paging + resume IS live-verified** against the live
  `ndlsearch.ndl.go.jp` OAI-PMH endpoint:
  - single window (2024-01-02): 200/200 real records matched the `ndl-dl-open`
    filter; `ndl_id` extracted; `digital_pid`/`manifest_url` correctly empty.
  - multi-page + resume (2024-01 window, `maxPages=2` ×2 calls): run 1 fetched 2
    pages / 400 records and stopped mid-window with `status=running` + a persisted
    `resumptionToken`; run 2 **resumed from the stored checkpoint** → 4 pages /
    800 cumulative records. Idempotent upsert confirmed (800 rows = 800 distinct
    `ndl_id`), and the bib-id-is-not-a-PID fix held at scale — **0 bogus manifests
    across 800 real records**.
- **The kotoba datomic write is NOT verifiable here**: the endpoint is in-cluster
  (`*.svc.cluster.local`, unreachable from the dev host) and datomic transact is
  gated on its scaling fix (vendor ADR-2605302130). That seam ships gate-ready,
  not running.
- The Zeebe worker registration (`ndl_worker_main.py`) is syntax-compiled but its
  imports (`langserver_compat`, `zeebe_worker_main.task_rw_health_probe`) are
  **not import-resolved** here — copied verbatim from the working
  `houbun_worker_main.py`; first in-cluster start is the import check.
- Vendor RW NDL adapter is untouched (no "moved" claim in vendor deps.toml).

# Alternatives Considered

- **Move the RW adapter as-is** → rejected: incoherent on an kotoba target
  (no RW to receive it) and the adapter is vendor-bound commercial-product
  internals (yatabase Settlement axis → vendor).
- **Port the kotoba datomic client now** → rejected: user assigned the datomic
  refactor to the kotoba side. We leave a documented seam instead.
- **Port the SRU image + IIIF + OCR path** → deferred to slice 2: it needs three
  further substrate swaps (B2 → IPFS blob, vendor OCR endpoint →
  `llm.etzhayyim.com`, datomic write) and warrants its own design.

# References

- vendor `60-apps/etzhayyim-project-yatabase/lg/lg_yatabase/ndl_ingest.py` (source-fetch origin)
- `90-docs/adr/2605172000-etzhayyim-kotoba-substrate.md`
- `90-docs/adr/2605172400-etzhayyim-vendor-three-axis-split-rule.md`
- vendor `90-docs/adr/2605302130-yatabase-rw-to-kotoba-datomic-...md` (kotoba-side refactor target)
