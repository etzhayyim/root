# Claude Agent Secret Handling — Practice Notes

**Date**: 2026-04-17
**Source event**: Google Workspace ingest (`60-apps/etzhayyim-project-gmail/`) OAuth bring-up — `client_secret` landed in a chat turn, which forced a rotation. Codified the principles we wanted in place *before* that happened.

## Why this doc

`CLAUDE.md` has Vault Zero-Knowledge invariants and `etzhayyim agent-token` scoped JWTs, but no single page says *"here is how to hand a secret to a Claude Code session safely"*. This is that page.

## Principles (in priority order)

1. **Don't put long-lived secrets into the transcript.** AI provider logs, local replay caches, screenshot artifacts — once a value is in conversation it's outside your custody.
2. **Prefer short-lived + scoped tokens over long-lived roots.** `etzhayyim agent-token --lxm <nsid> --ttl 60` is the canonical per-call JWT. One NSID, one minute, audit trail by `iss`.
3. **Secrets cross tool boundaries, not conversation boundaries.** `op read` / `wrangler secrets-store secret create <store> --value -` pipe values directly from source to sink. Claude knows the *name*, never the value.
4. **Make rotation a 1-liner.** If rotate is painful, the secret will leak and never get rotated. Design rotation first.

## Four tiers (by blast radius)

| Tier | Examples | Storage | How Claude agents interact |
|---|---|---|---|
| **T0 Device-only** | macOS Keychain, WebAuthn PRF, 1Password master password | Hardware / OS enclave | **Never share.** Human uses them directly. |
| **T1 Long-lived root** | `GOOGLE_OAUTH_CLIENT_SECRET`, `SS_REPO_SIGNING_KEK`, `CLOUDFLARE_API_TOKEN` | 1Password vault + CF Secrets Store | **Not in chat.** Pipe via `op read` or pre-provisioned env vars. Reference by secret *name*. |
| **T2 Mid-lived session** | `etzhayyim_TOKEN` API key (`sk_live_*`), `~/.etzhayyim/auth.json` JWT (90d refresh) | Encrypted at rest on dev box, `op` item | Export to env once per session. Claude references as `$etzhayyim_TOKEN`. |
| **T3 Ephemeral scoped** | `etzhayyim agent-token --lxm <nsid> --ttl 60`, OAuth access_token (1h) | In-memory, never persisted | **OK to pass directly.** 60s + single-method scope bounds blast radius. |

## Canonical flows

### Session setup (once per work day)

```bash
# 1. Root trust comes from 1Password
eval "$(op signin)"

# 2. Export T2 session key so Claude can reference it by name
export etzhayyim_TOKEN="$(op read 'op://Dev/etzhayyim-api-key/credential')"
```

Claude never sees the actual token; it runs `curl -H "Authorization: Bearer $etzhayyim_TOKEN" ...` with the shell variable.

### Per-call scoped token (the common case)

```bash
AT_TOKEN=$(etzhayyim agent-token --lxm com.etzhayyim.apps.gmail.syncInbox --ttl 60)
curl -H "Authorization: Bearer $AT_TOKEN" https://gmail.etzhayyim.com/xrpc/com.etzhayyim.apps.gmail.syncInbox -d '…'
```

One NSID per token. One minute lifetime. Caller DID in `iss` — audit trail intact.

### Provisioning a new T1 secret (value → CF Secrets Store, bypass chat)

```bash
# Whole value never touches stdout/Claude context
op read 'op://Dev/google-oauth-gmail/secret' | \
  wrangler secrets-store secret create "$STORE_ID" \
    --name google_oauth_client_secret --scopes workers --remote --value -
```

If Claude is driving: Claude runs the command, but the value is piped through stdin — it never appears in any stdout Claude can read.

### Rotation (after accidental exposure in chat)

```bash
# 1. Revoke at source
gcloud auth application-default revoke   # or Google Cloud Console OAuth Client → reset secret
# 2. Update 1Password
op item edit google-oauth-gmail.etzhayyim.com "client-secret=$(pbpaste)"
# 3. Re-provision downstream
op read 'op://Dev/google-oauth-gmail/secret' | \
  wrangler secrets-store secret update <STORE_ID> --name google_oauth_client_secret --value -
```

Timebox: if a T1 value appears in any chat transcript, rotate within 24h.

## Anti-patterns seen in this codebase

| Anti-pattern | Why bad | Do instead |
|---|---|---|
| Pasting client_secret into chat so Claude can `wrangler … put` | Value persists in transcript + local telemetry | `op read` pipe + Claude executes the piped command |
| Using Secrets Store binding (`SecretBinding`) directly as a string | serializes as `[object Fetcher]` in runtime (silent corruption, authz fails opaquely) | `const val = await resolveSecret(env.SS_FOO);` at point of use — see `60-apps/etzhayyim-project-gmail/.../src/app.ts` |
| Sharing `sk_live_*` API key to "let Claude test for me" | Unscoped, long-lived | Issue a separate API key per agent via `etzhayyim authz create-api-key --name claude-<purpose>` → revocable independently |
| Loading refresh_token as `TEXT` column in an AT Record | AT Repo is always federable — all subscribers see it | KEK envelope in a private D1 or `vault.etzhayyim.com` ciphertext |

## Claude Code Chrome extension setup conflict (2026-04-17)

Unrelated to secrets directly, but recording here because it blocked an agent-driven OAuth flow and the fix touches native messaging config:

**Symptom**: `claude-in-chrome` MCP returns `No Chrome extension connected` despite extension being installed and enabled.

**Cause**: Extension v1.0.68 enumerates 2 native messaging hosts in order —
`com.anthropic.claude_browser_extension` (Claude.app desktop) first, then
`com.anthropic.claude_code_browser_extension` (Claude Code CLI). If both
config files exist under `~/Library/Application Support/Google/Chrome/NativeMessagingHosts/`,
the extension binds to Claude.app's host and Claude Code CLI can never see it.

**Fix**:
```bash
# Option A: quit Claude.app (won't auto-relaunch its native host)
osascript -e 'quit app "Claude"'
# + kill orphan host + remove stale socket if present:
pkill -f '/Applications/Claude.app/Contents/Helpers/chrome-native-host'
rm -f /tmp/claude-mcp-browser-bridge-$USER/*.sock
# Then in Chrome: reload the extension at chrome://extensions → click icon → /chrome Reconnect

# Option B: permanently disable Claude.app's native host config (keeps the app running)
mv "$HOME/Library/Application Support/Google/Chrome/NativeMessagingHosts/com.anthropic.claude_browser_extension.json" \
   "$HOME/Library/Application Support/Google/Chrome/NativeMessagingHosts/.com.anthropic.claude_browser_extension.json.disabled"
# Reload extension in chrome://extensions.
```

Option B preferred when you mostly drive Chrome from Claude Code.

## Cross-references

- `CLAUDE.md` (root) — Vault Zero-Knowledge Invariant, ADR-0022 auth topology pointers
- `70-tools/etzhayyim/CLAUDE.md` — `etzhayyim auth`, `etzhayyim agent-token`, `etzhayyim xrpc` CLI
- `60-apps/etzhayyim-project-vault/CLAUDE.md` — per-user secret manager (future home for OAuth refresh tokens)
- `60-apps/etzhayyim-project-gmail/CLAUDE.md` — KEK envelope D1 token store reference impl
- `90-docs/260417-google-workspace-ingest-runbook.md` — Google Workspace ingest Phase 0 plan (Gmail is Phase 1)
