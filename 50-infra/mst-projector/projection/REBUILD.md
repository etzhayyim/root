# Rebuilding the feed-discover projection (L0)

Per ADR-2605231500 §"The 'rebuild' requirement" — this projection is
kotoba-datomic-compliant only if there is a documented, operator-state-free
procedure that reproduces the projection from `kotoba-datomic-chain` (PDS
MST) alone.

## Inputs

The rebuild requires only:

1. Access to a PDS that hosts (or federates with) `did:web:yoro.etzhayyim.com`
   and any other DIDs whose posts should appear in Discover.
2. Credentials for the projector DID's own PDS session (so the rebuilt
   snapshot can be re-emitted under the same identity). Per ADR-2605231525,
   these are *not* platform-held keys — they live in the operator's macOS
   Keychain (`service=etzhayyim, account=PROJECTOR_PDS_SESSION`) or 1Password.

No other state is required. There is no DB to back up, no KV namespace,
no Iroh blob to download.

## Procedure

```sh
# 1. Stop the live projector so the cursor file is quiescent.
launchctl stop com.etzhayyim.mst-projector  # or k3s equivalent

# 2. Move the cursor + any cached state out of the way (purely a safety
#    net — the daemon will rebuild from cursor 0 either way).
mv /data/mst-projector/firehose.cursor /data/mst-projector/firehose.cursor.bak

# 3. Optionally delete prior `com.etzhayyim.projection.feedDiscover`
#    records under the projector DID. They will continue to exist as
#    history; the rebuild appends fresh snapshots ordered by TID, so the
#    "latest snapshot wins" read semantics still hold without deletion.
#    Skip this step unless you need bit-exact replacement.

# 4. Start the projector with cursor 0:
ETZ_PROJECTOR_PDS_SESSION="$(security find-generic-password \
   -s etzhayyim -a PROJECTOR_PDS_SESSION -w)" \
ETZ_PROJECTOR_DID="did:web:projector.etzhayyim.com" \
ETZ_PROJECTOR_PDS_URL="https://pds.etzhayyim.com" \
ETZ_PROJECTOR_COLLECTIONS="com.etzhayyim.,com.etzhayyim.apps.,app.bsky.feed." \
ETZ_PROJECTOR_FLUSH_RECORDS=1000 \
ETZ_PROJECTOR_FLUSH_SECONDS=60 \
ETZ_PROJECTOR_IPFS_API_URL="http://localhost:5001" \
node dist/index.js
```

The first snapshot record under
`com.etzhayyim.projection.feedDiscover` will appear once the firehose has
caught up to the present and the first flush boundary fires (default:
1000 records OR 60 seconds, whichever first).

## Verifying the rebuild

```sh
# Fetch the most-recent snapshot:
curl -s \
  "https://pds.etzhayyim.com/xrpc/com.atproto.repo.listRecords?repo=did:web:projector.etzhayyim.com&collection=com.etzhayyim.projection.feedDiscover&limit=1&reverse=true" \
  | jq '.records[0].value | {snapshotAt, cursor, totalSeen, items: (.items | length)}'

# Cross-check item count against what listRecords returns for one source DID:
curl -s \
  "https://pds.etzhayyim.com/xrpc/com.atproto.repo.listRecords?repo=did:web:yoro.etzhayyim.com&collection=app.bsky.feed.post&limit=100" \
  | jq '.records | length'
```

If the snapshot's `totalSeen` is at least as large as the sum of
`listRecords` counts across all source DIDs, the rebuild is consistent.

## Conformance level

Currently **L0-projection** (manifest + this runbook, manual rebuild). Upgrade to
L1 lands when `test/feed-discover.replay.test.ts` exists and runs in CI;
upgrade to L2 lands when a 1% byte-identical random-slice replay is part
of pre-deploy gates.

## When *not* to rebuild

- A single missed post: the live projector picks it up on next firehose
  message. No rebuild needed.
- A clock-skewed `indexedAt`: the daemon clamps future-dated posts to
  wall-clock at observation; rebuild does not change this.
- A bad verdict from `FeedPostCell`: re-emit the membrane verdict; the
  projection consumes the latest verdict on next snapshot boundary.

Rebuild only when the projection's invariants are demonstrably violated
(e.g., `totalSeen` smaller than known post count, items missing from a
DID that has clearly posted). The cost is real (~60 minutes of replay
for a low-volume month) so investigate first.
