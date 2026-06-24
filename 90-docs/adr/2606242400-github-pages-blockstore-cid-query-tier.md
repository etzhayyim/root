---
id: adr-2606242400-github-pages-blockstore-cid-query-tier
title: "ADR-2606242400: GitHubPagesBlockStore — CARv1 + HTTP-Range CID query tier"
status: accepted
doc_type: adr
topic: github-pages-blockstore
authoritative: true
last_verified: 2026-06-24
priority: 4.5
axis: architecture
weight: 0.45
priority_note: "A static, serverless read/query tier: kotoba blocks as a CARv1 on GitHub Pages, queried by root CID over HTTPS Range — the export half the actor git-evolution PR (2606241500) deferred."
authoritative_for:
  - github-pages-blockstore
  - car-cid-query-tier
depends_on:
  - adr-2606241500  # sops/age + actor git evolution (the git transport half)
  - adr-2605312345  # kotoba Datom log = canonical state; IPFS/B2 = export tiers
  - adr-2605262130  # kotoba storage substrate; block backend layering
related: []
supersedes: []
superseded_by: []
---

# ADR-2606242400: GitHubPagesBlockStore — CARv1 + HTTP-Range CID query tier

**Status**: accepted
**Date**: 2026-06-24
**Deciders**: Jun Kawasaki

# Context

ADR-2606241500 let an actor evolve code + data + secrets through git, but
deferred the *read/query* side of the original question — "can we store the data
on GitHub (Pages) addressed by CID and query it, instead of running an IPFS
node?". The substrate already makes this natural: kotoba blocks are CIDv1
content-addressed (`etzhayyim.kotoba.cid`, raw/sha2-256, ipfs-parity) and
ADR-2605312345 fixes IPFS/B2 as **export tiers, not the system of record** — so
the blocks may live anywhere addressable. GitHub Pages (Fastly) is a free,
CDN-backed static host that **honours HTTP Range**, which is exactly what a
content-addressed block fetch needs.

The naive "one file per CID" approach explodes the git tree (the repo rule's #1
enemy). The right shape is a single **CARv1** bundle + an index so a client can
**Range-fetch one block** without downloading the bundle.

# Decision

Add **`GitHubPagesBlockStore`** — a static, serverless read/query tier, clj/bb,
over the existing CID primitives. Three new namespaces under `70-tools/src`:

- **`etzhayyim.kotoba.car`** — CARv1 writer + index. `pack` takes roots + ordered
  `[cid bytes]` blocks and returns `{:car bytes :index {cid [data-offset len]}}`.
  The index points at each block's **DATA region**, so a Range GET over
  `[offset, offset+len)` returns exactly the block — recompute its CID to verify.
  (`cid.cljc` gains `cid-str->bytes` / `cid-bytes->str` for the binary CID form
  CARv1 sections carry.)
- **`etzhayyim.kotoba.pages-store`**:
  - `publish!` packs a kotoba Datom journal into `<dir>/<graph>.car` +
    `.car.idx.edn` + `head.json` (the root CID) + `.nojekyll`. A graph is stored
    as one **root manifest** block listing its child CIDs (the prolly/commit-DAG
    head analogue) plus one block per datom.
  - `file-ranger` / `http-ranger` — the Range-fetch seam (`Range: bytes=o-o+l-1`,
    206 Partial Content). `get-block` recomputes + checks every fetched CID, so
    **the static host is untrusted** (tamper-evident).
  - `fetch-log` — resolve root → read manifest → Range-fetch + verify each child
    → reassemble the Datom log. "Query a static site by CID", end to end.
- `bb pages:publish` / `pages:query [--http]` / `test:pages-store`.

**Publish writes files only**; committing/pushing them is the ADR-2606241500
git tier (no-server-key). So an actor's data graph rides the SAME git flow as its
code, and is then queryable by anyone over plain HTTPS — no IPFS daemon, no
server, no trust in the host.

## Layering (unchanged grain)

This is a **read/export tier**, not a new system of record. Canonical state stays
the kotoba Datom log (ADR-2605312345); IPFS/Kubo + B2 remain the p2p / durable
cold tiers. GitHub Pages joins them as the *static query/distribution* surface —
small datom/index blocks only. Large binaries stay on B2 + DataLad (ADR-2605241500),
never in the CAR/Pages tier.

# Consequences

**正**
- Serverless, CDN-backed, trustless (CID-verified) query of a kotoba graph with
  zero IPFS infrastructure — a browser/peer reads it over HTTPS Range.
- One CAR + index per graph keeps the git tree small (no per-CID file blow-up);
  the same bundle is a valid CARv1, so it can also be `ipfs dag import`-ed later.
- Reuses the canonical CID framing; the manifest is the seam to a real
  prolly-tree DAG walk (chunked blocks) when graphs outgrow one-block-per-datom.

**負 / リスク**
- GitHub Pages soft limits (~1 GB site, ~100 GB/mo bandwidth, publish-build
  latency) — fine for read-mostly index/datom blocks, wrong for large binaries
  (→ B2/DataLad) and for the hot write path (→ embedded store).
- One-block-per-datom is the PoC granularity; a true prolly-tree chunker (so the
  manifest is a multi-level DAG, not a flat list) is the next step for big graphs.
- `head.json` is mutable (last-writer per publish); Pages build latency makes it
  eventually-consistent — acceptable for an export tier, not for hot reads.

# Alternatives Considered

- **One file per CID on Pages** — simplest to fetch (`/<cid>`) but explodes the
  git tree and clone time (the repo's #1 rule). CAR + Range avoids it.
- **Run an IPFS gateway / Kubo node** — the thing this tier removes; Kubo stays
  the optional p2p tier, not a requirement for query.
- **IPFS public gateway (ipfs.io)** — needs the blocks pinned somewhere first and
  adds a trusted third party; Pages + client-side CID verify is self-hosted and
  trustless.
- **CARv2 (with built-in index)** — heavier spec; an external `.car.idx.edn` is
  enough here and stays human-inspectable. CARv2 is a clean future upgrade.

# References

- ADR-2606241500 (sops/age + actor code+data git evolution — the git transport half)
- ADR-2605312345 (kotoba Datom log = canonical state; IPFS/B2 = export tiers)
- ADR-2605262130 (kotoba storage substrate; block backend layering)
- ADR-2605241500 (DataLad + git-annex + IPFS — large-binary tier)
- `70-tools/src/etzhayyim/kotoba/{car,pages_store,cid}.cljc`
- CARv1 spec <https://ipld.io/specs/transport/car/carv1/>
