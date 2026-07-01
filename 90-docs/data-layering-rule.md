---
id: data-layering-rule
title: "Data layering rule — kotoba graph vs etzhayyim repo + IPFS"
status: active
doc_type: reference
topic: data-layering-rule
authoritative: true
last_verified: 2026-07-01
authoritative_for:
  - "actor data-ownership :rad/layer assignment (ADR-2607010001 §D4)"
  - "com.etzhayyim.kotoba.datasetPointer lexicon (graph-layer pointer record)"
  - "80-data/* ingest (canonical projection + raw blob placement)"
depends_on:
  - adr-2607010001-actor-data-ownership-model
  - adr-2605312345-kotoba-datom-first-class-canonical-state
  - adr-2605241500-etzhayyim-dataset-cid-substrate
---

# Data layering rule — kotoba graph vs etzhayyim repo + IPFS

This is the **normative** rule (ADR-2607010001 §D4) for which layer holds a given
piece of an actor's real-world data. It closes the previously-undocumented
relationship between the kotoba graph layer (ATProto MST / PDS) and the
etzhayyim git repo + DataLad/IPFS layer.

## The two layers

- **kotoba graph layer** (`com.etzhayyim.apps.*` PDS collections, signed by the
  actor's own did:key). Holds **small signed records only** — identity/social/
  journal records today (`app.bsky.feed.post`, `app.bsky.graph.follow`,
  `com.etzhayyim.apps.kotoba.cc.*`), plus the new **dataset pointer** record
  `com.etzhayyim.kotoba.datasetPointer`. Bulk data is awkward and unbounded in
  the MST; **do not put datasets there**.
- **etzhayyim repo + DataLad/IPFS layer** (`orgs/etzhayyim/root/80-data/*/`,
  each actor's `com-etzhayyim-<name>/data/`, and the DataLad datasets +
  git-annex + B2/IPFS backends). Holds **canonical projections** (`*.kotoba.edn`,
  git-tracked, content-addressed CIDv1) and **raw blobs** (`*.raw.{json,csv,edn}`,
  gitignored, pinned to IPFS/DataLad). This is where jinushi / kanjo /
  hirameki-patents / genome already live.

## The rule

| Kind of data | Layer | RAD `:rad/layer` |
|---|---|---|
| Dataset **pointer / fingerprint** (dataset-id, layer, cidv1, freshness, last-verified) | graph (`datasetPointer` record) | `:graph` |
| Small signed **aggregate facts** a `/search` or `/rag` XRPC returns (counts, sector totals) | graph | `:graph` |
| **Canonical projection** (`*.kotoba.edn`, normalized, CIDv1) | repo + IPFS | `:repo` |
| **Raw blob** (`*.raw.*`, source fetch) | repo + IPFS (gitignored, annex/IPFS-pinned) | `:repo` |
| Anything **> a few KB**, any full table, any binary | repo + IPFS | `:repo` |

**Default to `:repo`.** Only a pointer + small aggregates go in graph. The
graph record's `cidv1` points at the repo-tier directory CID, so resolving the
pointer lands at the canonical projection.

## One field set, two representations

A holding has ONE anchor field set:

```
{dataset-id, layer, source, cidv1, freshness-days, retrieved,
 counts-toward-world-coverage, holder-rank}
```

expressed TWO ways:

1. **RAD journal datom** (`dataset:<id>` sub-entity) — the sovereign
   attestation, signed via the member key seam (no-server-key), append-only,
   RID-stable (ADR-2606231200 + ADR-2607010001 §D1).
2. **Graph `datasetPointer` record** — the runtime-discoverable pointer, signed
   by the actor's own did:key, living in the actor's PDS collection.

`holderRank` = `canonical` (this actor is the canonical holder) | `mirror`
(replicated for local presentation). **Exactly one canonical owner per
dataset.**

## Invariants

- **pin==HEAD** — a `:layer :repo` holding's `:rad/cidv1` / pointer `cidv1`
  MUST equal the directory CID at the holding repo's current HEAD. Stale claims
  are rejected by `lint:provenance`.
- **Identifier three-way equality** — `dataset-id` is identical across the RAD
  `:rad/dataset-id`, the `*.kotoba.edn` `:dataset-id` header, and
  `ingest-provenance.json` `ingest-id`.
- **Raw blobs never in git history** — `*.raw.*` are gitignored + IPFS/annex-
  pinned (ADR-2605241500); git carries only the `*.kotoba.edn` projection,
  provenance, and pin references.
- **Graph stays small** — the `datasetPointer` lexicon is pointer-only by
  construction; `lint:provenance` rejects any `:layer :graph` holding whose
  referenced artifact exceeds the byte ceiling.

## References

- ADR-2607010001 (actor data-ownership model) — §D4
- ADR-2605312345 (kotoba Datom log = first-class canonical state; IPFS = block
  backend, MST = ingress/interop wire)
- ADR-2605241500 (dataset CID substrate — DataLad + git-annex → IPFS)
- `00-contracts/lexicons/com/etzhayyim/kotoba/datasetPointer.json`
- `70-tools/src/etzhayyim/kotoba_rad.cljc` — `holding-datoms`
- `80-data/jinushi-land/ingest-provenance.json` — the canonical projection +
  raw-blob + pin pattern this rule generalizes
