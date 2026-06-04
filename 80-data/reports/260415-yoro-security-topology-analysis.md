# yoro.etzhayyim.com Security Topology Analysis

Date: 2026-04-15

## Scope

- Target: `https://yoro.etzhayyim.com`
- Code paths:
  - `60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/src/app.ts`
  - `60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/svelte/src/lib/auth/passkey.ts`
  - `60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/svelte/src/routes/profile/[handle]/post/[rkey]/+page.server.ts`
  - `60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/svelte/src/routes/profile/[handle]/post/[rkey]/+page.svelte`
  - `10-protocol/wproto/src/client.ts`
  - `60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/_svelte/_headers`
- Live checks:
  - `curl -I https://yoro.etzhayyim.com/`
  - `curl -I https://yoro.etzhayyim.com/profile/did:web:yoro.etzhayyim.com`
  - `curl -X POST https://yoro.etzhayyim.com/api/internal/cache/purge -H 'content-type: application/json' -d '{}'`

## Topology

1. Browser
   - Loads `yoro.etzhayyim.com` SPA or SSR route HTML.
   - Stores the active AT Protocol session in browser-readable state.
   - Uses `atproto.etzhayyim.com` / `authn.etzhayyim.com` for authenticated session creation and refresh.

2. yoro Worker
   - Serves `svelte/build` assets through the `ASSETS` binding.
   - Returns bot/fallback HTML directly from `src/app.ts`.
   - Exposes `/api/internal/cache/purge`.

3. Svelte SSR routes
   - Public `profile/{handle}/post/{rkey}` route builds OG and JSON-LD from post content.
   - Public `profile/{handle}` route is SSR-enabled but currently returns no JSON-LD payload.

4. PDS / Auth
   - `atproto.etzhayyim.com` is the XRPC gateway.
   - `authn.etzhayyim.com` issues and refreshes access/refresh JWTs.

The credible current attack chain is:

`attacker-controlled post text` -> `JSON-LD script break-out on /profile/{handle}/post/{rkey}` -> `browser JS execution on yoro.etzhayyim.com` -> `read access/refresh tokens from browser state` -> `session reuse against atproto/auth APIs`

## Current Findings

### P1: Stored XSS on public post detail route via JSON-LD script embedding

Evidence:

- `svelte/src/routes/profile/[handle]/post/[rkey]/+page.server.ts:45-94`
  - `post.record.text` flows into `title`, `description`, `og.postText`, and `jsonLd.articleBody`.
- `svelte/src/routes/profile/[handle]/post/[rkey]/+page.svelte:341-342`
  - `{@html \`<script type="application/ld+json">${JSON.stringify(data.jsonLd)}</script>\`}`

Why it is real:

- `JSON.stringify()` does not escape `</script>`.
- The route is SSR-enabled and public, so an attacker only needs a victim to open the post detail URL.
- A payload such as `</script><script>...</script>` in post text can terminate the JSON-LD block and execute JavaScript in the `yoro.etzhayyim.com` origin.

### P1: Same-origin JavaScript can read active access and refresh tokens

Evidence:

- `svelte/src/lib/auth/passkey.ts:34-39`
  - `StoredSession` includes both `accessJwt` and `refreshJwt`.
- `svelte/src/lib/auth/passkey.ts:75-78`
  - The session blob is persisted to `sessionStorage`.
- `svelte/src/lib/auth/passkey.ts:99-106`
  - `syncWprotoSession()` forwards both JWTs into the in-page client.
- `svelte/src/lib/auth/passkey.ts:467-476`
  - `getSessionToken()` returns the bearer token to page JavaScript.
- `10-protocol/wproto/src/client.ts:47-67`
  - `getWSession()` and `setWSession()` expose/store both tokens in the browser-side `AtpAgent`.

Interpretation:

- The stale `localStorage` claim is no longer correct for the main session blob.
- The security issue remains high-impact because any same-origin XSS can read active tokens from `sessionStorage` and the in-memory client session.

### P2: Intended security headers are not emitted by the live Worker response path

Evidence in repo:

- `appview/yoro-ui-g00h5zto/_svelte/_headers:8-11`
  - Declares `Referrer-Policy`, `X-Content-Type-Options`, `X-Frame-Options`, `Permissions-Policy`.

Evidence in runtime path:

- `src/app.ts:570-657`
  - SPA and bot/fallback responses set only `content-type` and `cache-control`.
  - The `index.html` asset response is rewrapped with `cache-control` only.

Observed live on 2026-04-15 17:02 JST:

- `curl -I https://yoro.etzhayyim.com/`
- `curl -I https://yoro.etzhayyim.com/profile/did:web:yoro.etzhayyim.com`

Observed headers do not include:

- `Content-Security-Policy`
- `X-Content-Type-Options`
- `X-Frame-Options`
- `Referrer-Policy`
- `Permissions-Policy`

Interpretation:

- The `_headers` hardening intent exists, but the actual Worker response path is not emitting those headers.
- This increases the blast radius of the stored XSS, especially because no CSP is present to constrain inline script execution.

## Pruned Branches

These were examined and intentionally downgraded or removed:

- `profile/[handle]/+page.svelte` JSON-LD
  - The page still contains the same JSON-LD embedding pattern.
  - But `profile/[handle]/+page.server.ts:18` currently returns only `{ handle, og: {} }`, so `data.jsonLd` is absent in the live implementation.
  - This is a dormant sink, not a current exploit path.

- Worker fallback/bot JSON-LD in `src/app.ts`
  - The Worker path uses `JSON.stringify(meta.jsonLd).replace(/</g, "\\u003c")`.
  - That specific branch is already hardened against `</script>` break-out.

- Main session in `localStorage`
  - No longer true for the primary session blob.
  - Current primary persistence is `sessionStorage`; `localStorage` is now mostly credential ID / DID metadata.

- Cache purge endpoint in source vs deployed runtime
  - Current source says `src/app.ts:511-523` should return `503 CachePurgeDisabled` when `CACHE_PURGE_API_KEY` is unset and `401` on missing/wrong bearer token.
  - Live on 2026-04-15 23:02 JST, unauthenticated `POST /api/internal/cache/purge` returned `500 CachePurgeSecretMissing`.
  - That means the deployed runtime is not behaving like the checked-in source on the auth gate. The most likely causes are deploy drift, an older Worker version, or a different route path in production.
  - This is not enough evidence to call the endpoint fully fail-open, but it is enough to keep it out of the pruned set. The correct branch cut is: lower priority than the stored XSS path, but still an active prod/source mismatch that needs immediate verification.

## Root Cause Graph

1. Public content is copied into HTML-adjacent contexts without safe serialization.
   - Post text flows into JSON-LD on an SSR route.

2. Browser secrets remain readable to page JavaScript.
   - Access and refresh JWTs are exposed to same-origin script.

3. Browser policy hardening is not applied on actual Worker responses.
   - The deployed route lacks CSP and basic hardening headers.

4. The codebase still contains multiple dormant JSON-LD sinks.
   - Only one is currently exploitable, but the pattern is repeated.

## Recommended Next Cut

1. Fix the public XSS first.
   - Replace JSON-LD injection with a helper that escapes `<` before insertion.
   - Apply the same helper everywhere `{@html}` emits `<script type="application/ld+json">`, even for currently static content.

2. Reduce token blast radius.
   - Remove refresh token access from browser JavaScript if at all possible.
   - Prefer an `HttpOnly` or server-managed refresh path for the long-lived credential.

3. Make response hardening effective in prod.
   - Emit `Referrer-Policy`, `X-Content-Type-Options`, `X-Frame-Options` or `frame-ancestors`, `Permissions-Policy`, and a workable CSP from the Worker itself.

4. Clean up dormant sinks and stale assumptions.
   - Standardize one safe JSON-LD serializer for Svelte routes and Worker HTML.
   - Re-run the security review after the XSS fix to verify no other public route still accepts attacker-controlled HTML-adjacent data.
