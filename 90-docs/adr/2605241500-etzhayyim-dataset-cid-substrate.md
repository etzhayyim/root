---
id: adr-2605241500-etzhayyim-dataset-cid-substrate
title: "ADR-2605241500: etzhayyim Dataset CID Substrate — DataLad + git-annex (directory special remote on local volume) + sidecar IPFS pinner, CIDs anchored as datasetPin records on PDS"
status: proposed
doc_type: adr
topic: dataset-cid-substrate
authoritative: true
last_verified: 2026-05-24
priority: 6.0
axis: architecture
weight: 0.55
priority_note: "Defines how this monorepo references large (10TB+) training / reference / baien datasets without putting bytes in git. Uses DataLad superdataset → git-annex (SHA256E backend, `directory` special remote on local volume) for the catalog + bytes-at-rest, and a sidecar IPFS pinner that mirrors each annex object to Kubo for substrate-compliant distribution; emits com.etzhayyim.substrate.datasetPin records to PDS as the religious-corp-canonical receipt. Local data root on this Mac: /Volumes/260317/etzhayyim/. The `type=external externaltype=ipfs` route is deliberately NOT taken because git-annex IPFS external remote implementations have an inherent CHECKPRESENT-always-fails limitation that re-uploads on every copy unless `git annex trust` is asserted; the sidecar pinner avoids that class of failure entirely."
authoritative_for:
  - dataset storage policy (bytes off git via git-annex; pointers in git; PDS-anchored receipt)
  - DataLad superdataset layout (90-docs/baien/datasets/)
  - git-annex `directory` special remote configuration (annex object dir on local volume)
  - sidecar IPFS pinner contract (annex-object → CID mapping + datasetPin emit)
  - com.etzhayyim.substrate.datasetPin lexicon
  - 70-tools/e7m-dataset thin Python wrapper (DataLad orchestration + Charter Rider gate + sidecar pin + PDS emit)
  - per-machine local path resolver (ETZ_DATASET_ROOT / ~/.etzhayyim/local-paths.toml)
  - dataset replication-factor + Charter Rider pre-pin gate
depends_on:
  - adr-2605170900-etzhayyim-root-adr-canonical-home
  - adr-2605171800-langgraph-mst-ipfs-l2-anchor-pipeline
  - adr-2605172000-etzhayyim-rw-free-substrate
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
related:
  - adr-2605231300-baien-distill-react-loop
  - adr-2605232500-baien-mx-move1-image-graft-self-training
supersedes: []
superseded_by: []
---

# ADR-2605241500: etzhayyim Dataset CID Substrate

**Status**: proposed
**Date**: 2026-05-24
**Deciders**: Jun Kawasaki

# Context

`baien-distill` (ADR-2605231300) and `baien-mx-move1` (ADR-2605232500) pull
multi-GB Hugging Face datasets, and the projected training / reference
corpus across the religious-corp ecosystem is expected to exceed **10 TB**
within the year. Substrate constraints (ADR-2605172000) prohibit
centralized off-chain data stores, so the natural target for the bytes is
IPFS — but a workable design also needs:

- **provenance** (which `baien-distill` run consumed which CID at which time);
- **per-file lineage** (one dataset = thousands of files; we want
  fine-grained accountability and `git annex whereis`-style location
  queries);
- **transactional add / remove** without forcing the operator to
  hand-author CARs;
- **the ability for `datalad run` to wrap a training script and capture
  inputs + outputs as a provenance record**.

git-annex (with its SHA256E backend) and DataLad (its provenance-aware
shell on top of git-annex) solve the per-file / lineage / `datalad run`
parts directly and have been in production at neuroimaging-scale (≫ 1 TB)
for years. git-annex supports IPFS as a **special remote** (community
implementations and historically a built-in), so the byte route can stay
on IPFS while git-annex handles the catalog and movement.

The deciding Mac's disk reality:

```
/dev/disk5s2   931Gi   6.8Gi   924Gi     1%   /Volumes/260317
```

The 931 GiB external volume is the only place this Mac can host its
share. The full 10 TB+ corpus must be sharded across the religious-corp
node fleet; this ADR specifies the per-machine contract that makes such
sharding mechanical.

# Decision

Adopt **DataLad + git-annex (directory special remote) + sidecar IPFS
pinner** as the dataset substrate, and keep
`com.etzhayyim.substrate.datasetPin` PDS records as the
religious-corp-canonical receipt. Six layers:

```
git (small)        : DataLad superdataset under 90-docs/baien/datasets/
                     — pointers, metadata, .gitattributes, lineage commits
git-annex (catalog): SHA256E keys for every annexed file, location tracking
local store        : `directory` special remote at
                     /Volumes/260317/etzhayyim/annex-store/  — bytes at rest
sidecar pinner     : e7m-dataset publish-ipfs walks the directory remote,
                     runs `ipfs add` per object, writes a
                     SHA256E-key → IPFS-CID mapping, pins the map itself
                     and emits the root CID
IPFS (distribution): Kubo data root on per-machine local volume
                     holds the pinned annex objects + map
PDS (receipt)      : com.etzhayyim.substrate.datasetPin records, DID-signed
human index        : 90-docs/baien/datasets.jsonl, append-only, summary view
```

The byte path is **git-annex first, IPFS second**: git-annex owns the
catalog, location tracking, and the on-disk objects; IPFS provides
substrate-compliant distribution. The two are bound by the sidecar
pinner's mapping file rather than by a git-annex external remote — this
sidesteps the well-known CHECKPRESENT / REMOVE limitations of all
in-the-wild `git-annex-remote-ipfs` implementations.

## D1. DataLad superdataset — `90-docs/baien/datasets/`

A DataLad superdataset rooted at `90-docs/baien/datasets/`, containing
one **subdataset per (kind, source-host)** pair. Initial layout:

```
90-docs/baien/datasets/                       # superdataset
├── .datalad/
├── .gitattributes        # backend=SHA256E, large=anything
├── README.md             # operator entry point
├── HF/                   # Hugging Face subdatasets
│   ├── HuggingFaceTB-smollm-corpus/  # one subdataset per HF repo
│   └── ...
├── reference/            # non-HF references (papers, dumps)
├── baien-graft-3d/
└── baien-graft-image/
```

Subdataset isolation lets us shard at subdataset granularity (a node
either has a subdataset's bytes or it doesn't) and lets reviewers
`datalad clone` a single subset without pulling the whole catalog.

`text2git` configuration is **on for the superdataset only** — the
superdataset holds only README, metadata, and subdataset pointers, all
of which should land in git directly. Subdatasets are created **without**
`text2git`: every file is annexed because the per-subdataset content is
dominated by binary archives and routing some files into git history by
extension would bloat the per-subdataset git size for no benefit.

## D2. Backend + git-annex configuration

| Setting | Value | Rationale |
|---|---|---|
| `annex.backend` | `SHA256E` | content-addressed, file-extension-preserving, IPFS-mapping friendly |
| `annex.largefiles` | `anything` | every file annexed (no `text2git`) |
| `annex.security.allowed-url-schemes` | `https http` | URL-add from HF / mirrors |
| `annex.thin` | `true` (on the staging volume) | hardlink working copy → annex object to save disk |

Local store (the only special remote on the byte path):

```sh
git annex initremote local-store \
    type=directory \
    directory=/Volumes/260317/etzhayyim/annex-store \
    encryption=none \
    chunk=64MiB
```

Replication ≥ 2 is achieved by initializing a **second** `directory`
remote on a different node's mounted volume (or a peer-to-peer
`rsync`-via-tor remote in the longer term), **plus** the sidecar IPFS
pinner which contributes a third logical replica via Kubo.

The IPFS path is intentionally NOT a git-annex special remote. Every
in-the-wild `git-annex-remote-ipfs` returns FAILURE for `CHECKPRESENT`
(IPFS has no reliable "is this pinned by my node?" query without trust)
and FAILURE for `REMOVE` (IPFS immutability). This makes the IPFS
external remote impractical as a primary store. We use it as a
**distribution layer downstream of the directory remote** instead.

## D3. Lexicon — `com.etzhayyim.substrate.datasetPin`

Kept (already created at
`00-contracts/lexicons/com/etzhayyim/substrate/datasetPin.json`). Emitted
once per `(name, revision)` pair after the sidecar pinner has copied all
new annex objects to IPFS.

The `cid` field holds the **map CID**: the IPFS CID of a small JSON
document of the form

```json
{
  "version": 1,
  "subdataset": "HF/HuggingFaceTB-smollm-corpus",
  "gitCommit": "<sha>",
  "annexBackend": "SHA256E",
  "entries": [
    { "key": "SHA256E-s12345--ab...ef.parquet", "ipfsCid": "bafyb...1" },
    { "key": "SHA256E-s67890--12...cd.parquet", "ipfsCid": "bafyb...2" }
  ]
}
```

Fetching the map CID + then each entry's CID from any IPFS gateway is
sufficient to reconstruct the subdataset's bytes; combined with the
git-annex catalog (a regular `git clone` of the superdataset) the
reader can repopulate `.git/annex/objects/` and check out the worktree
deterministically. `sha256` carries the SHA256 of the map JSON itself
for chunker-independent verification.

## D4. Thin wrapper — `70-tools/e7m-dataset/`

Python (DataLad is Python-native; reusing the same toolchain as
`kotodama.organism.sensors.charter_rider`):

```
e7m-dataset add <source-uri> [--kind <kind>] [--license <spdx>]
e7m-dataset sync
e7m-dataset gc
e7m-dataset verify <name>
e7m-dataset where <name>
```

`add` flow:
1. Resolve source (HF revision → `datalad clone -d HF/<owner>-<repo>
   <hf-url>`; HTTP → `datalad download-url`).
2. `charter_rider.scan()` over a deterministic sample of the staged
   subdataset. Fail-closed on violation.
3. `git annex copy --to local-store --jobs <N>` in the subdataset — bytes
   land on `/Volumes/260317/etzhayyim/annex-store/`.
4. **publish-ipfs sidecar**: walk the new annex objects in the directory
   remote, `ipfs add` each, build the SHA256E-key → IPFS-CID map JSON,
   `ipfs add` the map → root CID.
5. `git -C <super> commit` the subdataset state.
6. Append a row to `90-docs/baien/datasets.jsonl` (human index) with the
   map root CID.
7. Emit `com.etzhayyim.substrate.datasetPin` PDS record (or `--dry-run`).

The wrapper does **not** reimplement git-annex semantics; it orchestrates
existing commands and adds the Charter Rider gate + sidecar IPFS pin +
PDS emit + manifest update.

## D4a. publish-ipfs sidecar — algorithm

```
inputs:
  annex_store_dir = /Volumes/260317/etzhayyim/annex-store/
  subdataset      = HF/<owner-repo>
  git_commit      = HEAD of the subdataset

procedure:
  1. enumerate annex objects added since the last published commit
     (tracked in annex-store/.etzhayyim/published.json)
  2. for each object file `f` at path `<annex_store_dir>/.../<KEY>/<NAME>`:
       cid = ipfs add --quieter --cid-version=1 --pin=true f
       record { key: KEY, ipfsCid: cid }
  3. compose map JSON { version, subdataset, gitCommit, annexBackend, entries }
  4. map_cid = ipfs add --cid-version=1 --pin=true <map.json>
  5. write annex-store/.etzhayyim/published/<git_commit>.json (audit trail)
  6. update annex-store/.etzhayyim/published.json with last_commit
  7. return map_cid → wrapper emits datasetPin record
```

The audit-trail file is intentionally written **into the directory
remote tree** (under a reserved `.etzhayyim/` prefix that git-annex
ignores) so a separate node that mounts the same volume sees the
publish history.

## D5. Per-machine path resolver

Two-level override (unchanged from prior design):

1. `ETZ_DATASET_ROOT` env var (highest precedence).
2. `~/.etzhayyim/local-paths.toml` → `[machine.<hostname>].dataset_root`.
3. **No default.** Tool errors out if neither is set.

On this Mac the resolved layout is:

```
/Volumes/260317/etzhayyim/
├── ipfs-data/          # Kubo data root (IPFS_PATH points here)
├── annex-store/        # git-annex object dir for the superdataset
│                       # (configured via `git annex config annex.objectdir`)
├── datasets-staging/   # ephemeral download workspace
│   └── HF/<owner>/<repo>@<rev>/
└── ria-store/          # (future) DataLad RIA store for offline shipping
```

`~/.etzhayyim/local-paths.toml` is **not git-tracked**.

## D6. Sharding policy (10 TB scenario)

Sharding is at **subdataset granularity** (per D1). Each subdataset
carries a top-level `.datalad/config` key
`etzhayyim.assigned-nodes=did:web:...,did:web:...` listing the DIDs of
nodes that MUST hold its bytes. `e7m-dataset sync` honors this list.

Replication ≥ 2 invariant from ADR-2605171800 Stage 4 is inherited and
enforced at `sync` time with **warn-only severity** until a second
always-on node lands.

For the immediate term on this Mac:
- Holds whichever subdataset subset is assigned to its DID; suggested
  initial subset is `kind ∈ {baien-graft-3d, baien-graft-image,
  reference}` capped at ~700 GiB.
- `replicationMin: 1` is permitted in the bootstrap window; manifest +
  PDS records carry the elevated risk note explicitly.

## D7. Charter Rider pre-pin gate

`kotodama.organism.sensors.charter_rider.scan()` (CLAUDE.md baien
tooling index) is invoked over a sampled subset of each staged
subdataset before `git annex copy --to ipfs`:

- text datasets: sample N rows (default 200; tunable per `kind`).
- image datasets: skip text scan; require explicit `license` + `kind`
  confirmation; image-content scanning is out of scope (future ADR).
- model weights: scan accompanying README / config / tokenizer JSON only.

Scan failure aborts the add flow before any IPFS bytes are written. Scan
result is recorded both in the manifest row and in the PDS record.

## D8a. DID Worker — `did:web:dataset-pinner.etzhayyim.com`

The dataset pinner is a distinct AT-Protocol identity from
`pinner.etzhayyim.com` (which exists for ADR-2605171800 MST/CAR
pinning). A separate Cloudflare Worker publishes the DID Document at
`https://dataset-pinner.etzhayyim.com/.well-known/did.json` — the
spec-required resolution endpoint — mirroring the esign / pinner
Worker pattern.

Scaffold lives at `50-infra/etzhayyim-dataset-pinner-did-web/`:

- `did.json` — DID Document; `verificationMethod: []` at Phase 1
  (Ed25519 keypair generation deferred to Phase 2, same pattern as
  esign Phase 0 and ipfs-pinner Phase 0).
- `src/worker.ts` — serves `/.well-known/did.json` + `/healthz`;
  returns 404 otherwise.
- `wrangler.toml` — route `dataset-pinner.etzhayyim.com/.well-known/did.json`
  on the `etzhayyim.com` zone.
- `NOTICE` + `CHARTER-RIDER.md` symlink (per ADR-2605192200 §3+§4
  first-party package requirements).

Deploy gates:

1. **Worker push**: `npm install && npm run deploy`.
2. **DNS provision**: `AAAA dataset-pinner.etzhayyim.com 100::` proxied
   (CF orange-cloud) on the `etzhayyim.com` zone. One-time CF dashboard
   step; same pattern as `pinner.etzhayyim.com` / `esign.etzhayyim.com`.
3. **Keypair (Phase 2)**: generate Ed25519 → store private in
   macOS Keychain (service `etzhayyim`, account
   `DID_PRIVATE_KEY_ED25519_DATASET_PINNER`) + 1Password mirror →
   replace `did.json verificationMethod` placeholder.
4. **App-password**: PDS operator issues a handle+password for the
   `dataset-pinner.etzhayyim.com` repo; consumer (`70-tools/e7m-dataset`)
   reads it via the `ETZ_E7M_PDS_AUTH` env var (Keychain decant
   pattern documented in `70-tools/e7m-dataset/README.md`).

`e7m_dataset.pds.DEFAULT_DID` defaults to
`did:web:dataset-pinner.etzhayyim.com`; operators override per-deploy
via `ETZ_E7M_PDS_DID`.

## D8. Reuse boundary with `ipfs-pinner`

`50-infra/ipfs-pinner/` continues to own MST CAR pinning (ADR-2605171800
Stage 4) and is **unchanged**. Datasets and MST CARs intentionally use
different pipelines:

- MST CARs: produced by mst-projector on the firehose, emitted continuously, single root per CAR, no license gating, fixed lexicon (`ipfsPin`).
- Datasets: operator-triggered, very large, per-file lineage required, Charter Rider license-gated, different lexicon (`datasetPin`), bytes-at-rest in a git-annex `directory` remote and only mirrored to IPFS by the sidecar publisher.

Both eventually pin to the same local Kubo (D5), so the Kubo node serves
as the shared distribution substrate while the two pipelines remain
logically distinct. The dataset sidecar reuses the same Kubo HTTP API
(`/api/v0/add`, `/api/v0/pin/add`) that `ipfs-pinner` uses, but does so
from Python rather than via the TS `kubo.ts` client — sharing a network
contract, not a library.

# Consequences

## Positive

- ✅ 10 TB+ data referenced from git via DataLad pointers; bytes never
  enter git history.
- ✅ Per-file location tracking + `datalad run` provenance for
  `baien-distill` consumers (consumers can do `datalad get` lazily).
- ✅ Reproducibility anchored to (a) git commit SHA, (b) git-annex
  SHA256E keys, (c) IPFS export-tree CID, (d) PDS lexicon record — four
  redundant addressing layers.
- ✅ Mac internal SSD untouched — all bytes on `/Volumes/260317`.
- ✅ Charter Rider gate is inline with §2(a)..(h) enforcement
  (ADR-2605192200).
- ✅ git-annex is the de-facto data-science standard for this exact
  problem; we are not inventing operational patterns.

## Negative / costs

- ⚠️ Operator must install Kubo, git-annex, and DataLad (`brew install
  ipfs git-annex` + `pipx install datalad`) on every node that holds
  data.
- ⚠️ The community `git-annex-remote-ipfs` external implementations vary
  in maturity. We commit to a specific impl in the wrapper and pin its
  revision; if upstream breaks, we fork.
- ⚠️ Python toolchain joins the substrate-tool surface (was TS-only via
  ipfs-pinner). Acceptable cost given DataLad is the only mature
  data-versioning option that fits.
- ⚠️ Replication ≥ 2 invariant cannot be honored until a second always-on
  node lands. Documented warn-only window.
- ⚠️ Sharding-by-assignment is manual until `e7m-dataset plan` lands.

## Invariants introduced

1. No first-party dataset >100 MB enters git directly (all annexed).
2. Every emitted `com.etzhayyim.substrate.datasetPin` PDS record carries
   a Charter Rider scan result with `passed = true`.
3. `etzhayyim.assigned-nodes` in `.datalad/config` is the source of truth
   for which node MUST hold a subdataset's bytes.
4. `e7m-dataset add` is the only blessed entry point for first-party
   dataset ingestion. Manual `git annex add` is permitted for triage but
   does not emit a PDS record and is not considered substrate-canonical.

# Alternatives Considered

- **Git LFS** — rejected (2 GB/file cap; \$1000+/mo at 10 TB; GitHub coupling).
- **Custom TS dataset-pinner (initial proposal)** — rejected on second
  pass. Building per-file lineage + provenance + location tracking by
  hand reimplements git-annex badly. Existing TS `ipfs-pinner` is reused
  as the underlying Kubo client through the Kubo HTTP API, so there is
  no language coupling penalty.
- **DVC + S3** — rejected (centralized backend; can't be reframed as a
  kotoba-datomic-projection because it isn't derived from MST).
- **Hugging Face Hub direct reference (no local pin)** — rejected (no
  reproducibility guarantee).
- **DataLad + git-annex with IPFS as a `type=external externaltype=ipfs`
  special remote** (community impls e.g. `paperbenni/git-annex-remote-ipfs`)
  — rejected on operational grounds: every in-the-wild implementation
  returns FAILURE for `CHECKPRESENT` (IPFS has no reliable "is this CID
  pinned by my node" query without trust) and FAILURE for `REMOVE`
  (IPFS immutability). With `CHECKPRESENT` always false, git-annex
  re-uploads on every `copy --to ipfs` unless the remote is marked
  trusted, and the lack of `REMOVE` makes `git annex drop --from ipfs`
  a no-op. The sidecar pinner sidesteps both classes of failure by
  letting git-annex see only the `directory` remote and tracking IPFS
  CIDs in a separate map.
- **DataLad + git-annex with rsync / WebDAV / S3 special remote** —
  rejected: centralized server is the same anti-pattern as DVC + S3
  (ADR-2605172000 RW-free substrate). The `directory` remote on a
  per-machine volume is local-first and substrate-compliant.
- **One unified `pinner` tool for both MST CARs and datasets** —
  rejected on separation-of-concerns grounds (MST CARs are
  firehose-driven and license-free; datasets are operator-driven and
  Charter-gated).

# Verification (smoke test, 2026-05-24 JST)

End-to-end Phase-1 path exercised on the deciding Mac:

1. Kubo 0.41.0 installed via brew and initialized at
   `/Volumes/260317/etzhayyim/ipfs-data` (peer ID
   `12D3KooWGRnHP5hHAxSnPQE5gopDqAzWkZ2NAFi2ZZ6o85FnAiEc`); launchd plist
   at `~/Library/LaunchAgents/com.etzhayyim.kubo.plist` with `KeepAlive →
   PathState` so the daemon only runs while the external volume is
   mounted.
2. DataLad 1.4.1 superdataset created at `90-docs/baien/datasets/` with
   `git annex initremote local-store type=directory
   directory=/Volumes/260317/etzhayyim/annex-store/superdataset
   encryption=none chunk=64MiB`.
3. Two random 2 KiB / 3 KiB blobs were `git annex add`ed in the
   superdataset and `git annex copy --to local-store` mirrored them to
   the directory remote (on-disk leaves under the standard 3-level
   git-annex fanout).
4. `e7m-dataset publish-ipfs superdataset --git-commit <sha>
   --append-manifest --name local:smoke-test-adr-2605241500 ...` walked
   the directory remote, ran `POST /api/v0/add?cid-version=1&pin=true`
   per object, composed the map JSON, pinned it, and returned the map
   CID `bafkreiep2df7htkfdkzamahpbr6gmqatmkfxth2fzl3nmizd2ksldf5z2q`.
5. `ipfs cat <map_cid>` returned the map JSON with 2 entries; `ipfs cat
   <entry_cid>` for the first entry returned bytes whose SHA-256
   matched the original on-disk blob exactly
   (`a90e658f...`).
6. `90-docs/baien/datasets.jsonl` received the corresponding manifest
   row; `pds.build_record()` produced a structurally valid
   `com.etzhayyim.substrate.datasetPin` body (dry-run output — PDS
   network wiring deferred).

Status implication: D1–D8 are reachable in the current toolchain;
remaining gaps (HF `add` flow, real PDS emit, scanner availability,
SHA256E backend default, second always-on replica) are tracked as
follow-ups and listed in Consequences §Negative.

# References

- ADR-2605170900 (root ADR canonical home)
- ADR-2605171800 (MST → IPFS → L2 anchor pipeline — ipfs-pinner)
- ADR-2605172000 (RW-free substrate — prohibits centralized DB)
- ADR-2605192200 (Charter Compliance Rider v2.0 — §2 prohibited categories)
- ADR-2605231300 (baien-distill ReAct loop — primary dataset consumer)
- ADR-2605232500 (baien-mx-move1 image-graft self-training — image consumer)
- DataLad handbook: https://handbook.datalad.org/
- git-annex special remotes: https://git-annex.branchable.com/special_remotes/
- `50-infra/ipfs-pinner/src/providers/kubo.ts` — Kubo HTTP client used by `ipfs-pinner` (shared network contract, not a shared library)
- `00-contracts/lexicons/com/etzhayyim/substrate/datasetPin.json` — receipt lexicon (created with this ADR)
- `70-tools/e7m-dataset/` — operator wrapper (Phase 1: `where`, `publish-ipfs`)
- `90-docs/baien/datasets/README.md` — superdataset entry point
