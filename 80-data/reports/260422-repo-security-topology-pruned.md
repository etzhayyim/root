# Repo Security Topology (Pruned)

Date: 2026-04-22
Time: 2026-04-22 JST

## Scope

- Repository: `etzhayyim-root`
- Method:
  - static review of current `HEAD`
  - repo-wide pruning of branches that still have a live compromise path
  - `pnpm audit --prod --json` at workspace root

## Topology

1. Executable credential layer
   - live scripts still embed reusable storage, DB, and fleet credentials
   - compromise value is immediate because the secrets are in runnable paths, not only docs

2. Browser trust layer
   - some browser apps still keep refresh-capable auth material in script-readable storage
   - at least one frontend still pushes a third-party API key into `VITE_*`

3. Authz and public edge layer
   - a confirmed critical Clerk middleware advisory still lands on active route protection code
   - several public worker paths still widen caller trust with permissive CORS or optional auth

4. Dependency layer
   - there are multiple audit findings, but only the branches that directly intersect auth or public runtime were kept as top issues

## Active Repo Issues

### P0: Hardcoded reusable credentials remain in executable code

Evidence:

- [`60-apps/etzhayyim-project-common-crawl/scripts/ingest_chunked.py`](/Users/junkawasaki/etzhayyim/etzhayyim-root/60-apps/etzhayyim-project-common-crawl/scripts/ingest_chunked.py:17)
  - embeds Linode object-storage access and secret keys in `S3_CONF`
- [`70-tools/etzhayyim/etzhayyim/murakumo_fleet.go`](/Users/junkawasaki/etzhayyim/etzhayyim-root/70-tools/etzhayyim/etzhayyim/murakumo_fleet.go:31)
  - hardcodes fleet SSH password `fleetSSHPass`
- [`70-tools/scripts/bulk-stream-ingest.mjs`](/Users/junkawasaki/etzhayyim/etzhayyim-root/70-tools/scripts/bulk-stream-ingest.mjs:29)
  - hardcodes a password-bearing Kotoba/Datomic DSN
- [`70-tools/scripts/yabai-baseline-ingest.mjs`](/Users/junkawasaki/etzhayyim/etzhayyim-root/70-tools/scripts/yabai-baseline-ingest.mjs:16)
  - keeps the same DSN as default fallback

Why it survives pruning:

- these are live executable paths in `HEAD`
- multiple files reuse the same classes of secrets, so single-file cleanup is not enough
- direct repo disclosure is enough to turn this branch into infra access

### P1: Confirmed Clerk middleware auth bypass still lands on active route protection

Evidence:

- workspace `pnpm audit --prod --json`
  - reports `@clerk/nextjs 6.34.1` and `@clerk/shared 3.47.3` / `3.45.1` as affected by `GHSA-vqx2-fgx2-5wq9`
- [`60-apps/etzhayyim-project-hrse/appview/external-hrse/package.json`](/Users/junkawasaki/etzhayyim/etzhayyim-root/60-apps/etzhayyim-project-hrse/appview/external-hrse/package.json:77)
  - pins `@clerk/nextjs` to `6.34.1`
- [`60-apps/etzhayyim-project-hrse/appview/external-hrse/src/middleware.ts`](/Users/junkawasaki/etzhayyim/etzhayyim-root/60-apps/etzhayyim-project-hrse/appview/external-hrse/src/middleware.ts:5)
  - uses `createRouteMatcher(...)`
- [`60-apps/etzhayyim-project-hrse/appview/external-hrse/src/middleware.ts`](/Users/junkawasaki/etzhayyim/etzhayyim-root/60-apps/etzhayyim-project-hrse/appview/external-hrse/src/middleware.ts:59)
  - relies on `if (!isPublicRoute(request)) await auth.protect()`

Why it survives pruning:

- this is not generic package lag; it is a current critical advisory on an active middleware gate
- `hrse` matches the exact advisory shape closely enough that the branch remains live until upgraded

### P1: Browser auth still stores both access and refresh JWTs in script-readable state

Evidence:

- [`60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/svelte/src/lib/auth/passkey.ts`](/Users/junkawasaki/etzhayyim/etzhayyim-root/60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/svelte/src/lib/auth/passkey.ts:28)
  - `StoredSession` contains both `accessJwt` and `refreshJwt`
- [`60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/svelte/src/lib/auth/passkey.ts`](/Users/junkawasaki/etzhayyim/etzhayyim-root/60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/svelte/src/lib/auth/passkey.ts:65)
  - session is serialized into `sessionStorage`
- [`60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/svelte/src/lib/auth/passkey.ts`](/Users/junkawasaki/etzhayyim/etzhayyim-root/60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/svelte/src/lib/auth/passkey.ts:89)
  - both JWTs are synced into `@etzhayyim/wproto`
- [`60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/svelte/src/app.html`](/Users/junkawasaki/etzhayyim/etzhayyim-root/60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/svelte/src/app.html:9)
  - `#auth=` payload is copied into `sessionStorage` before cleanup

Why it survives pruning:

- any same-origin XSS or hostile dependency gets both current and refresh capability
- this is active runtime code on a browser auth surface

### P1: Frontend code exposes an OpenRouter key through `VITE_*`

Evidence:

- [`60-apps/etzhayyim-project-narou/ghosthacker/apps/web/src/lib/ai/openrouter-image.ts`](/Users/junkawasaki/etzhayyim/etzhayyim-root/60-apps/etzhayyim-project-narou/ghosthacker/apps/web/src/lib/ai/openrouter-image.ts:5)
  - reads `import.meta.env.VITE_OPENROUTER_API_KEY`
- [`60-apps/etzhayyim-project-narou/ghosthacker/apps/web/src/lib/ai/openrouter-image.ts`](/Users/junkawasaki/etzhayyim/etzhayyim-root/60-apps/etzhayyim-project-narou/ghosthacker/apps/web/src/lib/ai/openrouter-image.ts:53)
  - sends it as `Authorization: Bearer ...` from browser fetch
- [`60-apps/etzhayyim-project-narou/ghosthacker/apps/docker-compose.yml`](/Users/junkawasaki/etzhayyim/etzhayyim-root/60-apps/etzhayyim-project-narou/ghosthacker/apps/docker-compose.yml:30)
  - injects the same key into frontend runtime env

Why it survives pruning:

- if this app is deployed as written, the API key becomes recoverable by any browser user
- unlike many doc-only secret mentions, this branch is a live client-side exfil path

### P2: Public worker surfaces still permit over-broad caller trust

Evidence:

- [`50-infra/cloudflare/workers/bitwarden-mcp/src/index.ts`](/Users/junkawasaki/etzhayyim/etzhayyim-root/50-infra/cloudflare/workers/bitwarden-mcp/src/index.ts:216)
  - global CORS is `Access-Control-Allow-Origin: *`
- [`50-infra/cloudflare/workers/bitwarden-mcp/src/index.ts`](/Users/junkawasaki/etzhayyim/etzhayyim-root/50-infra/cloudflare/workers/bitwarden-mcp/src/index.ts:234)
  - auth is enforced only if `env.MCP_AUTH_TOKEN` is set
- [`50-infra/cloudflare/workers/atproto/src/auth.ts`](/Users/junkawasaki/etzhayyim/etzhayyim-root/50-infra/cloudflare/workers/atproto/src/auth.ts:112)
  - helper reflects request origin or falls back to `*`
- [`60-apps/etzhayyim-project-llm/appview/etzhayyim-wasm-llm-llm8cf4ai/src/app.ts`](/Users/junkawasaki/etzhayyim/etzhayyim-root/60-apps/etzhayyim-project-llm/appview/etzhayyim-wasm-llm-llm8cf4ai/src/app.ts:558)
  - OpenAI-compatible responses set `Access-Control-Allow-Origin: *`

Why it survives pruning:

- wildcard CORS by itself is not always enough for compromise
- optional auth on a secrets-adjacent service is the stronger branch, so this remains but below the direct credential and auth issues

## Dependency Audit Summary

Workspace root `pnpm audit --prod --json` result on 2026-04-22:

- 4 critical
- 10 high
- 8 moderate
- 2 low

Highest-signal dependency leaves after pruning:

1. `@clerk/nextjs` / `@clerk/shared` in `hrse`
2. `protobufjs < 7.5.5` via `orgs/etzhayyim/com-etzhayyim-ameno -> @huggingface/transformers -> onnxruntime-web`
3. `hono` advisory path via `40-engine/kotoba/crates/kotoba-kotodama/sdk/kotodama-host-sdk`
4. `undici` advisory path in `60-apps/etzhayyim-project-scap`

Pruning note:

- only the Clerk path was promoted to a top repo issue because it intersects active route protection
- the remaining audit findings matter, but current repo evidence does not beat the live secret and browser-exposure branches

## Pruned Branches

### Pruned: `docs` Clerk path as a top-level repo issue

Reason:

- `docs` still carries vulnerable `svelte-clerk` transitive packages in the lockfile
- this run did not confirm an equivalent live middleware auth boundary like `hrse`
- keep it in dependency remediation, but not in the top compromise tree

### Pruned: local ignored `.env` as a repo issue

Reason:

- still matters for workstation hygiene
- current evidence remains local residue, not tracked source in `HEAD`

### Pruned: history-only kubeconfig leakage as a current-tree issue

Reason:

- still a git-history and rotation problem
- no current `HEAD` evidence that beats the live executable-credential branch

## Root Cause Graph

1. Secrets are still treated as code defaults instead of runtime-injected configuration.
2. Browser trust boundaries are still too loose for auth and paid third-party APIs.
3. Public edge services still rely on permissive defaults and configuration discipline.
4. Dependency response is inconsistent: the auth-critical advisory is still present after disclosure.

## Next Cut

1. Rotate and remove every executable credential in `common-crawl`, `murakumo_fleet`, `bulk-stream-ingest`, and `yabai-baseline-ingest` as one batch.
2. Upgrade `@clerk/nextjs` in `hrse` to at least `6.39.2` and re-lock all affected Clerk paths.
3. Move `yoro` refresh capability out of browser-managed storage into `HttpOnly` or server-side session handling.
4. Remove `VITE_OPENROUTER_API_KEY` from the `narou` frontend path and proxy image generation through a server/worker.
5. Make `bitwarden-mcp` authentication mandatory at startup and replace wildcard CORS with explicit allowlists on exposed worker routes.
6. Run a second remediation pass for the remaining audit leaves once the live credential branches are closed.
