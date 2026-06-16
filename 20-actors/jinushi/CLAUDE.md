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

## Run

```bash
CP=20-actors
for ns in test-analyze test-datom-emit test-coverage; do
  bb --classpath $CP -e "(require 'clojure.set 'jinushi.methods.$ns) (clojure.test/run-tests 'jinushi.methods.$ns)"
done
# 16 tests / 55 assertions green

bb --classpath 20-actors -m jinushi.methods.coverage     # → out/coverage.md
bb --classpath 20-actors -m jinushi.methods.datom-emit   # → out/jinushi-datoms.kotoba.edn
```

## Status / roadmap

- **R0 (landed)** — analyze + datom-emit + coverage + ontology + synthetic seed + 16 tests. ✅
- **R1** — content-address the acquisition snapshot to a kotoba IPFS CIDv1 + append-only
  commit-DAG (`kotodama/src/kotoba/datom.cljc` reuse, `verify_chain` resume-safe).
- **R2** — live registry/OSM/Wikidata ingest via `70-tools/e7m-dataset` (operator/Council G4),
  raising real-world coverage off the synthetic floor; per-country normalization rules.
- **R3** — bridge confirmed-donation parcels to the on-chain `LandRegistry` lane (still a member
  donation, no-server-key) + maps.etzhayyim.com `:feature/*` layer.
- **ADR** — to author: `26xxxxxxxx-jinushi-land-ownership-acquisition-mirror.md` (mirror-lineage
  pattern; land-sovereignty §1.11 grounding).
