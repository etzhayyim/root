# yoro feed → kotoba read-path — deploy runbook (ADR-2606013200)

The yoro AppView feed (`etzhayyim.com` posts / profiles / follows) reads from the
**kotoba canonical Datom log** instead of the superseded kotoba-datomic-projection.
Data flow:

```
etzhayyim.com/xrpc/app.bsky.feed.getDiscoverFeed
  → etzhayyim-did-web worker (alias → com.etzhayyim.yoro.feed.*, YORO_XRPC)
  → yoro-xrpc-adapter  (KOTOBA_URL + YORO_GRAPH_CID)
  → @etzhayyim/yoro-rw-free → kotoba datomic.datoms
  → kotoba `yoro-social-v1` graph (Public) → :yoro/* datoms → feed JSON

ingest (operator-local, write): etzhayyim PDS repos / seed
  → datomic.transact (operator bearer, 127.0.0.1:8077) → :yoro/* datoms
```

## Landed (this change)

- **kotoba**: `yoro-social-v1` graph registered **Public** at boot
  (`crates/kotoba-server/src/server.rs`); binary rebuilt + reinstalled to
  `~/.local/bin/kotoba`; daemon restarted. Graph CID
  `bafyreibljg5gzye47fldkfq6m4vgy55kcjyez2vx432dubttou36g5yryq`
  (= `KotobaCid::from_bytes("yoro-social-v1")`).
- **rw-free**: `src/kotoba.ts` client + all 8 feed/graph/actor reads migrated to
  `datomic.datoms`; `EtzhayyimConfig.{kotobaUrl,yoroGraphCid}` added (sdk +
  sdk-auth). 32 vitest green.
- **adapter**: `KOTOBA_URL=https://kotoba.etzhayyim.com` + `YORO_GRAPH_CID`
  wired; **deployed** (`yoro-xrpc-adapter`).
- **tunnel**: dedicated `kotoba-etzhayyim` tunnel
  (`cbfcb9d5-a9a2-4db0-88b6-03fd0c1e24c7`) ingress made **READ-ONLY** for
  `kotoba.etzhayyim.com` (only `datomic.datoms`-family reads + `/health`; all
  writes → 403). Config: `~/.cloudflared/kotoba-etzhayyim.yml`. Running.
- **deps.toml**: `kotoba.etzhayyim.com` DNS row added.

## REMAINING — one operator step (needs the etzhayyim.com CF credential)

Create the CNAME in the **etzhayyim.com** zone (the `cloudflared` cert here is
etzhayyim.ai-scoped, and the assistant's wrangler token is `zone:read` only):

- **Dashboard**: etzhayyim.com → DNS → Add record
  - Type `CNAME`, Name `kotoba`,
    Target `cbfcb9d5-a9a2-4db0-88b6-03fd0c1e24c7.cfargotunnel.com`, Proxied ✅
- **or CLI** (re-auth cloudflared for the etzhayyim.com zone first):
  ```
  cloudflared tunnel login                 # pick the etzhayyim.com zone
  cloudflared tunnel route dns kotoba-etzhayyim kotoba.etzhayyim.com
  ```

## Verify (after the CNAME exists)

```
curl https://kotoba.etzhayyim.com/health                       # 200
curl -X POST https://kotoba.etzhayyim.com/xrpc/com.etzhayyim.apps.kotoba.datomic.transact \
  -H 'content-type: application/json' -d '{"graph":"x","tx_edn":"[]"}'   # 403 (write blocked)
curl "https://etzhayyim.com/xrpc/app.bsky.feed.getDiscoverFeed?limit=5"  # feed has posts
```
Then hard-reload `https://etzhayyim.com/` — posts render.

## Re-ingest / add content

Member repos are currently empty; the feed shows seeded etzhayyim announcements.
To pull etzhayyim member repos (when they have posts) or re-seed:

```
cd 60-apps/etzhayyim-project-yoro/rw-free
KOTOBA_OPERATOR_DID=did:key:ze2e169933f9bcc6cb218e083b3d2a80c5a5a2b92fbf3cb41b4d5283ce3f6939f \
  npx tsx scripts/ingest-to-kotoba.ts did:web:etzhayyim.com [more dids...]
```
(`KOTOBA_OPERATOR_DID` = the kotoba node DID from `~/.local/kotoba-etzhayyim/serve.log` `did=…`.)

## Write-cost economy — LIVE (ADR-2606013400)

`datomic.transact` now charges **mKOTO per datom** (`KOTOBA_WRITE_COST_MKOTO_PER_DATOM=10`
in the launchd plist). Operator (node owner) is exempt/unlimited; external
(CACAO) writers must hold mKOTO or get **HTTP 402**. Operator mints via
`econ.credit`. Verified live: `econ.balance` (external=0, enabled, cost=10),
`econ.credit` (operator-only, funds a DID), operator transact exempt (200).
Implementation: `40-engine/kotoba/crates/kotoba-server/src/econ.rs` + the
`datomic_transact` charge. Kill-switch: set the env to `0` and restart.

```
# read a DID's balance
curl -X POST https://kotoba.etzhayyim.com/xrpc/com.etzhayyim.apps.kotoba.econ.balance \
  -H 'content-type: application/json' -d '{"did":"did:key:..."}'
# operator mint (needs operator Bearer)
curl -X POST http://127.0.0.1:8077/xrpc/com.etzhayyim.apps.kotoba.econ.credit \
  -H "authorization: Bearer <operator-jwt>" -H 'content-type: application/json' \
  -d '{"did":"did:key:...","amount_mkoto":5000}'
```

## Notes / follow-ups

- **✅ Durability — graph heads survive restart (ADR-2606013600).** kotoba's
  datomic IPNS heads are now **disk-persistent** by default: `PersistentIpnsRegistry`
  mirrors each head to `${KOTOBA_STORE_PATH}/ipns-heads.json` (atomic write) and
  reloads it at boot. Verified: transact → restart → feed still serves (no
  re-ingest; boot log `IPNS Registry: disk-persistent graph heads heads=N`).
  Blocks remain in the Kubo cold tier; head + blocks ⇒ full recovery. Selection
  via `KOTOBA_IPNS`: unset = persistent (default), `kubo` = distributed Kubo IPNS,
  `memory` = ephemeral (tests). **Caveat**: block durability still needs the Kubo
  daemon up at publish time — if Kubo is down, blocks are hot-only and a restart
  loses data regardless of the head.
- **Availability**: kotoba is the dev Mac's launchd daemon (`com.etzhayyim.kotoba`)
  + tunnel; same posture as geth/pds. Depends on the local Kubo IPFS daemon
  (`127.0.0.1:5001`) — if Kubo is down, kotoba fails SovereignCrypto genesis on
  restart (start `IPFS_PATH=/Volumes/260317/etzhayyim/ipfs-data ipfs daemon`).
  After a binary swap, the launchd job only re-execs on a real process exit —
  kill the old PID (or `bootout`+`bootstrap`) if `kickstart` leaves it running.
- **CACAO-write 402** is unit-tested + logically guaranteed (charge runs after
  auth) but not curl-proven: a transact CACAO needs both `datom:transact` +
  `tx:create` capabilities, which `kotoba cacao-sign` (single `--capability`)
  doesn't cleanly emit. Better CACAO tooling (multi-capability) would close this.
- **kotoba.etzhayyim.com** ingress (full API, operator bridge) is left as-is but is not
  cleanly serving (404/timeout); lock down or remove separately if unused.
