# kotoba-b2-pin — Backblaze B2 cold-pin for the kotoba IPFS block store

DataLad + git-annex durable off-host tier for kotoba's content-addressed blocks.
Mirrors every block in the local kubo repo to **Backblaze B2** (S3-compatible)
through a git-annex special remote, and restores it on demand. This is the
sanctioned **DataLad + git-annex + IPFS-pinner** pattern (ADR-2605241500),
applied to the kotoba substrate's cold tier.

## Why (empirical)

kotoba's canonical state is the **Datom log**; IPFS is its cold *block* backend
(ADR-2605312345). Today that backend is a **single local copy** on one external
volume — no replication to B2 / ipfs.etzhayyim.com / kotobase.etzhayyim.com (all currently
disabled). One disk loss = data loss.

Backing up the *graph heads* alone is not enough: `ipfs dag export` of all IPNS
heads totals ~5 KB (commits are deltas with `covering_n=0`, no exportable parent
chain), while the real durable data is **26k+ flatfs blocks / ~3.3 GB**. So the
pin must mirror the **block store itself**, not the head DAGs.

The kubo block store is **multihash-keyed**: `ipfs refs local` enumerates every
block as a `raw`-codec CID, and a block's bytes restored under *any* codec are
still resolvable by the original `dag-cbor`/`dag-pb` CID (verified). So mirroring
the raw-CID block set is complete and codec-safe.

## How

```
ipfs refs local ──▶ for each new block:
   block/get ─▶ blocks/<shard>/<cid> ─▶ git annex add ─▶ git annex copy --to b2 ─▶ git annex drop
                                          (DataLad dataset)        (Backblaze B2)     (no 3rd local copy)
restore:  git annex get --from b2 ─▶ ipfs block put ─▶ multihash restored (kotoba reads by original CID)
```

* **Incremental** — `meta/backed.txt` records what's already on B2; reruns only
  push new blocks.
* **No disk duplication** — local annex object is dropped right after the copy
  to B2 succeeds; the bytes live in kubo + B2.
* **Durable roots** — each run also snapshots the signed IPNS head records
  (`meta/ipns-heads.*.json`, small, kept in git) so graph roots are recoverable.

## Charter / substrate compliance

* **Secrets never committed** (CLAUDE.md): B2 credentials are read at runtime
  from **1Password** via `op` into the child env only (`AWS_ACCESS_KEY_ID` /
  `AWS_SECRET_ACCESS_KEY`, which git-annex's S3 backend consumes).
  `embedcreds=no` — nothing lands in the repo or the annex config.
* **Not a parallel canonical state** — this is a colder tier *under* IPFS,
  storing opaque content-addressed blocks; the Datom log remains the SSoT.
* **No server key** — this is read/replicate-only infrastructure (no signing).

## Usage

```bash
cd 50-infra/kotoba-b2-pin

# 0) unlock 1Password (interactive — run yourself):
#    ! eval $(op signin)
# Point _lib.sh at the real B2 item if needed:
#    export B2_OP_KEYID_REF='op://Private/Backblaze B2 — kotoba/access key id'
#    export B2_OP_SECRET_REF='op://Private/Backblaze B2 — kotoba/secret access key'
#    export B2_KOTOBA_BUCKET=etzhayyim-kotoba-blockstore   # must exist in B2

# 1) one-time: create dataset + B2 special remote
bin/init-store.sh

# 2) snapshot (mirror new blocks to B2). Batchable:
KOTOBA_B2_MAX=2000 bin/pin-snapshot.sh     # first runs in chunks; omit MAX for all
# schedule periodically (launchd/cron) for ongoing durability.

# 3) disaster restore (B2 -> live kubo):
bin/restore.sh
#    then (gated) re-seed heads: stop kotoba, cp meta/ipns-heads.latest.json
#    -> ~/.local/kotoba-etzhayyim/sled/ipns-heads.json, restart.
```

### Self-test (no credentials)

Exercises the full add → copy → drop → get → block-put → CID-verify cycle against
a local `directory` special remote:

```bash
export KOTOBA_B2_STORE=/tmp/kotoba-b2-selftest/store B2_TEST_DIR=/tmp/kotoba-b2-selftest/remote
bin/init-store.sh --test-only
KOTOBA_B2_MAX=50 B2_ANNEX_REMOTE=b2-localtest bin/pin-snapshot.sh
KOTOBA_B2_MAX=1  B2_ANNEX_REMOTE=b2-localtest bin/restore.sh     # loss-recovery verified
```

## Config (env, see `bin/_lib.sh`)

| var | default | meaning |
|---|---|---|
| `KOTOBA_B2_STORE` | `/Volumes/260317/etzhayyim/kotoba-b2-pin-store` | DataLad dataset (annex index) |
| `KOTOBA_IPFS_API` | `http://127.0.0.1:5001` | kubo RPC |
| `B2_S3_HOST` | `s3.us-west-004.backblazeb2.com` | B2 S3 endpoint (deps.toml convention) |
| `B2_KOTOBA_BUCKET` | `etzhayyim-kotoba-blockstore` | B2 bucket (must exist) |
| `B2_ANNEX_REMOTE` | `b2` | git-annex remote name |
| `B2_OP_ITEM` / `B2_OP_VAULT` | `Backblaze B2 — etzhayyim kotoba` / `Private` | 1Password lookup |
| `B2_OP_KEYID_REF` / `B2_OP_SECRET_REF` | — | explicit `op://…` refs (override item lookup) |

## Status

* ✅ Mechanism verified end-to-end (snapshot + loss-recovery) via local remote.
* ⏳ Live B2 leg pending: 1Password unlock + confirmed bucket/region. The B2
  path is identical to the verified path — only the special-remote type differs
  (`directory` → `S3`).
