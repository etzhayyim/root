# yoro.etzhayyim.com Security Topology Analysis

Date: 2026-04-16
Time: 2026-04-16 08:02 JST

## Scope

- Target: `https://yoro.etzhayyim.com`
- Reviewed source:
  - `60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/src/app.ts`
  - `60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/_svelte/_headers`
  - `60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/svelte/src/app.html`
  - `60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/svelte/src/lib/auth/passkey.ts`
  - `60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/svelte/src/lib/apps/installed-apps.ts`
  - `10-protocol/wproto/src/client.ts`
  - `60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/svelte/src/routes/profile/[handle]/+page.server.ts`
  - `60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/svelte/src/routes/profile/[handle]/post/[rkey]/+page.server.ts`
  - `60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/svelte/src/routes/profile/[handle]/post/[rkey]/+page.svelte`
- Live verification:
  - `curl -I https://yoro.etzhayyim.com/`
  - `curl -I https://yoro.etzhayyim.com/profile/did:web:yoro.etzhayyim.com`
  - `curl https://yoro.etzhayyim.com/`
  - `curl https://yoro.etzhayyim.com/profile/did:web:yoro.etzhayyim.com`
  - `curl -X POST https://yoro.etzhayyim.com/api/internal/cache/purge -H 'content-type: application/json' -d '{}'`

## Topology

1. Public browser shell
   - `yoro.etzhayyim.com` currently serves the same generic SPA shell for `/` and `/profile/...`.
   - The live shell contains static JSON-LD plus Cloudflare-injected challenge JavaScript.
   - `svelte/src/app.html` also includes a hash-to-`sessionStorage` auth transfer shim.

2. Browser auth/session layer
   - `passkey.ts` persists `accessJwt` and `refreshJwt` in browser-readable `sessionStorage`.
   - `wproto/client.ts` mirrors both JWTs into the shared in-page `AtpAgent`.
   - Appstore requests additionally attach `X-etzhayyim-USER-ID` and `X-etzhayyim-ORG-ID`.

3. Edge worker layer
   - Source defines `withSecurityHeaders()` and mounts `/api/internal/cache/purge`.
   - Source says HTML responses should receive CSP and basic hardening headers.
   - Production HTML responses are not emitting those headers right now.

4. Dormant SSR route layer
   - Svelte SSR profile/post routes still exist in repo and still embed JSON-LD with `{@html}`.
   - Live production does not currently expose those SSR outputs; requests fall back to the SPA shell.

## Active Issues

### P1: Access and refresh tokens are readable to same-origin JavaScript

Evidence:

- `svelte/src/app.html:8-15`
  - Cross-origin auth handoff stores `#auth=...` into `sessionStorage`.
- `svelte/src/lib/auth/passkey.ts:31-38`
  - `StoredSession` includes both `accessJwt` and `refreshJwt`.
- `svelte/src/lib/auth/passkey.ts:67-70`
  - `storeSession()` writes the session blob to `sessionStorage`.
- `svelte/src/lib/auth/passkey.ts:94-100`
  - `syncWprotoSession()` copies both tokens into the browser-side W client.
- `svelte/src/lib/auth/passkey.ts:467-476`
  - `getSessionToken()` returns the bearer token to page JavaScript.
- `10-protocol/wproto/src/client.ts:35-61`
  - `getWSession()` / `setWSession()` expose and retain both JWTs in the in-page `AtpAgent`.

Why it survives pruning:

- This is active code, not a hypothetical path.
- Any same-origin script execution gets both immediate API access and refresh capability.
- This remains the highest-confidence blast-radius issue even if a specific XSS sink is currently dormant.

### P1: Production is not emitting the hardening headers that source intends

Evidence in source:

- `src/app.ts:151-159`
  - Defines `Referrer-Policy`, `X-Content-Type-Options`, `X-Frame-Options`, `Permissions-Policy`, `Strict-Transport-Security`, and HTML `Content-Security-Policy`.
- `src/app.ts:482-493`
  - `withSecurityHeaders()` applies them.
- `src/app.ts:860-865`
  - Worker fetch path wraps responses via `withSecurityHeaders()`.
- `_svelte/_headers:8-11`
  - Also declares header intent for the static site path.

Evidence in production on 2026-04-16 08:00 JST:

- `curl -I https://yoro.etzhayyim.com/` and `curl -I https://yoro.etzhayyim.com/profile/did:web:yoro.etzhayyim.com` returned `200` without:
  - `Content-Security-Policy`
  - `X-Content-Type-Options`
  - `X-Frame-Options`
  - `Referrer-Policy`
  - `Permissions-Policy`
  - `Strict-Transport-Security`

Why it survives pruning:

- This is a verified prod/source mismatch.
- It materially weakens containment for current and future client-side injection.
- It also means `_headers` is not the effective enforcement point for the live origin.

### P2: `/api/internal/cache/purge` is publicly enumerable and production behavior is drifting

Evidence in source:

- `src/app.ts:535-540`
  - Route should return `404` when `CACHE_PURGE_API_KEY` is unset.
- `src/app.ts:543-546`
  - Route should return `401` when bearer auth is missing or wrong.
- `src/app.ts:549-558`
  - Only after auth should it disclose missing Cloudflare purge secrets.
- `src/app.ts:833-837`
  - Route is mounted on the public origin.

Evidence in production on 2026-04-16 08:01 JST:

- Unauthenticated `POST /api/internal/cache/purge` returned:
  - `{"ok":false,"error":"CachePurgeSecretMissing","message":"CACHE_PURGE_CF_API_TOKEN and CACHE_PURGE_CF_ZONE_ID must be configured"}`

Why it survives pruning:

- The endpoint is externally discoverable today.
- Production is not following the checked-in auth gate semantics.
- Direct impact is lower than token exposure, but the operational drift is real and externally observable.

## Trust-Boundary Warnings

These are still suspicious, but not strong enough to keep as current issues without backend confirmation.

### P3: Client-supplied identity headers ride alongside bearer auth

Evidence:

- `svelte/src/lib/apps/installed-apps.ts:57-68`
  - Browser sends `Authorization`, `X-etzhayyim-USER-ID`, and `X-etzhayyim-ORG-ID`.

Assessment:

- This is only a vulnerability if the receiving service trusts those headers as authority.
- Keep it as a backend verification target, not a confirmed frontend-side issue.

## Pruned Branches

### Pruned: current live JSON-LD break-out on public pages

Evidence:

- Live `/` and live `/profile/...` both return the same generic shell.
- The shell JSON-LD is static platform metadata, not attacker-controlled content.

Why it is pruned:

- There is no current attacker-controlled value flowing into the live shell JSON-LD block.
- The existence of a `<script type="application/ld+json">` tag alone is not an issue.

### Dormant debt: SSR post-detail JSON-LD XSS sink

Evidence in code:

- `svelte/src/routes/profile/[handle]/post/[rkey]/+page.server.ts:43-88`
  - Post text flows into `jsonLd.articleBody`.
- `svelte/src/routes/profile/[handle]/post/[rkey]/+page.svelte:341-342`
  - JSON-LD is injected with raw `JSON.stringify(...)` inside `{@html}`.

Why it is not kept as an active production issue:

- Live `/profile/.../post/...` currently resolves to the generic SPA shell rather than this SSR output.
- The sink remains dangerous technical debt, but it is not the current live exploit path.

### Dormant debt: SSR profile JSON-LD sink

Evidence in code:

- `svelte/src/routes/profile/[handle]/+page.svelte:588-589`
  - Same raw JSON-LD injection pattern exists.
- `svelte/src/routes/profile/[handle]/+page.server.ts:16`
  - Current loader returns `{ handle, og: {} }`, so `jsonLd` is absent.

Why it is pruned:

- It is a sink pattern, but not populated in the present implementation.
- Keep it as clean-up debt, not a current issue.

### Pruned: worker fallback JSON-LD sink

Evidence:

- `src/app.ts:399`
  - Worker HTML generation escapes `<` via `.replace(/</g, "\\u003c")`.

Why it is pruned:

- That path is already hardened against `</script>` break-out.

## Root Cause Graph

1. Browser-side auth keeps long-lived credentials inside script-readable state.
2. Production response hardening is drifting from source control intent.
3. Internal maintenance surface is publicly mounted and runtime behavior differs from code.
4. Dormant SSR JSON-LD sinks still exist and could become live again with routing changes.

## Recommended Next Cut

1. Move refresh-token handling out of browser JavaScript.
   - If possible, make refresh server-managed or `HttpOnly`.

2. Fix prod/source drift before broader hardening.
   - Re-deploy the path that should emit security headers.
   - Re-check with `curl -I` immediately after deploy.

3. Remove or hide the purge route from the public origin.
   - If it must stay, make production behavior match the source auth gate now.

4. Clean dormant JSON-LD sinks before SSR routing is re-enabled.
   - Standardize one serializer that escapes `<` before embedding JSON-LD in HTML.
