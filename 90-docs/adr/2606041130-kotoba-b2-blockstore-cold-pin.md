---
id: adr-2606041130-kotoba-b2-blockstore-cold-pin
title: "ADR-2606041130: kotoba IPFS block-store off-host cold pin to Backblaze B2 (DataLad + git-annex)"
status: accepted
doc_type: adr
topic: kotoba-b2-blockstore-cold-pin
authoritative: true
last_verified: 2026-06-04
priority: 6.0
axis: architecture
weight: 0.62
priority_note: "Durability of the canonical Datom log substrate"
authoritative_for:
  - 50-infra/kotoba-b2-pin
depends_on:
  - "2605262130"
  - "2605312345"
  - "2605241500"
  - "2605231525"
related:
  - "2605215000"
  - "2606012100"
supersedes: []
superseded_by: []
---

# ADR-2606041130: kotoba IPFS block-store off-host cold pin to Backblaze B2

**Status**: accepted
**Date**: 2026-06-04
**Deciders**: Jun Kawasaki

# Context

The kotoba Datom log is the canonical state (ADR-2605312345); IPFS is its cold
**block backend** (DAG-CBOR/IPLD blocks, ProllyTree index nodes, commit blocks).
As of this ADR the running node persisted those blocks to **one local Kubo
repo only** (flatfs on a single external volume). Empirical findings during the
2026-06-04 durability review:

- The local Kubo repo held **26,634 blocks / ~3.3 GB**; there was **no
  replication** to any off-host tier (B2, `ipfs.gftd.ai`, `kotobase.gftd.ai` all
  disabled — `KOTOBA_IPFS_PIN_ENDPOINT`/`KOTOBA_IPFS_PIN_JWT` unset, `peer_count=0`).
  A single disk loss = data loss.
- Backing up only the **graph heads** is insufficient: `ipfs dag export` of every
  IPNS head totals ~5 KB because commits are deltas with `covering_n=0` (no
  exportable parent chain). The durable unit is the **block store itself**.
- The kubo block store is **multihash-keyed**: `ipfs refs local` enumerates every
  block as a `raw`-codec CID, and bytes restored under any codec are still
  resolvable by their original `dag-cbor`/`dag-pb` CID (verified). So mirroring
  the raw-CID block set is complete and codec-safe.

A durable, off-host, content-addressed backup tier is required — implemented
in-repo with the sanctioned **DataLad + git-annex + IPFS-pinner** pattern
(ADR-2605241500), not a new bespoke service.

# Decision

Add `50-infra/kotoba-b2-pin/` — a DataLad dataset whose **git-annex S3 special
remote** targets **Backblaze B2** (S3-compatible) and mirrors the kotoba IPFS
block store, with disaster restore back into a live Kubo.

- **Snapshot** (`pin-snapshot.sh`): for every block in `ipfs refs local` not yet
  recorded as backed, fetch raw bytes (`block/get`), `git annex add` keyed by the
  block CID, `git annex copy --to b2`, then **drop the local annex object** (bytes
  live in Kubo + B2 — no third local copy). Incremental via `meta/backed.txt`,
  self-healing (reconciles from `git annex find --in b2` on start), and resilient
  (a transient per-block B2 error never aborts the run; only blocks confirmed on
  the remote are recorded/dropped). Also snapshots the signed IPNS head records.
- **Restore** (`restore.sh`): `git annex get --from b2` → `ipfs block put`
  (codec-aware) → multihash restored; kotoba re-fetches by the original CID.
- **Init** (`init-store.sh`): `datalad create` + `git annex initremote b2 type=S3
  host=s3.us-west-004.backblazeb2.com bucket=ai-gftd-datasets
  fileprefix=kotoba-blockstore/ datacenter=us-west-004 signature=v4
  encryption=none embedcreds=no`.
- **Secrets**: B2 credentials are read at runtime from **1Password**
  (`op://gftdcojp/gftd.b2/datasets`) into `AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY`
  for the child process only. `embedcreds=no` — nothing is written to the repo,
  the dataset, or the git-annex config (CLAUDE.md "Do not commit secrets";
  consistent with the deps.toml B2 Stage-D credential inventory).

The pin is an **even-colder tier under IPFS**, storing opaque content-addressed
blocks. It is **not a parallel canonical state** (the Datom log remains the SSoT,
ADR-2605262130 + 2605312345) and holds **no server signing key** (replicate-only,
ADR-2605231525).

# Consequences

- kotoba blocks gain an off-host durable copy on B2 (868 GB-free volume vs the
  near-full internal disk). Restore is verified: `block rm` from Kubo →
  `restore.sh` from B2 → block re-present (957 B), end-to-end against real B2.
- The B2 mirror is **periodic / point-in-time**, not synchronous: blocks written
  after a snapshot are not on B2 until the next run. Continuous durability
  requires either a scheduled incremental `pin-snapshot` (recommended follow-up,
  launchd timer) or enabling kotoba's native remote-pin fanout
  (`KOTOBA_IPFS_PIN_ENDPOINT` → kotobase, a separate path).
- Operational: a single `pin-snapshot` run loads B2 creds once at start; 1Password
  CLI approval friction means the full 26k-block backfill should run as one
  resilient, resumable job. The dataset's git-annex index is the durable record
  of what is backed.
- ZERO Charter invariant amendments. Verified end-to-end: snapshot 100 blocks →
  B2 (`git annex find --in b2`=100), loss-recovery from B2.

# Alternatives Considered

- **Head-DAG CAR export** (`ipfs dag export` per IPNS head → CAR in DataLad):
  rejected — captures only ~5 KB; deltas are not transitively linked, so it does
  not back up the block store.
- **rclone/rsync the flatfs `blocks/` directory** directly to B2: rejected as the
  primary path — flatfs is keyed by multihash and loses the CID codec, and it is
  not DataLad/git-annex tracked (no per-block provenance/dedup index). Kept as a
  documented faster alternative for bulk cold archive.
- **kotobase / ipfs.gftd.ai remote-pin fanout** (`KOTOBA_IPFS_PIN_ENDPOINT`):
  complementary, not exclusive — a synchronous in-process path that needs a live
  pin endpoint + JWT. B2-pin is the out-of-band, operator-run durability floor;
  both can run together.
- **S3-backed datastore plugin (s3ds) in Kubo**: rejected — couples the live
  daemon to B2 latency/availability; the cold pin keeps the hot path local.

# References

- 90-docs/adr/2605262130-kotoba-storage-substrate-unification.md
- 90-docs/adr/2605312345-kotoba-datom-first-class-canonical-state.md
- 90-docs/adr/2605241500-etzhayyim-dataset-cid-substrate.md
- 90-docs/adr/2605231525 (no-server-key invariant)
- 50-infra/kotoba-b2-pin/README.md
- 40-engine/kotoba/docs/kotoba-datomic-architecture.svg
