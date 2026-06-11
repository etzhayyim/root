#!/usr/bin/env bash
# T+14d cleanup for ADR-2604241038 Phase γ2 — `LEGACY_TRUST_HEADERS` flip
# has run for 2 weeks with `[trust][legacy] hit = 0`, so now we drop the
# grace code + env vars from the codebase.
#
# This script is the pre-written PR body from
# `90-docs/260424-legacy-trust-headers-cutover-runbook.md` §Post-flip
# cleanup. Running it produces a commit-ready diff; nothing touches
# deployed Workers until the operator runs `wrangler deploy`.
#
# Usage:
#   bash 70-tools/scripts/cleanup-legacy-trust-headers.sh         # apply
#   DRY_RUN=1 bash 70-tools/scripts/cleanup-legacy-trust-headers.sh  # show diff
#
# Preconditions (the operator asserts these):
#   - γ2 Logpush query shows 0 `[trust][legacy] hit` events per 24h for
#     14 consecutive days (see runbook §2 Warn-log volume probe).
#   - The 4 Workers (atproto / appview / chat / signal) have shipped the
#     HMAC-trio emit + verify code for ≥ 14 days.
#   - `LEGACY_TRUST_HEADERS=off` has been live in production for ≥ 14d.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

DRY_RUN="${DRY_RUN:-0}"
TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT

# Each transform writes its new content into $TMPDIR then diff-or-apply.
apply_or_diff() {
  local label="$1" target="$2" new="$3"
  if ! [[ -f "$target" ]]; then
    printf '\033[33m⚠ %s: target missing — %s\033[0m\n' "$label" "$target"
    return
  fi
  if [[ "$DRY_RUN" == "1" ]]; then
    printf '\n── %s ──\n' "$label"
    diff -u "$target" "$new" || true
  else
    cp "$new" "$target"
    printf '  ✔ %s\n' "$label"
  fi
}

# ── 1. atproto wrangler.jsonc — remove LEGACY_TRUST_HEADERS env var ─────
ATPROTO_WRANGLER="${REPO_ROOT}/50-infra/cloudflare/workers/atproto/wrangler.jsonc"
awk '
  /ADR-2604241038 Phase γ2: emit the legacy x-etzhayyim-authenticated-did/ { skip = 3; next }
  skip > 0 { skip--; next }
  /"LEGACY_TRUST_HEADERS": "on"/ {
    # Drop the trailing comma on the preceding "DPOP_CNF_JKT_ENFORCEMENT"
    # line if it was the last in the vars block. We detect that by checking
    # the next non-blank line is a closing brace.
    next
  }
  { print }
' "$ATPROTO_WRANGLER" > "$TMPDIR/atproto-wrangler.jsonc"
# Strip the now-dangling trailing comma before the `}` close of "vars".
perl -i -0pe 's/("DPOP_CNF_JKT_ENFORCEMENT"\s*:\s*"(?:warn|strict)"),\s*\n(\s*})/$1\n$2/s' \
  "$TMPDIR/atproto-wrangler.jsonc"
apply_or_diff "atproto wrangler.jsonc" "$ATPROTO_WRANGLER" "$TMPDIR/atproto-wrangler.jsonc"

# ── 2. atproto dispatch.ts — drop emitLegacy branch in pipethroughAppView ─
ATPROTO_DISPATCH="${REPO_ROOT}/50-infra/cloudflare/workers/atproto/src/dispatch.ts"
# Remove lines 368-387 inclusive (the emitLegacy block + its preceding
# 4-line comment). Use awk so it's idempotent if someone already started
# the cleanup: we match on the distinctive opening comment + closing `}`.
awk '
  /ADR-2604241038 Phase γ2 — legacy shim emission\./ { skipping = 1 }
  skipping && /^    if \(emitLegacy\) \{/ { inBlock = 1 }
  !skipping { print; next }
  skipping && inBlock && /^    \}$/ { skipping = 0; inBlock = 0; next }
  skipping { next }
' "$ATPROTO_DISPATCH" > "$TMPDIR/atproto-dispatch.ts"
apply_or_diff "atproto dispatch.ts" "$ATPROTO_DISPATCH" "$TMPDIR/atproto-dispatch.ts"

# ── 3. appview wrangler.jsonc ──────────────────────────────────────────
APPVIEW_WRANGLER="${REPO_ROOT}/50-infra/cloudflare/workers/appview/wrangler.jsonc"
awk '
  /ADR-2604241038 Phase γ2: accept legacy x-etzhayyim-internal-trust/ { skip = 3; next }
  skip > 0 { skip--; next }
  /"LEGACY_TRUST_HEADERS": "on"/ { next }
  { print }
' "$APPVIEW_WRANGLER" > "$TMPDIR/appview-wrangler.jsonc"
perl -i -0pe 's/("ENVIRONMENT"\s*:\s*"production"),\s*\n(\s*})/$1\n$2/s' \
  "$TMPDIR/appview-wrangler.jsonc"
apply_or_diff "appview wrangler.jsonc" "$APPVIEW_WRANGLER" "$TMPDIR/appview-wrangler.jsonc"

# ── 4. appview handlers/appview.ts — drop legacy branch from trustedViewerDid ─
APPVIEW_HANDLER="${REPO_ROOT}/50-infra/cloudflare/workers/appview/src/handlers/appview.ts"
# Strategy: rewrite the function + drop the two legacy header constants.
# This is the most invasive surgery; we do it with a targeted
# here-doc-based replacement rather than awk.
python3 - "$APPVIEW_HANDLER" "$TMPDIR/appview-handler.ts" <<'PY'
import re, sys
src, dst = sys.argv[1], sys.argv[2]
with open(src) as f:
    txt = f.read()

# Drop the legacy header constants (lines 25-26 originally).
txt = re.sub(
    r'\nconst TRUSTED_VIEWER_DID_HEADER = "x-etzhayyim-authenticated-did";\n'
    r'const INTERNAL_TRUST_HEADER = "x-etzhayyim-internal-trust";\n',
    '\n',
    txt,
)

# Collapse the doc comment that talks about legacy shared secret.
txt = re.sub(
    r' \* Viewer identity: forwarded by the PDS `pipethroughAppView` helper on\n'
    r' \* `x-etzhayyim-authenticated-did`\. Trust is gated by the\n'
    r' \* `x-etzhayyim-internal-trust` shared secret — requests that reach this\n'
    r' \* Worker without that header stay anonymous so a public request to\n'
    r' \* bsky\.etzhayyim\.ai can\'t forge a viewer DID\.\n',
    ' * Viewer identity: forwarded by the PDS `pipethroughAppView` helper as\n'
    ' * the HMAC-signed `x-etzhayyim-viewer-{did,issued-at,signature}` trio\n'
    ' * (ADR-2604241038 Contract 3). Requests without a valid trio stay\n'
    ' * anonymous so a public request to bsky.etzhayyim.com can\'t forge a viewer DID.\n',
    txt,
)

# Drop the dual-accept comment block.
txt = re.sub(
    r'// ADR-2604241038 Contract 3: dual-accept during Phase γ grace\.\n'
    r'//   Primary — HMAC-signed trio \(x-etzhayyim-viewer-\{did,issued-at,signature\}\)\.\n'
    r'//   Legacy — plain x-etzhayyim-authenticated-did \+ x-etzhayyim-internal-trust shared\n'
    r'//            secret \(will be dropped once PDS has emitted HMAC for 1 release\)\.\n',
    '// ADR-2604241038 Contract 3: HMAC-signed 3-header viewer-DID envelope.\n',
    txt,
)

# Rewrite trustedViewerDid() to HMAC-only.
pattern = re.compile(
    r'async function trustedViewerDid\(request: Request, env: Env\): Promise<string> \{[\s\S]+?\n\}\n',
    re.MULTILINE,
)
replacement = '''async function trustedViewerDid(request: Request, env: Env): Promise<string> {
  const secret = await resolveInternalSecret(env);
  return verifyHmacTrio(request, secret);
}
'''
new_txt, n = pattern.subn(replacement, txt, count=1)
if n != 1:
    sys.stderr.write(f"WARN: trustedViewerDid replacement count={n} (expected 1)\n")
with open(dst, 'w') as f:
    f.write(new_txt)
PY
apply_or_diff "appview handlers/appview.ts" "$APPVIEW_HANDLER" "$TMPDIR/appview-handler.ts"

# ── 5. chat wrangler.jsonc ─────────────────────────────────────────────
CHAT_WRANGLER="${REPO_ROOT}/50-infra/cloudflare/workers/chat/wrangler.jsonc"
awk '
  /ADR-2604241038 Phase γ2 legacy-trust flag mirrors/ { skip = 4; next }
  skip > 0 { skip--; next }
  /"LEGACY_TRUST_HEADERS": "on"/ { next }
  { print }
' "$CHAT_WRANGLER" > "$TMPDIR/chat-wrangler.jsonc"
perl -i -0pe 's/("ENVIRONMENT"\s*:\s*"production"),\s*\n(\s*})/$1\n$2/s' \
  "$TMPDIR/chat-wrangler.jsonc"
apply_or_diff "chat wrangler.jsonc" "$CHAT_WRANGLER" "$TMPDIR/chat-wrangler.jsonc"

# ── 6. signal wrangler.jsonc ───────────────────────────────────────────
SIGNAL_WRANGLER="${REPO_ROOT}/50-infra/cloudflare/workers/signal/wrangler.jsonc"
awk '
  /"LEGACY_TRUST_HEADERS": "on"/ { next }
  { print }
' "$SIGNAL_WRANGLER" > "$TMPDIR/signal-wrangler.jsonc"
perl -i -0pe 's/("ENVIRONMENT"\s*:\s*"production"),\s*\n(\s*})/$1\n$2/s' \
  "$TMPDIR/signal-wrangler.jsonc"
apply_or_diff "signal wrangler.jsonc" "$SIGNAL_WRANGLER" "$TMPDIR/signal-wrangler.jsonc"

if [[ "$DRY_RUN" == "1" ]]; then
  printf '\n\033[36mDRY_RUN=1 — no files modified. Re-run without DRY_RUN to apply.\033[0m\n'
else
  cat <<'POST'

  ✔ Cleanup applied to 4 wranglers + 2 source files.

  Verify:
    cd 50-infra/cloudflare/workers/atproto && npx vitest run src/routing-table.test.ts
    cd 50-infra/cloudflare/workers/appview && npx vitest run 2>&1 | tail -5

  Then commit (one per Worker or one combined — maintainer's call):
    git add 50-infra/cloudflare/workers/{atproto,appview,chat,signal}/
    git commit -m "chore(trust): retire LEGACY_TRUST_HEADERS grace path (γ2 T+14d)"

  Then deploy in the runbook order (bsky → chat → signal → atproto):
    cd 50-infra/cloudflare/workers/appview && wrangler deploy
    cd ../chat && wrangler deploy
    cd ../signal && wrangler deploy
    cd ../atproto && wrangler deploy

  Last: update ADR-2604241038 status tag ("γ2-complete") and delete
  `90-docs/260424-legacy-trust-headers-cutover-runbook.md` per the
  ephemeral-runbook convention.
POST
fi
