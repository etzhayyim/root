# etzhayyim-esign-did-web

Cloudflare Worker serving `did:web:esign.etzhayyim.com` at the spec-required `/.well-known/did.json` resolution endpoint.

Per [ADR-2605231230](../../90-docs/adr/2605231230-etzhayyim-esign-actor-did-bound-mst-anchored.md).

## Deploy

```bash
npm install
npm run deploy
```

## Verify

```bash
curl -sS https://esign.etzhayyim.com/.well-known/did.json | jq .id
# → "did:web:esign.etzhayyim.com"

# Universal Resolver check (smoke):
curl -sS https://dev.uniresolver.io/1.0/identifiers/did:web:esign.etzhayyim.com | jq .didDocument.id
```

## DNS

Worker deploy alone does not provision the hostname. `esign.etzhayyim.com` requires an AAAA record `100::` (proxied / CF orange-cloud) on the `etzhayyim.com` zone — same pattern as the parent `etzhayyim.com` zone apex and the sibling `pinner.etzhayyim.com` / `anchorer.etzhayyim.com` records. Provision via Cloudflare dashboard or the zone DNS API; without it, the route binding has no traffic to attach to.

## License

Apache-2.0 + etzhayyim Charter Compliance Rider v2.0 (see repo-root `CHARTER-RIDER.md`).
