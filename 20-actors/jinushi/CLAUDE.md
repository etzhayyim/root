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
- `methods/ingest.cljc`      — **REAL multi-source acquisition** from COMMITTED snapshots →
  `{:owners :parcels}`, offline; double-count-honest (counting sources only) + **`sanitize`**
  data-quality gate (drops parcels larger than their country, using the real area denominator).
- `methods/normalize_wdqs.cljc` — PROCESS raw WDQS (`*.raw.json`) → committed snapshots
  (canonical unit map km²/ha/decare/dunam/acre/m²/sq-mile/rai/feddan + salvage parse, in code).
- `methods/cid.cljc`         — CIDv1 (raw/sha2-256) content-addressing of snapshots (R1).
- `methods/emit_real.cljc`   — emit the REAL acquisition → canonical kotoba Datom log + CID.
- `methods/verify.cljc`      — integrity: committed snapshots ↔ `ingest-provenance.json` (CID+sha256).
- `methods/buildings.cljc`   — building-level ownership KG (owner legal entity + floors) + company
  linkage (owner LEI/QID → kabuto/uchiwake/kanjō/keizu corp KGs); building-取-concentration.
- `methods/company_link.cljc` — AUTHORITATIVE company linkage: building-owner LEI → GLEIF legal
  entity (legal name/jurisdiction/status) → kabuto/uchiwake/kanjō; QID → keizu/tsumugi.
- `methods/jurisdiction.cljc` — per-jurisdiction PUBLIC-RECORD gate: which cadastres are
  public/bulk/owner-names-visible → whether natural-person ownership may be BULK-ingested
  (honest degrade to :unknown; SE/US/GB/IE/NL/NO=bulk-public, JP/KR=per-parcel, DE/AT/CH/FR=restricted).
- `methods/fetch_wdqs.sh`    — polite, EXPLICIT, operator-only WDQS refresh of the snapshot.

## Real acquisition + WDQS load discipline (operator directive 2026-06-16)

REAL data ingests PUBLIC protected land from Wikidata — G1-safe (public owners, no persons, no
coordinates; only country + area + a per-source per-country public-owner bucket). **Data lands in
the repo DATA LAYER via the datalad substrate** (ADR-2605241500; the genome convention) and the
actor PROCESSES it later:

```
80-data/jinushi-land/
  *.raw.json                            # RAW WDQS fetches (gitignored; annex/IPFS cold tier)
  wikidata-national-parks.kotoba.edn    # Q46169  — PRIMARY world-coverage source (counts=true)
  wikidata-nature-reserves.kotoba.edn   # Q179049 — observed-only (counts=false; overlap)
  country-areas.kotoba.edn              # Q6256 P2046 — real per-country denominator (203 cc)
  ingest-provenance.json                # sources + derived / sha256 / cidv1 / unit-map / pin path
  .gitignore                            # *.raw.json + the derived Datom log (regenerable; cold tier)
  (jinushi-land-datoms.kotoba.edn)      # DERIVED canonical EAVT Datom log (gitignored; CID in provenance)
```

Pipeline: `fetch_wdqs.sh` (operator, polite) → `*.raw.json` in the data layer →
`normalize_wdqs.cljc` (PROCESS later: canonical unit map + salvage parse, in code) → committed
snapshots → `ingest`/`emit_real` (offline).

| source | class | records | countries | area | counts toward world coverage |
|---|---|--:|--:|--:|---|
| national parks | Q46169 | 1859 | 85 | 9.94M km² | **yes** (primary, non-overlapping) |
| nature reserves | Q179049 | 497 | 3 | 0.23M km² | **no** (overlaps NP countries NO/IE/CA) |

**World acquisition coverage = 85 countries · 6.20M km² = 4.17% of world land** (HONEST, sanitized).
A real WDQS country-area denominator (`country-areas.kotoba.edn`, 203 countries) now (a) resolves
national fractions for every covered country and (b) drives a **data-quality gate (G4)**: parcels
whose area exceeds their country's total area are dropped (Wikidata P2046 unit errors / ocean-
spanning marine megaparks). This **corrected the headline 6.67% → 4.17%** — just 5 outlier parks
had inflated it by ~3.7M km². The earlier loop figures (0.056% → 3.34% → … → 6.67%) were RAW
(pre-sanitization) upper bounds; 4.17% is the honest current value, itself still an upper bound
(sub-country marine parks + overlapping parks are not yet geometry-de-duped). The real acquisition
is emitted to the **canonical kotoba Datom log** (`methods/emit_real.cljc` → `jinushi-land-datoms.kotoba.edn`,
ground `:owner/*`+`:parcel/*` `:add` + derived `:jinushi/*` transient), making the world land
data first-class canonical state (ADR-2605312345); the log is regenerable + content-addressed
(CID in provenance), so it is not committed to git. Multi-source is
**double-count-honest** (G2/G4): only non-overlapping counting sources sum into world coverage;
overlapping protected-area classes are observed separately until a geometry de-dup leg exists.
Units resolved at snapshot time (km²/hectare/decare/dunam/acre/sq-mile/m²); non-positive
bad-data areas dropped (disclosed). Each snapshot is **content-addressed to a CIDv1**
(`methods/cid.cljc`, raw/sha2-256, `bafkrei…`, recorded in `ingest-provenance.json`). Cold tier
(git-annex local-store → IPFS CID map → PDS `datasetPin`) is the operator step via
`e7m-dataset add 80-data/jinushi-land` against superdataset `90-docs/baien/datasets` — not auto-run.

## Building-level ownership + company linkage (operator directive 2026-06-16)

jinushi extends from land-AREA coverage to per-BUILDING ownership: who owns which building, how
many floors, and — via the owner's **LEI (P1278)** / Wikidata QID — the **bridge to the corporate
KGs** (kabuto 兜 · uchiwake 内訳 · kanjō 勘定 · keizu 系図 · tsumugi 紡ぎ). Current slice (`wikidata-buildings.kotoba.edn`, four polite country-bound fetches): **1,603
buildings · 6 countries (CA/FR/IE/JP/NO/US) · 839 owners · 152 LEI links · 202 natural-person
owners · 113 with floors**; building-取-concentration HHI 115 — SNCF 81, 東日本旅客鉄道 (JR East)
58, RATP 39 (rail operators own the most; the US slice is far more owner-diverse). Emitted
as a KG Datom log (`:building/*` nodes + `:building/owner` edges + `:owner.org/{wikidata,lei,label}`).
**202 `:natural-person` owners** (US/FR-heavy) demonstrate the reframed gate at scale — public-
registry natural-person owners represented, not excluded.

**Authoritative company linkage** (`methods/company_link.cljc` + `gleif-companies.kotoba.edn`):
each building-owner LEI is resolved against the **GLEIF public register** to its authoritative
legal identity (legal name / jurisdiction / status). **152 owners → GLEIF, 537 buildings linked** across 47 jurisdictions (incl. 30+ US states)
— SNCF 81 · 東日本旅客鉄道 / JR East 58 · RATP 39 · JR Central/West · ADP. The LEI is the cross-actor join key into the corporate KGs (kabuto/uchiwake/kanjō), the QID
into keizu/tsumugi — so "who owns this building" resolves to a real, registry-grounded company.
GLEIF registers legal persons only, so this layer is corporate by construction.

**Reframed gate (the charter does NOT ban personal data).** Land/building ownership is PUBLIC
RECORD. The constitution bans **asymmetric or monetized** surveillance (Rider v3.1 §2(c)
reciprocity axis, ADR-2606082400) while **affirming reciprocal/symmetric 相互監視** (Tier-0
神の監視, 村社会 transparency). So the gate is NOT "exclude natural persons" — it is:

- **P1 PUBLIC-RECORD provenance** only (already-disclosed registry / open KG; never covert/inferred).
- **P2 RECIPROCAL / SYMMETRIC** — the registry is open to all equally; an owner is as visible as
  anyone. Mirrored transparency, not a one-way watch-feed.
- **P3 MAP-NOT-TARGET, NON-MONETIZED** — routed to commons-return / transparency, never a
  seizure / eviction / targeting list, never sold.

Natural-person ownership is therefore **representable from a public registry** under P1–P3 (this
Wikidata slice happens to be all legal entities; `:owner/type :natural-person` is a public-record
attribute, not a person-exclusion). What stays unrepresentable: covert/inferred ownership,
asymmetric watch-lists, monetized resale. **Per-jurisdiction grounding** (`methods/jurisdiction.cljc`):
natural-person ownership is BULK-ingested only where the registry is public-by-law + bulk +
owner-names-visible (SE/US/GB/IE/NL/NO); per-parcel-only regimes (JP/KR) and restricted ones
(DE/AT/CH Grundbuch, FR owner names) are NOT bulk-ingested; unknown jurisdictions degrade honestly.

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
for ns in test-analyze test-datom-emit test-coverage test-ingest test-cid test-emit-real test-normalize-wdqs test-verify; do
  bb --classpath $CP -e "(require 'clojure.set 'jinushi.methods.$ns) (clojure.test/run-tests 'jinushi.methods.$ns)"
done
# 57 tests / 221 assertions green

bb --classpath 20-actors -m jinushi.methods.coverage     # synthetic seed → out/coverage.md
bb --classpath 20-actors -m jinushi.methods.datom-emit   # → out/jinushi-datoms.kotoba.edn
bb --classpath 20-actors -m jinushi.methods.ingest       # REAL snapshots → live world coverage (offline)
bb --classpath 20-actors -m jinushi.methods.cid          # CIDv1 of each committed snapshot
bb --classpath 20-actors -m jinushi.methods.normalize-wdqs # raw *.raw.json → committed snapshots (process)
bb --classpath 20-actors -m jinushi.methods.emit-real    # REAL acquisition → kotoba Datom log + CID
bb --classpath 20-actors -m jinushi.methods.verify       # snapshots ↔ provenance CID/sha256 integrity

# operator-only, rare, polite — refresh the snapshot from WDQS (NOT run by the loop):
methods/fetch_wdqs.sh 400
```

## Status / roadmap

- **R0 (landed)** — analyze + datom-emit + coverage + ontology + synthetic seed + 16 tests. ✅
- **R2 (landed)** — REAL multi-source public-land ingest (`normalize_wdqs.cljc` + `ingest.cljc`
  + `fetch_wdqs.sh`): committed Wikidata snapshots — national parks (1859 / **85 cc**, sanitized 6.20M km²,
  **counts**; four polite country-bound fetches) + nature reserves (497 / 3 cc, observed-only,
  overlap-excluded). World coverage **4.17%** HONEST (sanitized; raw 6.67% before dropping 5 over-country outliers). Processing is code (canonical unit map + salvage parse in `normalize_wdqs.cljc`).
  Double-count-honest (G2/G4), full unit map (km²/ha/decare/dunam/acre/sq-mile/m²), non-positive
  bad-data dropped, data in 80-data via datalad substrate, WDQS-load-safe (snapshot SoT; loop
  never queries WDQS). +7 tests. ✅
- **R1 (landed)** — CIDv1 (raw/sha2-256) content-addressing of every snapshot (`methods/cid.cljc`,
  verified against the canonical empty-block vector; CIDs recorded in `ingest-provenance.json`).
  Append-only commit-DAG (`kotodama/src/kotoba/datom.cljc` reuse) + dag-pb/UnixFS `ipfs add`
  parity remain follow-on legs. +4 tests. ✅
- **Datom log (landed)** — `methods/emit_real.cljc`: the REAL acquisition emitted to the canonical
  kotoba Datom log (counting dataset → analyze → EAVT `:add`/derived), CID in provenance. Makes
  the world land data first-class canonical state (ADR-2605312345). +4 tests. ✅
- **R2+** — broaden real sources (more national-park countries: JP/IN/AR/MX missed the LIMIT;
  protected landscapes / public-land registries / OSM landuse) one small polite batch at a time;
  geometry de-dup so overlapping protected-area classes can count.
- **R3** — bridge confirmed-donation parcels to the on-chain `LandRegistry` lane (still a member
  donation, no-server-key) + maps.etzhayyim.com `:feature/*` layer.
- **ADR** — to author: `26xxxxxxxx-jinushi-land-ownership-acquisition-mirror.md` (mirror-lineage
  pattern; land-sovereignty §1.11 grounding).
