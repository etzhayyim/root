---
id: adr-2604262359-risingwave-multimodal-vector-search-topology
title: RisingWave Multimodal Vector Search Topology
status: active
doc_type: adr
topic: search
authoritative: true
last_verified: 2026-05-01
authoritative_for:
  - yoro-search-vector-topology
  - risingwave-multimodal-search-topology
  - actor-post-media-search-embedding-model
  - 2b-10b-vector-search-query-shape
  - sensor-modality-embedding-roadmap
related:
  - adr-0002-persistence-risingwave-only
  - adr-0074-ethereum-identity-bridge-cacao-webauthn
  - adr-0028-cohort-mv-sharding
  - adr-0044-risingwave-udf-language-strategy
  - adr-0081-worker-direct-hyperdrive-persistence
  - adr-0094-risingwave-stable-three-node-topology
  - adr-2604261900-risingwave-ddl-backfill-path-topology
  - adr-2604270015-vector-embedding-backfill-zeebe-worker
supersedes: []
superseded_by: []
---

# Context

`https://yoro.etzhayyim.com/search` needs low-latency search across actors, posts,
and later text/image/audio/video/PDF media. The older actor search path used
lexical predicates over actor views, and the older post semantic path used a
384-dimensional HNSW index over `vertex_bluesky_post_embedding`. Production
search is migrating to the shared 768-dimensional vector tables introduced for
multimodal search: `vertex_vector_embedding_source` and
`vertex_vector_embedding_768`.

At the target scale of 2B-10B records, two constraints dominate the design:

- raw vector storage is already terabytes to tens of terabytes before index
  overhead;
- no single RisingWave vector index should be treated as the global search
  engine for all tenants, modalities, and time ranges.

RisingWave's official vector index support is `FLAT` and `HNSW`. The official
docs do not expose IVF. `FLAT` is exact but scans the candidate set. `HNSW` is
approximate and suitable for large candidate sets, but it adds graph memory and
build overhead. Therefore the topology must combine lexical/token routing,
sharding, hot/cold tiering, HNSW, exact rerank, and caching.

# Decision

Use a hybrid multimodal search topology:

1. User-facing search must return lexical/prefix/token results first.
2. Semantic vector search runs in parallel or as a second phase and merges into
   the visible result set.
3. Multimodal embeddings are generated outside RisingWave by workers or batch
   jobs, then stored as `VECTOR(n)` in append-only RisingWave tables.
4. RisingWave `openai_embedding()` may be used for low-volume text query
   embedding or demos, but not for corpus-scale embedding generation.
5. Embedded Python/Rust/JavaScript UDFs are not used for LLM or multimodal
   embedding inference. They may be used only for lightweight normalization,
   tokenization, hashing, or scoring.
6. The default production embedding dimension is 768 for unified multimodal
   vectors. Higher dimensions require an explicit quality/cost exception.
7. `HNSW` is the default RisingWave vector index for hot semantic search.
   `FLAT` is allowed only for exact rerank or small prefiltered candidate sets.
8. Actor semantic search uses the ERC725 root DID as the canonical vector
   identity key. `did:web` and `did:plc` are AT Protocol facade/profile keys
   and must not be used as canonical actor embedding keys.

## Embedding Model

Prefer a single unified embedding space for text, images, audio, video, and
documents so that text-to-image, image-to-text, audio-to-text, and mixed media
search use the same vector column and distance operator.

| Provider          | Model                              | Modalities                                                                | Production role                                                        |
| ----------------- | ---------------------------------- | ------------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| Google Gemini API | `gemini-embedding-2`               | text, image, video, audio, PDF                                            | default candidate for unified multimodal search                        |
| Amazon Bedrock    | Amazon Nova Multimodal Embeddings  | text, documents, image, video, audio                                      | acceptable when Bedrock is the deployment boundary                     |
| Voyage AI         | `voyage-multimodal-3.5`            | text and visual-rich content, including screenshots and video-like inputs | acceptable for document/screenshot-heavy RAG                           |
| Cohere            | Embed v4 / multimodal embed family | text and images                                                           | acceptable for text-image only surfaces                                |
| Google Gemma      | EmbeddingGemma                     | text only, 768d                                                           | acceptable for local/open text retrieval, not native multimodal search |

The first production implementation should use `gemini-embedding-2` at
768 dimensions unless provider, privacy, or cost constraints require another
model. Do not mix embeddings generated by different models, versions, prompts,
or dimensions in one vector index.

## Sensor Modality Roadmap

The current production pipeline is text-first. The schema is sensor-ready
(`modality`, `media_type`, `sample_rate_hz`, `sensor_vendor`, `sensor_model`,
`sensor_frame`, `captured_at`, `metadata_json`, and chunk-level
`sensor_axis_json`), but non-text sensors are **planned adapters**, not
production-complete embedding paths.

All sensor adapters must write into the same normalized contract:

- `vertex_vector_embedding_source` stores source-level provenance, device
  metadata, capture time, visibility, and consent/safety labels;
- `vertex_vector_embedding_chunk` stores time windows, frame windows, bounding
  boxes, axis/channel metadata, and normalization metadata;
- `vertex_vector_embedding_768` stores only projected, L2-normalized
  `etzhayyim-mm-768` vectors;
- raw samples, point clouds, images, or time series stay in blob/object storage
  or domain tables and are referenced by `blob_ref`, `source_vertex_id`, and
  `metadata_json`.

Planned modality coverage:

| Group | Inputs | Planned modality labels | Adapter status |
| ----- | ------ | ----------------------- | -------------- |
| Motion / location | IMU accelerometer, IMU gyroscope, GPS, UWB | `imu`, `motion_timeseries`, `position`, `uwb_position` | planned |
| 3D / perception | LiDAR point cloud, depth camera, radar | `pointcloud`, `depth`, `radar` | planned |
| Thermal / visual | thermal camera, RGB/depth-derived pose | `thermal`, `image`, `pose` | planned; image path lands first |
| Biomedical | ECG, EEG, EMG, GSR, respiration | `ecg`, `eeg`, `emg`, `gsr`, `respiration` | planned; requires explicit consent and higher sensitivity defaults |
| Environment | VOC/gas/smell, temperature, humidity, light, UV, sound pressure | `gas_voc`, `environment_timeseries`, `audio_level` | planned |
| Behavior | pose, gait, eye tracking, touch, pressure | `pose`, `gait`, `eye_tracking`, `touch_pressure` | planned; biometric/behavioral policy gate required |

Implementation phases:

1. **Phase S0: registry only** — keep model/space rows and table columns in
   place. No product surface may claim sensor embedding support from registry
   metadata alone.
2. **Phase S1: media-adjacent adapters** — add image, depth, thermal, and
   audio-derived embeddings where existing multimodal models already provide
   native support or stable projections.
3. **Phase S2: motion and spatial adapters** — add IMU, GPS/UWB, LiDAR
   point-cloud, and radar encoders with explicit windowing, coordinate frame,
   calibration, and unit metadata.
4. **Phase S3: biomedical and behavioral adapters** — add ECG/EEG/EMG/GSR,
   respiration, gait, eye-tracking, touch, and pressure only after consent,
   sensitivity, retention, and audit gates are implemented.
5. **Phase S4: cross-modal retrieval** — allow routed search across text,
   image, audio, spatial, biomedical, environmental, and behavioral vectors
   only after per-modality quality metrics and false-match risk are measured.

Sensor embeddings must not be inserted with `model_id=bge-m3`. Each adapter
needs an explicit `model_id`, `projection_id`, source dimension, target
dimension, normalization rule, and evaluation record in
`vertex_vector_embedding_model` and `vertex_vector_embedding_projection`.
ImageBind-class models may be used as research baselines, but production use
requires license clearance and modality-specific quality evaluation.

## Table Shape

Use append-only embedding tables partitioned by search surface, tenant/shard,
modality, and freshness. Do not build one global table/index for every record.

```sql
CREATE TABLE media_embedding_hot (
  shard_id INT,
  tenant_id VARCHAR,
  item_id VARCHAR,
  uri VARCHAR,
  modality VARCHAR,
  lang VARCHAR,
  created_at TIMESTAMPTZ,
  text_preview VARCHAR,
  emb VECTOR(768),
  PRIMARY KEY (shard_id, item_id)
) APPEND ONLY;
```

```sql
CREATE INDEX media_embedding_hot_hnsw_768
ON media_embedding_hot
USING HNSW (emb)
INCLUDE (item_id, uri, modality, lang, created_at, text_preview)
WITH (
  distance_type = 'cosine',
  m = 16,
  ef_construction = 200
);
```

Separate tables or materialized views are preferred when a filter is part of
the routing key:

- `actor_embedding_hot`
- `post_embedding_hot`
- `media_embedding_image_hot`
- `media_embedding_audio_hot`
- `media_embedding_video_hot`
- `media_embedding_cold_daily_*` or equivalent cold-tier projections

This avoids asking one HNSW graph to absorb all tenant, modality, and time
filtering after retrieval.

## Production 768d Table

The first deployed implementation uses the normalized graph table pair:

- `vertex_vector_embedding_source`
- `vertex_vector_embedding_768`

Actor profile rows use:

```text
source_kind      = actor_profile
source_uri       = actor:did:erc725:etzhayyim:260425:<identity>
source_vertex_id = did:erc725:etzhayyim:260425:<identity>
repo             = did:web:* or did:plc:* facade when available
space_id         = etzhayyim-mm-768
model_id         = bge-m3
projection_id    = bge-m3-to-etzhayyim-mm-768
```

Bluesky post rows keep the AT URI as `source_uri` and `vertex_bluesky_post`
metadata as source context. Both actor and post surfaces share `VECTOR(768)`
but are filtered by `source_kind`, `space_id`, `model_id`, and modality.

## Query Shape

For text search, run lexical/token and semantic paths together:

```sql
SET batch_hnsw_ef_search = 80;

SELECT
  item_id,
  uri,
  modality,
  text_preview,
  emb <=> $1::VECTOR(768) AS distance
FROM media_embedding_hot
WHERE shard_id = $2
  AND tenant_id = $3
  AND created_at >= now() - interval '90 days'
ORDER BY emb <=> $1::VECTOR(768)
LIMIT 50;
```

The application must not issue global semantic search without a shard, tenant,
cohort, time window, or other routing predicate. For public/global search, the
router expands to a bounded set of hot shards, collects top-k from each shard,
then reranks.

The live Yoro actor search path runs lexical actor lookup first and uses 768d
HNSW as a semantic refinement path when the request supplies a 768-dimensional
query vector. It filters actor HNSW rows to
`actor:did:erc725:etzhayyim:260425:%` and joins `view_actor_unified` on `root_did`
to recover facade handle/display fields.

For image search:

```text
image bytes -> embedding worker -> VECTOR(768) -> routed HNSW search
```

For audio search:

```text
audio chunk -> embedding worker -> VECTOR(768) -> routed HNSW search
audio chunk -> transcript -> token/lexical search
```

Audio and video records should store both native multimodal embeddings and
derived text/transcript features. Native embeddings preserve visual/audio
semantics; transcripts provide exact term recall, names, quotes, and debugging
visibility.

## Ranking

Final ranking uses at least these signals:

- lexical exact/prefix/token match;
- semantic distance from the routed HNSW query;
- recency;
- actor/social authority or graph-local trust signal;
- modality-specific quality signals;
- safety and visibility policy.

HNSW distance alone is not a product ranking function. It is a candidate
retrieval signal.

# Consequences

- Search can show fast lexical results while semantic retrieval is still
  running, reducing perceived latency.
- Corpus embedding generation moves out of RisingWave and into resumable batch
  or worker infrastructure.
- Re-embedding is required when the embedding model, output dimension, or
  prompt format changes.
- 768-dimensional vectors are the default cost/latency/quality tradeoff. At
  10B rows, raw 768d float32 vectors are about 30TB before index overhead; raw
  3072d vectors are about 122TB before index overhead.
- HNSW index count and shard shape become capacity-planning objects. They must
  follow the DDL/backfill gates in ADR-2604261900.
- `LIKE '%query%'` over actor/post text is not acceptable as the primary search
  path at actor scale. Prefix/exact/token tables or materialized views must
  front actor search.
- Existing legacy actor embedding rows keyed by `actor:did:web:*` or
  `actor:did:plc:*` are migration artifacts. They may remain stored for audit,
  but production actor HNSW search must exclude them.

# Alternatives Considered

- Use `FLAT` as the only RisingWave vector index. Rejected. It is exact, but at
  2B-10B records it is useful only after a strong prefilter or as a rerank over
  a small candidate set.
- Use one global HNSW table for all actors, posts, and media. Rejected. It
  pushes tenant, time, modality, and safety filtering after ANN retrieval and
  creates one large operational blast radius.
- Use IVF in RisingWave. Rejected for now because the official RisingWave vector
  index docs expose `FLAT` and `HNSW`, not IVF.
- Generate all embeddings inline with RisingWave `openai_embedding()`. Rejected
  for corpus scale because it couples query execution to external model API
  latency, cost, rate limits, and retry behavior.
- Use embedded Python/Rust UDFs for model inference. Rejected. Embedded UDFs are
  appropriate for lightweight CPU-bound transforms, not external network calls
  or large model inference.
- Convert every image/audio/video to text first and use text embeddings only.
  Rejected as the primary strategy because it loses visual/audio semantics.
  Accepted as a secondary lexical/transcript path.

# References

- RisingWave vector indexes: https://docs.risingwave.com/processing/vector-indexes
- RisingWave vector data type and distance operators: https://docs.risingwave.com/sql/data-types/vector
- RisingWave `openai_embedding`: https://docs.risingwave.com/sql/functions/ai#openai_embedding
- RisingWave embedded Python UDFs: https://docs.risingwave.com/sql/udfs/embedded-python-udfs
- RisingWave Rust UDFs: https://docs.risingwave.com/sql/udfs/use-udfs-in-rust
- Gemini embeddings: https://ai.google.dev/gemini-api/docs/embeddings
- Gemini OpenAI compatibility: https://ai.google.dev/gemini-api/docs/openai
- EmbeddingGemma model card: https://ai.google.dev/gemma/docs/embeddinggemma/model_card
- Amazon Nova Multimodal Embeddings: https://aws.amazon.com/blogs/aws/amazon-nova-multimodal-embeddings-now-available-in-amazon-bedrock
- Voyage multimodal embeddings: https://docs.voyageai.com/docs/multimodal-embeddings
- Cohere multimodal embeddings: https://docs.cohere.com/docs/multimodal-embeddings

# Addendum 2026-05-01: site.wet IVF+PQ Embedding Pipeline

## Decision

`site.etzhayyim.com` corpus (`vertex_wet_chunk`, 19,660 markdown rows from site
crawl) uses CPU-based K8s Job batch embedding + faiss IVF+PQ codebook for the
`site.searchSemantic` XRPC handler with `method=ivf_pq`.

## Embedding approach

4 parallel K8s Jobs (`embed-wet-f0..f3`), each pinned to a hash-shard:
`int(md5(vertex_id), 16) % 4 == shard`. Each job runs
`pymagatama.primitives.vector_embedding.embed_texts_768` (BAAI/bge-m3, 768d,
max 2048 chars input) with `OMP_NUM_THREADS=2` matching the 2-CPU limit.
Throughput: ~5.74 s/text CPU-bound. Total wall-clock: ~7–8 h for full corpus.

Image: `ghcr.io/etzhayyim/pymagatama:0.3.22-202605010216-amd64` (built
2026-05-01, includes `faiss-cpu>=1.8.0` and `site_ivf_pq.py`). The original
image built at 00:39 UTC predated the `site_ivf_pq.py` commit (00:42 UTC) and
lacked faiss; a `--no-cache` rebuild was required.

**RisingWave recovery risk**: DML fails with
`DML is not permitted during cluster recovery` when the compute nodes restart.
Two of four shards (f1, f3) hit this when `risingwave-compute-0` had 6
restarts in the same window. Pattern: shard computes embeddings successfully,
then crashes on the subsequent `UPDATE vertex_wet_chunk SET embedding = ...`
batch write. Mitigation: K8s Job restart (new job name picks up from
`embedding IS NULL` predicate). Production embedding pipelines should add a
retry loop around the DB write phase.

## IVF+PQ parameters

| Parameter | Value |
|-----------|-------|
| `n_centroids` | 256 |
| `m_subspaces` | 96 |
| `k_centroids` | 256 |
| `dim` | 768 |
| `collection` | `site.wet` |
| `encode_batch` | 500 |
| `train_sample_max` | 200,000 |

Three sequential K8s Jobs run after embedding completes:
1. `ivf-update-centroids` — faiss K-means → `vertex_ivf_centroid` + sets
   `vertex_wet_chunk.ivf_cluster_id`
2. `ivf-train-codebook` — PQ codebook on centroid residuals → `vertex_pq_codebook`
3. `ivf-encode-chunks` — encode all chunks → `vertex_wet_chunk_pq` (loops
   until `encoded==0`)

Job template: `/tmp/ivf-pq-pipeline.yaml` (same image as embedding jobs).
Resource profile: 2–4 CPU / 4–8 Gi each.

## Status (2026-05-01)

Embedding in progress: 5,143 / 19,660 rows (26%) at session close. ETA
~13:00 UTC. IVF+PQ pipeline starts after all shards complete. Migration entry:
`deps.toml [[migrations]] id="site-wet-embed-ivf-pq-pipeline"`.
