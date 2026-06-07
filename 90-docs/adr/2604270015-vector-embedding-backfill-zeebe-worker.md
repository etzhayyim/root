---
id: adr-2604270015-vector-embedding-backfill-zeebe-worker
title: Vector Embedding Backfill via Zeebe Python Worker
status: active
doc_type: adr
topic: search
authoritative: true
last_verified: 2026-04-27
authoritative_for:
  - actor-profile-embedding-backfill
  - bluesky-post-embedding-backfill
  - vector-embedding-zeebe-worker-contract
related:
  - adr-2604262359-kotoba-multimodal-vector-search-topology
  - adr-0074-ethereum-identity-bridge-cacao-webauthn
  - adr-2604262100-erc725-erc8004-k8s-ipfs-agent-runtime
  - adr-2604261900-kotoba-ddl-backfill-path-topology
  - adr-2604262000-edge-thin-app-runtime-k8s-zeebe-registry
supersedes: []
superseded_by: []
---

# Context

`etzhayyim-project-vector-embedding` now has the Kotoba/Datomic schema for Phase 1
768-dimensional search embeddings:

- `vertex_vector_embedding_source`
- `vertex_vector_embedding_768`
- `vertex_vector_embedding_model`
- `vertex_vector_embedding_space`
- `vertex_vector_embedding_projection`

The first production surfaces are actor profiles and Bluesky posts. Both are
public text surfaces and can use BGE-M3-derived 768d embeddings before image,
video, audio, and sensor adapters are introduced.

# Decision

Actor/profile and post embedding backfill is a Zeebe-orchestrated Python worker
path, not a direct CronJob-to-Kotoba/Datomic loop.

The initial task contract is:

| Zeebe task type                 | Input                                   | Output                                                |
| ------------------------------- | --------------------------------------- | ----------------------------------------------------- |
| `vectorEmbedding.backfillBatch` | `surface`, `limit`, `shardId`, `dryRun` | `surface`, `planned`, `written`, `modelId`, `spaceId` |

`surface` accepts `actors` or `posts`.

The task performs one bounded batch:

1. Select candidates that do not already have `vertex_vector_embedding_768`
   rows for `(source_uri, model_id='bge-m3', space_id='etzhayyim-mm-768')`.
2. Build source text:
   - actor profile: display name, handle, description, ERC725 root DID,
     facade DID, kind;
   - post: text, embed alt text, handle, source URI.
3. Generate or receive native model embeddings.
4. Project to 768d and L2-normalize.
5. Insert source metadata into `vertex_vector_embedding_source` if missing.
6. Insert embedding row into `vertex_vector_embedding_768` if missing.

The BPMN process repeats this task while `planned > 0`, with a small batch size
and normal Zeebe retry/backoff. It must call `rw.health.probe` before write
batches in production.

The first BPMN artifact is intentionally one-batch:

- `etzhayyim-root/00-contracts/bpmn/com/etzhayyim/vector-embedding/backfillBatch.bpmn`

K8s CronJobs start repeated one-batch instances for each surface. They are
suspended by default:

- `yoro-vector-embedding-actors`
- `yoro-vector-embedding-posts`

## Actor Identity Key

Actor profile embeddings are keyed by the canonical ERC725 root DID, not by an
AT Protocol facade DID.

For actor rows:

- `source_uri = 'actor:' || root_did`
- `source_vertex_id = root_did`
- `repo = facade_did` when a facade is available

`did:web` and `did:plc` remain federation/profile facades. They may be used for
display, AT repo lookup, and profile enrichment, but must not be treated as the
canonical vector identity key. This follows ADR-0074 and ADR-2604262100.

The current production predicate is:

```sql
root_did LIKE 'did:erc725:etzhayyim:260425:%'
```

The AppView actor HNSW path likewise filters `source_uri` to
`actor:did:erc725:etzhayyim:260425:%` and joins `view_actor_unified` by
`v.root_did = e.source_vertex_id` for facade/profile display fields.

# Runtime

The Python implementation lives in:

- `20-actors/magatama/py/src/pymagatama/primitives/vector_embedding.py`
- `20-actors/magatama/py/src/pymagatama/vector_embedding_worker_main.py`
- `50-infra/multicluster/murakumo-vke/yoro-actors/vector-embedding-worker.yaml`

The module lazy-loads `sentence-transformers` only when the task runs. Local
and test environments can set `VECTOR_EMBEDDING_FAKE=1` to generate
deterministic hash vectors without torch.

Default model settings:

- `VECTOR_EMBEDDING_TEXT_MODEL=BAAI/bge-m3`
- `model_id=bge-m3`
- `projection_id=bge-m3-to-etzhayyim-mm-768`
- `space_id=etzhayyim-mm-768`

# Consequences

- Backfill is resumable because rows are idempotent on `embedding_id` and
  candidate selection excludes already embedded source URIs.
- Backfill pressure is bounded by Zeebe batch size and worker replica count.
- Search can move from the old 384d post-only read model to the shared 768d
  table without mixing vector dimensions.
- Actor semantic search now returns ERC725 root DIDs for semantic hits while
  keeping facade handles for display. Legacy facade-keyed actor embedding rows
  can remain in storage but are excluded from the HNSW actor search path.
- The same table can later receive Qwen3-VL, OpenCLIP, CLAP/transcript, and
  sensor adapter rows by changing `model_id` and `projection_id`.

# Operational Status

Verified on 2026-04-27:

- worker image:
  `ghcr.io/etzhayyim/pymagatama:yoro-vector-embedding-20260427-search768d-amd64`
- AppView version:
  `3f5dd746-87e0-4da1-9a88-e5f91ec2a009`
- yoro actor root:
  `did:erc725:etzhayyim:260425:0xe506d815690ab0b81bf2f34b5057d7b8b96fe643`
- yoro facade:
  `did:web:yoro.etzhayyim.com`
- live counters after the first ERC725 actor backfill:
  `view_root_erc725=1`, `edge_actual_yoro=1`,
  `embedding_erc725_actor=1`

# Alternatives Considered

- Direct SQL/UDF embedding in Kotoba/Datomic. Rejected for corpus backfill because
  model inference and API calls should not run inside query execution.
- One large Python script that scans all actors/posts. Rejected because retry,
  cursor state, and RW health gating belong in Zeebe.
- Continue using `vertex_bluesky_post_embedding` only. Rejected because it is
  384d/post-specific and does not support actor, media, or future sensor reuse.

# References

- `60-apps/etzhayyim-project-vector-embedding/README.md`
- `20-actors/magatama/py/src/pymagatama/primitives/vector_embedding.py`
- Kotoba/Datomic vector indexes: https://docs.kotoba.com/processing/vector-indexes
