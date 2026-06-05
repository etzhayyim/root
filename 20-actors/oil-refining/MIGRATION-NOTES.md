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

## Executable migration bridge (legacy graph → kotoba EAVT)

The ETL is implemented (watari `ingest.py` precedent):

```
20-actors/kamado/methods/ingest.py            # legacy node export → kotoba EAVT + kg.ingest_batch
20-actors/kamado/data/ingest/legacy-oil-refining-export.sample.json   # Cypher-node-shaped sample
```

Run (offline, `:representative`):

```
cd 20-actors/kamado/methods
python3 ingest.py --export ../data/ingest/legacy-oil-refining-export.sample.json
# → out/refinery-graph.migrated.kotoba.edn   (kotoba EDN, dedup vs seed — seed identity wins)
# → out/oil-refining-kotoba-batch.json       (kg.ingest_batch body: 12 entities/claims/relations)
```

A real RisingWave dump (`apoc.export.json` / cypher-shell of the `MATCH (r:Refinery)…` nodes)
drops into `--export` unchanged. The bridge enforces **G4** (operator must be an `org.corp.*` id —
a refinery is never a person; person fields are refused), **G1** (migrated assets are
`:observed-fossil` — observation, not a `:synthesis` record, so `feedstock_guard` is never
bypassed), and **G7** (`:representative`).

## Promotion to live KV / kotoba (operator-gated, G8)

Live kotoba endpoint VERIFIED 2026-06-05: **`https://kotobase.net`** (gftd kotobase,
`did:web:kotobase.net`, etzhayyim/kotoba upstream; `/health` ok). The KG ingest surface is
`POST https://kotobase.net/xrpc/ai.gftd.apps.kotobase.kg.ingest_batch` `{entities:[...]}` —
a **tenant write** (`sub == tenant_did`), `Authorization: Bearer <JWT>`. The JWT is issued by
the gftd auth service `authn.gftd.ai` (its `sub` is the tenant DID); `datomic.transact` is
operator-only and not used. `ingest.py` already emits the live `{id, type, label_en, claims,
relations}` entity contract.

Two independent surfaces, both Council Lv6+ + operator gated:

1. **Domain data** (refinery/unit/outage) → the refining graph — one command:
   ```
   KOTOBA_JWT=<bearer> python3 20-actors/kamado/methods/ingest.py --push
   ```
   (refused with a G8 message if `KOTOBA_JWT` is unset). Live legacy *read* from a RisingWave
   dump is the separate `ingest.py --live` path (refused unless `KAMADO_OPERATOR_GATE=1`).
2. **Actor-profile identity** (already wired in the publisher):
   `node 50-infra/etzhayyim-did-web/scripts/publish-actor-records.mjs --actor kamado --put-kv --ingest-kotoba`
   → CF KV `actor:kamado` + the `actors-v1` graph. NOTE: the publisher still targets the
   internal `com.etzhayyim.apps.kotobase.*` nsid with a `kind` field; pointing it at the live
   gftd `ai.gftd.apps.kotobase.*` + `type` contract is a shared-infra follow-up (the kamado
   domain bridge above is already on the live contract).

Until an operator runs the above, the apex Worker serves kamado from the compiled `INFRA_ACTORS`
fallback (3-tier fail-open KV → kotoba → compiled), so `/actor/kamado/did.json` resolves today.

The legacy manifest is retained for reference until a dedicated cutover PR removes it (watari
precedent); no new work should target it.
