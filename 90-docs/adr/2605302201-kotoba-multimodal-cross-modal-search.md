---
id: adr-2605302201-kotoba-multimodal-cross-modal-search
renumbered_from: "2605302200"
title: "ADR-2605302201: kotoba multimodal cross-modal search — shared-embedding-space media retrieval"
status: proposed
doc_type: adr
topic: kotoba-multimodal-search
authoritative: true
last_verified: 2026-05-30
priority: 5.0
axis: architecture
weight: 0.50
priority_note: "Extends kotoba from text-only semantic search to cross-modal retrieval: a text query retrieves image/audio/video/document assets from one shared embedding space, reusing the existing Datom + Vault + IVF substrate. Heavy multimodal encoders stay out-of-process behind KOTOBA_MM_EMBED_URL per the no-commercial-GPU inference invariant."
authoritative_for:
  - "kotoba multimodal cross-modal search (media.* XRPC + media_embed/media crates)"
  - "media/* datom predicate namespace + media:2026:assets named graph"
  - "IvfIndex namespace-generalised persistence (cc/ivf/* and media/ivf/*)"
depends_on:
  - adr-2605240001-kotoba-cleanroom-architecture
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
related:
  - adr-2605250006-kotoba-cc-ingest-predicate-namespace
supersedes: []
superseded_by: []
---

# ADR-2605302201: kotoba multimodal cross-modal search — shared-embedding-space media retrieval

**Status**: proposed
**Date**: 2026-05-30
**Deciders**: Jun Kawasaki

# Context

Before this change kotoba could do **text** semantic search: `kotoba-ingest::cc`
embeds Common Crawl WET chunks into `cc/embed/*` datoms, builds a pure-Rust IVF
index (`kotoba-ingest::ivf`), and serves ANN queries over
`com.etzhayyim.apps.kotoba.cc.search` / `cc.rag`. The substrate *to store other
modalities already existed* — the KSE `Vault` chunks `image/*`, `video/*`,
`audio/*` and document bytes content-addressed, and `kotoba-kqe::Value` carries
`VectorF32` / `TensorCid` — but there was **no pipeline that embedded images,
video, audio, or books/PDFs into a searchable space, and no way for a text query
to retrieve a non-text asset** (the "Google-style" multimodal experience the
operator asked for).

Constraints that shaped the design:

- **Charter / inference invariant** (ADR-2605215000 + Charter Rider §2(i)): no
  commercial-GPU inference baked into religious-corp paths. Heavy multimodal
  encoders (CLIP / SigLIP / ImageBind) must stay *out of process* behind an HTTP
  boundary, exactly as text embedding already delegates to Ollama / OpenAI-compat
  via `KOTOBA_EMBED_URL`.
- **Substrate boundary** (ADR-2605262130): everything is Datoms over
  content-addressed blocks. No new storage engine, no parallel index format.
- **Offline-operable**: the open node must function (and be testable) with no
  encoder deployed — consistent with the `Blake3EmbedClient` text fallback.

# Decision

Add a multimodal cross-modal search capability across three crates, reusing the
existing Datom + Vault + IVF substrate. **Text, image, audio, video, and
document embeddings share ONE vector space**; a text query is embedded into that
space and cosine-ranked against all stored media embeddings, so any modality is
retrievable from a text query.

### 1. `kotoba-ingest::media_embed` — shared-space embedding clients

- `Modality` enum: `Text | Image | Audio | Video | Document`, classified from
  MIME (`Modality::from_mime`); unknown binary falls back to `Document` (never
  dropped).
- `MediaEmbedClient` trait: `embed_media(&[MediaItem]) -> Vec<Vec<f32>>`.
  `MediaItem { modality, mime, bytes, caption }`.
- `HttpMediaEmbedClient` — POSTs `{modality, mime, b64, text}` batches to an
  external multimodal encoder (CLIP / SigLIP / ImageBind), response is
  OpenAI-shaped `{data:[{embedding}]}`. Config via `KOTOBA_MM_EMBED_URL` /
  `KOTOBA_MM_EMBED_MODEL` / `KOTOBA_MM_EMBED_DIM` / `KOTOBA_MM_EMBED_BATCH`.
- `Blake3MediaEmbedClient` — deterministic caption-bridged offline client. Seed
  precedence: caption → raw bytes. Uses the **same blake3 formula** as the text
  `Blake3EmbedClient`, so a text query and a media caption carrying the same
  string land on the same vector — making the shared space exercisable with no
  encoder.

### 2. `kotoba-ingest::media` — `MediaIngestor`

- Stores each asset's bytes in the KSE `Vault` (content-addressed, idempotent),
  embeds it into the shared space, and projects `media/*` datoms into the
  `media:2026:assets` named graph + a `media/ivf/*` IVF index.
- Predicate namespace `media/*`: `media/mime`, `media/modality`, `media/blob`
  (Vault CID), `media/size`, `media/page` (book/PDF pagination), `media/title`,
  `media/caption`, `media/embed/{model}` (`VectorF32` ≤1024-dim, else
  `TensorCid`), `media/embed_norm`, `media/ivf/cluster`.
- `ingest_items` (commits) / `ingest_items_datoms` (returns datoms, still writes
  blobs — for the distributed-commit path) / `ingest_paths` (whole files from
  disk, MIME inferred from extension).
- `rank_by_cosine(query, embeddings, top_k)` — the cross-modal retrieval helper,
  shared by the search handler.

### 3. `kotoba-ingest::ivf` — namespace-generalised persistence

- `IvfIndex::to_quads_ns(graph, counts, ns)` writes `{ns}/ivf/*` (e.g. `"cc"` or
  `"media"`). `from_quads` / `from_datoms` made namespace-agnostic via an
  `ivf_leaf` splitter, so one index implementation serves both `cc/ivf/*` and
  `media/ivf/*`. `to_quads` retained as `to_quads_ns(.., "cc")` for back-compat.

### 4. `kotoba-server::media_xrpc` — XRPC endpoints

- `com.etzhayyim.apps.kotoba.media.search` (GET) — embeds the TEXT query in the shared
  space, cosine-ranks all modalities, optional `modality` filter, returns
  subject / modality / blob CID / mime / title / caption / source / score.
- `com.etzhayyim.apps.kotoba.media.ingest` (POST, 36 MiB body limit) — base64 assets.
- `com.etzhayyim.apps.kotoba.media.status` (GET) — asset / embedding / IVF-centroid
  counts + per-modality breakdown.
- All operator-auth-gated (`require_operator_auth`).
- `KotobaState.media_embed_client: Option<Arc<dyn MediaEmbedClient>>` — populated
  only when `KOTOBA_MM_EMBED_URL` is set; otherwise the handler falls back to a
  deterministic `Blake3MediaEmbedClient` at request time, so the endpoint is
  always functional.

### 5. `kotoba-cli` — operator subcommands

- `kotoba media-ingest <file> [--caption --title --page]`,
  `kotoba media-search "<query>" [--top-k --modality]`, `kotoba media-status` —
  drive the endpoints over HTTP with an operator-JWT built from the local
  `kotoba init` identity (same pattern as `kotoba commit`).
- Runnable offline demo: `cargo run --example media_e2e -p kotoba-ingest`.

# Consequences

**Positive**:

- A text query retrieves images / video / audio / books from one shared space —
  the requested capability — with no new storage engine or index format.
- Charter-compatible: the heavy encoder stays behind an HTTP boundary; the node
  runs and is tested offline via the deterministic client.
- Reuses the proven IVF + Vault + Datom substrate; the cross-modal path is the
  same cold-path read the text search already uses.
- Verified end-to-end 2026-05-30: ingested image+video+audio+PDF via the CLI over
  HTTP; `media-search "a solo piano playing a slow classical sonata"` ranked the
  **audio** asset top (score 1.0); `--modality image` returned only the image.
  53 `kotoba-ingest` lib tests + 3 `media_xrpc` tests pass; `media_e2e` example
  green.

**Negative / risks**:

- **Retrieval quality depends on the external encoder.** With none configured
  (`embedConfigured: false`), the caption-bridge fallback is functional and
  reproducible but **not semantic** — it matches on caption text, not pixels /
  audio. Real cross-modal semantics require a deployed CLIP/SigLIP/ImageBind
  endpoint at `KOTOBA_MM_EMBED_URL`.
- **No content-extraction pipeline.** Captions / OCR / ASR transcripts / PDF page
  text are caller-supplied; kotoba does not yet extract them from raw bytes.
- Search is brute-force cosine over the candidate set; the `media/ivf/*` index is
  persisted but the search handler does not yet prune by centroid (same
  known limitation as `cc.search`). Acceptable at current corpus sizes.

# Alternatives Considered

- **External vector DB (LanceDB / FAISS / Qdrant)**: rejected — violates the
  single-substrate rule (ADR-2605262130); the pure-Rust IVF over Datoms already
  exists and round-trips through content-addressed blocks.
- **Per-modality separate indexes / graphs**: rejected — defeats the purpose;
  cross-modal retrieval *requires* one shared space. Modality is a `media/modality`
  attribute + an optional query filter, not a storage partition.
- **In-process encoder (bundled CLIP weights)**: rejected — would pull a heavy ML
  runtime into the religious-corp inference path against ADR-2605215000 + Charter
  Rider §2(i); the HTTP boundary mirrors the existing text-embedding design.

# References

- Code: `40-engine/kotoba/crates/kotoba-ingest/src/{media_embed,media,ivf}.rs`,
  `crates/kotoba-server/src/media_xrpc.rs`, `crates/kotoba-cli/src/main.rs`
  (`media-search`/`media-ingest`/`media-status`),
  `crates/kotoba-ingest/examples/media_e2e.rs`.
- ADR-2605240001 (kotoba cleanroom architecture), ADR-2605262130 (storage
  substrate unification), ADR-2605215000 (Murakumo-only inference, no-RunPod),
  ADR-2605192200 (Charter Rider §2(i) no-commercial-GPU).
- `40-engine/kotoba/deps.toml` (`[subdirs."crates/kotoba-ingest"]`,
  `[subdirs."crates/kotoba-server"]` notes).
