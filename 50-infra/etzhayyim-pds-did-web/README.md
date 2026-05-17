# etzhayyim-pds-did-web

Cloudflare Worker that serves the **DID Document for `did:web:pds.etzhayyim.com`** at the spec-required resolution endpoint:

```
https://pds.etzhayyim.com/.well-known/did.json
```

Other paths on `pds.etzhayyim.com` (e.g., `/xrpc/com.atproto.*`) fall through to the CF tunnel CNAME → simeon Mac mini PDS on port 2583.

## Why this Worker

- AT Protocol clients resolve a PDS's DID via `https://<host>/.well-known/did.json`.
- The simeon Bun PDS does NOT serve `/.well-known/did.json` (it serves `/xrpc/*` instead).
- We deploy this Worker at the path `/.well-known/did.json` to provide the DID document **without modifying the upstream PDS**.
- Same pattern as `50-infra/etzhayyim-did-web/` for `etzhayyim.com/.well-known/did.json`.

## Files

| File | Purpose |
|---|---|
| `did.json` | The DID document. Declares `id`, `service[AtprotoPersonalDataServer]`. |
| `src/worker.ts` | Worker fetch handler. Serves did.json on GET/HEAD; 405 / 404 otherwise. |
| `wrangler.toml` | Route binding `pds.etzhayyim.com/.well-known/did.json`. |
| `package.json` | wrangler + types. |
| `tsconfig.json` | resolveJsonModule for the did.json import. |

## did.json

Minimal for v1. AT Protocol PDS resolution needs only the `AtprotoPersonalDataServer` service entry. `verificationMethod` is empty — the PDS asserts identity via TLS, not signed assertions, at this layer.

Future: add `verificationMethod` entries when needed for signed federation messages (PDS-to-PDS, relay handshakes).

## Deploy

```bash
cd 50-infra/etzhayyim-pds-did-web
npm install      # first-time only
wrangler deploy
```

After deploy:

```bash
curl -i https://pds.etzhayyim.com/.well-known/did.json | head -5
# HTTP/2 200
# content-type: application/did+json; charset=utf-8

curl https://dev.uniresolver.io/1.0/identifiers/did:web:pds.etzhayyim.com
# should return the DID document via Universal Resolver
```

## Related

- `50-infra/etzhayyim-did-web/` — sister Worker for `etzhayyim.com/.well-known/did.json` (apex DID).
- ADR-2605172800 § "PDS at pds.etzhayyim.com"
- ADR-2605172000 § "Identity substrate"
