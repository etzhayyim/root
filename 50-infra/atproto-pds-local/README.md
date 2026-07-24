# atproto-pds-local — Phase 1 bring-up runbook (mini-01 → mini-04)

> **Status: `dev-scaffold` — per ADR-2606242330** (PDS consolidation).
> Local Bun reference `@atproto/pds` for dev / upstream-compat checks only — NOT the
> canonical PDS. The canonical `pds.etzhayyim.com` stack is clj-on-kotoba
> (`50-infra/etzhayyim-atproto-pds-clj`) + kotoba-server + aozora AppView.

Local PDS (AT Protocol Personal Data Server) + Kubo IPFS for the etzhayyim Mac-mini fleet. Phase 1 of the artificial-organism bootstrap (per the substrate ADRs).

## What this gives you

```
this Mac (laptop)  ─dev / forge / cli─┐
                                       │
                                       ▼
mini-01  ─Bun PDS + Kubo IPFS─▶ substrate L1 (state + storage)
mini-02  ─LangGraph runtime ─▶ cell execution
mini-03  ─mst-projector + ipfs-pinner + anchor-cron─▶ substrate workers
mini-04+ ─more cells / PDS replicas / IPFS mirrors
```

Phase 1 is mini-01 only: PDS + Kubo. Once that's healthy, Phase 2 onward layers on top.

## Prerequisites on mini-01

- macOS 14+ (any recent Apple Silicon)
- Network: same LAN as this Mac, mDNS reachable
- Storage: ≥ 100 GB free (chain growth + IPFS pin cache)
- SSH access from this Mac to mini-01

## Step 1 — Install Bun + git + curl

```bash
ssh mini-01

# Bun (PDS runtime per atproto-pds Bun container ADR-2605111300)
curl -fsSL https://bun.sh/install | bash
exec "$SHELL"   # reload
bun --version   # >= 1.1
```

## Step 2 — Clone PDS reference

```bash
mkdir -p ~/etzhayyim && cd ~/etzhayyim
git clone --depth 1 https://github.com/bluesky-social/atproto.git
cd atproto/services/pds
bun install
```

## Step 3 — Configure PDS for etzhayyim

Generate hosting domain + signing keys + admin password:

```bash
cd ~/etzhayyim/atproto/services/pds

# PDS env
cat > .env <<'EOF'
NODE_ENV=production
PDS_HOSTNAME=pds.mini-01.etzhayyim.local
PDS_PORT=2583
PDS_DB_POSTGRES_URL=  # leave empty for SQLite
PDS_DATA_DIRECTORY=/Users/$USER/etzhayyim/pds-data
PDS_BLOB_UPLOAD_LIMIT=52428800
PDS_BLOBSTORE_DISK_LOCATION=/Users/$USER/etzhayyim/pds-blobs
PDS_DID_PLC_URL=https://plc.directory       # external PLC for now; can self-host later
PDS_BSKY_APP_VIEW_URL=https://api.bsky.app   # external for now
PDS_REPORT_SERVICE_URL=
PDS_CRAWLERS=https://bsky.network            # firehose relay (will switch to etzhayyim-relay later)

# Secrets — generate fresh
PDS_JWT_SECRET=$(openssl rand -hex 32)
PDS_ADMIN_PASSWORD=$(openssl rand -hex 16)
PDS_PLC_ROTATION_KEY_K256_PRIVATE_KEY_HEX=$(openssl rand -hex 32)
PDS_REPO_SIGNING_KEY_K256_PRIVATE_KEY_HEX=$(openssl rand -hex 32)
EOF

mkdir -p ~/etzhayyim/pds-data ~/etzhayyim/pds-blobs
```

> **Store JWT_SECRET + ADMIN_PASSWORD + the 2 K256 keys in 1Password** (vault `etzhayyim`, item `etzhayyim/pds-mini-01`) before starting, then add a Keychain entry on this Mac (mirror).

## Step 4 — Start PDS

```bash
cd ~/etzhayyim/atproto/services/pds
bun run start 2>&1 | tee ~/etzhayyim/pds.log &
sleep 5
curl http://localhost:2583/xrpc/_health    # → {"version":"..."}
```

Optionally `launchctl` it for auto-restart (see `mini-01-launchd.plist` template at end of this file).

## Step 5 — Install Kubo IPFS

```bash
brew install ipfs
ipfs init --profile=server
ipfs config Addresses.API '/ip4/0.0.0.0/tcp/5001'
ipfs config Addresses.Gateway '/ip4/0.0.0.0/tcp/8080'
ipfs config Discovery.MDNS.Enabled true     # so mini-02..04 auto-peer on LAN
ipfs daemon &
sleep 3
ipfs id | head -3
```

## Step 6 — Smoke tests from this Mac (laptop)

```bash
# from this Mac
curl http://mini-01.local:2583/xrpc/_health
# → {"version":"..."}

curl http://mini-01.local:8080/ipfs/bafkqaaa
# → empty file (sentinel CID)

curl -X POST http://mini-01.local:2583/xrpc/com.atproto.server.createAccount \
  -H "Content-Type: application/json" \
  -d '{
    "handle":"firstbreath.mini-01.etzhayyim.local",
    "email":"firstbreath@etzhayyim.com",
    "password":"<a strong throwaway password>"
  }'
# → {"accessJwt":"...","refreshJwt":"...","handle":"firstbreath...","did":"did:plc:..."}
```

Save the returned `did:plc:...` — that's the first cell's identity. Persist in 1Password (`etzhayyim/pds-mini-01-accounts`).

## Step 7 — DNS for mini-01 (optional, recommended)

If you want a stable hostname over LAN (no mDNS dependency):

```bash
# On this Mac, edit /etc/hosts:
sudo sh -c "echo '$(ssh mini-01 'ipconfig getifaddr en0')  pds.mini-01.local kubo.mini-01.local' >> /etc/hosts"
```

For external (cross-network) access, set up a Cloudflare Tunnel from mini-01 → CF Worker → `pds.etzhayyim.com` (out of scope for Phase 1).

## Layout left behind on mini-01

```
~/etzhayyim/
├── atproto/                  # cloned atproto monorepo (for the PDS source)
├── pds-data/                 # SQLite DB + ephemeral
├── pds-blobs/                # blob storage (large records)
├── pds.log                   # tail this on issues
└── pds-mini-01-launchd.plist # (optional) launchd unit file
```

## launchd template (optional)

`~/Library/LaunchAgents/com.etzhayyim.pds-mini-01.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple Inc.//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>com.etzhayyim.pds-mini-01</string>
  <key>WorkingDirectory</key><string>/Users/USERNAME/etzhayyim/atproto/services/pds</string>
  <key>ProgramArguments</key>
  <array>
    <string>/Users/USERNAME/.bun/bin/bun</string>
    <string>run</string>
    <string>start</string>
  </array>
  <key>EnvironmentVariables</key>
  <dict><key>PATH</key><string>/Users/USERNAME/.bun/bin:/usr/local/bin:/usr/bin:/bin</string></dict>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>StandardOutPath</key><string>/Users/USERNAME/etzhayyim/pds.log</string>
  <key>StandardErrorPath</key><string>/Users/USERNAME/etzhayyim/pds.log</string>
</dict>
</plist>
```

`launchctl load -w ~/Library/LaunchAgents/com.etzhayyim.pds-mini-01.plist`

## Acceptance criteria for Phase 1 done

- [ ] PDS responds 200 at `pds.mini-01.local:2583/xrpc/_health`
- [ ] Kubo responds at `mini-01.local:8080/ipfs/<any-cid>`
- [ ] First account creation produces a `did:plc:...`
- [ ] PDS + Kubo survive a mini-01 reboot (launchd active)
- [ ] Backups of `pds-data/` snapshot daily to mini-03 or laptop

After acceptance, Phase 2 (mini-02 LangGraph worker) can start.

## See also

- ADR-2605171800 § Stage 1-2 — PDS + LangGraph cell runtime
- ADR-2605172000 — kotoba substrate (PDS is the AT MST host)
- Vendor monorepo `etzhayyim/etzhayyim-root/90-docs/adr/2605111300-pds-to-pod-bun-container.md` — Bun container PDS reference (we use the same source, packaged for mini deploy)
- atproto PDS docs — https://atproto.com/guides/self-hosting
