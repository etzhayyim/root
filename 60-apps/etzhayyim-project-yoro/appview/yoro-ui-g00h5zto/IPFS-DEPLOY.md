# yoro AppView — IPFS deploy design / runbook

Status: **design + verified PoC** (2026-05-30). Frontend (static SPA) can be
served from IPFS today. Full "no Cloudflare" is **not** achievable yet — the
data plane (PDS/XRPC), DNS, and the SEO Worker remain on Cloudflare. Target
end-state is a hybrid: **IPFS frontend + kotoba/CF backend**, collapsing to
fully decentralized only after the PDS/AppView → kotoba migration.

---

## 1. What is / isn't movable off Cloudflare

| Concern | Today (CF) | IPFS-able? | Notes |
|---|---|---|---|
| Static SPA shell (`index.html` + `_app/immutable/*` + assets) | CF Worker Assets (`kotodama-yoro`, `assets.directory: ./static`) | **Yes** | adapter-cloudflare `fallback:'spa'` already emits a self-contained static SPA. |
| SPA deep-link routing | Worker `not_found_handling: single-page-application` | **Yes**, via IPFS `_redirects` (`/* /index.html 200`) on a **subdomain/DNSLink** gateway | path-gateways (`/ipfs/<cid>/foo`) do **not** honor `_redirects`. |
| Data / XRPC | `atproto.etzhayyim.com` (CF PDS + Hyperdrive + RisingWave) | **No (still CF)** | SPA calls it directly from the browser. Drop only after PDS/AppView → kotoba. |
| Cross-origin access to PDS | same-site today | needs **CORS** change | PDS must allow the new IPFS origin (`https://<cid>.ipfs.dweb.link`, `ipfs://…`, or the DNSLink host). |
| SEO bot/LLM OGP snapshots, dynamic sitemap, cache purge | `src/worker.ts` | **No** | server logic; IPFS is static-only. Needs prerender or a thin bots-only Worker. |
| DNS / TLS at `yoro.etzhayyim.com` | CF Registrar + DNS | DNSLink uses CF DNS (movable) | pure `ipfs://<CID>` / public-gateway access needs no DNS at all. |
| Persistent availability | CF edge | needs **reachable pin** | a laptop Kubo (dhtclient/NAT) can NOT serve public gateways (PoC: `provide` timed out, dweb.link → 504). |

---

> Note: at session time the canonical `ipfs.etzhayyim.com` write/gateway front was DNS-absent; only a legacy read-only gateway (pre-ADR-2605212340 cutover) answered, and read-only (`/api/v0/*` -> 405). Treat the gateway URLs below as the canonical target to bring up, not a currently-live endpoint.

## 2. Verified PoC (2026-05-30)

Local Kubo 0.41 (`:5001`) + kotoba 0.1.0 (`:8077`) present.

```bash
printf '/*  /index.html  200\n' > static/_redirects     # SPA fallback for gateways
ipfs add -r -Q --cid-version=1 static                    # -> root CID, pinned locally
```

- Root CID (this build): `bafybeidl5t4ztktqmfcqrfqpio6qf64n6t65a7inkz2pa6jq4tyqwfjfhy`
- Contains `_app/`, `index.html` (4663 B), `_redirects`, `_headers`, assets — verified via `ipfs cat $CID/index.html`; `ipfs pin ls --type=recursive $CID` → pinned.
- **Public reachability NOT achieved** from this box: the local Kubo daemon is running in **offline mode** (`swarm connect` / `routing provide` refuse with "must be run in online mode"; `swarm peers` = 0). Even online, a NAT'd dev laptop is not a reliable public provider. ⇒ public serving requires pinning on a reachable host/service (next section). Do not assume `dweb.link/<CID>` resolves until that pin exists.

The fix for the black-screen bug (`/` renders `<VibesPanel/>`, no `<App/>` SPA-router recursion) is baked into this CID's build, so the IPFS-served site renders the feed, not a black screen.

---

## 3. Pin / serve options (pick one for public reachability)

Public retrievability = content must live on an always-on, network-dialable peer.

1. **Remote pinning service** (Pinata / web3.storage / Storacha-Filecoin).
   - ⚠️ `50-infra/ipfs-pinner` is a *substrate MST-CAR* pinner (Stage 4 of
     ADR-2605171800), and its Pinata/web3.storage/Filecoin providers are
     **stubs (throw-on-call)** — only the **Kubo** provider works today. It is
     not a general static-site publisher as-is.
   - So for now pin directly: Pinata (`/pinning/pinFileToIPFS` or pin-by-CID),
     or `w3 up` (web3.storage/Storacha). Needs an API token (1Password). Pin the
     **directory CID**, not individual files.
   - Pro: zero infra. Con: third-party dependency (mild centralization), token
     mgmt. (Implementing the pinner's remote providers would make this Charter-clean.)
2. **Self-hosted IPFS Cluster** (the Charter-aligned, no-3rd-party path).
   - Run `ipfs-cluster` over ≥3 always-on Kubo nodes (e.g. the Mac-mini fleet / Murakumo nodes); `cluster pin add <CID>`.
   - Pro: no external vendor, matches substrate self-containment. Con: ops.
3. **kotoba / Kubo always-on node** with public addrs (AutoNAT + relay or a routable host).
   - kotoba already wraps Kubo (`KOTOBA_IPFS_ENDPOINT`); use it as the pin host on a server with a public address. dhtclient on a laptop is NOT sufficient.

> The CID is identical regardless of who pins it — pin the **same** `bafybei…` CID on the chosen backend.

---

## 4. Addressing & domain

- Raw: `ipfs://<CID>/` (Brave / IPFS Companion) — no DNS, no CF.
- Subdomain gateway (honors `_redirects` ⇒ deep links work): `https://<CID>.ipfs.dweb.link/`.
- DNSLink to keep the brand domain:
  - `_dnslink.yoro.etzhayyim.com  TXT  "dnslink=/ipfs/<CID>"`
  - serve via a gateway that resolves DNSLink (public, or self-hosted Kubo gateway behind the domain).
  - DNS record still lives at CF (movable later). Update the TXT on each release (or use **IPNS** to keep a stable name and republish the pointer instead of editing DNS each build).
- IPNS (optional, stable mutable pointer): `ipfs name publish /ipfs/<CID>` → `/ipns/<key>`; DNSLink to `/ipns/<key>` so releases don't touch DNS.

---

## 5. Required backend changes (so the IPFS-served SPA actually works)

1. **CORS on the PDS** (`atproto.etzhayyim.com`, `50-infra/cloudflare/workers/atproto`):
   add the IPFS origin(s) to `Access-Control-Allow-Origin` for `/xrpc/*`
   (`https://<cid>.ipfs.dweb.link`, the DNSLink host, and/or `ipfs://` / `null`
   origin used by `ipfs://`). Without this the browser blocks all XRPC.
2. **Auth redirects**: `authn.etzhayyim.com` sign-in `redirect_url` must allow the
   new origin(s).
3. **SEO / OGP / sitemap** (lost on static IPFS) — choose:
   - keep a **thin CF (or any) Worker for bots only** that serves
     `renderRichBotSnapshot()` + `/sitemap.xml`, routing humans to the IPFS CID; or
   - **prerender** OGP HTML per route at build and ship it inside the CID
     (heavier; no live data in tags).

---

## 6. Release procedure (hybrid IPFS frontend)

```bash
cd 60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto
( cd svelte && pnpm build )                       # emits ./static (SPA)
printf '/*  /index.html  200\n' > static/_redirects
CID=$(ipfs add -r -Q --cid-version=1 static)
# pin for public reachability (pick one):
#   pnpm -C ../../../../50-infra/ipfs-pinner start -- --cid "$CID"   # Pinata/web3.storage
#   ipfs-cluster-ctl pin add "$CID"                                  # self-hosted cluster
# point the domain (or republish IPNS):
#   set _dnslink.yoro.etzhayyim.com TXT "dnslink=/ipfs/$CID"
# verify:
curl -s -o /dev/null -w "%{http_code}\n" "https://$CID.ipfs.dweb.link/"   # expect 200 once pinned on a reachable node
```

---

## 7. Road to fully Cloudflare-free (decentralized)

1. **Frontend → IPFS** (this doc) — done in principle; needs a reachable pin. ✅ mechanism
2. **PDS / AppView / XRPC → kotoba** — replace `atproto.etzhayyim.com` (CF Worker
   + Hyperdrive + RisingWave) with kotoba (`kotoba-graph` XRPC + EAVT read path,
   `kotoba-net` libp2p, IPFS cold tier). Largest piece; in progress per
   ADR-2605262130. Until done, data plane stays on CF.
3. **DNS** — move `etzhayyim.com` DNS off CF (or rely on `ipfs://` / `/ipns/`),
   keeping DNSSEC + DNSLink.
4. **SEO** — bots-only renderer on a neutral host or prerender-in-CID.

Only after (2)+(3) is "no Cloudflare" actually true end-to-end. Until then this is
**IPFS frontend + CF data backend** (a real, shippable improvement, but a hybrid).

---

## Notes
- `static/_redirects` is required for gateway SPA routing; keep it in the build
  output (add to the build step, not just ad-hoc).
- The black-screen fix (routes/+page.svelte → `<VibesPanel/>`) is independent of
  hosting and applies to both the CF Worker and the IPFS deploy.
