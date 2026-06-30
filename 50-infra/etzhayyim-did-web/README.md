# etzhayyim-did-web

Cloudflare Worker that serves the **DID Document for `did:web:etzhayyim.com`** and the local public surfaces (`/`, `/organism`, `/system-dynamics`, actor DID/profile views) from the same edge origin:

```
https://etzhayyim.com/.well-known/did.json
```

## What this implements

- W3C DID Core 1.0 — DID Document JSON-LD
- did:web Method Specification — apex domain resolution via `/.well-known/did.json`
- Ed25519 verification key (both `JsonWebKey2020` and `Ed25519VerificationKey2020` representations for broad verifier compatibility)
- Linked-Domain service endpoints pointing at the GitHub org, the monorepo, and the apex domain
- cljs-owned Hiccup rendering for `/organism` and the other local HTML surfaces

## Files

| File | Purpose |
|---|---|
| `did.json` | The DID Document (canonical artifact). 1.5 KB. |
| `src/worker.ts` | Worker fetch handler. Imports `did.json` at build time, injects cljs deps, and serves the local public surfaces. |
| `cljs/src/did_web/core.cljs` | cljs request core. Owns the local HTML/JSON routes and renders `/organism` from Hiccup. |
| `cljs/src/did_web/router.cljc` | Pure route ownership table for the cljs-owned surfaces. |
| `wrangler.toml` | Route binding: `etzhayyim.com/*` and `www.etzhayyim.com/*` → this Worker. |
| `package.json` | Wrangler + Cloudflare Workers types. |
| `tsconfig.json` | TS config with `resolveJsonModule` for the `did.json` import. |

## Key material

- **Public key** lives inside `did.json` in two formats:
  - JWK: `verificationMethod[0].publicKeyJwk.x`
  - Multibase: `verificationMethod[1].publicKeyMultibase`
- **Private key** is in **macOS Keychain** (per CLAUDE.md "Local Secret Storage" rule):
  - Service: `etzhayyim.etzhayyim`
  - Account: `DID_PRIVATE_KEY_ED25519`
  - Label: "etzhayyim did:web Ed25519 private key (created 2026-05-17, key-0)"
  - Read: `security find-generic-password -s etzhayyim.etzhayyim -a DID_PRIVATE_KEY_ED25519 -w`
- **1Password mirror**: pending. Mirror to `etzhayyim Japan株式会社` vault, item name `etzhayyim/did-web/key-0`.
- **Key rotation**: append a new `#key-N` verification method to `did.json`, re-deploy, then remove `#key-0` after the rotation window. Never re-use a `kid`.

## Prerequisites for deployment

1. `etzhayyim.com` zone must exist in the same Cloudflare account that owns the Cloudflare Registrar registration (default behavior — registering via CF Registrar auto-adds the zone).
2. The apex `etzhayyim.com` must have **at least one DNS record proxied (orange cloud)** so requests to `etzhayyim.com/...` hit Cloudflare's edge where the Worker route can fire. Without a proxied DNS record on the apex, the Worker route is inert. Minimum viable setup:
   - Record type: AAAA
   - Name: `@` (etzhayyim.com)
   - Target: `100::` (RFC 6666 discard prefix — never resolves; only exists so CF accepts the route)
   - Proxy status: Proxied (orange)
3. `wrangler` CLI authenticated against the correct Cloudflare account: `wrangler login` (one-time).

## Deploy

```bash
cd 50-infra/etzhayyim-did-web
npm install      # first-time only
wrangler deploy
```

## Verify

```bash
curl -i https://etzhayyim.com/.well-known/did.json | head -5
# HTTP/2 200
# content-type: application/did+json; charset=utf-8
# cache-control: public, max-age=300, must-revalidate
# ...

# Universal resolver (optional, third-party):
curl https://dev.uniresolver.io/1.0/identifiers/did:web:etzhayyim.com
```

## Extending

The Worker owns the apex public surfaces listed above. Local HTML routes are rendered in cljs/Hiccup and are not served from a standalone static `index.html`. JSON snapshots for `/organism` live under `public/organism/*.json`.

- `/organism` is owned by cljs/Hiccup in `did-web.core`; do not reintroduce `scittle.js` or a standalone `public/organism/index.html`.
- Additional `.well-known/` artifacts (`atproto-did`, `openid-configuration`, `security.txt`, `apple-app-site-association`) can still be added by extending the Worker's path matcher rather than scattering across multiple deployments.

## Related

- **ADR** (vendor monorepo): `etzhayyim/etzhayyim-root` → `90-docs/adr/2605152100-etzhayyim-github-org-boundary.md` § "did:web publish"
- **Operating entity SSoT**: `etzhayyim/etzhayyim-root` → `deps.toml [platform.operating_entity]`
- **Cloudflare Registrar registration**: 2026-05-15T12:08:36Z, NS `everton/vivienne.ns.cloudflare.com`
