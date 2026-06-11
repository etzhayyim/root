# Repo Security Topology

Date: 2026-04-16
Time: 2026-04-16 16:01 JST

## Scope

- Repository: `etzhayyim-root`
- Method:
  - static review of tracked secrets, auth/session code, edge worker CORS, and public operational endpoints
  - live verification against selected public surfaces on 2026-04-16

## Topology

1. Secret material layer
   - Infra and ingestion scripts contain direct credentials or admin tokens.
   - Some of these files are tracked in git and therefore replicate into every clone, backup, and CI artifact.

2. Browser auth layer
   - `yoro` keeps access and refresh JWTs in browser-readable storage.
   - The same session is also transferred through a URL fragment handoff before being copied into storage.

3. Cross-origin/API layer
   - `atproto.etzhayyim.com` reflects arbitrary origins in CORS and allows credentials.
   - Browser-held bearer material from the previous layer amplifies this exposure.

4. Public maintenance surface
   - Internal-looking endpoints are mounted on public origins.
   - Current production behavior leaks configuration state before auth succeeds.

## Pruning Rule

- Keep only issues that satisfy both:
  - repo evidence exists now, and
  - there is a credible compromise path or direct credential exposure
- Prune issues that are merely broad hardening gaps unless they amplify an active path above.

## Active Issues

### P0: Tracked Kubernetes admin token in repo

Evidence:

- `50-infra/linode/kotoba-iceberg/kubeconfig.yaml:12-17`
  - tracked kubeconfig contains a live-style bearer token for `lke589404-admin`
- `git ls-files 50-infra/linode/kotoba-iceberg/kubeconfig.yaml`
  - file is committed, not local-only

Why it survives pruning:

- This is direct cluster access material, not an example or template.
- Compromise impact is cluster-admin scope until rotated.
- Repo cloning alone is enough to spread it.

### P0: Hardcoded object storage credentials in tracked ingestion script

Evidence:

- `60-apps/etzhayyim-project-common-crawl/scripts/ingest_chunked.py:20-23`
  - embedded S3 access key and secret
- `git ls-files 60-apps/etzhayyim-project-common-crawl/scripts/ingest_chunked.py`
  - file is committed

Why it survives pruning:

- The secret pair is executable config, not placeholder text.
- It likely grants direct object-store access to ingestion data.
- Rotation is required even if the script is no longer actively used.

### P1: Browser-readable access and refresh tokens in `yoro`

Evidence:

- `60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/svelte/src/lib/auth/passkey.ts:34-39`
  - session model stores both `accessJwt` and `refreshJwt`
- `60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/svelte/src/lib/auth/passkey.ts:75-78`
  - session blob is written to `sessionStorage`
- `60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/svelte/src/lib/auth/passkey.ts:99-106`
  - both JWTs are mirrored into the in-page `wproto` session
- `60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/svelte/src/app.html:8-17`
  - `#auth=` fragment is copied into `sessionStorage` before URL cleanup

Why it survives pruning:

- Any same-origin script execution gets immediate API access plus refresh capability.
- This is active runtime code, not dormant SSR debt.
- It is the main credential-exposure node for the browser-facing apps.

### P1: Reflective credentialed CORS on `atproto.etzhayyim.com`

Evidence in source:

- `50-infra/cloudflare/workers/atproto/src/auth.ts:112-120`
  - origin is reflected and credentials are enabled whenever an origin is present

Live verification on 2026-04-16 16:01 JST:

- `OPTIONS https://atproto.etzhayyim.com/xrpc/com.atproto.server.refreshSession`
- Request headers:
  - `Origin: https://evil.example`
  - `Access-Control-Request-Method: POST`
  - `Access-Control-Request-Headers: Authorization, Content-Type`
- Response headers:
  - `Access-Control-Allow-Origin: https://evil.example`
  - `Access-Control-Allow-Credentials: true`

Why it survives pruning:

- In isolation, reflective CORS is already risky on auth endpoints.
- Combined with browser-readable JWT storage, it becomes a clear blast-radius multiplier.
- This is live behavior, not only checked-in intent.

### P1: Publicly reachable internal cache-purge endpoint leaks runtime configuration

Evidence:

- Existing focused analysis already flagged this path:
  - `80-data/reports/260416-yoro-security-topology-analysis.md`
- Live verification on 2026-04-16 16:01 JST:
  - `POST https://yoro.etzhayyim.com/api/internal/cache/purge`
  - unauthenticated response: `500 CachePurgeSecretMissing`
- Live headers on `https://yoro.etzhayyim.com/` still do not include CSP/HSTS/XFO hardening headers

Why it survives pruning:

- The route is externally enumerable today.
- Production leaks operational state before proving caller authority.
- The header drift weakens containment if any client-side issue is found later.

### P2: Plaintext fleet password committed in ops documentation

Evidence:

- `60-apps/etzhayyim-project-murakumo/CLAUDE.md:503`
  - contains a plaintext fleet SSH password
- `git ls-files 60-apps/etzhayyim-project-murakumo/CLAUDE.md`
  - file is committed

Why it survives pruning:

- It is not a fake example and includes adjacent host addressing context.
- Even if limited to a private subnet, repo disclosure turns it into usable lateral-movement data.

## Pruned Branches

### Pruned: local `.env` and `.envrc`

- Present in workspace, but not tracked by git in the current repo snapshot.
- They remain local hygiene concerns, not repo-distribution issues.

### Pruned: `vault` wildcard CORS by itself

- `60-apps/etzhayyim-project-vault/worker/src-ts/util.ts:41-51`
- `60-apps/etzhayyim-project-vault/worker/src-ts/index.ts:64-72`

Reason:

- The worker still requires bearer authentication and vault membership checks:
  - `60-apps/etzhayyim-project-vault/worker/src-ts/auth.ts`
  - `60-apps/etzhayyim-project-vault/worker/src-ts/handlers.ts:443-451`
- This is worth tightening, but it is not a stronger repo-wide issue than the confirmed token exposure paths above.

### Pruned: `git-server` internal auth pattern

- `50-infra/cloudflare/workers/git-server/worker.js:243-287`

Reason:

- The code accepts an internal token via `Bearer` or `Basic`, but no shared token is committed in the repo snapshot.
- The stronger, confirmed finding is the separate committed secret material elsewhere.

## Root Cause Graph

1. Secrets are being committed into operational scripts and kube material.
2. Browser apps retain high-value session material in script-readable storage.
3. Auth-related edge services expose permissive cross-origin behavior.
4. Internal maintenance paths are mounted publicly and production drift is not being caught fast enough.

## Next Cut

1. Rotate and purge all committed credentials first.
   - kube admin token
   - object storage keypair
   - fleet SSH password or any reused derivative

2. Remove secrets from git history, not only from `HEAD`.

3. Move refresh capability out of browser JavaScript.
   - server-managed refresh or `HttpOnly` cookie

4. Replace reflective credentialed CORS with a strict allowlist on auth surfaces.

5. Hide or strictly gate public maintenance endpoints and make production behavior fail closed before revealing config state.
