#!/usr/bin/env bash
# Resolve DATABASE_URL for graph-schema migrations.
#
# Lookup chain (highest privilege first):
#
#   1. Already-set `DATABASE_URL` env var               (caller-provided, win)
#   2. 1Password item `etzhayyim.rw/ROOT_URL`                (root user, full DDL)
#   3. macOS Keychain `etzhayyim.rw / KAISYA_URL`            (kaisya_app, read-only)
#   4. `~/.etzhayyim/rw-credentials.env` ROOT_URL            (last-resort fallback)
#
# This file MUST be `source`d, not executed, because it sets
# `DATABASE_URL` in the parent shell.
#
#   source 30-graph/graph-schema/scripts/load-database-url.sh
#   pnpm db:migrate
#
# Or one-shot:
#
#   eval "$(30-graph/graph-schema/scripts/load-database-url.sh print)"
#   pnpm db:migrate
#
# ADR root CLAUDE.md "Local Secret Storage" + ADR 2605092800 §D14
# bring-up note. Used by maps gsplat schema (`r_20260509220000_*`,
# `r_20260510120000_*`, `r_20260510130000_*`, `r_20260510140000_*`).

set -e -o pipefail

_PRINT_MODE="${1:-source}"

_emit() {
    local url="$1"
    local origin="$2"
    if [[ "$_PRINT_MODE" == "print" ]]; then
        printf 'export DATABASE_URL=%q\n' "$url"
        echo "# loaded from: $origin" >&2
    else
        export DATABASE_URL="$url"
        echo "[load-database-url] DATABASE_URL set from $origin" >&2
    fi
}

# 1. Already in env
if [[ -n "${DATABASE_URL:-}" ]]; then
    _emit "$DATABASE_URL" "env (already set)"
    return 0 2>/dev/null || exit 0
fi

# 2. 1Password — preferred (root user). The Japanese vault name
# breaks `op://` reference syntax, so we resolve by item ID.
# Item id `yi7hc5wozgfhbaneb3ny46w6ua` = `etzhayyim.rw/ROOT_URL` in
# vault `etzhayyim Japan株式会社`.
if command -v op >/dev/null 2>&1 && op whoami >/dev/null 2>&1; then
    if url=$(op item get yi7hc5wozgfhbaneb3ny46w6ua --fields label=credential 2>/dev/null) \
       && [[ -n "$url" ]]; then
        _emit "$url" "1Password etzhayyim.rw/ROOT_URL"
        return 0 2>/dev/null || exit 0
    fi
fi

# 3. macOS Keychain — KAISYA_URL only (kaisya_app user). OK for
# read-only / drift checks; insufficient for `db:migrate` if it
# needs CREATE / ALTER. Caller can use it then re-try with op
# signed in for write paths.
if url=$(security find-generic-password -s etzhayyim.rw -a KAISYA_URL -w 2>/dev/null) \
   && [[ -n "$url" ]]; then
    _emit "$url" "Keychain etzhayyim.rw/KAISYA_URL (read-only kaisya_app)"
    return 0 2>/dev/null || exit 0
fi

# 4. Local fallback file (chmod 600). May contain stale Linode IP —
# refresh by re-pulling from 1Password.
if [[ -f "$HOME/.etzhayyim/rw-credentials.env" ]]; then
    # shellcheck disable=SC1091
    set -a; source "$HOME/.etzhayyim/rw-credentials.env"; set +a
    if [[ -n "${ROOT_URL:-}" ]]; then
        _emit "$ROOT_URL" "$HOME/.etzhayyim/rw-credentials.env (may be stale)"
        return 0 2>/dev/null || exit 0
    fi
fi

echo "[load-database-url] FAIL: no source. Run: op signin" >&2
return 1 2>/dev/null || exit 1
