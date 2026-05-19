# kg-appview

Stage **K2.a** of ADR-2605190900 (Knowledge Graph as Lexicon).

Ephemeral in-memory SPARQL AppView for the etzhayyim Knowledge Graph.

## What it is

- Loads `kg.node` / `kg.edge` records (emitted by `@etzhayyim/kg-projector` into
  `30-graph/kg-projector/out/`) into an [OxiGraph](https://github.com/oxigraph/oxigraph)
  in-memory triplestore.
- Exposes the resulting graph over a SPARQL 1.1 Protocol endpoint at
  `GET|POST /sparql`.
- Holds no durable state of its own. On every restart the store is rebuilt
  from `out/` (and, in K2.c, from the PDS firehose).

## What it is not (K2.a scope)

- No SPARQL UPDATE. Mutations come from writing `app.etzhayyim.kg.*` records
  to MST; the AppView is read-only by construction.
- No disk-backed cache. RW-free per ADR-2605172000.
- No Jetstream firehose subscriber yet (K2.c).
- No cold-start IPFS replay yet (K3).
- No XRPC facade yet (K2.b).

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
| `kg.edge.context` | quad graph name (named-graph IRI under the same `kg/n/` prefix) |

A `PREFIX` snippet for queries:

```sparql
PREFIX etzn: <https://etzhayyim.com/kg/n/>
PREFIX etzp: <https://etzhayyim.com/kg/p#>
PREFIX etzv: <https://etzhayyim.com/kg/v#>
```

## Usage

```bash
cargo build --release
./target/release/kg-appview \
    --kg-out ../kg-projector/out \
    --listen 127.0.0.1:8080
```

Then:

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
```

## Status

K2.a — **in-memory + SPARQL only**. K2.b (XRPC facade), K2.c (firehose
subscription), K3 (cold-start IPFS replay) are follow-up PRs.
