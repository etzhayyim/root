# etzhayyim PDS — k8s-free mesh deployment

The independent etzhayyim atproto PDS runs **on the Murakumo mesh, with NO Kubernetes**.
This is the same residence pattern the rest of the org uses (kaname / ibuki heartbeats):
a babashka process as a launchd LaunchAgent, state on the kotoba Datom log, exposed to
the apex Worker through a Cloudflare Tunnel.

## Why no k8s

A PDS is "an HTTP server + a Datom log + signing keys." None of those need a cluster:

| Concern        | k8s way (old `50-infra/k8s/atproto-pds`) | mesh way (this dir)                                |
|----------------|------------------------------------------|----------------------------------------------------|
| **State**      | StatefulSet + PersistentVolume           | `KotobaStore` → the LOCAL kotoba engine (`KOTOBA_URL=http://127.0.0.1:8077`). The kotoba mesh already holds the canonical Datom log (ADR-2605312345); the PDS is a thin XRPC client of it. |
| **Run / restart** | Deployment + kubelet                  | launchd LaunchAgent (`RunAtLoad` + `KeepAlive`) — survives reboot + auto-restarts, per CLAUDE.md §"Operational code = clj/bb". |
| **Ingress**    | Service + LoadBalancer / Ingress         | Cloudflare Tunnel (`cloudflared`) from the node's loopback — no public IP, no LB. |
| **Signing key**| k8s Secret (custodial)                   | actor-sealed P-256 keystore (`PDS_ACTOR_KEYS_DIR` + `MURAKUMO_SEAL_KEY`), present-only — **no-server-key**: the platform holds no custodial key, the seed contents are sealed (kaname/ibuki/tsubasa pattern). |

So the entire k8s footprint collapses to **one launchd plist + one tunnel**. The legacy
`50-infra/k8s/atproto-pds/` (a TypeScript/Bun PDS in a Deployment) is **superseded** — see
its `SUPERSEDED.md`.

## Components

- `com.etzhayyim.pds.plist.template` — the LaunchAgent. Runs `bb serve` (the clj PDS HTTP
  server) with `KOTOBA_URL` = loopback engine, `PDS_ACTOR_KEYS_DIR` + `MURAKUMO_SEAL_KEY`
  for per-actor sealed signing. `KeepAlive`/`RunAtLoad` = resident.
- `install.clj` — bb installer (`install` / `uninstall` / `status`). Renders the plist from
  the node's env into `~/Library/LaunchAgents` (mode 600 — the rendered plist holds the
  seal; it is machine-local and **never committed**), bootstraps, kickstarts.
- `cloudflared-pds.config.yml.template` — the tunnel ingress mapping `PDS_HOST` →
  `http://127.0.0.1:PORT`.

## Bring-up (operator)

```bash
cd 50-infra/etzhayyim-atproto-pds-clj

# 0. the local kotoba engine must be up on :8077 (the mesh node already runs it).
#    smoke-test the server first (ephemeral, no key):
bb serve            # ^C after it prints "[pds] … up"

# 1. install the resident PDS (state = local kotoba engine, writes = sealed actor keys)
MURAKUMO_SEAL_KEY="$(…)" PDS_ACTOR_KEYS_DIR=/path/to/sealed/keys \
  bb deploy/install.clj install
bb deploy/install.clj status            # state = running, last log healthy

# 2. expose it to the apex Worker via the tunnel (one-time)
cloudflared tunnel login
cloudflared tunnel create etzhayyim-pds
cloudflared tunnel route dns etzhayyim-pds atproto.etzhayyim.com
cp deploy/cloudflared-pds.config.yml.template ~/.cloudflared/etzhayyim-pds.yml
#   fill the tunnel UUID, then run it (ideally as its own LaunchAgent):
cloudflared --config ~/.cloudflared/etzhayyim-pds.yml tunnel run
```

## Cutover (flip the apex — INERT until this step)

The apex Worker (`50-infra/etzhayyim-did-web`) already routes `com.atproto.repo.*`,
`com.atproto.sync.*`, and `app.bsky.feed.getAuthorFeed` to `XRPC_PDS_UPSTREAM`, falling
back to the gftd AppView while that secret is empty (so prod is byte-identical today).

```bash
cd 50-infra/etzhayyim-did-web
wrangler secret put XRPC_PDS_UPSTREAM     # → https://atproto.etzhayyim.com (the tunnel host)
wrangler deploy
```

**Rollback** (instant, non-destructive): clear the secret and redeploy — every route
falls back to the gftd AppView again.

```bash
echo -n "" | wrangler secret put XRPC_PDS_UPSTREAM   # (or `wrangler secret delete`)
wrangler deploy
```

Do the cutover **only after** `bb deploy/install.clj status` is healthy AND the tunnel
host answers `GET https://atproto.etzhayyim.com/xrpc/com.atproto.server.describeServer` —
otherwise the apex would proxy live traffic to a dead origin.
