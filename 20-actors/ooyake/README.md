# ooyake 公 — World Government Atlas

> A civic wayfinding map of every government on Earth — **not** the government.

`did:web:ooyake.etzhayyim.com` · Tier-B · ADR-2606021600 · **R0 scaffold**

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

## Layout

```
20-actors/ooyake/
├── manifest.jsonld              # DID manifest + 6 cells + 12 gates + 11 non-goals
├── CLAUDE.md                    # actor dev guide
├── README.md                    # this file
├── MATURITY.md                  # honest R0 coverage scorecard
└── registry/
    └── gov-units.seed.edn       # proof-of-model seed (all :unverified-seed)

00-contracts/schemas/gov-atlas-ontology.kotoba.edn   # :gov.* ontology
00-contracts/lexicons/com/etzhayyim/ooyake/*.json    # 8 XRPC lexicons (read-only)
00-contracts/bpmn/com/etzhayyim/ooyake/*.bpmn        # 3 process models (model-only)
90-docs/adr/2606021600-ooyake-world-government-atlas-tier-b-actor-r0.md
```

## Query surface (read-only XRPC)

- `com.etzhayyim.ooyake.getUnit` — resolve a unit + its children/addresses/windows
- `com.etzhayyim.ooyake.resolvePath` — resolve a dotted path / atlas DID to a unit
- `com.etzhayyim.ooyake.findService` — *"where do I do procedure X near me?"* →
  procedure + window + address (the citizen wayfinding query)
- `com.etzhayyim.ooyake.searchUnits` — text/geo search; backs civic search at
  `etzhayyim.com` (`/actors` kotoba-wasm search surfaces gov units at R1)

## Status

R0 ships **substrate + a proof-of-model seed**, not coverage. Every seed row is
`:sourcing :representative` + `:verification-status :unverified-seed`. No cell
runs and no per-unit DID is served until Council Lv6+ ratifies ADR-2606021600.
See [`MATURITY.md`](MATURITY.md).
