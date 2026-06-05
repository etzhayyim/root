# oil-refining — SUPERSEDED by kamado 竈 (ADR-2606051500)

**Status**: legacy · superseded-not-deleted · do not extend.

This actor (`actor-manifest.jsonld`) is a pre-kotoba **observation/intel** actor. It is
charter-**non-compliant** on two counts and carries no robotics, plant, or construction:

1. **Canonical-state violation** — every pipeline step drives `graph.query` / `graph.write`
   Cypher (`MATCH (r:Refinery) …`, `MERGE (c:ActorCoverageSnapshot …)`), the RisingWave /
   graph-DB pattern prohibited by **ADR-2605262130** (the kotoba Datom log is canonical state).
2. **Legacy identity stack** — `did:web:oil-refining.etzhayyim.com`, `legacyExecutionTier:T1`,
   `operator: etzhayyim.co.jp`, `kyumei-shinka` standard. Not in the Tier-B roster.

## Replacement

**`kamado` 竈** (`20-actors/kamado/`, ADR-2606051500, DID
`did:web:etzhayyim.com:actor:kamado`) is the kotoba-native successor. It keeps the observation
surface (refinery / unit / outage registry + transition-readiness, as an as-of history on the
Datom log — a **resilience+transition map, never a target-list**) and adds the two faces this
legacy actor lacked:

- **§2(d) decommission / transition robotics** for existing fossil assets (wind down / remediate /
  convert → hikari / synthesis plant / hodoki+kanayama);
- **closed-loop synthetic refining** on biogenic / captured-CO₂ / recycled carbon only
  (net atmospheric carbon Δ ≤ 0; `:fossil-virgin-crude` is unrepresentable by construction).

## Field mapping (legacy Cypher → kamado kotoba EAVT)

| legacy (`oil-refining`) | kamado |
|---|---|
| `(:Refinery)` node | `:refinery/*` (`com.etzhayyim.kamado.refineryAsset`) |
| `(:RefineryUnit)` node | `:unit/*` (`com.etzhayyim.kamado.refineryUnit`) |
| `(:RefineryOutage)` node | `:outage/*` (as-of history, non-mutating) |
| `(:ActorCoverageSnapshot)` `MERGE` | derived datoms via `methods/analyze.py` (`:derived`) |
| `com.etzhayyim.apps.oilRefining.*` XRPC | superseded by kamado cells + offline analyzer |

Migration of any live data follows the **watari** precedent (ADR-2606041827): the legacy manifest
is retained for reference until a dedicated cutover PR removes it; no new work should target it.
