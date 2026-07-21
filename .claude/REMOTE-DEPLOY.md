# Remote (Claude Code on the web) — dev → deploy for etzhayyim

How a cloud session takes etzhayyim from **development through to deploy**, and
the hard boundary of what a cloud container can and cannot do.

## What runs where

| Capability | Cloud session (here) | Where it actually deploys |
|---|---|---|
| Edit / build / test (Rust, TS, Python, Solidity) | ✅ in-container | — |
| Constitutional gate (`lefthook` + `substrate-boundary.mjs`, mirrors `.github/workflows/ci.yml`) | ✅ in-container | — |
| Build kotoba / actor **WASM** → strip → validate → **CIDv1** → **CAR** | ✅ in-container, **no secrets** | — |
| Pin WASM CAR to **IPFS** | ⛔ never (no creds in cloud) | **GitHub Actions** (`kotoba-wasm-ipfs-deploy`) using repo secrets |
| Deploy **Cloudflare Workers** (`etzhayyim.com` did-web, …) | ⛔ never (no token in cloud) | Your Mac / a GitHub Action with `CLOUDFLARE_API_TOKEN` |
| Sign the actor **DID / registry** with the new CID | ⛔ never | Operator, **macOS Keychain** (`did:web:etzhayyim.com`) — separately signed |
| Deploy the **Mac-mini fleet / LiteLLM / pinner** (`deploy-religious-corp-stack.sh`) | ⛔ unreachable (LAN `192.168.1.x` + SSH) | Your Mac on the LAN |

This matches the no-server-key / no-secrets-in-cloud invariant
(`CLAUDE.md` → "Server-side signing capability", "Do not commit secrets").

## Session bootstrap (automatic)

`.claude/hooks/session-start.sh` runs on every **web** session and installs,
all from public sources with no credentials:

- `wasm32-unknown-unknown` rust target
- `wasm-tools` (strip / validate)
- `kubo` (`ipfs`) + an **offline** repo (CID + CAR need no daemon, no network)
- `lefthook` (the constitutional pre-commit gate)
- `xxd` (real, or an `od`-backed shim — the gate's end-of-file check needs it)

It is registered under `hooks.SessionStart` in `.claude/settings.json`. Local
Macs are skipped (they already have the toolchain).

## Dev loop in a session

```bash
# verify like CI does
lefthook run pre-commit
node 70-tools/scripts/lint/substrate-boundary.mjs <changed files…>

# build + content-address a kotoba/actor WASM component (no secrets)
70-tools/scripts/deploy/kotoba-wasm-build.sh orgs/etzhayyim/com-etzhayyim-tsumugi/wasm/tsumugi-core
#  → dist/tsumugi-core.{wasm,cid,car}
```

## Deploy (GitHub-driven)

1. Commit + push to the working branch; open a PR.
2. Trigger **Actions → kotoba-wasm-ipfs-deploy** (`workflow_dispatch`), giving
   the actor crate dir. It builds, content-addresses, uploads the
   `.wasm/.cid/.car` as artifacts, and — **only if** these repo secrets exist —
   pins the CAR to etzhayyim's kubo pinner:
   - `KOTOBA_IPFS_ENDPOINT` (kubo RPC base, e.g. `https://kotobase.gftd.ai`)
   - `KOTOBA_IPFS_TOKEN` (optional Bearer)
   It uses the same `/api/v0/dag/import` + `/api/v0/pin/add` RPC as kotoba's
   `KuboBlockStore` / `IpfsPinClient`.
3. The workflow **stops at "pinned + CID reported"**. Updating the actor's
   `did.json` / registry with the new CID is a separately-signed operator step
   (macOS Keychain), never automated in CI.

Cloudflare-Worker and fleet deploys remain operator/LAN actions (see the table).
