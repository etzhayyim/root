# Repo Security Topology (Pruned)

Date: 2026-04-21
Time: 2026-04-21 09:01:42 JST

## Scope

- Repository: `etzhayyim-root`
- Method:
  - static review of current `HEAD`
  - repo-wide pruning of public attack branches, credential residue, and dependency-driven auth breakage
  - `pnpm audit --prod` at workspace root

## Topology

1. Credential residue layer
   - reusable infrastructure and storage credentials are still embedded in executable scripts and CLI fleet tooling
   - several data-ingest paths also hardcode direct production or staging database endpoints

2. Identity and session layer
   - browser auth still keeps refresh capability in script-readable state
   - middleware-based route protection depends on currently vulnerable Clerk packages in active apps

3. Public edge worker layer
   - multiple public worker surfaces still expose wildcard or reflective CORS helpers
   - at least one secrets-adjacent worker makes authentication optional by configuration

## Active Repo Issues

### P0: Hardcoded reusable credentials remain in executable code

Evidence:

- `60-apps/etzhayyim-project-common-crawl/scripts/ingest_chunked.py`
  - embeds Linode object-storage access and secret keys in `S3_CONF`
- `60-apps/etzhayyim-project-common-crawl/scripts/s3_upload_and_ingest.py`
  - same keypair is used as executable default fallback
- `70-tools/etzhayyim/etzhayyim/murakumo_fleet.go`
  - hardcodes fleet SSH password `fleetSSHPass`
- `70-tools/scripts/bulk-stream-ingest.mjs`
  - hardcodes a Kotoba/Datomic password-bearing DSN
- `70-tools/scripts/yabai-baseline-ingest.mjs`
  - keeps the same DSN as default fallback

Why it survives pruning:

- these are not examples or docs; they are live executable paths
- compromise value is immediate after repo disclosure
- several credentials are duplicated across files, so one missed cleanup leaves the branch open

### P1: Auth boundary depends on vulnerable Clerk middleware packages

Evidence:

- `pnpm audit --prod` reported critical advisories for:
  - `@clerk/nextjs < 6.39.2`
  - `@clerk/shared < 4.8.1` and `< 3.47.4` on affected paths
- `60-apps/etzhayyim-project-hrse/appview/external-hrse/package.json`
  - pins `@clerk/nextjs` to `6.34.1`
- `60-apps/etzhayyim-project-hrse/appview/external-hrse/src/middleware.ts`
  - relies directly on `clerkMiddleware(...)` and `auth.protect()`
- `60-apps/etzhayyim-project-docs/appview/docs-performers-r5ycqp6x/svelte/package.json`
  - uses `svelte-clerk`, which pulls the vulnerable `@clerk/shared` path in audit output

Why it survives pruning:

- this is a critical authz bypass class on route protection, not a cosmetic package lag
- the vulnerable packages sit on active authentication and route-guard codepaths
- unlike many moderate audit findings, this directly weakens authorization semantics

### P1: Browser session still stores both access and refresh JWTs in script-readable state

Evidence:

- `60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/svelte/src/lib/auth/passkey.ts`
  - `StoredSession` contains `accessJwt` and `refreshJwt`
  - session is stored in `sessionStorage`
  - both JWTs are synced into `@etzhayyim/wproto`
- `60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/svelte/src/app.html`
  - `#auth=` hash content is copied into `sessionStorage` before URL cleanup

Why it survives pruning:

- any same-origin XSS or malicious third-party script gets present and refresh capability
- this is active runtime code on a browser auth surface

### P1: Public worker surfaces still expose permissive CORS and optional auth branches

Evidence:

- `50-infra/cloudflare/workers/atproto/src/auth.ts`
  - `withCors()` reflects request origin or falls back to `*`
- `60-apps/etzhayyim-project-llm/appview/etzhayyim-wasm-llm-llm8cf4ai/src/app.ts`
  - OpenAI-compatible `/v1/*` responses and preflight return `Access-Control-Allow-Origin: *`
- `50-infra/cloudflare/workers/bitwarden-mcp/src/index.ts`
  - global CORS policy is `*`
  - auth guard only runs if `env.MCP_AUTH_TOKEN` is configured, making unauthenticated deployment possible

Why it survives pruning:

- this is no longer a single dead helper; the same trust-widening pattern exists across several externally callable workers
- wildcard CORS alone is not always exploitable, but optional auth on secrets-adjacent infrastructure materially raises risk

## Dependency Audit Summary

Workspace root `pnpm audit --prod` result:

- 4 critical
- 6 high
- 8 moderate
- 2 low

Highest-signal branches after pruning:

1. Clerk middleware auth bypass in `hrse` and `docs`
2. `protobufjs < 7.5.5` via `orgs/etzhayyim/com-etzhayyim-ameno -> @huggingface/transformers -> onnxruntime-web`
3. `undici < 7.24.0` in `60-apps/etzhayyim-project-scap` workflow chain
4. `hono < 4.12.14` in `40-engine/kotoba/crates/kotoba-kotodama/sdk/kotodama-host-sdk`

Pruning note:

- `protobufjs` is critical by advisory severity, but current path looks narrower than the authz and embedded-credential branches because it sits in a browser inference package rather than a core auth surface
- moderate and low package issues were not promoted unless they intersected auth, HTML injection, or externally exposed worker paths

## Pruned Branches

### Pruned: root ignored `.env` as a repo-tracked issue

Reason:

- it still matters operationally, but current evidence shows local workstation residue rather than tracked repository content
- keep treating it as local secret hygiene, not the main repo branch

### Pruned: standalone reflective `atproto` helper as the only CORS concern

Reason:

- it remains worth deleting
- the bigger current issue is the broader pattern across `atproto`, `llm`, and `bitwarden-mcp`, so the helper is no longer the right leaf to track on its own

## Root Cause Graph

1. Secrets continue to be embedded directly into runnable code instead of injected at runtime.
2. Browser auth still treats refresh capability as JavaScript-readable state.
3. Public worker code and auth middleware still allow trust boundaries to be widened by configuration drift and stale dependencies.

## Next Cut

1. Rotate the S3 object-storage keypair and every DSN secret currently embedded in code.
2. Remove hardcoded credentials from `common-crawl`, `bulk-stream-ingest`, `yabai-baseline-ingest`, and `murakumo_fleet` in the same sweep.
3. Upgrade `@clerk/nextjs` and all transitive `@clerk/shared` consumers above the patched versions before relying on middleware route protection.
4. Move `yoro` refresh capability out of browser-managed storage into `HttpOnly` or server-side session handling.
5. Make authentication mandatory for `bitwarden-mcp` deployments and replace permissive CORS defaults on public worker surfaces with explicit allowlists.
6. Schedule a second pass focused only on `pnpm audit` remediation for `protobufjs`, `undici`, and `hono`.
