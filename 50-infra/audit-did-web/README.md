# audit-did-web

Cloudflare Worker serving **`did:web:audit.etzhayyim.com`** — the canonical audit subject targeted by every actor manifest's `agent.invoke` audit emission step. Per ADR-2605231700.

## What this implements

- W3C DID Core 1.0 — DID Document at `/.well-known/did.json`
- `EtzhayyimAuditSubject` service endpoint declaring the `com.etzhayyim.audit.event` lexicon contract
- XRPC dispatch to the audit aggregator (which signs the event + writes it into the named subject's PDS, forming the per-(actor, subject) hash-chain)
- `/healthz` Worker-side liveness probe

## Why a separate DID Worker

Audit events are written to the **subject's** PDS (not the actor's, not a centralized log), so the audit DID is the routing target — not the storage target. Centralizing the routing through a single Worker:

1. Gives every actor (karute, hc, etc.) a stable `targetDid` to invoke
2. Allows the aggregator implementation to swap (k3s pod / serverless / proxy) without changing actor manifests
3. Provides a single signature-verification boundary for audit-event integrity

## Pre-deploy

Generate Ed25519 keypair and store private key:
- Keychain `service=etzhayyim, account=DID_PRIVATE_KEY_ED25519_AUDIT`
- 1Password mirror `audit/did-web/key-0`

Replace placeholders in `did.json` with the generated public key.

## Deploy

```bash
cd 50-infra/audit-did-web
pnpm install
wrangler deploy

# DNS
#   AAAA audit  100::  Proxied
```

## Smoke

```bash
curl -fsS https://audit.etzhayyim.com/.well-known/did.json | jq .id
curl -fsS https://audit.etzhayyim.com/healthz | jq
```

## See also

- ADR-2605231700 — audit webhook subsystem spec
- ADR-2605231603 — per-record rekey + tombstone protocol (a major event producer)
- ADR-2605231400 — consent capability (auditWebhookDid constraint pattern)
