# Seibutsu (生物) — Biological Entities as Actors

Living taxa and observed individuals as DID-addressed actors. Procedural-generation profiles (`com.etzhayyim.apps.seibutsu.traits`) feed `kami-vegetation` engine 1:1.

## Runtime

| key | value |
|---|---|
| domain | `seibutsu.etzhayyim.com` |
| primary DID | `did:plc:seibutsu` (self-hosted via `plc.etzhayyim.com`, ADR-0019/0014) |
| performerType | `service` |
| Language | TypeScript (TS Native) |
| Build | `etzhayyim deploy` |
| Architecture | Design E (3-Tier Write, reactive) |
| Data store | RisingWave via PDS / Hyperdrive |

## Identity model (ADR-0019)

- **Taxon actor** = `did:plc:*`, handle `{slug}.seibutsu.etzhayyim.com` (e.g. `bamboo.seibutsu.etzhayyim.com`).
- **Individual actor** = path-based DID `did:plc:seibutsu:individual:{tid}` for tracked specimens.
- No nanoid usage. NSID = `com.etzhayyim.apps.seibutsu.*` (4-segment, ADR-0019).
- 1 project = N actor DIDs (taxa + individuals), scoped by `projectId = did:plc:seibutsu`.

## Linnaean → DID graph

```
domain → kingdom → phylum/division → class → order → family → genus → species → individual
                                                                          ↓ hasParent edge
```

Hierarchy is edge-only (`graphar.edge_hasParent`). Records do not nest.

## Lexicons (`00-contracts/lexicons/com/etzhayyim/apps/seibutsu/`)

| NSID | type | role |
|---|---|---|
| `com.etzhayyim.apps.seibutsu.taxon` | record | rank + scientific name + GBIF/NCBI/Wikidata cross-refs |
| `com.etzhayyim.apps.seibutsu.traits` | record | procedural profile (kami-vegetation TaxonomicProfile mirror) |
| `com.etzhayyim.apps.seibutsu.observation` | record | individual sighting (geo-h3, image, observer) |
| `com.etzhayyim.apps.seibutsu.getProfile` | query | DID → taxon + traits + lineage chain |
| `com.etzhayyim.apps.seibutsu.renderProfile` | query | DID → engine-ready TaxonomicProfile JSON |

## Kotodama capabilities

- `kotodama:bio/taxonomy` — Linnaean traversal, Wikidata/GBIF sync
- `kotodama:bio/traits` — taxonomy → procedural traits derive
- `kotodama:bio/identify` — image → species (Murakumo fleet inference)
- Host imports: `kagami` (graph), `app.bsky.feed.post` (sighting broadcast — derive rule)

## Write-Only Derived rules

handler は `taxon` / `traits` / `observation` の `writePublic()` のみ。`kotodama.jsonld` の `derive` で:

| trigger | derives |
|---|---|
| `observation.create` | `app.bsky.feed.post` (sighting summary, posted as `observerDid`) |
| `taxon.create` (rank=species, new) | `conversation.invoke(researcher-bio-gene, lookupGenome)` |
| `traits.create` | `kami-vegetation` cache invalidation event (stream-out) |

## kagami graph schema

```
graphar.vertex_taxon(did, rank, scientific_name, authority, gbif_id, ncbi_id, wikidata_qid)
graphar.vertex_individual(did, taxon_did, geo_h3, observed_at)
graphar.edge_hasParent(child_did, parent_did)
graphar.edge_synonymOf(did_a, did_b)
graphar.edge_observedBy(individual_did, observer_did)
```

PII = none (taxa public). Observer DID is plaintext (Tier 1 social context).

## Engine integration

`kami-vegetation::taxonomy::TaxonomicProfile` ↔ `traits` record 1:1. `renderProfile` query lets isekai / quarry scenes resolve a real species DID before instancing — procedural geometry anchored to biological reality.

## Seed catalog (PoC)

7 preset taxa from `40-engine/kami-engine/kami-vegetation/src/taxonomy.rs`:
grass / fern / palm / conifer / bush / cactus / moss. See `seed/preset-taxa.json`.

## Related projects

| project | relation |
|---|---|
| `researcher-bio-gene` | cross-actor peer (genomic enrichment) |
| `anima` | sibling for animal-side (future merge candidate) |
| `kami-sabiotoshi` | downstream consumer (ecosystem game references seibutsu DIDs) |

## Build & deploy

```bash
cd 60-apps/etzhayyim-project-seibutsu/appview/etzhayyim-wasm-seibutsu-s3ibtsu1
etzhayyim deploy
curl https://seibutsu.etzhayyim.com/health
```

## Bring-up runbook (PoC)

### 1. Worker (`src/app.ts`)

5 commands wired (`getProfile`, `renderProfile`, `taxon`, `traits`, `observation`)
+ reactive `onCommit` for `com.etzhayyim.apps.seibutsu.*`. Reads via Kysely against
`graphar.vertex_seibutsu_taxon` / `graphar.vertex_seibutsu_traits`. Writes via
`com.atproto.repo.createRecord` (Design E Tier 2).

### 2. Seed (`seed.ts`)

```bash
etzhayyim_TOKEN=$(etzhayyim authn token) \
PDS=https://atproto.etzhayyim.com \
ROOT_DID=did:plc:seibutsu \
npx tsx 60-apps/etzhayyim-project-seibutsu/seed.ts
```

Loads the 7 preset taxa from `seed/preset-taxa.json` — registers each as an
actor + writes one `taxon` and one `traits` record per species. Also creates
parent kingdom/division actors so `hasParent` resolves.

### 3. Mint did:plc (ADR-0014)

`seibutsu` is registered in `deps.toml [[mitama_actors]]` with placeholder
`did:plc:pending`. Mint the real DID via `plc.etzhayyim.com`:

```bash
# preview
etzhayyim actors migrate-to-plc --actor seibutsu --offline

# real (PDS signs genesis op with rotation key from D1, ADR-0010)
etzhayyim actors migrate-to-plc --actor seibutsu --apply

# verify
etzhayyim identifier-audit --deps deps.toml | grep seibutsu
```

After `--apply`, deps.toml `did = "did:plc:pending"` is rewritten to the
24-char base32 identifier returned from `plc.etzhayyim.com`, and `kotodama.jsonld`
`@id` should be updated to match (and `seed.ts` `ROOT_DID` env).

### 4. kami-vegetation bridge

`40-engine/kami-engine/kami-vegetation/src/taxonomy.rs` exposes:

- `OwnedTaxonomicProfile::from_json_str(json)` — parses a single
  `seibutsu.renderProfile` response (camelCase)
- `RemoteCatalog::from_default()` — same 7 presets but owned (heap-allocated
  `common_name` so dynamic species names are allowed)
- `RemoteCatalog::push_json(json)` — append a remote profile

Browser shell (`kami-web`) flow:

```js
const res = await fetch(`https://atproto.etzhayyim.com/xrpc/com.etzhayyim.apps.seibutsu.renderProfile?did=${did}`);
const json = await res.text();
catalog.push_json(json);   // WASM call
```

Tests: `cargo test -p kami-vegetation` (6 pass, incl. `remote_catalog_round_trip`).
