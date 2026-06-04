# Open-data ingest — vendor (etzhayyimcojp) cutover & removal runbook

**Date**: 2026-05-31 · **Owner**: Jun Kawasaki · **Status**: migration landed; vendor removal GATED (not executed)

Tracks the staged sequence for removing the migrated open-data / public-internet
ingest from the vendor repo `etzhayyimcojp/etzhayyim-apps-etzhayyimcojp`, once it is safe. No
`git rm` has been performed — this document is the plan, and the gates below are
not yet cleared.

Related: ADR-2605312000 (NDL) · ADR-2605312100 (open-data KG) · vendor
`60-apps/etzhayyim-project-yatabase/docs/MIGRATION-rw-to-kotoba-datomic.md` · vendor
ADR-2605302130 (RW→kotoba datomic).

## 1. Migration status (what now lives on etzhayyim)

| Source | etzhayyim home | Live-verified | Notes |
|---|---|---|---|
| NDL (国立国会図書館) | `ingest/ndl.py` | ✅ 2026-05-31 | OAI-PMH metadata slice; OCR/IIIF = slice 2 |
| wikidata (SPARQL) | `ingest/kg_open.py` | ✅ 2026-05-31 | CC0 |
| crossref (REST) | `ingest/kg_open.py` | ✅ 2026-05-31 | CC0 |
| openstreetmap (Overpass) | `ingest/kg_open.py` | ✅ 2026-05-31 | ODbL |
| hf_rebel / hf_conceptnet | `ingest/hf_dataset.py` (pre-existing) | n/a | not re-ported (already covered) |
| egov_laws | — (excluded) | n/a | redundant with `ingest/houbun.py`; vendor adapter also broken vs live API (v1=XML) |
| japan_company_registry (gBiz) | — (out of scope) | n/a | not migrated per user direction 2026-05-31 (token-gated open data); vendor copy untouched |

## 2. Kotoba handoff (item 2) — READY, not executed here

Every etzhayyim ingest worker isolates ALL domain-fact writes to a single seam:
- `ingest.ndl._persist_items`
- `ingest.kg_open._persist_entities`

The kotoba-side RW→datomic refactor (vendor ADR-2605302130) is a one-function
swap per seam → `com.etzhayyim.apps.kotoba.datomic.transact` of the same entity dicts,
into an **etzhayyim-owned graph** (never the vendor commercial `kotobase-kg-v1`).
The kotoba datomic endpoint is in-cluster (`*.svc.cluster.local`) and gated on its
scaling fix, so it is **not executable / verifiable from the dev host** — this is
the kotoba team's step.

## 3. Why vendor removal is gated (NOT a file delete)

Unlike NDL's standalone `ndl_ingest.py`, the other adapters are entries in one
shared `_SOURCES` registry inside `lg_yatabase/graphs/kg_ingest.py`, consumed by
the **live commercial yatabase/kotobase product**: `server.py` scheduler
(`_run_kg_ingest` cron) + `kg_handlers.py` reads (`kg.entity/search`, served from
RisingWave `kg.vertex_entity`). A raw `git rm` now darks a running product.

### 3a. Scope correction (read the real cutover doc, 2026-05-31)

The "7-step sovereign cutover gate" referenced by
`MIGRATION-rw-to-kotoba-datomic.md` resolves to vendor
`90-docs/MIGRATION-rw-to-kotoba-sovereign.md` (iter-58). Two facts from the real
doc matter here:

1. **That cutover is scoped to `jp-ashiba` only** ("Scope: jp-ashiba only for the
   first cutover. lawfirm / shinshi / kaisya / vault later"). The open-data KG /
   yatabase is **not in its scope**. So "the sovereign cutover" is not a literal
   prerequisite for the open-data KG — it is a sibling migration.
2. Its 7 steps are heavy **because jp-ashiba holds PII** (operator key genesis,
   CACAO chains, SecureVault AEAD, `signal:v1:` tier-3 envelopes, FileVault). The
   open-data KG sources migrated here are **100% public** (wikidata CC0, crossref
   CC0, osm ODbL, NDL CC-BY) — **none of the PII-crypto steps apply**.

**So the open-data KG cutover is much lighter than the jp-ashiba sovereign one.**
Its real gates are only:

- **G1** — kotoba datomic write activated for an etzhayyim-owned public graph
  (kotoba-side; gated on the transact scaling fix, vendor ADR-2605302130). Note
  `kotoba-server` is **not yet deployed publicly** (`kotoba.etzhayyim.com/health → 404`
  per the sovereign doc's "Status today"), so this is upstream of everything.
- **G2** — vendor read path (`kg_handlers`) redirected RW → kotoba/etzhayyim.
  (`handle_entity` already does kotoba-first read with RW fallback; `catalog` /
  `search` still need kotoba aggregate/SPARQL surfaces — see datomic doc.)
- **G3** — read parity confirmed: etzhayyim/kotoba vs vendor RW `kg.vertex_entity`
  (row counts + sampled entities per source), the public-data analogue of the
  sovereign doc's Step-7 14-day diff.

**Critical path = G1.** Until kotoba datomic write is live for a public graph,
nothing downstream (parity, read-redirect, deletion) can proceed — and G1 is
in-cluster + kotoba-team work, not executable from a dev session.

## 4. Staged removal sequence (run only after G1–G3)

1. **Stop double-ingest** — disable the vendor scheduler jobs for the migrated
   sources in `lg_yatabase/server.py` (`_run_kg_ingest` registrations).
2. **Redirect reads** — point `kg_handlers.py` read path at kotoba datomic /
   etzhayyim instead of RW `kg.vertex_entity`.
3. **Verify parity (G3)** — run `70-tools/kg-parity/parity_check.py` (exit 0 =
   0 diff per source). Ready now; operator runs it once G1 is live. The pure diff
   core + SQLite reader are unit-tested; the RW/kotoba readers are guarded.
4. **Remove code** — `git rm` the migrated `_SOURCES` entries (or `kg_ingest.py` /
   `ndl_ingest.py` once fully drained); archive to
   `etzhayyimcojp:_archive/migrated-to-etzhayyim-2026-XX/`.
5. **Update vendor deps.toml** — drop the `ndl_*` keys / migrated `kg_adapters`
   entries; mark moved → etzhayyim. Leave `gBiz` (out of scope) and `egov_laws`
   (excluded) untouched in vendor.

## 5. Open decisions

- ~~gBiz~~ — **resolved: out of scope** (user direction 2026-05-31). Not migrated;
  the vendor copy stays in `kg_ingest.py` as-is. No etzhayyim counterpart.
- **NDL slice 2** (SRU image + IIIF + OCR): needs B2→IPFS blob + OCR endpoint
  re-point + datomic write — separate work item.
- **egov KG nodes**: if wanted, derive from `ingest.houbun` data (do not re-fetch
  e-Gov).

**Nothing in §3–§4 has been executed. Vendor repo is untouched and still live.**
