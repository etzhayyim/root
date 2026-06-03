#!/usr/bin/env bash
# Wrapper that pulls PDS app-password from macOS Keychain and calls the
# Node CLI. Keep the credential out of shell history and env exports.
#
# Keychain conventions (per CLAUDE.md):
#   service=etzhayyim, account=PDS_APP_PASSWORD            (operator app-pwd)
#   service=etzhayyim, account=PDS_HANDLE                   (PDS handle / identifier)
#
# Override per invocation:
#   PDS_URL=https://pds.etzhayyim.com PDS_HANDLE=yoro.etzhayyim.com \
#     PDS_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx ./bin/seed-post.sh "text"

set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"

if [[ -z "${PDS_HANDLE:-}" ]]; then
  if PDS_HANDLE="$(security find-generic-password -s etzhayyim -a PDS_HANDLE -w 2>/dev/null)"; then
    export PDS_HANDLE
  fi
fi
if [[ -z "${PDS_APP_PASSWORD:-}" ]]; then
  if PDS_APP_PASSWORD="$(security find-generic-password -s etzhayyim -a PDS_APP_PASSWORD -w 2>/dev/null)"; then
    export PDS_APP_PASSWORD
  fi
fi

if [[ -z "${PDS_HANDLE:-}" || -z "${PDS_APP_PASSWORD:-}" ]]; then
  cat >&2 <<'EOF'
[seed-post.sh] missing credentials.

Provision once:
  security add-generic-password -s etzhayyim -a PDS_HANDLE        -w '<your-handle>'
  security add-generic-password -s etzhayyim -a PDS_APP_PASSWORD  -w '<app-password>'

Then re-run:
  ./bin/seed-post.sh "hello kotoba-datomic"

Or pass inline (note: leaks into shell history):
  PDS_HANDLE=... PDS_APP_PASSWORD=... ./bin/seed-post.sh "..."
EOF
  exit 2
fi

cd "$HERE/.."
if [[ ! -d node_modules ]]; then
  echo "[seed-post.sh] installing deps via pnpm install (one-time)..." >&2
  pnpm install --silent
fi
exec node "$HERE/seed-post.mjs" "$@"
