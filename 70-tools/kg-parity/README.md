# kg-parity — open-data KG cutover parity check (G3)

Confirms the etzhayyim open-data KG store is at parity with the vendor RisingWave
`kg.vertex_entity` **per source_id**, before any vendor `git rm`. This is gate
**G3** in `90-docs/2605312200-open-data-ingest-vendor-cutover-runbook.md` — the
public-data analogue of the sovereign migration's Step-7 "RW diff = 0".

## Status

- Pure `diff_snapshots` core + the etzhayyim SQLite reader are unit-tested
  (`python test_kg_parity.py` → green, no network).
- The **RW side and kotoba side are not runnable from a dev session**: the RW
  side needs `KOTOBA_URL` reachability; the kotoba side needs a live kotoba-server
  (gated on **G1**, kotoba datomic activation). Both are guarded and fail loudly.
- **Operator runs this once G1 lands**, where RW (and optionally kotoba) is
  reachable.

## Run (operator)

```bash
# etzhayyim side = local SQLite ingest store (ingest_kg_open.db), RW side = KOTOBA_URL
KOTOBA_URL='http://127.0.0.1:8077' \ # EXAMPLE
ORGANISM_SQLITE_DIR=/var/lib/etzhayyim/organism \
python parity_check.py \
  --sources wikidata,crossref,openstreetmap \
  --out report.json

# once G1 is live, read the etzhayyim side from kotoba datomic instead:
KOTOBA_URL='…' KOTOBA_XRPC_URL='http://kotoba.kotoba.svc.cluster.local:8080' \
python parity_check.py --etz-backend kotoba --sources wikidata,crossref,openstreetmap
```

Exit code `0` = full parity (0 diff on every source) → the cutover gate is green
and removal step 3 of the runbook may proceed. Exit `1` = drift; inspect
`missing_in_etz` / `missing_in_rw` per source in the report.

## Why id-set diff is meaningful

Both sides compute the entity `id` with the **same** algorithm (qid for wikidata,
`sha256(doi)[:16]` for crossref, `sha256(osm_id)[:16]` for osm,
`sha256(corp_num)[:16]` for gBiz) — the etzhayyim extractors are faithful ports of
the vendor ones — so a set difference is a genuine missing/extra entity, not a
keying artifact.

Scope: the `kg.vertex_entity`-shaped sources (wikidata / crossref / openstreetmap
/ gBiz). NDL parity is separate (its own RW tables `vertex_ndl_*` ↔ etzhayyim
`vertex_ndl_bib_item`, different schema/granularity).
