---
id: adr-2606041827-watari-live-ship-aircraft-position-kotoba-native
title: "ADR-2606041827: watari 渡り — kotoba-native live ship + aircraft position knowledge graph"
status: proposed
doc_type: adr
topic: watari-live-moving-craft
authoritative: true
last_verified: 2026-06-04
priority: 5.0
axis: architecture
weight: 0.50
priority_note: ""
authoritative_for:
  - live real-time ship (AIS) + aircraft (ADS-B) position ingestion onto the kotoba Datom log
  - watari actor design, ontology, lexicons, gates
depends_on:
  - "2606012600"
  - "2605262130"
  - "2605312345"
  - "2605215000"
  - "2605241500"
  - "2605192200"
related:
  - "2605011500"
supersedes: []
superseded_by: []
---

# ADR-2606041827: watari 渡り — kotoba-native live ship + aircraft position knowledge graph

**Status**: proposed
**Date**: 2026-06-04
**Deciders**: Jun Kawasaki

# Context

The question *「船舶や飛行機のリアルタイムな位置情報を取得、更新する actor は設計されているか」*
has a partial-yes-but-non-compliant answer.

**Two legacy actors already ingest live craft positions**, but both predate the kotoba
storage pivot and violate the current substrate boundary:

- **`maps`** (`20-actors/maps/`, ADR-2605011500, 2026-05-01) runs two real-time pipelines:
  - `aismarine` — an AISStream.io WebSocket consumer writing vessel positions into
    **Kotoba/Datomic** tables `vertex_vessel` / `vertex_vessel_position` / `vertex_vessel_voyage`.
  - `aircraft_live` — an OpenSky Network + adsb.fi poller writing aircraft state vectors into
    Kotoba/Datomic `vertex_aircraft_state` / `vertex_aircraft_track` (source DID
    `did:web:maps.etzhayyim.com:adsb`, 5 m TTL).
- **`vessel`** (`20-actors/vessel/`) tracks IMO/MMSI ships with a `tracking:ais` component,
  storing positions in a graph DB via **`graph.write` SQL** (`VesselPosition` / `Voyage` /
  `PortCall` nodes) and narrating with off-Murakumo `agent.chat`.

Both are **non-compliant with the canonical substrate**:

1. **State store** — ADR-2605262130 + ADR-2605312345 make the **kotoba Datom log** the
   first-class canonical state. Kotoba/Datomic / Postgres / graph.write SQL as a canonical store
   is prohibited.
2. **Inference** — ADR-2605215000 makes the Murakumo fleet the sole inference SSoT; the
   legacy `agent.chat` narration is off-Murakumo.
3. **No anti-surveillance invariant** — moving-craft position is uniquely sensitive: a
   private yacht or private jet track can de-anonymize an *individual*. The legacy surfaces
   carry no constitutional gate against person-tracking / pattern-of-life.

The data sources themselves are legitimate: **AIS** (ships) and **ADS-B** (aircraft) are
*open public transponder broadcasts* that craft lawfully emit in the clear; terrestrial and
space receivers (AISStream, OpenSky, adsb.fi) aggregate them as free public data. The
problem is purely the **store + narration + missing guardrails**, not the inputs.

The monorepo already has the right pattern for a kotoba-native *observation-face* actor:
**watatsuna 綿津綱** (ADR-2606012600) datafies the *static* submarine-cable network as an
EAVT resilience map, framed toward redundancy and **never** a target-list, paired with the
*operational* watatsumi 綿津見. watatsuna keys chokepoints (`:malacca` `:luzon-strait`
`:suez-red-sea` `:hormuz` …) — but it has no notion of the *moving* traffic over those same
chokepoints. That is the gap watari fills.

# Decision

Author **`watari 渡り`** — a Tier-B, kotoba-native, observation-face actor that ingests the
**live positions of public, transponder-broadcasting moving craft** (ships via AIS, aircraft
via ADS-B) onto the kotoba Datom log and surfaces aggregate situational concentration. It is
the kotoba-native **successor to the legacy `maps` `aismarine`/`aircraft_live` and `vessel`
`tracking` pipelines**.

The name 渡り unifies the two craft classes in one kami of passage: 渡り鳥 (migratory birds →
aircraft) + 渡し・渡海 (ferry crossing → ships). It joins **watatsumi 綿津見** (sea body) and
**watatsuna 綿津綱** (sea cables) as the 海/空 path lineage.

## D1 — Ontology (`00-contracts/schemas/moving-craft-ontology.kotoba.edn`)

- `:craft/*` — a moving craft's stable **identity**: `:kind` ∈ `:vessel | :aircraft`; vessel
  identity (`:mmsi` `:imo` `:vessel-type`), aircraft identity (`:icao24` `:registration`
  `:aircraft-type`); `:flag`, `:operator` (a **company org id, never a person**).
- `:craft.fix/*` — a **first-class, append-only POSITION FIX** (the heart): `:lat` `:lon`
  `:alt-m` `:speed-kn` `:course` `:nav-status` (AIS) `:on-ground` (ADS-B) `:lane`
  `:observed-at` `:source` ∈ `:ais | :adsb`. **The latest fix per craft (max `:observed-at`,
  ISO-8601 sorts lexically) IS the current position; the fix stream IS the trajectory** —
  appended, never overwritten (非終末論; there is no terminal "final position" datom).
- `:craft.leg/*` — an observed/declared voyage (ship) or flight (aircraft) leg; mirrors the
  public AIS-destination / schedule only (no intent adjudication, no ETA forecasting).
- `:lane/*` — a sea-lane / air-corridor / chokepoint / approach (the density unit). Its
  `:lane/chokepoint` keyword is **shared with watatsuna `:station/chokepoint`**.
- `:movement/*` (derived) — lane-load, chokepoint-transit, approach-congestion,
  track-freshness; computed by `analyze.py`, flagged `:derived`, **never re-ingested as fact**.

## D2 — Cells

- `cell:watari.analyze` (`methods/analyze.py`, stdlib) — classify → latest as-of fix per
  craft → lane/corridor load (by kind) → **chokepoint transit (composes with watatsuna)** →
  approach congestion → **freshness tail**. Aggregate-first; idempotent.
- `cell:watari.ingest` (`methods/ingest.py`, R0) — normalize an AISStream / OpenSky public
  batch → `:craft/:craft.fix` → dedup-merge vs seed. **Live network fetch is G7-gated**
  (`WATARI_OPERATOR_GATE=1` + `--live`); default mode is offline, tagged `:representative`.

## D3 — Lexicons (`com.etzhayyim.watari.*`)

`registerCraft` · `recordFix` · `recordLeg` · `registerLane` — kotoba-native, superseding the
legacy maps/vessel surfaces. Mapping in
`00-contracts/lexicons/com/etzhayyim/watari/MIGRATION-NOTES.md`.

## D4 — Coupling to watatsuna (静 ↔ 動 maritime resilience)

Because watari `:lane/chokepoint` and watatsuna `:station/chokepoint` use the **same
keywords**, a chokepoint's *static* submarine-cable dependence (watatsuna) and its *live*
vessel transit (watari) **compose into one maritime resilience picture** — both routed to
redundancy + faster repair + safer routing, never to interdiction.

## D5 — Gates (constitutional)

- **G1 public transponder broadcasts only** — AIS + ADS-B + public registries (ITU MMSI,
  ICAO 24-bit, national reg). Non-broadcasting / military / blocked-from-display (FAA LADD,
  PIA) craft = out of scope.
- **G2 situational-awareness, not surveillance / not targeting** — aggregate-first density
  routed to safety + collision-avoidance + congestion-easing + resilience; never a "follow
  this craft" tool, never a targeting feed (Charter Rider §2(a) force-separation + §2(d);
  mirrors watatsuna G2).
- **G3** aggregate-first + claimed-first.
- **G4 no person-tracking / no pattern-of-life (the defining gate)** — a craft is a craft,
  not a person; MUST NOT de-anonymize a private-craft owner/crew/passenger, build
  pattern-of-life on an individual, or answer "where is person X". Private-owner identity →
  encrypted / excluded. This is the invariant the legacy surfaces lacked.
- **G5 sourcing honesty** (`:authoritative | :representative | :synthesized`) — **no
  fabricated live coverage**; a craft not seen in the latest wave is reported in the
  *freshness tail*, not silently shown as current.
- **G6 Murakumo-only** narration (ADR-2605215000).
- **G7 outward-gated** — live AISStream/OpenSky/adsb.fi ingest = Council + operator; R0 ships
  a bounded seed only.
- **G8 no git-lfs** — bulk position history / replay tiles → DataLad → IPFS
  (`80-data/moving-craft`).
- **G9 no PII** — craft graph only; incidental owner/crew/passenger data → encrypted envelope.

## D6 — Non-goals

N1 not a weapons/targeting/fire-control feed (§2(a) force-separation) · N2 not a
person-surveillance / pattern-of-life tool (G4) · N3 **not real-time control** — observes
craft, never flies/sails one (that is kami-autodrive / funadaiku / watatsumi; observe ≠
control) · N4 **not a safety-of-life service** — NOT GMDSS / ATC / VTS certified;
situational-awareness only · N5 no Kotoba/Datomic / SQL store · N6 no military /
blocked-from-display de-anonymization.

# Consequences

**Positive**

- Real-time ship + aircraft position becomes **substrate-compliant**: state on the kotoba
  Datom log (canonical), narration Murakumo-only — the first such surface to honor
  ADR-2605262130 + 2605215000.
- "Current position" stops being a mutable overwritten row and becomes the **latest as-of
  fix** in an append-only log; the full trajectory (and its history) is queryable via
  kotoba-kqe arrangements (非終末論).
- watari's live transit + watatsuna's static cable load **compose over shared chokepoint
  keywords** → a unified maritime resilience picture across the 静/動 faces.
- A **constitutional anti-surveillance invariant (G4)** now governs craft-position data that
  the legacy `maps`/`vessel` surfaces handled without guardrails.
- Verified R0: `analyze.py` runs green on the seed (13 craft / 26 fixes / 9 lanes; top
  chokepoint transit Malacca 3, Suez-Red-Sea 1, Hormuz 1, Luzon 1; freshness tail 2);
  `ingest.py` normalizes an offline public batch and **refuses live fetch without the G7
  gate**; 4 lexicons + manifest lint clean; DID registered in `INFRA_ACTORS`.

**Negative / honest limits**

- R0 is **design + data-model + analyzer only**. The seed is a bounded `:representative`
  sample (rounded coords, illustrative timestamps — NOT a live capture). Live AIS/ADS-B
  ingest is Council + operator gated (G7).
- `ingest.py` is an offline normalizer; the live AISStream WS + OpenSky REST wiring and the
  dedup-merge-to-EDN step are R1.
- No viz yet (a self-contained aggregate density map / globe, shared with watatsuna/kanae,
  is deferred — the `out/movement-situation.kotoba.edn` derived datoms are the contract).
- The legacy `maps` / `vessel` pipelines are **superseded, not yet deleted**; they remain as
  historical reference pending a follow-up archive cutover (mirrors the watatsuna →
  legacy-telecom-lexicon retirement).

**Constitutional**

- **Zero invariant amendments.** watari adds an actor + ontology + lexicons within existing
  substrate, force-separation, Murakumo-only, and no-git-lfs rules. G4 is a *new actor-local
  gate*, strictly tighter than the Charter, not an amendment.

# Alternatives Considered

1. **Extend `maps` / `vessel` in place.** Rejected — both are Kotoba/Datomic / graph.write SQL
   actors; "extending" them deepens a prohibited store. The migration value is precisely in
   moving state to the Datom log, which is a rewrite, not an extension.
2. **Fold live craft into watatsuna.** Rejected — watatsuna is a *static infrastructure*
   resilience map; mixing high-frequency append-only position fixes into it would blur a
   clean 静/動 boundary. Sharing chokepoint *keywords* (D4) gives the coupling benefit
   without conflating the two.
3. **Aircraft-only or ship-only actor.** Rejected — AIS and ADS-B are the same shape
   (identity + append-only fix stream + lane density) and share every gate; 渡り (migratory
   birds + ferry crossing) names exactly that union. One actor, `:kind`-discriminated.
4. **No G4 anti-surveillance gate (parity with legacy).** Rejected — moving-craft tracks can
   de-anonymize individuals; an observation actor without a person-tracking prohibition would
   be a surveillance tool. G4 is load-bearing and encoded structurally (operator = a company
   org id; private craft out of scope by G1).

# References

- ADR-2606012600 (watatsuna 綿津綱 submarine-cable KG + watatsumi cable-laying robotics) — the
  observation-face pattern + shared chokepoint keywords
- ADR-2605262130 (kotoba storage substrate unification — no Kotoba/Datomic)
- ADR-2605312345 (kotoba Datom log = first-class canonical state)
- ADR-2605215000 (Murakumo-only inference)
- ADR-2605241500 (Dataset CID substrate — DataLad → IPFS, no git-lfs)
- ADR-2605192200 (Charter Rider v2.0 — §2(a) force-separation, §2(d) infrastructure-attack)
- ADR-2605011500 (legacy maps aismarine pipeline — superseded for new work)
- `00-contracts/schemas/moving-craft-ontology.kotoba.edn` — vocabulary
- `00-contracts/lexicons/com/etzhayyim/watari/MIGRATION-NOTES.md` — legacy → watari mapping
- `20-actors/watari/` — manifest, CLAUDE.md, cells, seed
