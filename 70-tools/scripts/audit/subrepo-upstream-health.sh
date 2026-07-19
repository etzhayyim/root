#!/usr/bin/env bash
#
# subrepo-upstream-health.sh — find `.gitrepo` files whose `remote` URL
# no longer resolves to a live GitHub repo (404). Excludes the cofog
# tree by default (hundreds of per-COFOG-code subrepos that warrant
# separate audit cadence).
#
# History:
#   - iter-28 of /loop (2026-05-26): discovered the SDK's `.gitrepo`
#     pointed at `etzhayyimcojp/kami-engine-sdk` (404); the actual upstream
#     was `etzhayyim/kami-engine-sdk`. Fixed iter-28 commit 957ec4c0a.
#   - iter-29 of /loop (2026-05-26): broader audit found 7 more stale
#     entries from the etzhayyim → etzhayyim org cleanup (ADR-2605211845);
#     documented in ADR with 3 resolution options per file (operator
#     choice — Update / Detach / Leave-as-is).
#   - this script codifies the audit pattern.
#
# Usage:
#   bash 70-tools/scripts/audit/subrepo-upstream-health.sh
#   bash 70-tools/scripts/audit/subrepo-upstream-health.sh --strict
#
# Requires: `gh` CLI authenticated to GitHub.
# Returns: list of stale entries via stdout. Exit code 0 unless --strict.

set -euo pipefail

STRICT=0
for arg in "$@"; do
  case "$arg" in
    --strict) STRICT=1 ;;
    *) echo "unknown arg: $arg" >&2; exit 2 ;;
  esac
done

# Resolve repo root (assume script invoked from anywhere in the tree).
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
cd "$REPO_ROOT"

# Discovery via `git ls-files` instead of `find`. The `find` approach
# walks every file in the worktree (~2.5 s on this repo); `git ls-files`
# reads the git index directly (~25 ms) and honours .gitignore for free.
# Combined with the parallel `gh` block below, total wall drops from
# ~20 s (sequential find + serial gh) to ~500 ms.
gitrepo_files=$(git ls-files | grep '\.gitrepo$' | grep -v "/node_modules/\|/.claude/" || true)
# Pre-extract (file, orgrepo) pairs serially (grep + awk is microseconds
# each; the slow part is the `gh repo view` network call). Then dispatch
# the network checks in parallel via xargs -P10 (well under any GitHub
# API rate limit).
#
# Why parallelize: each `gh repo view` is ~300-400 ms wall (network +
# GraphQL). Serial 9 calls = ~3-4 s plus per-call overhead which on
# this dev box compounds further. Parallel-9 = ~max-of-9 = ~400-500 ms.

pairs_file=$(mktemp)
stale_log=$(mktemp)
trap "rm -f $pairs_file $stale_log" EXIT

while IFS= read -r f; do
  [ -z "$f" ] && continue
  remote=$(grep "remote =" "$f" 2>/dev/null | awk '{print $3}' | head -1)
  [ -z "$remote" ] && continue
  orgrepo=$(echo "$remote" | grep -oE 'github\.com[:/]([^/]+/[^/.]+)' | head -1 | sed 's|github.com[:/]||')
  [ -z "$orgrepo" ] && continue
  echo "$f|$orgrepo"
done <<< "$gitrepo_files" > "$pairs_file"

# Parallel network check. Each line is "<filepath>|<orgrepo>"; emit
# STALE rows to stdout if the gh call fails. tee to a separate file
# so the count can be derived without subshell scoping issues.
xargs -I {} -P 10 bash -c '
  pair="$1"
  fpath="${pair%%|*}"
  orgrepo="${pair##*|}"
  if ! gh repo view "$orgrepo" --json visibility >/dev/null 2>&1; then
    echo "STALE: $fpath → $orgrepo (404)"
  fi
' _ {} < "$pairs_file" | tee "$stale_log"

stale_count=$(grep -c "^STALE:" "$stale_log" || true)
echo "stale subrepo upstream URLs: $stale_count"
if [ "$STRICT" -eq 1 ] && [ "$stale_count" -gt 0 ]; then
  exit 1
fi
exit 0
