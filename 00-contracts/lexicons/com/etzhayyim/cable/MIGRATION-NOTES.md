# `com.etzhayyim.cable.*` — kotoba-native cable lexicons + legacy migration inventory

**ADR-2606012600 · actor: watatsuna 綿津綱**

The `com.etzhayyim.cable.*` namespace is the **kotoba-native** home for the world
submarine-cable knowledge graph. It supersedes seven legacy `etzhayyim`-namespaced lexicons
that were authored against the (now-deprecated) RisingWave vertex/instanceKey model. The
new lexicons assert into the **kotoba Datom log** (`txCid` + `datomCount`; ADR-2605312345),
not a SQL vertex store, and carry **sourcing-honesty** (`:sourcing`) on every record.

## New lexicons (this directory)

| Lexicon | Asserts | kotoba vocab |
|---|---|---|
| `registerCableSystem` | a cable system | `:cable/*` |
| `registerLandingStation` | a landing station | `:station/*` |
| `registerSegment` | landing sequence → incidence + segments | `:cable.link/*`, `:cable.seg/*` |
| `flagCableFault` | observed public fault bulletin (as-of history) | `:cable.fault/*` |

Vocabulary: [`00-contracts/schemas/submarine-cable-ontology.kotoba.edn`](../../../../../schemas/submarine-cable-ontology.kotoba.edn).

## Legacy → kotoba-native mapping (inventory of every cable lexicon found)

| Legacy lexicon (`com.etzhayyim.apps.*`) | Disposition | Maps to | Notes |
|---|---|---|---|
| `telecom.registerSubmarineCableSystem` | **superseded** | `cable.registerCableSystem` | `ownerOrgId`→`ownerConsortium[]`; `vertexId`/`instanceKey`→`txCid`/`datomCount`; adds `:sourcing` |
| `telecomInfra.registerCable` | **superseded** | `cable.registerCableSystem` | `landingPointsIso3` (CSV) → register stations + `registerSegment.landingSequence`; `capacityTier` derived, not stored raw |
| `telecom.recordSubmarineCableRepair` | **superseded** | `cable.flagCableFault` | `faultKind` enum folded into `kind`; `routeSegmentId`→`segmentId`; `vesselRef`→`repairVessel` |
| `telecomInfra.flagCableFault` | **superseded** | `cable.flagCableFault` | `faultType` enum folded into `kind`; `severityTier` (state_sponsored) **dropped** — watatsuna G4 forbids intent adjudication; `cyberIncidentVid` bridge deferred to a separate observation actor |
| `cableRepairFleet.registerRepairVessel` | **moved to watatsumi** | `watatsumi/data/cable-laying-fleet.kotoba.edn` + (future) `com.etzhayyim.watatsumi.cableLayVesselAttestation` | repair/lay fleet is operational → belongs to watatsumi 綿津見, not the KG actor |
| `cableRepairFleet.logRepairMission` | **moved to watatsumi** | watatsumi cable-laying fleet ops | operational mission log; watatsumi side |
| `cableRepairFleet.flagSubseaCableTamper` | **RETIRED (not ported)** | — | "tamper/妨害 flag" presumes intent adjudication → violates watatsuna **G4** + reads as an interdiction-adjacent signal. Faults are recorded neutrally via `flagCableFault` with the bulletin's own `:kind` only. |

## Why `flagSubseaCableTamper` is retired (constitutional)

watatsuna does **not** adjudicate sabotage. A "tamper flag" lexicon asserts an actor's
intent classification, which (a) watatsuna has no standing to determine, and (b) drifts
toward an interdiction/target framing that **watatsumi N8** + **Charter Rider §2(d)**
prohibit. Cable disruptions are recorded only as neutral fault bulletins whose `:kind`
mirrors the *public source's own* wording (e.g. `under_investigation`). Determination of
sabotage is a state matter, surfaced — if at all — by `danjo`/`tadori` from public record,
never asserted here.

## Migration status

- **R0 (this ADR)**: new lexicons authored; legacy lexicons **left in place** (no deletion)
  with this inventory as the SoT for the cutover. Per repo-root `CLAUDE.md` §Do-Not, the
  legacy `etzhayyim-` rename/removal executes as one atomic wave, not piecemeal.
- **R1+**: any live caller migrates to `com.etzhayyim.cable.*`; legacy lexicons then archived.
