# kg-appview

Stages **K2.a + K2.b + K2.c + K3.a** of ADR-2605190900 (Knowledge Graph as Lexicon).

Ephemeral in-memory SPARQL AppView for the etzhayyim Knowledge Graph.

## What it is

- Loads `kg.node` / `kg.edge` records into an
  [OxiGraph](https://github.com/oxigraph/oxigraph) in-memory triplestore from
  any combination of three cold-start sources:
  - `--kg-out <dir>` — a `kg-projector` directory tree (`nodes/*.json` +
    `edges/*.json`). The default behavior; equivalent to K2.a.
  - `--snapshot-file <path>` — a `kg-projector` `bundle.jsonl` (one record
    per line). The K3.a substrate-anchored replay primitive.
  - `--firehose-url <wss://...>` — a Jetstream-format WebSocket emitting
    `com.etzhayyim.kg.*` commits. The K2.c live-update path. Disabled by
    default; reconnects with exponential backoff on disconnect.
- Exposes the resulting graph over:
  - `GET|POST /sparql` — SPARQL 1.1 Protocol endpoint (SELECT / ASK /
    CONSTRUCT / DESCRIBE). UPDATE keywords are rejected with HTTP 403.
  - `GET /xrpc/com.etzhayyim.kg.query` — ATProto XRPC facade with the same
    behavior, conforming to the lexicon at
    `00-contracts/lexicons/com/etzhayyim/kg/query.json`.
- Holds no durable state of its own. On every restart the store is rebuilt
  from the configured sources.

## What it is not (current scope)

- No SPARQL UPDATE. Mutations come from writing `com.etzhayyim.kg.*` records
  to MST; the AppView is read-only by construction.
- No disk-backed cache. RW-free per ADR-2605172000.
- No edge-metadata triples (weight / context / createdAt). The shape is on
  the to-do list and will land via RDF-star or reification in K4.
- K3.b — fetch the snapshot bundle directly from an IPFS gateway URL whose
  CID is resolved from the latest Base L2 anchor — is deferred. The current
  `--snapshot-file` flag accepts a local path that the future
  `ipfs-pinner` module would download into.
- K2.c does not yet resolve rkey → nodeId on `delete` events. Live deletes
  are logged but not applied to the store; the canonical "K2.c+ cache"
  follow-up tracks this.

## IRI mapping

Records → RDF quads using a stable, lossless encoding:

| Source field | RDF target |
|---|---|
| `kg.node.nodeId` (e.g. `urn:adr:2605190900-...`, `lexicon:com.atproto.repo.strongRef`) | IRI `<https://etzhayyim.com/kg/n/{percent-encoded nodeId}>` |
| `kg.node.nodeType` | `<https://etzhayyim.com/kg/v#nodeType>` |
| `kg.node.label` / `summary` / `source` / `createdAt` | `<https://etzhayyim.com/kg/v#label>` etc. |
| each tag in `kg.node.tags` | `<https://etzhayyim.com/kg/v#tag>` (multi-valued) |
| `kg.edge.predicate` (e.g. `depends_on`, `uses-lexicon`, `authoritative-for`) | IRI `<https://etzhayyim.com/kg/p#{predicate}>` |
| `kg.edge.subject` / `object` | node IRI (same encoding as nodeId) |
| `kg.edge.literal` | plain string literal |

A `PREFIX` snippet for queries:

```sparql
PREFIX etzn: <https://etzhayyim.com/kg/n/>
PREFIX etzp: <https://etzhayyim.com/kg/p#>
PREFIX etzv: <https://etzhayyim.com/kg/v#>
```

## Usage

```bash
cargo build --release

# K2.a — directory load
./target/release/kg-appview --kg-out ../kg-projector/out --listen 127.0.0.1:8080

# K3.a — bundle.jsonl replay (disable the default kg-out with `--kg-out none`)
./target/release/kg-appview \
    --kg-out none \
    --snapshot-file ../kg-projector/out/bundle.jsonl \
    --listen 127.0.0.1:8080

# K2.c — bundle as cold start + Jetstream firehose for live updates
./target/release/kg-appview \
    --snapshot-file ../kg-projector/out/bundle.jsonl \
    --firehose-url 'wss://jetstream.example.com/subscribe?wantedCollections=com.etzhayyim.kg.*' \
    --listen 127.0.0.1:8080
```

Smoke-test queries:

```bash
# Count ADR nodes
curl -sG http://localhost:8080/sparql \
  --data-urlencode 'query=PREFIX etzv: <https://etzhayyim.com/kg/v#>
    SELECT (COUNT(?n) AS ?n_adr) WHERE { ?n etzv:nodeType "adr" }'

# List ADRs and what they depend on
curl -sG http://localhost:8080/sparql \
  --data-urlencode 'query=PREFIX etzp: <https://etzhayyim.com/kg/p#>
    PREFIX etzv: <https://etzhayyim.com/kg/v#>
    SELECT ?adr ?dep WHERE {
      ?adr etzv:nodeType "adr" ; etzp:depends_on ?dep
    } ORDER BY ?adr'

# CONSTRUCT the lexicon dependency subgraph
curl -sG http://localhost:8080/sparql \
  -H 'Accept: text/turtle' \
  --data-urlencode 'query=PREFIX etzp: <https://etzhayyim.com/kg/p#>
    CONSTRUCT { ?a etzp:uses-lexicon ?b } WHERE { ?a etzp:uses-lexicon ?b }'

# Same, via the XRPC facade
curl -sG http://localhost:8080/xrpc/com.etzhayyim.kg.query \
  --data-urlencode 'query=…' --data-urlencode 'format=turtle'
```

## Status

- **K2.a** — in-memory load from `kg-projector` directory + SPARQL JSON / XML / CSV ✅
- **K2.b** — CONSTRUCT / DESCRIBE Turtle / N-Triples / RDF/XML + XRPC facade ✅
- **K2.c** — Jetstream-format firehose subscriber (live `com.etzhayyim.kg.*` updates) ✅
- **K3.a** — `bundle.jsonl` snapshot replay (substrate-anchored cold start) ✅
- **K3.b** — fetch bundle from IPFS gateway URL resolved off the L2 anchor — deferred
- **K4** — RDF-star or reification for edge metadata — deferred
- **K5** — federation across third-party DIDs publishing `com.etzhayyim.kg.*` — deferred
