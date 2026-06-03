# yoro.etzhayyim.com Security Topology (2026-04-15)

## Scope

- Target: `yoro.etzhayyim.com`
- Related trust boundaries:
  - `60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/svelte`
  - `60-apps/etzhayyim-project-auth/worker`
  - `50-infra/cloudflare/workers/atproto`

## Topology

```text
browser (yoro.etzhayyim.com)
  -> local/sessionStorage
  -> third-party JS (Google AdSense)
  -> authn.etzhayyim.com (#auth transfer + refreshSession)
  -> atproto.etzhayyim.com (XRPC, credentials include, Bearer/session)
  -> app iframes on *.etzhayyim.com / external app hosts

authn.etzhayyim.com
  -> sets Domain=.etzhayyim.com HttpOnly session cookie
  -> also returns access/refresh JWTs to browser JS

atproto.etzhayyim.com
  -> reflects Origin in CORS
  -> accepts credentials + Authorization
```

## Primary Findings

### 1. Browser-side session persistence is the main compromise path

`yoro` stores `accessJwt` and `refreshJwt` in browser storage and mirrors them into client-side session objects.

- Evidence:
  - [`60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/svelte/src/lib/auth/passkey.ts`](/Users/junkawasaki/etzhayyim/etzhayyim-root/60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/svelte/src/lib/auth/passkey.ts:34)
  - [`60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/svelte/src/lib/auth/passkey.ts`](/Users/junkawasaki/etzhayyim/etzhayyim-root/60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/svelte/src/lib/auth/passkey.ts:75)
  - [`60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/svelte/src/lib/auth/passkey.ts`](/Users/junkawasaki/etzhayyim/etzhayyim-root/60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/svelte/src/lib/auth/passkey.ts:101)
  - [`60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/svelte/src/lib/atproto-agent.ts`](/Users/junkawasaki/etzhayyim/etzhayyim-root/60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/svelte/src/lib/atproto-agent.ts:23)

- Impact:
  - Any XSS, compromised third-party script, or malicious same-origin code can exfiltrate both access and refresh tokens.
  - Because refresh is browser-usable, compromise is durable, not just session-length.

- Why this is top priority:
  - This collapses the value of the HttpOnly cookie path. The browser already has the raw bearer material.

### 2. Secret material is committed in auth Worker config

`auth` Worker config currently contains live/secret-looking values in `vars`.

- Evidence:
  - [`60-apps/etzhayyim-project-auth/worker/wrangler.jsonc`](/Users/junkawasaki/etzhayyim/etzhayyim-root/60-apps/etzhayyim-project-auth/worker/wrangler.jsonc:24)

- Notable values:
  - `SS_AT_SESSION_SECRET` placeholder in `vars`
  - `SS_STRIPE_SECRET_KEY` with a live `sk_live_...` value

- Impact:
  - Repo read access becomes production secret access.
  - Any fork, backup, CI artifact, or accidental paste becomes a credential leak channel.

- Why this is top priority:
  - This is a direct secret hygiene failure, independent of frontend exploitability.

### 3. Cross-origin auth surface is broader than necessary

PDS reflects request origin for CORS and allows credentials. Auth uses a cross-subdomain cookie and also exposes HTML with permissive CORS.

- Evidence:
  - [`50-infra/cloudflare/workers/atproto/src/middleware/index.ts`](/Users/junkawasaki/etzhayyim/etzhayyim-root/50-infra/cloudflare/workers/atproto/src/middleware/index.ts:24)
  - [`60-apps/etzhayyim-project-auth/worker/src-ts/index.ts`](/Users/junkawasaki/etzhayyim/etzhayyim-root/60-apps/etzhayyim-project-auth/worker/src-ts/index.ts:171)
  - [`60-apps/etzhayyim-project-auth/worker/src-ts/index.ts`](/Users/junkawasaki/etzhayyim/etzhayyim-root/60-apps/etzhayyim-project-auth/worker/src-ts/index.ts:251)
  - [`60-apps/etzhayyim-project-auth/worker/src-ts/index.ts`](/Users/junkawasaki/etzhayyim/etzhayyim-root/60-apps/etzhayyim-project-auth/worker/src-ts/index.ts:1438)

- Impact:
  - If an allowlisted or same-site origin is compromised, cookie-backed XRPC becomes reachable with fewer barriers.
  - The design is survivable if tokens stay HttpOnly-only and origin allowlists are tight; it is much less survivable when browser JS also holds refresh tokens.

- Severity note:
  - This is important, but it is currently downstream of finding #1. Tightening CORS without removing browser-held refresh tokens does not materially close the main path.

## Amplifiers

### Third-party script inclusion raises the cost of browser-held tokens

- Evidence:
  - [`60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/svelte/src/app.html`](/Users/junkawasaki/etzhayyim/etzhayyim-root/60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/svelte/src/app.html:25)

- Observation:
  - `yoro` loads Google AdSense JS.
  - I did not find a source-side CSP in `static/_headers`; build output headers differ from source.

### Header source of truth is drifting

- Evidence:
  - [`60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/static/_headers`](/Users/junkawasaki/etzhayyim/etzhayyim-root/60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/static/_headers:1)
  - [`60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/_svelte/_headers`](/Users/junkawasaki/etzhayyim/etzhayyim-root/60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/_svelte/_headers:9)

- Observation:
  - Source headers are minimal.
  - Built artifact has `Referrer-Policy`, `X-Frame-Options`, and `Permissions-Policy`.
  - This drift makes it unclear which protections are intentional and reproducible.

## Pruned Branches

These are not the current root issues.

### Rich text rendering is not the immediate XSS root

- [`60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/svelte/src/lib/w/RichText.svelte`](/Users/junkawasaki/etzhayyim/etzhayyim-root/60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/svelte/src/lib/w/RichText.svelte:1)
- I did not find `{@html}` or raw HTML injection in the path I checked.

### `getSession()` raw unauth bootstrap regression appears already pruned

- The codebase guidance and current search results are consistent with `getWSession()` replacing raw unauth session probes.
- This was a prior hygiene issue, but not the main current exposure.

### Iframe embedding is secondary, not primary

- Some embeds are sandboxed, some game embeds intentionally are not:
  - [`60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/svelte/src/routes/profile/[handle]/AgentProfile.svelte`](/Users/junkawasaki/etzhayyim/etzhayyim-root/60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/svelte/src/routes/profile/[handle]/AgentProfile.svelte:1235)
- This matters, but iframe isolation is not the first branch to cut while refresh tokens remain readable in JS.

## Recommended Cut Order

1. Remove browser-readable refresh tokens from `yoro`.
2. Rotate and remove committed secrets from `auth` Worker config.
3. Replace reflective CORS with a strict origin allowlist for credentialed endpoints.
4. Make header policy source-of-truth explicit and add CSP deliberately.

## Minimum Viable Fix Direction

### Auth/session

- Keep `accessJwt` short-lived in memory only.
- Keep refresh capability in HttpOnly cookie only.
- Remove `refreshJwt` from `setWSession()` and any browser persistence path.

### Secret hygiene

- Delete `SS_STRIPE_SECRET_KEY` from repo config.
- Rotate the Stripe secret immediately.
- Move session/Stripe secrets to Secrets Store only.

### Browser hardening

- Add explicit CSP for `yoro.etzhayyim.com`.
- Review whether AdSense is worth the attack-surface cost before token persistence is fixed.

