# watari 渡り — lexicon migration notes (ADR-2606041827)

`com.etzhayyim.watari.*` is the **kotoba-native** successor to the legacy real-time
ship/aircraft position surfaces, which violated the substrate boundary (RisingWave /
graph.write SQL store; ADR-2605262130 + 2605215000). This file is the authoritative
mapping from the retired surfaces to the watari lexicons + `:moving-craft-ontology`
EAVT attributes.

## Retired legacy surfaces → watari

| legacy surface | legacy store | watari lexicon | kotoba EAVT |
|---|---|---|---|
| `maps` `aismarine` pipeline (`primitives/aismarine.py`) | RisingWave `vertex_vessel`, `vertex_vessel_position`, `vertex_vessel_voyage` | `registerCraft` (kind=vessel) + `recordFix` (source=ais) + `recordLeg` | `:craft/*` `:craft.fix/*` `:craft.leg/*` |
| `maps` `aircraft_live` pipeline (`primitives/aircraft_live.py`) | RisingWave `vertex_aircraft_state`, `vertex_aircraft_track`, `vertex_aircraft` | `registerCraft` (kind=aircraft) + `recordFix` (source=adsb) | `:craft/*` `:craft.fix/*` |
| `maps` source DID `did:web:maps.etzhayyim.com:adsb` (OpenSky, 5m TTL) | — | `recordFix` (source=adsb, G7-gated) | `:craft.fix/source :adsb` |
| `vessel` `tracking:ais` component | graph DB `VesselPosition` (graph.write SQL) | `recordFix` (source=ais) | `:craft.fix/*` |
| `vessel` `voyage:manager` + `PortCall` | graph DB `Voyage` / `PortCall` | `recordLeg` | `:craft.leg/*` |
| `vessel` XRPC `com.etzhayyim.apps.vessel.tracking.*` (getVesselPosition / listVesselsInArea / getPositionHistory) | RisingWave-backed read | read path = `kotoba-kqe` arrangements over `:craft.fix/*` (EAVT / AEVT) | — |

## What changed (constitutional)

1. **State store**: RisingWave `vertex_vessel_position` / `vertex_aircraft_state` and the
   `vessel` graph DB → the **kotoba Datom log** (`:craft.fix/*`, content-addressed,
   first-class canonical state per ADR-2605312345). N5 — no SQL / RisingWave.
2. **"Current position"** is no longer a mutable row that is overwritten; it is the
   **latest as-of fix** in an append-only log. The trajectory is the EAVT history (非終末論).
3. **Narration** (the `agent.chat` maritime-summary steps in the legacy vessel manifest) →
   **Murakumo-only** (ADR-2605215000). No off-Murakumo inference in a religious-corp path.
4. **Person-tracking gate (G4, NEW)**: the legacy surfaces had no explicit anti-surveillance
   invariant. watari forbids by construction any de-anonymization of the person behind a
   craft, any pattern-of-life on a private-craft owner, and any "where is person X" query.
   Private yachts / private jets / military / blocked-from-display craft are out of scope (G1).

## Status

R0 design-only. The legacy `maps` / `vessel` pipelines remain as historical reference under
`20-actors/maps/` and `20-actors/vessel/`; they are superseded by watari for any NEW
real-time-position work and will be archived in a follow-up cutover (mirrors the watatsuna
→ legacy-telecom-lexicon retirement pattern, ADR-2606012600).
