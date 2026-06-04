# Repo Security Topology (Pruned)

Date: 2026-04-18
Time: 2026-04-18 JST

## Scope

- Repository: `etzhayyim-root`
- Method:
  - static review of current `HEAD`, selected git history, and workspace-local secret residue
  - pruning rule: keep only branches with current evidence and a direct or credible compromise path

## Topology

1. Credential residue layer
   - tracked executable credentials in ingestion and ops files
   - workspace-local `.env` secrets outside git tracking
   - deleted-but-still-in-history admin credentials

2. Browser session layer
   - `yoro` keeps both access and refresh JWTs in script-readable storage
   - auth transfer still lands in a JS-readable fragment handoff before cleanup

3. Edge and helper layer
   - reviewed prior CORS/auth helper concerns
   - kept only branches with current runtime reachability

4. Public service layer
   - reviewed public proxy / inference surfaces
   - pruned paths without a stronger privilege or data-exposure story than the credential leaks

## Active Repo Issues

### P0: Tracked S3 credentials in ingestion script

Evidence:

- [`60-apps/etzhayyim-project-common-crawl/scripts/ingest_chunked.py`](/Users/junkawasaki/etzhayyim/etzhayyim-root/60-apps/etzhayyim-project-common-crawl/scripts/ingest_chunked.py:17)
  - hardcoded `s3.credentials.access` and `s3.credentials.secret`

Why it survives pruning:

- executable credentials are still present in `HEAD`
- compromise path is immediate after repo disclosure
- likely grants bucket-level read/write against ingestion data or adjacent object-storage scope

### P1: Browser-readable access and refresh JWTs in `yoro`

Evidence:

- [`60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/svelte/src/lib/auth/passkey.ts`](/Users/junkawasaki/etzhayyim/etzhayyim-root/60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/svelte/src/lib/auth/passkey.ts:29)
  - `StoredSession` contains both `accessJwt` and `refreshJwt`
- [`60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/svelte/src/lib/auth/passkey.ts`](/Users/junkawasaki/etzhayyim/etzhayyim-root/60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/svelte/src/lib/auth/passkey.ts:66)
  - session is serialized into `sessionStorage`
- [`60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/svelte/src/lib/auth/passkey.ts`](/Users/junkawasaki/etzhayyim/etzhayyim-root/60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/svelte/src/lib/auth/passkey.ts:91)
  - both JWTs are copied into `@etzhayyim/wproto`
- [`60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/svelte/src/app.html`](/Users/junkawasaki/etzhayyim/etzhayyim-root/60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/svelte/src/app.html:8)
  - `#auth=` transfer is copied into `sessionStorage` before URL cleanup

Why it survives pruning:

- any same-origin XSS, compromised dependency, or injected script can read both current access and refresh capability
- this is live runtime code, not a dead path or doc artifact

### P1: Plaintext fleet SSH password in ops documentation

Evidence:

- [`60-apps/etzhayyim-project-murakumo/CLAUDE.md`](/Users/junkawasaki/etzhayyim/etzhayyim-root/60-apps/etzhayyim-project-murakumo/CLAUDE.md:503)
  - shared fleet password appears alongside node names and private IP inventory

Why it survives pruning:

- direct credential disclosure remains in `HEAD`
- surrounding host inventory sharply lowers attacker effort for lateral movement
- even if the subnet is private, the repo disclosure materially weakens internal trust

## History-Only Findings

### Downgraded: Kubernetes admin kubeconfig is no longer in `HEAD`

Evidence reviewed:

- commit `32aadce7b7d` added `50-infra/linode/risingwave-iceberg/kubeconfig.yaml`
- current tree no longer contains that file

Why it was pruned from active issues:

- this is no longer a current-tree exposure
- it remains a git-history contamination problem until history is rewritten or the token is fully rotated
- severity is still high operationally, but it is not a current `HEAD` branch anymore

## Workspace-Local Findings

### Local-only: ignored `.env` contains live-style infra secrets

Evidence:

- [`.env`](/Users/junkawasaki/etzhayyim/etzhayyim-root/.env:1)
  - `PULUMI_ACCESS_TOKEN`, `PULUMI_CONFIG_PASSPHRASE`, and a Linode API key are present
- [`.gitignore`](/Users/junkawasaki/etzhayyim/etzhayyim-root/.gitignore:62)
  - `.env` and `.envrc` are ignored

Why it is separated from repo issues:

- current evidence suggests local workspace residue, not tracked source
- still critical for workstation hygiene, shell history, and accidental copy/paste leakage

## Pruned Branches

### Pruned: `atproto` reflective CORS helper as a current runtime issue

Evidence reviewed:

- [`50-infra/cloudflare/workers/atproto/src/auth.ts`](/Users/junkawasaki/etzhayyim/etzhayyim-root/50-infra/cloudflare/workers/atproto/src/auth.ts:112)
- [`50-infra/cloudflare/workers/atproto/src/auth-context.test.ts`](/Users/junkawasaki/etzhayyim/etzhayyim-root/50-infra/cloudflare/workers/atproto/src/auth-context.test.ts:29)

Reason:

- `withCors()` appears to be dead helper code in the current tree
- this run found no runtime call sites under `50-infra/cloudflare/workers/atproto/src`
- dead insecure helper code should still be deleted, but it is weaker than the live credential leaks

### Pruned: moderation proxy as a top repo issue

Evidence reviewed:

- [`50-infra/cloudflare/workers/moderation/worker.ts`](/Users/junkawasaki/etzhayyim/etzhayyim-root/50-infra/cloudflare/workers/moderation/worker.ts:9)

Reason:

- allowlist is explicit
- privileged NSIDs still require bearer or verified headers
- current repo evidence does not beat the direct-secret findings

## Root Cause Graph

1. Secrets are still being embedded directly into executable scripts and internal runbooks.
2. Browser apps still retain long-lived refresh capability in script-readable state.
3. Some previously reported branches were fixed or became dead code, but the stronger credential-residue layer remains.

## Next Cut

1. Rotate the object-storage keypair from `ingest_chunked.py`.
2. Rotate the Murakumo fleet password and audit reuse.
3. Remove the hardcoded values from `HEAD`, then purge them from git history where applicable.
4. Move `yoro` refresh capability out of browser JavaScript into server-managed or `HttpOnly` handling.
5. Delete dead auth/CORS helper code that no longer has runtime callers.
6. Clean local `.env` secrets from the workstation or move them into a secret manager / shell vault.
