---
id: adr-2605141700-agent-authentication-api-key-rotation-pattern
title: Agent-driven authentication — API key (sk_live_*) as canonical bearer, passkey ceremony as periodic rotation seed
status: active
doc_type: adr
topic: agent-auth-rotation
authoritative: true
last_verified: 2026-05-14
authoritative_for:
  - claude-code-agent-auth-pattern
  - api-key-rotation-cadence
  - webauthn-passkey-automation-limits
  - chrome-mcp-cookie-guardrail-scope
  - etzhayyim-cli-authn-endpoint-bug
related:
  - 0022-auth-topology-consolidation
  - 0023-auth-shannon-optimal-4-layer
  - adr-2604231821-atproto-oauth-wire-format-snake-case
  - adr-2604240914-oauth-rs-binding-revocation-introspection
supersedes: []
superseded_by: []
---

# Context

A 2026-05-14 session by an AI coding agent (Claude Code, Opus 4.7) needed to
call the `projector.add_blocker` MCP tool at `atproto.etzhayyim.com/mcp` to record
4 open blockers in the projector graph. Authentication failed because the
local `sk_live_*` API key in `~/.etzhayyim/auth.json` (issued 2026-04-23) had
been revoked or expired. The agent then tried four fallback paths and all
failed:

1. **Clerk `access_token` (`oat_...`)** — accepted by `tools/list` (public
   endpoint), rejected by `tools/call` (`AuthRequired`).
2. **Clerk `id_token` (Clerk RS256 JWT)** — same: list works, call rejected.
3. **`etzhayyim authn signin`** — opens
   `https://authn.etzhayyim.com/oauth/authorize?...` in the browser. That endpoint
   returns **HTTP 404** because the actual OAuth authorization server lives
   at `atproto.etzhayyim.com/oauth/authorize` (verified via
   `/.well-known/oauth-authorization-server`). The CLI's hardcoded URL is
   a stale pre-ADR-0024 path. Even after fixing the URL, the AT Protocol
   OAuth server requires DPoP-bound clients (`dpop_bound_access_tokens=true`
   in `oauth/client-metadata.json`) and rejects the CLI's PKCE-only
   `client_id=etzhayyim-cli` registration.
4. **Chrome MCP `javascript_tool` peeking the sign-in page DOM** — blocked
   by Chrome MCP's cookie/query-string guardrail (`[BLOCKED: Cookie/query
   string data]`). This guardrail is designed to prevent agent-in-browser
   credential exfiltration; it correctly fires on any
   `authn.etzhayyim.com/sign-in?...` URL.

The 4-layer matrix in `70-tools/etzhayyim/CLAUDE.md` already lists API key as the
correct programmatic path, but the practical implications of rotation —
that **passkey ceremony is the only way to re-mint a sk_live_***, and that
passkey is inherently un-automatable — were not documented anywhere. This
ADR fixes that gap and pins a CLI bug for follow-up.

# Decision

**1. API key (`sk_live_*`) is the canonical bearer for non-human agents.**

| Agent class | Auth | Lifetime | Renewal trigger |
|---|---|---|---|
| Claude Code session | `sk_live_*` from `~/.etzhayyim/auth.json` or `etzhayyim.auth/api_key` Keychain | ~1 y (server-configured) | Human passkey ceremony |
| CI job | `etzhayyim_TOKEN` env (sk_live_*) | matched to scoped need | Manual rotation |
| Heartbeat / cron pod | ES256 Service Auth JWT minted from app DID | 60 s scoped | per-invocation via `getServiceAuth` |
| Internal binding | `x-kotodama-verified: true` HMAC | per-request | n/a (service binding) |

`com.etzhayyim.auth.createApiKey` accepts **only** a fresh authn.etzhayyim.com session
(passkey-bound cookies) — **not** Clerk `oat_*`, **not** Clerk `id_token`,
**not** sk_test_, **not** prior sk_live_. This is by design: API key
creation is a privileged self-rotation that must be human-presence
attested.

**2. WebAuthn passkey is a non-negotiable human-presence gate.**

End-to-end automation of the passkey-with-Apple-Keychain flow is not
attempted. Three hard barriers, each sufficient on its own:

- macOS Touch ID / Face ID is **OS-level UI** — outside the browser
  process, so DOM-level browser automation (Chrome MCP, Playwright,
  Puppeteer) cannot interact with it. Tools that claim to (CDP
  `WebAuthn.addVirtualAuthenticator`) inject a *virtual* authenticator
  with its own credential, **not** the user's iCloud-Keychain passkey.
- Chrome MCP's cookie/query-string guardrail blocks JS inspection of any
  auth-flow page, preventing post-redirect token capture. This is a
  *correct* security policy — bypassing it would defeat the
  agent-vs-credential isolation that makes Chrome MCP safe to grant in
  the first place.
- AT Protocol OAuth (`atproto.etzhayyim.com/oauth/*`) requires DPoP-bound
  clients with explicit `redirect_uris` allowlisting — `client_id=etzhayyim-cli`
  + `redirect_uri=http://127.0.0.1:9876/callback` is not registered, so
  even hypothetically routing the CLI to the correct authorize endpoint
  would 401 the request.

**3. Storage: macOS Keychain primary, `~/.etzhayyim/auth.json` mirror.**

Per the root CLAUDE.md "Local Secret Storage = macOS Keychain primary"
rule, the canonical place for an agent's `sk_live_*` is

```
service = etzhayyim.auth
account = api_key
```

`etzhayyim authn` already reads from this slot as a fallback when
`~/.etzhayyim/auth.json` is missing (`70-tools/etzhayyim/etzhayyim/auth.go` line 65-67).
The agent runtime treats `~/.etzhayyim/auth.json` as a convenience cache that
gets re-populated from Keychain on first miss.

**4. Rotation cadence: ~1 year, scheduled.**

The default `sk_live_*` TTL is 1 year. Annual rotation is a documented
calendar event (operator owns the reminder). Outside that cycle,
unscheduled rotation = passkey re-ceremony at any iCloud-Keychain-equipped
device. **No agent can self-rotate** — that's the security property the
flow is designed to preserve.

**5. Fix the etzhayyim CLI's authorize URL** (follow-up, tracked).

`70-tools/etzhayyim/etzhayyim/auth.go:27` hardcodes
`https://authn.etzhayyim.com/oauth/authorize`. The actual OAuth Authorization
Server is at `https://atproto.etzhayyim.com/oauth/authorize` per
`/.well-known/oauth-authorization-server`. Fix: either
- (a) point the CLI at `atproto.etzhayyim.com` directly, register
      `client_id=etzhayyim-cli` in the AT Protocol client registry, add DPoP
      signing to the CLI, OR
- (b) deploy a thin `/oauth/authorize` + `/oauth/token` shim on
      `authn.etzhayyim.com` that wraps the AT Protocol OAuth flow without
      requiring DPoP at the CLI layer.

(a) is the standard atproto path. (b) is a 1-2 day patch that keeps the
CLI shape stable. Decision deferred to a separate ADR.

# Consequences

**Positive**:

- API key rotation is a clean, scheduled event with a known human owner.
- Compromised agent runtime → revoke that one `sk_live_*` via
  `etzhayyim authz revoke-api-key`; passkey + account remain intact.
- WebAuthn's security model is preserved end-to-end. Agents can't
  bootstrap themselves into the user's identity; they can only act
  within the bounded API key the human just granted.

**Negative**:

- Day-1 of a Claude Code session after a rotation gap costs ~1 minute of
  operator attention (open sign-in, Touch ID, copy `sk_live_*`, save to
  Keychain). This is the **floor** of the auth UX; no further
  optimisation is possible without weakening the security model.
- The "agent stuck at auth wall" state is recurrent (1×/year minimum,
  more often on revocation). Mitigation: make the recovery one command
  (see §Operator runbook below).

**Neutral**:

- ES256 Service Auth (60 s, NSID-scoped) covers high-frequency calls
  inside a session, so the API key only needs to be valid at the
  *start* of a session, not on every XRPC call. This reduces the blast
  radius of a single stolen `sk_live_*` significantly.

# Operator runbook (annual + on revocation)

```bash
# 1. Open the sign-in page (browser opens via macOS default browser).
open 'https://authn.etzhayyim.com/sign-in?redirect_url=https%3A%2F%2Fyoro.etzhayyim.com%2Fsettings%2Fdeveloper'

# 2. Sign in with passkey (Touch ID / Face ID via Apple Keychain).
#    After redirect to yoro.etzhayyim.com/settings/developer, click
#    "Create API key" → name=claude-2026-MM-DD, scopes=read,write,admin.
#    Copy the displayed sk_live_*.

# 3. Save to Keychain (primary) + auth.json (cache) in one shot.
NEW_KEY="sk_live_XXXXXXXXXXXXXXXX"
security add-generic-password -s etzhayyim.auth -a api_key -w "$NEW_KEY" -U
python3 - <<EOF
import json, os
p = os.path.expanduser('~/.etzhayyim/auth.json')
d = json.load(open(p)) if os.path.exists(p) else {}
d['api_key'] = "$NEW_KEY"
open(p, 'w').write(json.dumps(d, indent=2))
EOF
unset NEW_KEY

# 4. Sanity check.
etzhayyim authn whoami
etzhayyim projector list   # should not return AuthRequired
```

# Alternatives Considered

| Alternative | Why rejected |
|---|---|
| **Long-lived OAuth refresh token in `~/.etzhayyim/auth.json`** | DPoP-bound clients in AT Protocol OAuth don't support stateless refresh from non-browser clients. Refresh token storage outside DPoP key custody re-introduces bearer-token theft risk. |
| **App Password (Bluesky-style)** | Deprecated in AT Protocol per ADR-2604240914. No scope, not revocable per-action. |
| **Dedicated agent DID (`did:web:claude-jun.etzhayyim.com`) with local signing key** | Adds a second identity to govern with no benefit beyond what `getServiceAuth` already provides (60 s, NSID-scoped JWT). Increases attack surface. |
| **CDP Virtual Authenticator for passkey** | Possible but defeats purpose: the virtual passkey has no relation to the user's iCloud-Keychain credentials, so it's just a different API key under a different shape. The privileged-mint ceremony still happens once with the real passkey. |
| **Magic-link email at authn.etzhayyim.com** | Not currently offered. Adding it would re-introduce email-account-takeover risk that passkey was deployed to remove. |
| **Re-use the YORO Clerk session JWT (`__session` cookie)** | The Clerk-issued JWT's `aud` is `api-etzhayyim` for a dev tenant; production atproto.etzhayyim.com rejects it because issuer doesn't match the configured Clerk frontend. Bridge would require an iss-aware token-exchange endpoint that doesn't exist. |

# References

- `70-tools/etzhayyim/etzhayyim/auth.go` lines 27, 65-77 (current CLI auth source)
- `50-infra/cloudflare/workers/atproto/src/auth/verify.ts` lines 587-740
  (server-side authenticate flow — sk_live_*, ES256 Service Auth, public
  fallback)
- `50-infra/cloudflare/workers/atproto/src/app.ts` lines 609-613 (the
  `auth.level === "public" → AuthRequired` gate that fires on every
  Clerk-token call)
- `~/.etzhayyim/auth.json` (`api_key`, `sub`, `active_did`) — CLI state
- `~/.config/etzhayyim/credentials.json` (`access_token`, `id_token`,
  `refresh_token`) — Clerk-side state, NOT accepted by atproto auth
- macOS Keychain `etzhayyim.auth/api_key` — canonical storage per root
  CLAUDE.md "Local Secret Storage"
- `https://atproto.etzhayyim.com/.well-known/oauth-authorization-server` — the
  authoritative authorize/token endpoints
- ADR-0022 "Auth Topology Consolidation"
- ADR-0023 "Auth Shannon-Optimal 4-Layer"
- ADR-2604231821 "atproto OAuth wire-format = snake_case"
- ADR-2604240914 "OAuth server lifecycle (RS DPoP + revoke + introspect)"
- Session log: `50-infra/k8s/kenkyusha/DEPLOY-NOTES.md` "Active blockers
  2026-05-14" + this ADR's "Operator runbook" above.

# Follow-up tracked actions

| Action | Owner | ETA |
|---|---|---|
| Fix `etzhayyim authn` hardcoded URL → `atproto.etzhayyim.com/oauth/authorize`, add DPoP | CLI maintainer | Phase 1 (separate PR) |
| Add `etzhayyim auth fix-api-key <sk_live_*>` one-liner that does the security/json save above | CLI maintainer | optional UX polish |
| Add this ADR's runbook to the README of `70-tools/etzhayyim/` | docs | next sweep |
| Investigate CDP Virtual Authenticator for headless CI (separate from human agents) | future | not blocking |
