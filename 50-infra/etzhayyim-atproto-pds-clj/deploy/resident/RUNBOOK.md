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

## 3. Durability + federation (follow-ups)

- **Data durability across PDS restarts**: the resident PDS runs on the in-process
  `MemStore`. Set `KOTOBA_URL=http://localhost:8077` (the co-located kotoba mesh
  node) once `store.clj`'s `KotobaStore` is wired to a verified kotoba write
  endpoint — then records persist to the append-only kotoba Datom log.
- **Federation** (so posts appear on AppViews/relays): implement
  `com.atproto.sync.{getRepo,getBlocks,subscribeRepos}` + MST/CAR (the PDS README's
  R1) and register the repo with a relay. Until then the PDS stores + serves
  records but does not federate into the public bsky network.
