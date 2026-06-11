# Repo Security Topology (Pruned)

Date: 2026-04-19
Time: 2026-04-19 JST

## Scope

- Repository: `etzhayyim-root`
- Method:
  - static review of current `HEAD`
  - focus on live compromise paths, not theoretical smell
  - prune duplicate leaves into a smaller set of attack branches

## Topology

1. Credential residue layer
   - executable secrets in ingestion and fleet tooling
   - workspace-local secrets outside git tracking

2. Browser session layer
   - browser app persists both access and refresh capability in script-readable state
   - cross-page auth handoff still uses JS-visible fragment transfer

3. Edge/helper layer
   - prior CORS concerns were re-checked
   - only runtime-reachable branches survive

## Active Repo Issues

### P0: Hardcoded object-storage credentials in executable ingestion scripts

Evidence:

- [`60-apps/etzhayyim-project-common-crawl/scripts/ingest_chunked.py`](/Users/junkawasaki/etzhayyim/etzhayyim-root/60-apps/etzhayyim-project-common-crawl/scripts/ingest_chunked.py:20)
  - embedded `s3.credentials.access` and `s3.credentials.secret`
- [`60-apps/etzhayyim-project-common-crawl/scripts/s3_upload_and_ingest.py`](/Users/junkawasaki/etzhayyim/etzhayyim-root/60-apps/etzhayyim-project-common-crawl/scripts/s3_upload_and_ingest.py:34)
  - same keypair is also used as the default runtime fallback

Why it survives pruning:

- this is live `HEAD` code, not docs or an example
- compromise path is immediate after repo disclosure
- duplication means rotation is not enough unless both call sites are cleaned

### P0: Shared Murakumo fleet SSH password exposed in code and runbook inventory

Evidence:

- [`70-tools/etzhayyim/etzhayyim/murakumo_fleet.go`](/Users/junkawasaki/etzhayyim/etzhayyim-root/70-tools/etzhayyim/etzhayyim/murakumo_fleet.go:37)
  - CLI deployment code hardcodes fleet SSH password
- [`60-apps/etzhayyim-project-murakumo/CLAUDE.md`](/Users/junkawasaki/etzhayyim/etzhayyim-root/60-apps/etzhayyim-project-murakumo/CLAUDE.md:507)
  - same password is published with node naming and private IP inventory

Why it survives pruning:

- this is not just documentation residue; the credential is wired into executable code
- surrounding inventory lowers attacker effort for lateral movement across the fleet
- even on a private subnet, repo disclosure materially weakens trust boundaries

### P1: `yoro` keeps access and refresh JWTs in script-readable storage

Evidence:

- [`60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/svelte/src/lib/auth/passkey.ts`](/Users/junkawasaki/etzhayyim/etzhayyim-root/60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/svelte/src/lib/auth/passkey.ts:34)
  - `StoredSession` contains both `accessJwt` and `refreshJwt`
- [`60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/svelte/src/lib/auth/passkey.ts`](/Users/junkawasaki/etzhayyim/etzhayyim-root/60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/svelte/src/lib/auth/passkey.ts:75)
  - session is serialized into `sessionStorage`
- [`60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/svelte/src/lib/auth/passkey.ts`](/Users/junkawasaki/etzhayyim/etzhayyim-root/60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/svelte/src/lib/auth/passkey.ts:100)
  - both JWTs are copied into `@etzhayyim/wproto`
- [`60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/svelte/src/app.html`](/Users/junkawasaki/etzhayyim/etzhayyim-root/60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/svelte/src/app.html:8)
  - `#auth=` transfer is copied into `sessionStorage` before URL cleanup

Why it survives pruning:

- any same-origin XSS, injected third-party script, or compromised dependency can read both present and refresh capability
- this is active runtime code on an auth surface

## Workspace-Local Findings

### Local-only: ignored root `.env` contains live infra secrets

Evidence:

- [`.env`](/Users/junkawasaki/etzhayyim/etzhayyim-root/.env:1)
  - `PULUMI_ACCESS_TOKEN`, `PULUMI_CONFIG_PASSPHRASE`, and a Linode API key are present
- [`.gitignore`](/Users/junkawasaki/etzhayyim/etzhayyim-root/.gitignore:62)
  - `.env` and `.envrc` are ignored

Why it is separated:

- current evidence says workstation residue, not tracked repo content
- it still matters for shell history, local exfiltration, and accidental reuse

## Pruned Branches

### Pruned: `atproto` reflective CORS helper as a current runtime issue

Evidence reviewed:

- [`50-infra/cloudflare/workers/atproto/src/auth.ts`](/Users/junkawasaki/etzhayyim/etzhayyim-root/50-infra/cloudflare/workers/atproto/src/auth.ts:112)

Reason:

- `withCors()` still looks permissive, but current review did not find a live runtime caller that beats the credential-residue branches above
- delete it, but it is not the top current compromise path

### Pruned: local GeoIP token in DNS collector as a top repo issue

Evidence reviewed:

- [`70-tools/scripts/collect-dns-global.sh`](/Users/junkawasaki/etzhayyim/etzhayyim-root/70-tools/scripts/collect-dns-global.sh:17)

Reason:

- it is a hardcoded secret, but current code points it at `http://localhost:8083/json`
- that makes it weaker than the directly reusable S3 and SSH credentials unless the local service is externally bridged

## Root Cause Graph

1. Secrets are still being embedded directly into executable code and operational tooling.
2. Browser auth still treats refresh capability as JavaScript-readable state.
3. Several previously suspicious helper branches are lower risk than the still-live credential residue.

## Next Cut

1. Rotate the Linode object-storage keypair used by the common-crawl scripts.
2. Remove the keypair from both scripts in the same change and purge from history if it was ever valid.
3. Rotate the Murakumo fleet password and replace password-based SSH automation with per-node keys or a vault-backed fetch.
4. Move `yoro` refresh capability out of browser JavaScript into `HttpOnly` or server-managed handling.
5. Delete dead permissive CORS helper code once the stronger issues are closed.
6. Remove or vault the local root `.env` secrets.
