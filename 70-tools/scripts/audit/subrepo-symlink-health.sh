#!/usr/bin/env bash
#
# subrepo-symlink-health.sh — find symlinks INSIDE git-subrepo trees
# whose targets escape the subrepo boundary (`../../...`) and therefore
# dangle when the subrepo is checked out standalone or extracted as
# an npm tarball.
#
# Typical pattern (and the one this script was written for): a
# religious-corp NOTICE/CHARTER-RIDER pair is propagated into the
# monorepo via symlinks pointing at the monorepo root's canonical
# `/CHARTER-RIDER.md` (see `70-tools/charter-rider-applicator/`). That
# works inside the monorepo — the symlink stays within the same
# repository — but when a subrepo is cloned standalone or `npm publish`
# extracts the tarball, the symlink's target is N parent-directories
# away in a tree that doesn't exist.
#
# History:
#   - iter-24 of /loop (2026-05-26): SDK's CHARTER-RIDER.md was a
#     dangling symlink (-> ../../../CHARTER-RIDER.md). Fixed by
#     replacing with a real-file mirror (commit bdecb113e).
#   - iter-25 of /loop (2026-05-26): even after iter-24's fix, the
#     real-file CHARTER-RIDER.md wasn't in the npm tarball because
#     `files: ["dist"]` excluded it; fixed in iter-25 commit ea87f5eaf.
#   - iter-31 of /loop (2026-05-26): broader audit found 18 same-
#     pattern symlinks in 40-engine/kotoba/ subrepo (1 root + 17
#     per-crate); documented in ADR-2605262130 with the iter-24 fix
#     pattern as precedent + this script codifies the audit.
#
# Usage:
#   bash 70-tools/scripts/audit/subrepo-symlink-health.sh
#   bash 70-tools/scripts/audit/subrepo-symlink-health.sh --strict
#
# Output: each escape-symlink as `<subrepo>: <symlink> -> <target>`,
# followed by a count.
#
# Exit code 0 unless --strict.

set -euo pipefail

STRICT=0
for arg in "$@"; do
  case "$arg" in
    --strict) STRICT=1 ;;
    *) echo "unknown arg: $arg" >&2; exit 2 ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
cd "$REPO_ROOT"

# Find all subrepo roots (dirs with `.gitrepo`).
SUBREPOS=$(find . -name ".gitrepo" -not -path "*/node_modules/*" -not -path "*/.claude/*" 2>/dev/null | sed 's|/.gitrepo$||')

escape_count=0
for subrepo in $SUBREPOS; do
  # All symlinks within this subrepo
  while IFS= read -r symlink; do
    target=$(readlink "$symlink" 2>/dev/null || true)
    [ -z "$target" ] && continue
    # If the target is an absolute path, it's outside the subrepo by definition.
    # If it's a relative path starting with `../`, count how many `../`s and
    # compare to the symlink's depth within the subrepo. If `../` count >= depth,
    # the target escapes the subrepo.
    if [[ "$target" == /* ]]; then
      echo "ABSOLUTE: $subrepo: $symlink -> $target"
      escape_count=$((escape_count + 1))
      continue
    fi
    # Count consecutive leading "../" segments
    dotdots=$(echo "$target" | grep -oE '^(\.\./)+' | grep -oE '\.\./' | wc -l | tr -d ' ')
    # Symlink's depth within the subrepo (number of segments after subrepo root)
    relative=${symlink#"$subrepo/"}
    depth=$(echo "$relative" | tr -cd '/' | wc -c | tr -d ' ')
    # If dotdots > depth, the target escapes the subrepo
    if [ "$dotdots" -gt "$depth" ]; then
      echo "ESCAPE: $subrepo: $symlink -> $target  (target leaves subrepo)"
      escape_count=$((escape_count + 1))
    fi
  done < <(find "$subrepo" -type l -not -path "*/node_modules/*" -not -path "*/.git/*" 2>/dev/null)
done

echo "escape-symlinks in subrepos: $escape_count"
if [ "$STRICT" -eq 1 ] && [ "$escape_count" -gt 0 ]; then
  exit 1
fi
exit 0
