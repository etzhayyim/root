# ooyake 公 — World Government Atlas

> A civic wayfinding map of every government on Earth — **not** the government.

`did:web:ooyake.etzhayyim.com` · Tier-B · ADR-2606021600 · **R1 — real verified data, every tier**

ooyake is the kotoba-Datomic-native **structural atlas** of public administration:
supranational → country → region → prefecture → municipality/ward → ministry (省)
→ agency (庁) → bureau (局) → division (課) → section → **窓口**, each unit carrying
its **住所 (address) · 窓口 (service window) · 書式 (form) · 手続き (procedure) ·
BPMN (process model)**.

It is the single read-side SSoT that the other government-facing actors consume:

| Actor | Uses ooyake for |
|---|---|
| **toritsugi** 取次 | which 窓口 / 所管 / 書式 a citizen procedure routes to (delivery) |
| **danjo** 弾正 | the canonical unit list to cross-reference open-data against |
| **kanae** 鼎 | the units to render fiscal flows over |
| **tsumugi** 紡ぎ | reconciling a unit to its `:organism` 縁/取 karma node |
| **himotoki** 繙き | which authority + 窓口 to file a 開示請求 / FOIA against |

## Posture

An **observational mirror + civic wayfinding map** — like tsumugi ("accountability
map, never a target-list") and watatsuna ("resilience map, never a target-list").

- Per-unit atlas DIDs (`did:web:etzhayyim.com:gov:<iso3>:...`) are etzhayyim
  **mirror records** of real public bodies. They never claim to BE the
  government, never act as an official channel (G3, §2(c)).
- **Read-only**: ooyake catalogs. Filing/submitting is toritsugi (gated);
  auditing is danjo. ooyake does neither (G9).
- Civic wayfinding only — never an attack-surface map of the state (G10).

## Coverage (real data, 2026-06-04)

**~6,535 `:gov.unit` rows across ~190 jurisdictions, all `:authoritative` /
`:maintainer-verified`** with an independently-verified Wikidata QID and (where
recorded) the body's own official URL. Spans every tier:

| Tier / branch | What | ~count |
|---|---|---|
| supranational | UN system + major IGOs (intergovernmental) | 96 |
| country | current UN member states | 192 |
| subnational | first-level admin divisions (states/provinces/regions) | 3,599 |
| legislative | national legislatures | 186 |
| judicial | supreme/highest courts | 144 |
| executive | 18 ministry types (finance/foreign/defense/interior/health/justice/education/…) | ~1,850 |
| independent | central banks (158) + audit / ombudsman / electoral / NHRI / anti-corruption / data-protection / competition / financial-regulator / statistics | ~420 |

Plus **~5,693 `:gov.address`** (4,521 with precise lat/lon: national-body HQs +
subnational seats + national capitals) → a derivable world-government **GeoJSON**.

Honest gaps: a few categories are Wikidata-typing-thin (water/industry/competition);
microstates carry fewer bodies; some bodies are sub-national mis-typings retained by
the one-per-country dedup. See [`MATURITY.md`](MATURITY.md) (per-iteration record).

## Layout

```
20-actors/ooyake/
├── manifest.jsonld              # DID manifest + cells + gates + non-goals
├── CLAUDE.md / README.md / MATURITY.md
├── registry/                    # ~30 gov-units*.edn (the canonical EDN data)
│   ├── gov-units.seed.edn / gov-units.jp-central.seed.edn   # JP backbone
│   ├── gov-units.g20*.edn       # G20 countries + finance ministries + central banks
│   ├── gov-units.world-*.edn    # world countries / ministries / legislatures / courts / central banks
│   ├── gov-units.oversight-*.edn# audit/ombudsman/electoral/NHRI/anticorruption/… /statistics/revenue
│   ├── gov-units.adm1-*.edn      # first-level subdivisions (5 continent files) + adm1-coords
│   ├── gov-units.intergov.edn / gov-units.capitals.edn / gov-units.hq-locations*.edn
│   └── authority-reference.edn  # reconcile-demo fixture
├── scripts/                     # check_seed_integrity · atlas_summary · coverage_matrix
│   │                            #   · world_coverage · g20_coverage · reconcile · export_geojson
├── cells/reconcile/             # ReconcileCell + tests (incl. integrity-guard self-tests)
├── deploy/run_tests.sh          # offline gate runner (integrity + coverage + reconcile + …)
└── viz/
    ├── gov-atlas.geojson         # 4,521-feature world-government map (generated)
    └── gov-atlas-map.htm         # self-contained browser viewer (no CDN/tiles)

00-contracts/schemas/gov-atlas-ontology.kotoba.edn   # :gov.* ontology (level/branch enums)
00-contracts/lexicons/com/etzhayyim/ooyake/*.json    # XRPC lexicons (read-only)
90-docs/adr/2606021600-ooyake-world-government-atlas-tier-b-actor-r0.md
```

## Tooling (all offline, `bash deploy/run_tests.sh`)

- `scripts/check_seed_integrity.py` — guards QID uniqueness/format, the
  level/branch/sourcing enums, G5 provenance, and address→unit + parent refs.
- `scripts/atlas_summary.py` — by level / branch / sourcing / jurisdiction.
- `scripts/coverage_matrix.py` — per-country presence across 35 functional categories.
- `scripts/export_geojson.py` — derive `viz/gov-atlas.geojson` from the registry.
- open `viz/gov-atlas-map.htm` in a browser to explore the map.

## Query surface (read-only XRPC)

- `com.etzhayyim.ooyake.getUnit` — resolve a unit + its children/addresses/windows
- `com.etzhayyim.ooyake.resolvePath` — resolve a dotted path / atlas DID to a unit
- `com.etzhayyim.ooyake.findService` — *"where do I do procedure X near me?"* →
  procedure + window + address (the citizen wayfinding query)
- `com.etzhayyim.ooyake.searchUnits` — text/geo search; backs civic search at
  `etzhayyim.com` (`/actors` kotoba-wasm search surfaces gov units at R1)

## Status

**R1 — real verified data, committed.** The registry holds ~6,535 maintainer-verified
units (real Wikidata QIDs, body-own provenance) across every governance tier, with a
derivable GeoJSON map. What remains **gated** (operator/Council, NOT done here):

- **Live kotoba ingest** of the registry into the `gov-atlas-v1` Datom graph — needs an
  operator token + node (`KOTOBA_TOKEN`).
- **Publishing** national `:authoritative` rows to `/.well-known/gov-units.json` — the
  Council-Lv6+ / bootstrap-attestation gate (`validate_atlas.py` check #5 currently
  admits only the JP prefecture/city backbone as published-authoritative).

i.e. this is the committed registry **record** of real data; ingest + public
publication are the separate operator/Council steps. See [`MATURITY.md`](MATURITY.md)
for the full per-iteration build log.
