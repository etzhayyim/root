# etzhayyim-dataset-pinner-did-web

Cloudflare Worker serving `did:web:dataset-pinner.etzhayyim.com` at the
spec-required `/.well-known/did.json` resolution endpoint, plus a
`/healthz` liveness probe.

Per [ADR-2605241500](../../90-docs/adr/2605241500-etzhayyim-dataset-cid-substrate.md).

## What it is

Identity of the religious-corp **dataset pinner** — the operator-side
actor that:

1. Mirrors `git-annex` `directory`-remote objects to IPFS via Kubo
   (`e7m-dataset publish-ipfs`).
2. Emits `com.etzhayyim.substrate.datasetPin` records to PDS as the
   religious-corp-canonical pin receipt.

Distinct from `pinner.etzhayyim.com` (`did:web:pinner.etzhayyim.com`,
ADR-2605171800 Stage 4) — that DID is for the MST/CAR pinner. The
dataset pinner is a separate identity with its own emission lexicon
and Charter Rider §2 gate (per ADR-2605241500 §D8 — reuse boundary).

## Deploy

```bash
npm install
npm run deploy
```

## Verify

```bash
curl -sS https://dataset-pinner.etzhayyim.com/.well-known/did.json | jq .id
# → "did:web:dataset-pinner.etzhayyim.com"

curl -sS https://dataset-pinner.etzhayyim.com/healthz
# → ok

# Universal Resolver check (smoke):
curl -sS https://dev.uniresolver.io/1.0/identifiers/did:web:dataset-pinner.etzhayyim.com | jq .didDocument.id
```

## DNS

Worker deploy alone does not provision the hostname.
`dataset-pinner.etzhayyim.com` requires an AAAA record `100::`
(proxied / CF orange-cloud) on the `etzhayyim.com` zone — same pattern
as `pinner.etzhayyim.com` / `esign.etzhayyim.com` / `audit.etzhayyim.com`.
Provision via Cloudflare dashboard or the zone DNS API; without it,
the route binding has no traffic to attach to.

## Verification method (Phase 2)

`did.json` currently has `verificationMethod: []` (matching the esign /
pinner Phase 0/1 pattern). Before any `e7m-dataset add --emit` call
goes live in production, generate an Ed25519 keypair, store the
private key in macOS Keychain (`service=etzhayyim,
account=DID_PRIVATE_KEY_ED25519_DATASET_PINNER`) + 1Password mirror,
and populate `did.json` with the public key's `publicKeyJwk.x` and
`publicKeyMultibase`. The companion app-password (handle+password)
that `e7m-dataset/pds.py` consumes via `ETZ_E7M_PDS_AUTH` is a
separate credential set issued by the PDS operator.

## License

Apache-2.0 + etzhayyim Charter Compliance Rider v2.0 (see repo-root
`CHARTER-RIDER.md`).
