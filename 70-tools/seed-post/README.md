# @etzhayyim/seed-post

Step 1 of "display posts on https://etzhayyim.com/ via kotoba-datomic".

Writes a single `app.bsky.feed.post` record into the operator DID's MST so
the substrate read path returns a non-empty feed. See ADR-2605172000 and
kotoba-datomic SPEC §1 + §2.

## Usage

```sh
cd 70-tools/seed-post

# One-time Keychain provisioning (macOS):
security add-generic-password -s etzhayyim -a PDS_HANDLE       -w '<your-handle>'
security add-generic-password -s etzhayyim -a PDS_APP_PASSWORD -w '<app-password>'

# Post:
./bin/seed-post.sh "hello kotoba-datomic"

# Verify:
curl -s 'https://etzhayyim.com/xrpc/app.bsky.feed.getTimeline?limit=5' | jq
```

## Env

| Var | Default | Required? |
|---|---|---|
| `PDS_URL` | `https://pds.etzhayyim.com` | no |
| `ACTOR_DID` | `did:web:yoro.etzhayyim.com` | no — overridden by the actual session DID |
| `PDS_HANDLE` | (from Keychain) | yes (or `ETZ_PROJECTOR_PDS_SESSION`) |
| `PDS_APP_PASSWORD` | (from Keychain) | yes (or `ETZ_PROJECTOR_PDS_SESSION`) |
| `ETZ_PROJECTOR_PDS_SESSION` | — | alternative resumable session (matches mst-projector/emit.ts shape) |
| `SEED_POST_TEXT` | (positional argv) | no |

## Why not the SDK?

`@etzhayyim/sdk.write()` adds IPFS pin + L2-anchor-pending bookkeeping. For
the minimal seed we only need the AT-Protocol write. The mst-projector + the
anchor-cron pick up the new commit from the firehose automatically.

When kotoba-datomic §4 membrane lands (Step 2), this CLI will route writes
through the LangGraph `feed_post` cell verdict gate instead of the bare
`com.atproto.repo.createRecord` call.
