# Resident etzhayyim atproto PDS — make `atproto.etzhayyim.com` independent

Goal: serve `atproto.etzhayyim.com` from **this repo's independent clj+kotoba PDS**
(`did:web:atproto.etzhayyim.com`, `availableUserDomains: ["etzhayyim.com"]`) instead
of the gftd.ai PDS worker it currently aliases (`did:web:atproto.gftd.ai`).

## Status (2026-06-24)

- **Resident PDS: DONE** — running as a self-healing macOS LaunchDaemon on the
  murakumo fleet node `asher`, verified end-to-end (createRecord → getRecord on
  `did:web:atproto.etzhayyim.com`). Survives reboot + crash (`RunAtLoad` +
  `KeepAlive`). This breaks the gftd.ai dependency for the storage layer.
- **Public hostname cutover: founder step** — pointing `atproto.etzhayyim.com` at
  the resident PDS needs a Cloudflare Tunnel, which requires a browser login
  (`cloudflared tunnel login`) only the operator can do.

## 1. Resident PDS (reproducible — already applied on `asher`)

```bash
HOST=asher                       # any always-on fleet node
ssh $HOST 'mkdir -p ~/.etzhayyim-pds/bin'
rsync -az $(which bb) $HOST:.etzhayyim-pds/bin/bb        # babashka (single binary)
rsync -az --exclude .cpcache src bb.edn did.json $HOST:.etzhayyim-pds/
# install the LaunchDaemon (system domain → headless, no GUI session needed)
cat deploy/resident/com.etzhayyim.atproto-pds.plist | \
  ssh $HOST 'sudo tee /Library/LaunchDaemons/com.etzhayyim.atproto-pds.plist >/dev/null && \
             sudo launchctl bootstrap system /Library/LaunchDaemons/com.etzhayyim.atproto-pds.plist'
# verify
ssh $HOST 'curl -s localhost:9911/xrpc/com.atproto.server.describeServer'
```

## 2. Public hostname cutover (operator — needs Cloudflare login)

```bash
ssh $HOST
brew install cloudflared
cloudflared tunnel login                       # ← browser auth (operator only)
cloudflared tunnel create etzhayyim-pds        # writes ~/.cloudflared/<uuid>.json
# put deploy/resident/cloudflared-config.yml at ~/.cloudflared/config.yml
#   (set tunnel: <uuid> + credentials-file to the generated json)
cloudflared tunnel route dns etzhayyim-pds atproto.etzhayyim.com
# run cloudflared resident (LaunchDaemon) so it survives reboot:
sudo cloudflared service install
```

After this, `https://atproto.etzhayyim.com/xrpc/com.atproto.server.describeServer`
returns `did:web:atproto.etzhayyim.com` (the independent PDS), not gftd's. Flip the
apex DNS / Worker so the etzhayyim DID document advertises this PDS as the actor
service endpoint.

## 3. Durability — DONE

The resident PDS persists to a **durable on-disk datom log**: set
`PDS_STORE_PATH=/Users/asher/.etzhayyim-pds/repo.edn` (now in the plist). Every
record write is write-through to an append-only EDN journal and replayed on boot,
so records **survive a restart** with no external service. (Setting `KOTOBA_URL`
instead routes to the live kotoba engine; `store.clj` `KotobaStore` is the
engine-backed variant.) Verified live on `asher`.

## 4. Federation sync surface — R1 implemented

`com.atproto.sync.{getRepo,getLatestCommit,listRepos}` are served (`repo.clj`):
- **DAG-CBOR** deterministic encoder (validated against the canonical IPLD vector:
  `cid({}) == bafyreigbtj4x7ip5legnfznufuopl4sg4knzc2cof6duas4b3q2fy6swua`),
- **CIDv1** (dag-cbor / sha2-256),
- an **MST** over the repo records (atproto reference layering, 2 zero-bits/level),
- an **Ed25519-signed commit** (`sig` over the dag-cbor commit; sign/verify tested),
- **CAR v1** serialization. `getRepo` returns `application/vnd.ipld.car`.

**Remaining federation step**: publish the commit signing key in the did:web
document (`config.clj` `verificationMethod`) so a relay can verify `sig`, then
register the repo with a relay (`com.atproto.sync.subscribeRepos` firehose is the
further R2). Until then the PDS *serves* a well-formed, signed repo CAR but is not
yet crawled by the public network.
