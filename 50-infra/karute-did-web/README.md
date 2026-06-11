# karute-did-web

Cloudflare Worker serving the **DID Document for `did:web:karute.etzhayyim.com`** and routing the karute SuperApp + XRPC. Per ADR-2605231900 (deployment topology).

## What this implements

- W3C DID Core 1.0 — DID Document JSON-LD at `/.well-known/did.json`
- did:web Method Specification — subdomain resolution
- Ed25519 verification key (JWK + multibase representations for broad compatibility)
- Service endpoints: `AtprotoPersonalDataServer` (XRPC origin) + `LinkedDomains` (actor manifest) + `EtzhayyimCharterCompliance` (ADR pointers)
- Reverse-proxy to the karute LangServer Pod for `/xrpc/*`
- Reverse-proxy to the Cloudflare Pages bundle for the SuperApp UI

## Files

| File | Purpose |
|---|---|
| `did.json` | DID Document (placeholder keys until `key-0` is generated) |
| `src/worker.ts` | Fetch handler — DID, XRPC dispatch, static asset proxy |
| `wrangler.toml` | Route binding + vars |
| `package.json` | Wrangler + types |
| `tsconfig.json` | TS config with `resolveJsonModule` |

## Pre-deploy: generate the Ed25519 keypair

Per the etzhayyim CLAUDE.md "Local Secret Storage" rule — macOS Keychain primary + 1Password mirror.

```bash
# Generate Ed25519 keypair (no openssl libsodium dep needed)
node --input-type=module -e '
import { generateKeyPairSync } from "node:crypto";
const { publicKey, privateKey } = generateKeyPairSync("ed25519");
const pub = publicKey.export({ type: "spki", format: "der" });
const priv = privateKey.export({ type: "pkcs8", format: "der" });
// Raw 32-byte key extraction
const rawPub = pub.subarray(pub.length - 32);
const rawPriv = priv.subarray(priv.length - 32);
console.log("publicKeyJwk.x =", Buffer.from(rawPub).toString("base64url"));
console.log("publicKeyMultibase = z" + bs58encode(Buffer.concat([Buffer.from([0xed, 0x01]), rawPub])));
console.log("privateKey (write to Keychain ONLY) =", Buffer.from(rawPriv).toString("base64url"));
function bs58encode(buf) {
  const alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz";
  let n = 0n; for (const b of buf) n = (n << 8n) | BigInt(b);
  let out = ""; while (n > 0n) { out = alphabet[Number(n % 58n)] + out; n /= 58n; }
  for (const b of buf) { if (b === 0) out = "1" + out; else break; }
  return out;
}
'

# Store the private key in macOS Keychain
security add-generic-password \
  -s "etzhayyim" \
  -a "DID_PRIVATE_KEY_ED25519_KARUTE" \
  -l "karute did:web Ed25519 private key (key-0)" \
  -w "$PRIVATE_KEY_BASE64URL"

# Mirror to 1Password (etzhayyim Japan株式会社 vault → karute/did-web/key-0)
op item create --vault "etzhayyim Japan株式会社" \
  --category "API Credential" \
  --title "karute/did-web/key-0" \
  --tags "etzhayyim,karute,did:web" \
  password="$PRIVATE_KEY_BASE64URL" \
  notesPlain="Ed25519 private key for did:web:karute.etzhayyim.com#key-0. Created $(date -Iseconds)."
```

Then replace the placeholders in `did.json`:
- `verificationMethod[0].publicKeyJwk.x` ← `publicKeyJwk.x` from above
- `verificationMethod[1].publicKeyMultibase` ← `publicKeyMultibase` from above

## Deploy

```bash
cd 50-infra/karute-did-web
pnpm install
wrangler login          # one-time
wrangler deploy

# DNS — Cloudflare dashboard or `cf-cli`
#   AAAA karute  100::  Proxied
# (Per ADR-2605231900; CF Worker route binds when both records resolve.)
```

## Smoke test

```bash
curl -fsS https://karute.etzhayyim.com/.well-known/did.json | jq .id
# expect: "did:web:karute.etzhayyim.com"

# Universal Resolver
curl -fsS https://dev.uniresolver.io/1.0/identifiers/did:web:karute.etzhayyim.com | jq '.didDocument.id'

# Healthz (Worker liveness, no Pod dependency)
curl -fsS https://karute.etzhayyim.com/healthz | jq
```

Once the LangServer Pod is reachable, set:

```bash
wrangler secret put XRPC_KARUTE_UPSTREAM   # e.g. https://lg-karute-tunnel.etzhayyim.com
wrangler secret put KARUTE_STATIC_UPSTREAM # e.g. https://karute-pages.pages.dev
wrangler deploy
```

## Key rotation

Append a new `#key-N` to `did.json`, deploy, then remove `#key-0` after the rotation window. Never re-use a `kid`.
