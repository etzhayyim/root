# Repo Security Topology (Pruned)

Date: 2026-04-17
Time: 2026-04-17 JST

## Scope

- Repository: `etzhayyim-root`
- Method:
  - static review of tracked credentials, browser session handling, CORS/auth edges, and public infra exposure
  - pruning rule: keep only branches with current repo evidence and a credible compromise path

## Topology

1. Secret distribution layer
   - tracked kube/admin material
   - tracked object-store credentials
   - tracked plaintext fleet password in ops docs

2. Browser session layer
   - `yoro` stores access + refresh JWTs in script-readable storage
   - auth transfer still arrives through URL fragment before storage

3. Edge trust-expansion layer
   - `atproto` helper CORS reflects arbitrary origins and enables credentials
   - browser-held JWTs amplify the impact of any same-origin script execution

4. Public compute/maintenance layer
   - internet-facing inference endpoints and public proxy surfaces exist
   - keep only the branches that are clearly exploitable from repo evidence

## Active Issues

### P0: Tracked Kubernetes admin bearer token

Evidence:

- `50-infra/linode/risingwave-iceberg/kubeconfig.yaml:12-16`
  - committed kubeconfig includes a bearer token for `lke589404-admin`

Why it survives pruning:

- direct credential exposure
- cluster access material replicates into every clone and backup
- impact is administrative until rotated

### P0: Tracked S3 credentials in ingestion script

Evidence:

- `60-apps/etzhayyim-project-common-crawl/scripts/ingest_chunked.py:20-23`
  - embedded Linode object storage access key and secret

Why it survives pruning:

- executable credentials, not placeholders
- likely grants direct access to ingestion bucket contents
- compromise path is immediate after repo disclosure

### P1: Browser-readable access and refresh JWTs in `yoro`

Evidence:

- `60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/svelte/src/lib/auth/passkey.ts:34-39`
  - session shape contains both `accessJwt` and `refreshJwt`
- `.../passkey.ts:75-78`
  - session is serialized into `sessionStorage`
- `.../passkey.ts:99-106`
  - both JWTs are copied into `@etzhayyim/wproto`
- `60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/svelte/src/app.html:8-18`
  - `#auth=` fragment is copied into `sessionStorage` before URL cleanup

Why it survives pruning:

- any same-origin XSS or third-party script compromise gets both current access and refresh capability
- this is current runtime code, not a dormant note or template

### P1: Reflective credentialed CORS in `atproto`

Evidence:

- `50-infra/cloudflare/workers/atproto/src/auth.ts:112-120`
  - `Access-Control-Allow-Origin` reflects `requestOrigin`
  - `Access-Control-Allow-Credentials` is enabled whenever an origin is present

Why it survives pruning:

- permissive cross-origin behavior sits directly on auth/helper code
- it combines badly with browser-readable JWT storage
- risk is current source behavior, not speculative drift

### P2: Plaintext fleet SSH password committed in ops docs

Evidence:

- `60-apps/etzhayyim-project-murakumo/CLAUDE.md:503`
  - committed doc includes `password=\`260308\`` and fleet addressing context

Why it survives pruning:

- direct credential disclosure
- adjacent host/IP inventory lowers attacker work for lateral movement

## Pruned Branches

### Pruned: `yoro` cache purge endpoint as a current top issue

Evidence reviewed:

- `60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/src/app.ts:753-782`
- `.../src/app.ts:1069-1073`

Reason:

- current code fails closed before any purge action
- missing `CACHE_PURGE_API_KEY` returns `404`
- missing bearer auth returns `401` before the Cloudflare purge secret check
- still public, but no longer one of the repo’s strongest issues

### Pruned: public moderation proxy route by itself

Evidence reviewed:

- `50-infra/cloudflare/workers/moderation/worker.ts:9-20`
- `.../worker.ts:54-64`

Reason:

- `com.etzhayyim.kagami.sql` is intentionally unauthenticated in current policy
- repo evidence alone does not prove data sensitivity or privilege escalation
- keep under review, but weaker than direct secret exposure

### Pruned: public inference `LoadBalancer` surfaces by themselves

Evidence reviewed:

- `50-infra/linode/inference-gpu/kustomize/base/ollama.yaml:1-26`
- `.../ollama.yaml:143-156`

Reason:

- clearly internet-facing, but repo evidence does not show whether upstream DNS, WAF, or caller filtering makes abuse practical
- this is an attack surface / cost-control concern, but not stronger than the committed-credential findings

### Pruned: dependency vulnerability audit as a repo-wide primary signal

Reason:

- root `npm audit` cannot run because the workspace root has no npm lockfile
- monorepo contains many independent package managers and lockfiles, so a meaningful dependency-vuln pass needs a separate dedicated sweep
- for this run, direct credential exposure and auth topology dominate the risk picture

## Root Cause Graph

1. Secrets are still being committed into operational files and docs.
2. Browser apps still retain high-value tokens in script-readable state.
3. Edge auth helpers still widen trust with reflective credentialed CORS.
4. Public operational surfaces exist, but most of them are secondary compared with the direct secret leaks.

## Next Cut

1. Rotate and revoke leaked credentials first.
   - Kubernetes admin token
   - S3/Object Storage keypair
   - Murakumo fleet password and any reused variants

2. Remove those secrets from git history, not only from `HEAD`.

3. Move refresh capability out of browser JavaScript.
   - server-managed refresh or `HttpOnly` cookie

4. Replace reflective credentialed CORS with an explicit origin allowlist on auth surfaces.

5. Run a separate dependency-vulnerability sweep per lockfile family after the secret rotation work.
