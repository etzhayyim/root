# jinushi 地主 — world land-ownership ACQUISITION (取得) mirror

The data-acquisition (取得) feeder of the etzhayyim **land-sovereignty stack** (Tree-of-Life
land doctrine, ADR-2605192100 §1.11 + ADR-2605192245). The on-chain `LandRegistry.sol` records
only **DONATED, waqf-inalienable** land and starts at **0 parcels**; jinushi is the upstream
**observational mirror** that measures *how much of the world's land we have data on, who holds
it, and where the 取-concentration is* — the map that tells the registry what to seek and routes
land back toward the commons.

It is the land-scale sibling of the KG-mirror lineage (inochi 命 / tsumugi 紡ぎ / kabuto 兜 /
kanae 鼎): ingest PUBLIC records → normalize onto the kotoba Datom log → edge-primary
取-concentration routed to **RETURN-to-commons**.

This is the **clj-native** realization of the legacy `crawler → land-owners → maps` design
(`80-data/reports/260225-land-owners-crawler-maps-design.md`), re-homed off RDBMS/KV onto the
canonical kotoba Datom log (no RisingWave/Kysely; ADR-2605262130 + 2605312345).

## What it is (R0)

Reads a kotoba-EDN land record set (`:owners` + `:parcels`) and computes, aggregate-first:

- **acquisition coverage** — acquired land area ÷ world land area, per country, with a
  self-pruning **ingest worklist** of known countries still at zero parcels.
- **land 取-concentration** — HHI over owners by area + top-holder share.
- **RETURN-to-commons candidates** — private non-aggregate holders above a documented share
  threshold, routed to Council as an **advisory** (never a write-back, never a seizure list).

`「全世界の不動産の取得 coverage は?」` is now a runnable metric, not a guess:

```
$ bb --classpath 20-actors -e "(require 'jinushi.methods.coverage 'jinushi.methods.analyze)
    (println (jinushi.methods.coverage/render
      (jinushi.methods.analyze/analyze
        (jinushi.methods.analyze/load-file* \"20-actors/jinushi/data/seed-parcels.kotoba.edn\"))))"
# → 6 countries touched, 83,207 km² acquired = 0.056% of world land; HHI 2635; worklist RU/CN/CA/IN
```

(The 0.056% is the **honest** acquisition coverage on the synthetic seed — sparse data reads as
a tiny fraction, as it should. The real number rises only with operator/Council-gated live
registry ingest.)

## Gates (constitutional)

- **G1** a RETURN/commons **MAP**, NEVER a per-person holdings dossier or occupancy target list.
  Owners are PUBLIC entities or AGGREGATE buckets; natural-person land folds to one
  `:owner/aggregate` owner with no person name; centroids are coarse region centroids, never a
  dwelling fix; the ingest worklist names **jurisdictions**, never parcels/persons;
  return-candidates are advisory + aggregate, never a natural person. Test-enforced (no
  `:person`/`:worker` token may appear in the Datom log or report).
- **G2** non-adjudicating. Owner/area are DISCLOSED facts; concentration + coverage are read-time
  aggregates flagged `:bond/is-transient`, never verdicts/scores.
- **G3** acquisition only — jinushi **cannot move land**. It asserts no transfer/mint/donation;
  only the on-chain `LandRegistry` changes a parcel's hands, and only via member donation
  (no-server-key). Routed candidates go to a human/Council, never written back.
- **G4** sourcing honesty — R0 seed is `:representative` synthetic; live registry/OSM/Wikidata
  pull (`70-tools/e7m-dataset`) is operator/Council-gated. National fractions are reported only
  where land area is documented, never guessed.

## Methods (pure, portable .cljc — file I/O only at the `#?(:clj)` edge)

- `methods/analyze.cljc`     — ingest + normalize (owner-name suffix/case fold, sha256 record-id
  upsert/dedup) → coverage + concentration + return-candidates.
- `methods/datom_emit.cljc`  — canonical EAVT emit: ground `:owner/*` + `:parcel/*` `:add`
  datoms + derived `:jinushi/*` transient aggregates.
- `methods/coverage.cljc`    — world acquisition-coverage report + self-pruning ingest worklist.
- `methods/ingest.cljc`      — **REAL acquisition** from a COMMITTED public-data snapshot in the
  repo DATA LAYER (`80-data/jinushi-land/*.kotoba.edn`) → `{:owners :parcels}`, offline.
  `merge-datasets` combines snapshot + synthetic seed into one acquisition view.
- `methods/fetch_wdqs.sh`    — polite, EXPLICIT, operator-only WDQS refresh of the snapshot.

## Real acquisition + WDQS load discipline (operator directive 2026-06-16)

REAL data ingests PUBLIC protected land from Wikidata — G1-safe (public owners, no persons, no
coordinates; only country + area + a per-source per-country public-owner bucket). **Data lands in
the repo DATA LAYER via the datalad substrate** (ADR-2605241500; the genome convention) and the
actor PROCESSES it later:

```
80-data/jinushi-land/
  wikidata-national-parks.kotoba.edn    # Q46169  — PRIMARY world-coverage source (counts=true)
  wikidata-nature-reserves.kotoba.edn   # Q179049 — observed-only (counts=false; overlap)
  ingest-provenance.json                # sources / WDQS / date / sha256 / unit-map / pin path
  .gitignore                            # *.raw.json (transient fetch; annex/IPFS cold tier)
```

| source | class | records | countries | area | counts toward world coverage |
|---|---|--:|--:|--:|---|
| national parks | Q46169 | 294 | 26 | 4.97M km² | **yes** (primary, non-overlapping) |
| nature reserves | Q179049 | 499 | 3 | 0.23M km² | **no** (overlaps NP countries NO/IE/CA) |

**World acquisition coverage = 26 countries · 4.97M km² = 3.34% of world land** (up from the
0.056% synthetic floor). Multi-source is **double-count-honest** (G2/G4): only non-overlapping
counting sources sum into world coverage; overlapping protected-area classes are observed
separately until a geometry de-dup leg exists — summing them would inflate coverage. Units
resolved at snapshot time (km²/hectare/decare/dunam/acre/m²), 0 dropped. Cold tier (git-annex
local-store → IPFS CID map → PDS `datasetPin`) is the operator step via
`e7m-dataset add 80-data/jinushi-land` against superdataset `90-docs/baien/datasets` — not auto-run.

**「wdqs に負担をかけない」 is enforced by design:**

- The committed **snapshot is the loop's source of truth**. Each loop iteration re-ingests the
  snapshot with **ZERO network I/O** (`ingest.cljc`). A 30-min loop hitting WDQS would be abuse;
  it never does.
- A live refresh is an **explicit, rare, operator-only** step (`fetch_wdqs.sh`): ONE small
  LIMITed query, descriptive User-Agent **with a contact address**, `--max-time`, a courtesy
  sleep, no retry loop, and it **refuses `LIMIT > 800`**. If WDQS hits its 60 s server cap,
  LOWER the limit — never hammer. The 15-min result cache is honoured by reusing the snapshot.
- Area is **honest**: rows whose unit could not be resolved are dropped at snapshot time and the
  dropped count is disclosed in the snapshot (`:dropped-unknown-unit`), never guessed (G4).

## Run

```bash
CP=20-actors
for ns in test-analyze test-datom-emit test-coverage test-ingest; do
  bb --classpath $CP -e "(require 'clojure.set 'jinushi.methods.$ns) (clojure.test/run-tests 'jinushi.methods.$ns)"
done
# 21 tests / 71 assertions green

bb --classpath 20-actors -m jinushi.methods.coverage     # synthetic seed → out/coverage.md
bb --classpath 20-actors -m jinushi.methods.datom-emit   # → out/jinushi-datoms.kotoba.edn
bb --classpath 20-actors -m jinushi.methods.ingest       # REAL snapshot → live coverage (offline)

# operator-only, rare, polite — refresh the snapshot from WDQS (NOT run by the loop):
methods/fetch_wdqs.sh 400
```

## Status / roadmap

- **R0 (landed)** — analyze + datom-emit + coverage + ontology + synthetic seed + 16 tests. ✅
- **R2 (landed)** — REAL multi-source public-land ingest (`ingest.cljc` + `fetch_wdqs.sh`):
  committed Wikidata snapshots — national parks (294 / 26 cc / 4.97M km², **counts**) + nature
  reserves (499 / 3 cc, observed-only, overlap-excluded). World coverage **3.34%** (up from the
  0.056% synthetic floor). Double-count-honest (G2/G4), full unit map (km²/ha/decare/dunam/acre/
  m²), data in 80-data via datalad substrate, WDQS-load-safe (snapshot SoT; loop never queries
  WDQS). +7 tests. ✅
- **R1** — content-address the acquisition snapshot to a kotoba IPFS CIDv1 + append-only
  commit-DAG (`kotodama/src/kotoba/datom.cljc` reuse, `verify_chain` resume-safe).
- **R2+** — broaden real sources (protected areas / public-land registries / OSM landuse) one
  small polite batch at a time; per-country `country-land-area-km2` table expansion so national
  fractions resolve for the 26 ingested countries.
- **R3** — bridge confirmed-donation parcels to the on-chain `LandRegistry` lane (still a member
  donation, no-server-key) + maps.etzhayyim.com `:feature/*` layer.
- **ADR** — to author: `26xxxxxxxx-jinushi-land-ownership-acquisition-mirror.md` (mirror-lineage
  pattern; land-sovereignty §1.11 grounding).
