# @etzhayyim/kg-projector

Stage **K1** of ADR-2605190900 (Knowledge Graph as Lexicon).

Projects the etzhayyim/root SSoTs into `com.etzhayyim.kg.{node,edge}` records as plain JSON files. A later
stage will write these records to the PDS / MST.

## What it reads

| Source | Layer | Emits |
|---|---|---|
| `90-docs/adr/*.md` front-matter | ADR graph | `kg.node` per ADR + edges (`depends_on` / `related` / `supersedes` / `superseded_by` / `authoritative-for`) |
| `00-contracts/lexicons/**/*.json` | Lexicon graph | `kg.node` per lexicon definition |
| `deps.toml` `[platform.operating_entity]` + `[platform.l2.*]` | Platform graph | Org node + L2-contract nodes + `owns` edges |

The set of sources is intentionally minimal in v1 (K1). Module manifests, capability lexicons, and DNS
records are deferred to K1.x follow-ups.

## What it writes

```
out/
├── nodes/
│   └── <rkey>.json     # one file per kg.node record
├── edges/
│   └── <rkey>.json     # one file per kg.edge record
└── manifest.json       # node_count / edge_count / source_counts / content_hash / generated_at
```

`<rkey>` is a **deterministic** 13-character base32 string derived from a canonical projection of the
record's identifying fields (`nodeType|nodeId` for nodes; `subject|predicate|object|literal` for edges).
Same input → same rkey → same path. This makes the projection idempotent and CI-checkable.

The `manifest.json` `content_hash` is the SHA-256 of the sorted list of `<rkey> <sha256(body)>` lines —
one stable scalar that summarizes the entire projection state. CI compares it against the committed value.

## Usage

```bash
pnpm install
pnpm dev project           # write out/ from current SSoTs
pnpm dev project --check   # exit non-zero if a fresh projection differs from out/manifest.json
```

Add `--repo-root <path>` to point at a different monorepo checkout (defaults to two levels up from this
package — i.e. the `etzhayyim/root` repo root).

## kotoba guarantee

This package has **no** dependency on RisingWave / Postgres / Kysely / any centralized database. Its only
runtime dependencies are `smol-toml` and `yaml` (pure-JS parsers). Per ADR-2605172000 the projector lives
in `30-graph/` only because that is the architectural home for KG tooling; it explicitly does not share
the substrate of `30-graph/graph-schema` (which is RW-bound and out of scope for the open monorepo).

## Status

Stage K1 — **JSON-file output only**. MST write, firehose subscription, and SPARQL AppView are
follow-up PRs (K1.5 → K2). The output of this projector is the input contract those stages will consume.
