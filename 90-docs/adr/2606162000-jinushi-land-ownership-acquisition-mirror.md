---
id: adr-2606162000-jinushi-land-ownership-acquisition-mirror
title: "ADR-2606162000: jinushi 地主 — world land/building ownership ACQUISITION mirror (multi-source, clj-native, public-record gate)"
status: accepted
doc_type: adr
topic: jinushi-land-ownership-acquisition-mirror
authoritative: true
last_verified: 2026-06-17
priority: 5.0
axis: architecture
weight: 0.5
priority_note: "Data-acquisition feeder of the land-sovereignty stack (ADR-2605192100 §1.11 + 2605192245). Upstream observational mirror that measures world real-estate acquisition coverage + ownership 取-concentration; the on-chain LandRegistry remains the only place land moves."
authoritative_for:
  - "20-actors/jinushi/ (actor: methods, ontology, seed, data layer 80-data/jinushi-land/)"
  - "jinushi public-record ingest gate (public-record + reciprocal-symmetric + map-not-target + non-monetized)"
  - "jinushi multi-source ingest + per-source reliability (信頼度) + as-of diff (差分)"
depends_on:
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192245-etzhayyim-global-land-sovereignty
  - adr-2605241500
  - adr-2605262130
  - adr-2605312345
  - adr-2606082400
related:
  - adr-2606013800
  - adr-2606022000
  - adr-2606032000
  - adr-2606101000
supersedes: []
superseded_by: []
---

# ADR-2606162000: jinushi 地主 — world land/building ownership ACQUISITION mirror

**Status**: accepted — RATIFIED 2026-06-17 by PR merge (Council attestation = PR review, founder
operational premise 2026-06-11); landed across PR #1820 / #1874 / #1878.
**Date**: 2026-06-16 (closing record 2026-06-17)
**Deciders**: Jun Kawasaki

# Context

The on-chain `LandRegistry.sol` (ADR-2605192245) records only **donated, waqf-inalienable** land
and starts at **0 parcels**. There was no upstream actor measuring *how much of the world's land
we have data on, who holds it, where the 取-concentration is* — the map that tells the registry
what to seek and routes land back toward the commons (Tree-of-Life land doctrine,
ADR-2605192100 §1.11). The legacy `crawler → land-owners → maps` design
(`80-data/reports/260225-…`) was RDBMS/KV and never built.

jinushi is the land-scale sibling of the KG-mirror lineage (inochi 命 / tsumugi 紡ぎ / kabuto 兜 /
kanae 鼎 / keizu 系図), clj-native, re-homed onto the canonical kotoba Datom log
(ADR-2605262130 + 2605312345; no RisingWave/KV). Built over a `/loop` across ~14 iterations.

# Decision

Adopt `20-actors/jinushi/` — a **multi-source, clj-native real-estate acquisition mirror**:

1. **Land layer** — Wikidata national parks / nature reserves (public land), normalized to m²
   across 9 area units, sanitized against a real WDQS country-area denominator (a parcel cannot
   exceed its country → drops Wikidata P2046 unit errors / marine megaparks). Honest world
   coverage = **85 countries / 6.20M km² = 4.17%** (corrected down from an un-sanitized 6.67%).
2. **Building layer** — Wikidata buildings with owner / floors / height; **2,405 buildings / 19
   countries / 1,389 owners**; two 取-concentration lenses (by #buildings = rail operators; by
   total FLOORS = real-estate developers — Mitsui Fudosan / Mitsubishi Estate …).
3. **Government cadastre** — NYC PLUTO (Socrata, public domain): parcel owner + floors + BBL,
   **including natural persons** (`methods/nyc_pluto.cljc`).
4. **Authoritative company linkage** — every owner LEI resolved against the **GLEIF** public
   register → legal name / jurisdiction; the LEI is the join key to kabuto/uchiwake/kanjō, the
   Wikidata QID to keizu/tsumugi. **221 owners → 690 buildings** linked.
5. **Per-source reliability (信頼度)** — `methods/confidence.cljc`: documented trust tiers
   (authoritative-gov/registry > curated-crowd Wikidata > open-crowd OSM > web), trust-weighted
   conflict resolution (highest-trust wins, disagreement recorded).
6. **As-of diff (差分)** — `methods/diff.cljc`: added/removed/changed records between snapshots.
7. **Capstone digest** — `methods/digest.cljc` fuses all layers into one answer to
   「全世界の不動産の取得 coverage は?」.

## Reframed public-record gate (the constitution does NOT ban personal data)

Land/building ownership is **public record**. Per Rider v3.1 §2(c) / ADR-2606082400 the
constitution bans **asymmetric or monetized** surveillance while **affirming reciprocal/symmetric
相互監視** (Tier-0 神の監視, 村社会 transparency). So the gate is **not** "exclude natural persons":

- **P1 PUBLIC-RECORD provenance** only (disclosed registry / open KG; never covert/inferred).
- **P2 RECIPROCAL / SYMMETRIC** — registry open to all equally; mirrored transparency, not a
  one-way watch-feed.
- **P3 MAP-NOT-TARGET, NON-MONETIZED** — routed to commons-return / transparency; never a
  seizure / eviction / targeting list; never sold.

Per-jurisdiction grounding (`methods/jurisdiction.cljc`): natural-person ownership is BULK-ingested
only where the registry is public-by-law + bulk + owner-names-visible (SE/US/GB/IE/NL/NO);
per-parcel-only (JP/KR) and legitimate-interest-restricted (DE/AT/CH Grundbuch; FR owner names)
are not bulk-ingested; unknown jurisdictions degrade honestly.

**Ingest vs publish** are distinct: the gate permits ingest; the published analytical KG keeps a
publish-prudence layer (legal entities named for accountability; natural persons anonymized by
sha256-key in the analytical snapshot; no dwelling coordinates — G1). Raw acquired source data is
stored in the repo data layer per operator directive (2026-06-16).

## Substrate

Data lands in the repo DATA LAYER `80-data/jinushi-land/` (datalad substrate, ADR-2605241500;
genome convention): raw `*.raw.json` (acquired source, committed) → `normalize_*` (process in
code) → committed snapshots → `ingest`/`emit_real` → canonical kotoba Datom log. Every artifact
is content-addressed (CIDv1 raw/sha2-256, `methods/cid.cljc`) and recorded in
`ingest-provenance.json`; `methods/verify.cljc` re-derives + checks all CIDs. Cold-tier
git-annex → IPFS pin via `e7m-dataset add` against superdataset `90-docs/baien/datasets` is the
operator step.

# Consequences

- First runnable answer to world real-estate acquisition coverage, on the canonical Datom log,
  with authoritative company linkage and a principled public-record gate.
- 70 tests / ~290 assertions green (bb clojure.test); WDQS-load-safe (snapshot is SoT; the loop
  never queries WDQS; live fetch is the polite operator step `methods/fetch_wdqs.sh`).
- jinushi asserts no transfer/mint (G3): only the on-chain LandRegistry moves land, by member
  donation (no-server-key).

# Alternatives Considered

- **RDBMS/KV (legacy design)** — rejected; off-substrate (ADR-2605262130 bans RW/KV).
- **Exclude natural persons entirely** — rejected as over-restrictive vs the charter (the
  reciprocity axis, not a personal-data ban); replaced by the public-record + jurisdiction gate.
- **CommonCrawl/Archive blind web mining first** — deferred; heavy + low-precision + license/G1
  care. Government open-data portals + OSM + GLEIF are the higher-yield, charter-clean sources.

# Implementation record (closing, 2026-06-17)

Built end-to-end over a `/loop` session and landed to `main` across three PRs
(#1820 → #1874 → #1878). Final state:

**Sources (6) + denominator, each carrying a documented reliability tier (`confidence.cljc`)**:
- NYC PLUTO (Socrata, public domain) — gov cadastre, parcel owner + floors; `authoritative-gov 0.95`
- FR DVF (DGFiP/Etalab geo-dvf) — property VALUES (€, €/m²), no owner identity; `authoritative-gov 0.95`
- GLEIF — authoritative legal-entity identity for owner LEIs; `authoritative-registry 0.95`
- Wikidata national parks / nature reserves / buildings; `curated-crowd 0.70`
- OSM (Overpass, ODbL) — `building:levels` + operator; `open-crowd 0.60`
- Wikidata country `P2046` area — the real per-country coverage denominator

**Coverage / dimensions**:
- LAND: national parks (protected PUBLIC land) **137 countries / 7.07M km² = 4.76%** of world land,
  sanitized against the real country-area denominator (a parcel > its country is dropped, G4). The
  metric is labelled honestly as national-park land ÷ world land, NOT all-land-ownership.
- BUILDINGS: 2,405 buildings / 19 countries / 1,389 owners (313 natural-person, public-figure) /
  floors + height; two 取-concentration lenses (#buildings = rail; total FLOORS = developers —
  Mitsui Fudosan / Mitsubishi Estate).
- COMPANY: 221 owners → GLEIF authoritative entities → 690 buildings; LEI → kabuto/uchiwake/kanjō,
  QID → keizu/tsumugi.
- VALUE: DVF medians per commune (€1,438/m² Saint-Étienne … €12,707/m² Paris-5e) + YoY trajectory
  (`value_trend.cljc`; Paris-5e −3.4% 2022→2023).

**Maturity layers**: per-source reliability + trust-weighted cross-source `reconcile` (221 owners,
GLEIF authoritative name wins over Wikidata crowd label) · as-of `diff` (差分) · `sanitize` (G4) ·
per-jurisdiction public-record gate (`jurisdiction.cljc`) · content-addressing (`cid.cljc`,
CIDv1 raw/sha2-256, verified ipfs-compatible) · integrity `verify.cljc` (committed-only) ·
**unified canonical kotoba Datom log** across all sources (`emit_all.cljc`, ~37k datoms, source-
tagged) · capstone `digest.cljc`.

**Storage**: working copies git-committed + **IPFS-pinned** (real CIDs; clean public bundle
`bafybeih33zveijs2zkc35srt25fcvwsegdvjmddlqb6lorrejwopha5pbe` DHT-announced); raw acquired data +
resolution caches committed so a rebuild never re-queries any source; full DataLad superdataset +
remote IPFS pin remain the operator cold-tier step (ADR-2605241500).

**Production scale (R2, `scale_ingest.cljc` + `PRODUCTION.md`)**: bounded-memory line-streaming
ingest for full bulk (PLUTO ~860k lots / nationwide DVF), aggregates byte-identical to the sample
path, natural-person names anonymized on the fly; operator runs the one-shot bulk download (the
loop never fetches at scale — 負担をかけない).

**Privacy correction (high-effort code-review, pre-merge)**: an earlier commit un-ignored
`*.raw.json`, which would have published ~1,500 ORDINARY natural persons (NYC PLUTO) by name to the
public repo — contradicting the actor's own publish-prudence invariant. Fixed before reaching
`main`: `nyc-pluto*.raw.csv`/`.json` are gitignored (local / IPFS cold-tier only); the committed
`nyc-pluto-parcels.kotoba.edn` is anonymized (persons → sha256-key, 0 names; verified). The
principled line: **bulk-cadastre ordinary individuals are anonymized/local-only; notable
public-figure owners from open KGs (Wikidata, already-public QID) are represented** per the
public-record directive. The feature branch (carrying the intermediate raw) was deleted, so the
names never persist in any reachable ref on the public repo.

**Tests**: 100 tests / 388 assertions green (bb `clojure.test`); every charter gate
(person-privacy/anonymization, sanitize, confidence, honesty, no-transfer/mint, Murakumo-only)
test-enforced and holding at scale.

# References

- `20-actors/jinushi/CLAUDE.md` — actor doc + method index + source roadmap
- ADR-2605192100 §1.11 (land doctrine) · ADR-2605192245 (land sovereignty) · ADR-2606082400
  (Rider v3.1 reciprocity axis) · ADR-2605241500 (datalad substrate) · ADR-2605262130 +
  2605312345 (kotoba Datom canonical state)
- GLEIF `api.gleif.org` · NYC PLUTO (Socrata) · Wikidata WDQS
