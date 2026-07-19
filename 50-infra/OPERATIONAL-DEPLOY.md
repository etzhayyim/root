# Substrate pipeline — operational deploy runbook

Operator-side runbook for the substrate pipeline (mst-projector → ipfs-pinner → anchor-cron) per [ADR-2605171800](../90-docs/adr/2605171800-langgraph-mst-ipfs-l2-anchor-pipeline.md). Code is on `main`; this file lists the remaining gates that require credentials, infrastructure, or network access only the operator has.

**Status (2026-05-21 session close)**:

| Gate | State |
|---|---|
| Code: mst-projector Phase 2 + ipfs-pinner Stage 4 + anchor-cron substrate mode + Anvil smoke | ✅ on `main` |
| Code: substrate DID Workers x 3 (projector / pinner / anchorer) | ✅ on `main` |
| Operational deploy | ⏳ this runbook |

Five gates remain, ordered by dependency. Each step lists pre-reqs + exact commands + verification.

---

## Gate 1 — Cloudflare DNS AAAA records

**Pre-req**: Cloudflare API token with `Zone:Edit` for the `etzhayyim.com` zone (or web UI access to the Cloudflare dashboard).

Three new subdomains need AAAA records so wrangler can bind Workers to them:

| Subdomain | Type | Value |
|---|---|---|
| `projector.etzhayyim.com` | AAAA | `100::` (proxied) |
| `pinner.etzhayyim.com` | AAAA | `100::` (proxied) |
| `anchorer.etzhayyim.com` | AAAA | `100::` (proxied) |

The `100::` placeholder + Cloudflare proxy is the same pattern as the existing `etzhayyim.com` zone apex (set 2026-05-15 per `deps.toml [platform.dns]`). Workers handle the actual response; the AAAA only needs to exist + be proxied so the route binding works.

### Commands

```bash
# Web UI (simplest):
#   1. Cloudflare dashboard → etzhayyim.com → DNS → Records
#   2. Add Record × 3 (Type: AAAA, Name: projector / pinner / anchorer,
#      IPv6: 100::, Proxy: Proxied, TTL: Auto)

# API equivalent (CF_API_TOKEN scoped to the zone):
ZONE_ID="$(curl -s -H "Authorization: Bearer $CF_API_TOKEN" \
  "https://api.cloudflare.com/client/v4/zones?name=etzhayyim.com" \
  | jq -r '.result[0].id')"

for sub in projector pinner anchorer; do
  curl -s -X POST \
    -H "Authorization: Bearer $CF_API_TOKEN" \
    -H "Content-Type: application/json" \
    "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records" \
    -d "{\"type\":\"AAAA\",\"name\":\"$sub\",\"content\":\"100::\",\"proxied\":true}"
  echo
done
```

### Verify

```bash
for sub in projector pinner anchorer; do
  dig +short "$sub.etzhayyim.com" AAAA | head -1
done
# Expected: each returns a Cloudflare proxy IP (e.g. 2606:4700:...)
```

---

## Gate 2 — Wrangler deploy of the 3 DID Workers

**Pre-req**: `wrangler` installed (`npm i -g wrangler`) + authenticated to the Cloudflare account that owns `etzhayyim.com` (`wrangler login`).

Each Worker is a stand-alone package; deploy in any order.

```bash
for actor in projector pinner anchorer; do
  cd /path/to/etzhayyim-root/50-infra/etzhayyim-${actor}-did-web
  npm install
  wrangler deploy
  cd -
done
```

### Verify

```bash
for actor in projector pinner anchorer; do
  echo "=== did:web:$actor.etzhayyim.com ==="
  curl -s -o /dev/null -w "%{http_code}\n" \
    "https://$actor.etzhayyim.com/.well-known/did.json"
  # Expected: 200
done

# Universal Resolver cross-check:
for actor in projector pinner anchorer; do
  curl -s "https://dev.uniresolver.io/1.0/identifiers/did:web:$actor.etzhayyim.com" \
    | jq -r '.didDocument.id'
  # Expected: each returns "did:web:<actor>.etzhayyim.com"
done
```

If any returns 404 / 522 / 530, check (a) DNS AAAA is set + proxied; (b) `wrangler.toml` route `zone_name` matches; (c) wrangler shows a successful deploy URL.

---

## Gate 3 — EtzhayyimAnchor deploy on Base Sepolia

**Pre-req**: A funded EOA on Base Sepolia (testnet faucet at https://www.alchemy.com/faucets/base-sepolia or https://www.coinbase.com/faucets/base-ethereum-goerli-faucet). 0.02 ETH is more than enough for the deploy + a few hundred anchor txs.

### Commands

```bash
cd /path/to/etzhayyim-root/50-infra/l2-anchor-contract

# Build (one-time, idempotent):
forge install foundry-rs/forge-std --no-commit   # if not already vendored
forge build

# Deploy. DEPLOYER_PRIVATE_KEY is read from env by script/Deploy.s.sol.
DEPLOYER_PRIVATE_KEY=0x<funded-sepolia-key> \
  forge script script/Deploy.s.sol \
  --rpc-url https://sepolia.base.org \
  --broadcast \
  --verify \
  --etherscan-api-key "$BASESCAN_KEY"

# Pull the deployed address out of the broadcast artifact:
ADDRESS=$(jq -r '.transactions[0].contractAddress' \
  broadcast/Deploy.s.sol/84532/run-latest.json)
echo "EtzhayyimAnchor on Base Sepolia: $ADDRESS"
```

### Update `deps.toml`

```bash
# Edit /path/to/etzhayyim-root/deps.toml:
#   [platform.l2.anchor_contract]
#   address_testnet = "0x..."        ← set this
#   deploy_status   = "sepolia-deployed"
```

### Verify

```bash
# Read rootCount() on the deployed contract. For a fresh deploy this is 0.
cast call "$ADDRESS" "rootCount()(uint256)" --rpc-url https://sepolia.base.org
# Expected: 0

# After the first anchor lands, this becomes 1, 2, ...
```

### Mainnet variant

When ready for mainnet, replace `--rpc-url https://sepolia.base.org` with `https://mainnet.base.org`, fund the EOA with mainnet ETH (~$1–2 covers a year of anchor txs at the current Base L2 cost), and update `address_mainnet` instead of `address_testnet`.

---

## Gate 4 — Mac mini fleet deploy of mst-projector + ipfs-pinner

**Pre-req**: SSH access to `simeon` (`mini-01`) per the [`50-infra/atproto-pds-local/`](atproto-pds-local/) runbook. Bun is already installed there (from PDS bring-up); add Kubo + Node 22.

### Step 4a — Kubo install on simeon

```bash
ssh simeon

# Kubo via Homebrew (Apple Silicon)
brew install ipfs
ipfs init --profile=server
mkdir -p ~/Library/LaunchAgents
cat > ~/Library/LaunchAgents/io.ipfs.kubo.plist <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>io.ipfs.kubo</string>
  <key>ProgramArguments</key>
  <array>
    <string>/opt/homebrew/bin/ipfs</string>
    <string>daemon</string>
  </array>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>StandardOutPath</key><string>/Users/simeon/Library/Logs/ipfs/kubo.out.log</string>
  <key>StandardErrorPath</key><string>/Users/simeon/Library/Logs/ipfs/kubo.err.log</string>
</dict>
</plist>
EOF
launchctl load ~/Library/LaunchAgents/io.ipfs.kubo.plist

# Verify
curl -s -X POST http://127.0.0.1:5001/api/v0/id | jq -r '.ID'
# Expected: a base58 peer-ID (12D3KooW... or QmZ...)
```

### Step 4b — Clone + install mst-projector + ipfs-pinner

```bash
ssh simeon

# Node.js 22 (mst-projector + ipfs-pinner both require node:test built-in
# + AsyncIterable in @atproto/repo). nvm or fnm both work; `node -v` ≥ 22.
fnm install 22 || nvm install 22

mkdir -p ~/etzhayyim
cd ~/etzhayyim
git clone git@github.com:etzhayyim/root.git
cd root

# mst-projector (Phase 2): uses its own pnpm install --ignore-workspace
cd 50-infra/mst-projector
pnpm install --ignore-workspace
pnpm test    # 10/10 should pass

# ipfs-pinner (Stage 4 Phase 1): same pattern
cd ../ipfs-pinner
pnpm install --ignore-workspace
pnpm test    # 12/12 should pass
```

### Step 4c — Create PDS sessions for the 3 actor DIDs

**Pre-req**: each DID needs a PDS account on `pds.etzhayyim.com`. Use the Bun PDS admin CLI from `50-infra/atproto-pds-local/`:

```bash
ssh simeon
cd ~/etzhayyim/root/50-infra/atproto-pds-local

# Per-actor: invite + signup
for actor in projector pinner anchorer; do
  bun cli admin create-account \
    --did "did:web:$actor.etzhayyim.com" \
    --handle "$actor.etzhayyim.com" \
    --password "$(openssl rand -hex 16 | tee /tmp/$actor-pw.txt)"
done
```

Then export sessions for the projector + pinner runtimes (anchorer credentials live elsewhere — see Gate 5):

```bash
# Capture session JWTs once; runtime resumes them via ETZ_*_PDS_SESSION env.
for actor in projector pinner; do
  PASSWORD="$(cat /tmp/$actor-pw.txt)"
  SESSION=$(curl -s -X POST \
    -H "Content-Type: application/json" \
    -d "{\"identifier\":\"$actor.etzhayyim.com\",\"password\":\"$PASSWORD\"}" \
    https://pds.etzhayyim.com/xrpc/com.atproto.server.createSession \
    | jq -c '{did,handle,accessJwt,refreshJwt}')
  echo "ETZ_${actor^^}_PDS_SESSION='$SESSION'"
done > ~/etzhayyim/sessions.env

# Store /tmp/*-pw.txt in 1Password under
#   etzhayyim › substrate › <actor>-pds-password
# then delete the local files.
rm /tmp/projector-pw.txt /tmp/pinner-pw.txt /tmp/anchorer-pw.txt
```

### Step 4d — Run the two daemons

`launchd` units per actor. Template (substitute `projector` → `pinner` for the second unit):

```bash
ssh simeon
mkdir -p ~/Library/LaunchAgents ~/Library/Logs/etzhayyim

cat > ~/Library/LaunchAgents/com.etzhayyim.mst-projector.plist <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>com.etzhayyim.mst-projector</string>
  <key>WorkingDirectory</key>
  <string>/Users/simeon/etzhayyim/root/50-infra/mst-projector</string>
  <key>ProgramArguments</key>
  <array>
    <string>/Users/simeon/.local/share/fnm/aliases/22/bin/node</string>
    <string>--import</string><string>tsx</string>
    <string>src/index.ts</string>
  </array>
  <key>EnvironmentVariables</key>
  <dict>
    <key>ETZ_PDS_FIREHOSE_URL</key>
    <string>wss://pds.etzhayyim.com/xrpc/com.atproto.sync.subscribeRepos</string>
    <key>ETZ_PROJECTOR_DID</key>
    <string>did:web:projector.etzhayyim.com</string>
    <key>ETZ_PROJECTOR_PDS_URL</key>
    <string>https://pds.etzhayyim.com</string>
    <key>ETZ_PROJECTOR_PDS_SESSION</key>
    <string>$ETZ_PROJECTOR_PDS_SESSION</string>     <!-- from sessions.env -->
    <key>ETZ_PROJECTOR_DATA_DIR</key>
    <string>/Users/simeon/etzhayyim/var/mst-projector</string>
    <key>ETZ_PROJECTOR_IPFS_API_URL</key>
    <string>http://127.0.0.1:5001</string>
    <key>ETZ_PROJECTOR_COLLECTIONS</key>
    <string>com.etzhayyim.,com.etzhayyim.apps.</string>
  </dict>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>StandardOutPath</key><string>/Users/simeon/Library/Logs/etzhayyim/mst-projector.out.log</string>
  <key>StandardErrorPath</key><string>/Users/simeon/Library/Logs/etzhayyim/mst-projector.err.log</string>
</dict>
</plist>
EOF

launchctl load ~/Library/LaunchAgents/com.etzhayyim.mst-projector.plist
```

For `ipfs-pinner`, the same template with:
- `Label` → `com.etzhayyim.ipfs-pinner`
- `WorkingDirectory` → `…/50-infra/ipfs-pinner`
- env: `ETZ_PINNER_DID` / `ETZ_PINNER_PDS_SESSION` (from sessions.env) / `ETZ_PINNER_DATA_DIR=/Users/simeon/etzhayyim/var/mst-projector` (shared with projector) / `ETZ_PINNER_PROVIDERS=kubo`

### Verify

```bash
ssh simeon

# Logs
tail -f ~/Library/Logs/etzhayyim/mst-projector.err.log &
tail -f ~/Library/Logs/etzhayyim/ipfs-pinner.err.log &

# After a few minutes the projector should emit shardSnapshot records;
# query PDS for them:
curl -s "https://pds.etzhayyim.com/xrpc/com.atproto.repo.listRecords?repo=did:web:projector.etzhayyim.com&collection=com.etzhayyim.substrate.shardSnapshot&limit=5" \
  | jq '.records[0].value'
# Expected: { shardKey, phase: 2, rootCid, snapshotCid, ... }

# ipfsPin records should follow shortly:
curl -s "https://pds.etzhayyim.com/xrpc/com.atproto.repo.listRecords?repo=did:web:pinner.etzhayyim.com&collection=com.etzhayyim.substrate.ipfsPin&limit=5" \
  | jq '.records[0].value'
# Expected: { shardKey, rootCid, carCid, providers: ["kubo"], ... }

# Kubo pin check
ipfs pin ls --type=recursive | head -5
```

---

## Gate 5 — anchor-cron substrate mode

**Pre-req**: Gate 3 done (`address_testnet` set in `deps.toml`) + Gate 4d done (ipfsPin records flowing). Run anchor-cron from a machine with the funded anchorer EOA's private key — ideally a separate Mac mini (so the EOA key isn't on the projector/pinner host), or a K8s pod with the key in a Sealed Secret.

The anchorer DID (`did:web:anchorer.etzhayyim.com`) is separate from the EOA address; the EOA signs txs, the DID publishes receipts.

### One-shot first run

```bash
cd /path/to/etzhayyim-root/50-infra/anchor-cron
pnpm install --ignore-workspace

# Substrate mode entrypoint
ETZ_ANCHOR_CONTRACT="<address_testnet from deps.toml>" \
ETZ_ANCHOR_RPC_URL="https://sepolia.base.org" \
ETZ_ANCHOR_SIGNER_KEY="0x<funded sepolia key>" \
ETZ_ANCHOR_CHAIN_ID="84532" \
ETZ_ANCHOR_PDS_URL="https://pds.etzhayyim.com" \
ETZ_ANCHOR_PDS_SESSION='<from sessions.env or sealed-secret>' \
ETZ_ANCHOR_PINNER_REPO="did:web:pinner.etzhayyim.com" \
ETZ_ANCHOR_ANCHORER_REPO="did:web:anchorer.etzhayyim.com" \
ETZ_ANCHOR_CONFIRMATIONS="3" \
ETZ_ANCHOR_BATCH_MAX="10" \
ETZ_ANCHOR_WARN_BALANCE_WEI="2000000000000000" \
pnpm exec tsx src/index-substrate.ts
```

### Verify

```bash
# l2Anchor receipts should appear in the anchorer's PDS repo:
curl -s "https://pds.etzhayyim.com/xrpc/com.atproto.repo.listRecords?repo=did:web:anchorer.etzhayyim.com&collection=com.etzhayyim.substrate.l2Anchor&limit=5" \
  | jq '.records[0].value'
# Expected: { shardKey, rootCid, rootHash, txHash, blockNumber, contract, anchorer, ipfsPinUri }

# rootCount on-chain should increment:
cast call "$ETZ_ANCHOR_CONTRACT" "rootCount()(uint256)" --rpc-url https://sepolia.base.org

# Per-root verification:
ROOT_HASH=$(curl -s "https://pds.etzhayyim.com/xrpc/com.atproto.repo.listRecords?repo=did:web:anchorer.etzhayyim.com&collection=com.etzhayyim.substrate.l2Anchor&limit=1" \
  | jq -r '.records[0].value.rootHash')
cast call "$ETZ_ANCHOR_CONTRACT" "anchors(bytes32)" "$ROOT_HASH" --rpc-url https://sepolia.base.org
# Expected: tuple with non-zero blockNumber
```

### Recurring cron (K8s)

The existing K8s manifest at [`50-infra/anchor-cron/k8s/cronjob.yaml`](anchor-cron/k8s/cronjob.yaml) is for sidecar mode. For substrate mode, copy the manifest and replace:

- `command: ["node", "dist/index.js"]` → `["node", "dist/index-substrate.js"]`
- Drop `volumeMounts` for the checkpointer Unix socket (substrate mode doesn't need it)
- Add the 4 substrate-mode env vars (`ETZ_ANCHOR_PINNER_REPO` / `ETZ_ANCHOR_ANCHORER_REPO` / `ETZ_ANCHOR_CHAIN_ID` / `ETZ_ANCHOR_PDS_SESSION` from sealed secret)
- `schedule: "*/15 * * * *"` (every 15 min, same cadence)

Or run as a second launchd unit on a non-simeon Mac mini — simpler for the Mac mini fleet posture.

---

## Verification matrix (final end-to-end)

After all 5 gates land, the substrate pipeline produces a trust-less chain that any third party can replay:

| Step | Verifier |
|---|---|
| 1. Any record lands on `pds.etzhayyim.com` | `curl /xrpc/com.atproto.repo.listRecords` |
| 2. `shardSnapshot` emitted under `did:web:projector.etzhayyim.com` | `listRecords` against the projector repo |
| 3. CAR file pinned to IPFS + `ipfsPin` emitted under `did:web:pinner.etzhayyim.com` | `curl https://ipfs.io/ipfs/<carCid>` returns CAR bytes; `listRecords` against the pinner repo |
| 4. MST root anchored to Base L2 + `l2Anchor` emitted under `did:web:anchorer.etzhayyim.com` | `cast call anchors(rootHash)`; `listRecords` against the anchorer repo |
| 5. Original record re-derivable from the CAR | `ipfs dag get <rootCid>` → MST → record bytes |

Anyone running their own projector against the same firehose should converge on identical `rootCid`s — that's the no-single-operator-trust property.

---

## Post-deploy: seed first records

Once the pipeline is live, exercise it by seeding the first kotoba actor's taxonomy:

```bash
# open-isco (525 occupations) — already on main, requires ETZ_SEEDER_DID + PDS auth
cd /path/to/superproject/orgs/etzhayyim/com-etzhayyim-app-open-isco/kotoba
pnpm install
ETZ_SEEDER_DID="did:web:etzhayyim.com" \
  pnpm seed data/isco08.sample.json   # 5-record smoke

# open-isic (428 classes) — second kotoba actor
cd ../../etzhayyim-project-open-isic/kotoba
pnpm install
ETZ_SEEDER_DID="did:web:etzhayyim.com" \
  pnpm seed --only=2520               # weapons manufacturing (single-record smoke)
```

Each seeded record should propagate through the pipeline within 1–2 minutes (projector flush threshold default = 60 s).

---

## See also

- [ADR-2605171800](../90-docs/adr/2605171800-langgraph-mst-ipfs-l2-anchor-pipeline.md) — substrate pipeline architecture
- [ADR-2605172000](../90-docs/adr/2605172000-etzhayyim-kotoba-substrate.md) — kotoba substrate posture
- [`atproto-pds-local/`](atproto-pds-local/) — simeon PDS bring-up (Phase 1, already done 2026-05-17)
- [`mst-projector/`](mst-projector/) — Stage 3 (Phase 2 on main)
- [`ipfs-pinner/`](ipfs-pinner/) — Stage 4 Phase 1 (on main)
- [`anchor-cron/`](anchor-cron/) — Stage 5b sidecar + substrate modes (both on main)
- [`l2-anchor-contract/`](l2-anchor-contract/) — Solidity for `EtzhayyimAnchor`
- [`etzhayyim-{projector,pinner,anchorer}-did-web/`](.) — DID Workers (on main, deploy pending Gate 1+2)
