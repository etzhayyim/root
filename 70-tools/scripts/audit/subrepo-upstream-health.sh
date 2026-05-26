#!/usr/bin/env bash
#
# subrepo-upstream-health.sh — find `.gitrepo` files whose `remote` URL
# no longer resolves to a live GitHub repo (404). Excludes the cofog
# tree by default (hundreds of per-COFOG-code subrepos that warrant
# separate audit cadence).
#
# History:
#   - iter-28 of /loop (2026-05-26): discovered the SDK's `.gitrepo`
#     pointed at `gftdcojp/kami-engine-sdk` (404); the actual upstream
#     was `etzhayyim/kami-engine-sdk`. Fixed iter-28 commit 957ec4c0a.
#   - iter-29 of /loop (2026-05-26): broader audit found 7 more stale
#     entries from the gftd → etzhayyim org cleanup (ADR-2605211845);
#     documented in ADR with 3 resolution options per file (operator
#     choice — Update / Detach / Leave-as-is).
#   - this script codifies the audit pattern.
#
# Usage:
#   bash 70-tools/scripts/audit/subrepo-upstream-health.sh
#   bash 70-tools/scripts/audit/subrepo-upstream-health.sh --include-cofog
#   bash 70-tools/scripts/audit/subrepo-upstream-health.sh --strict
#
# Requires: `gh` CLI authenticated to GitHub.
# Returns: list of stale entries via stdout. Exit code 0 unless --strict.

set -euo pipefail

INCLUDE_COFOG=0
STRICT=0
for arg in "$@"; do
  case "$arg" in
    --include-cofog) INCLUDE_COFOG=1 ;;
    --strict) STRICT=1 ;;
    *) echo "unknown arg: $arg" >&2; exit 2 ;;
  esac
done

# Resolve repo root (assume script invoked from anywhere in the tree).
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
cd "$REPO_ROOT"

EXCLUDES=(-not -path "*/node_modules/*" -not -path "*/.claude/*")
if [ "$INCLUDE_COFOG" -eq 0 ]; then
  EXCLUDES+=(-not -path "*/ai-gftd-project-cofog/*")
fi

stale_count=0
while IFS= read -r f; do
  remote=$(grep "remote =" "$f" 2>/dev/null | awk '{print $3}' | head -1)
  [ -z "$remote" ] && continue
  # Extract org/repo from URL like https://github.com/<org>/<repo>.git
  orgrepo=$(echo "$remote" | grep -oE 'github\.com[:/]([^/]+/[^/.]+)' | head -1 | sed 's|github.com[:/]||')
  [ -z "$orgrepo" ] && continue
  if ! gh repo view "$orgrepo" --json visibility >/dev/null 2>&1; then
    echo "STALE: $f → $orgrepo (404)"
    stale_count=$((stale_count + 1))
  fi
done < <(find . -name ".gitrepo" "${EXCLUDES[@]}" 2>/dev/null)

echo "stale subrepo upstream URLs: $stale_count"
if [ "$STRICT" -eq 1 ] && [ "$stale_count" -gt 0 ]; then
  exit 1
fi
exit 0
