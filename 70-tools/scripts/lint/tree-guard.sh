#!/bin/sh
# tree-guard — local pre-push structural guards (lefthook pre-push).
#
# Post-#1680 incident (a "one-line kotoba pin bump" whose branch tree
# contained only 40-engine; merging it deleted 77,504 files from main —
# every CI workflow stayed green because all are path-triggered) + the
# 2026-06-12 merge-history audit (orphan kotoba pins 98f9d2b3fd /
# 46e0bdaa6a permanently broke `git submodule update` at those main
# states; #1403 regressed the pin and un-pinned d7941966's work).
#
# Runs BEFORE push, on every push (operator direction 2026-06-12:
# local pre-push, not a GitHub Action; the server-side gate is the
# required-review ruleset on main).
#
#   1. sentinel files   — load-bearing files/dirs must exist in the
#                         HEAD tree being pushed (#1680 class).
#   2. submodule pins   — engine-submodule gitlinks must point to
#                         commits that EXIST on their upstream remote,
#                         and a pin change vs origin/main must be
#                         fast-forward (descendant of the base pin).
#                         Network checks fire ONLY when a pin changed;
#                         offline → warn and pass (cannot distinguish
#                         orphan from no-network without the remote).
#   3. mass-deletion    — >3000 files deleted vs origin/main blocks
#                         unless the HEAD commit message contains
#                         [mass-delete-ok] or TREE_GUARD_MASS_DELETE_OK=1.
#
# Exit 1 on any violation. Bypassing with `git push --no-verify` is
# visible in history (the violation lands in the PR diff for review).

set -u

fail=0
note() { printf '  tree-guard: %s\n' "$1"; }
err()  { printf '\xe2\x9c\x98 tree-guard: %s\n' "$1"; fail=1; }

# ── 1. sentinel files ────────────────────────────────────────────────
for f in deps.edn CLAUDE.md CHARTER-RIDER.md LICENSE LANDS.md MEMBERS.md \
         90-docs/adr/README.edn 90-docs/_registry/docs.json .gitmodules \
         00-contracts 50-infra 70-tools 90-docs; do
  if ! git cat-file -e "HEAD:$f" 2>/dev/null; then
    err "sentinel missing from HEAD tree: $f"
  fi
done
if [ "$fail" != 0 ]; then
  err "the tree being pushed is missing load-bearing files — this is the #1680 tree-wipe signature. Refusing to push."
  exit 1
fi

# ── base ref for diff-based checks (skip gracefully if absent) ───────
BASE=""
if git rev-parse --verify -q origin/main >/dev/null 2>&1; then
  BASE=$(git merge-base origin/main HEAD 2>/dev/null || true)
fi

# ── 2. submodule pins ────────────────────────────────────────────────
for path in 40-engine/kotoba 40-engine/kami-engine; do
  url=$(git config -f .gitmodules "submodule.$path.url" 2>/dev/null || true)
  [ -n "$url" ] || continue
  pin=$(git ls-tree HEAD "$path" 2>/dev/null | awk '$2=="commit"{print $3}')
  if [ -z "$pin" ]; then
    err "$path has no gitlink in HEAD"
    continue
  fi
  base_pin=""
  [ -n "$BASE" ] && base_pin=$(git ls-tree "$BASE" "$path" 2>/dev/null | awk '$2=="commit"{print $3}')
  # Only hit the network when this push actually moves the pin.
  [ "$pin" = "$base_pin" ] && continue

  # Connectivity probe — offline must not block an unrelated push.
  if ! git ls-remote -q "$url" HEAD >/dev/null 2>&1; then
    note "WARN: cannot reach $url — pin checks for $path skipped (offline?)"
    continue
  fi
  tmp=$(mktemp -d)
  git init -q "$tmp"
  # GitHub serves any reachable SHA (allowAnySHA1InWant): a failed fetch
  # of the exact pin means the commit does NOT exist on the remote.
  if ! git -C "$tmp" fetch -q "$url" "$pin" 2>/dev/null; then
    err "$path pin $pin does not exist on $url — an orphan gitlink permanently breaks 'git submodule update' (the 98f9d2b3fd / 46e0bdaa6a failure mode). Push the submodule commit upstream first."
    rm -rf "$tmp"
    continue
  fi
  if [ -n "$base_pin" ]; then
    if ! git -C "$tmp" fetch -q "$url" "$base_pin" 2>/dev/null; then
      note "WARN: $path base pin $base_pin absent from $url (pre-existing orphan) — ancestry check skipped"
    elif git -C "$tmp" merge-base --is-ancestor "$base_pin" "$pin" 2>/dev/null; then
      note "$path pin moves forward: $base_pin -> $pin"
    else
      err "$path pin $pin does NOT descend from origin/main's pin $base_pin — pin regression / parallel-history swap (the #1403 failure mode). Rebase the submodule bump onto current upstream history."
    fi
  fi
  rm -rf "$tmp"
done

# ── 3. mass-deletion ─────────────────────────────────────────────────
if [ -n "$BASE" ]; then
  deleted=$(git diff --name-only --diff-filter=D "$BASE" HEAD 2>/dev/null | wc -l | tr -d ' ')
  if [ "${deleted:-0}" -gt 3000 ]; then
    if [ "${TREE_GUARD_MASS_DELETE_OK:-}" = "1" ] || git log -1 --format=%B HEAD | grep -q '\[mass-delete-ok\]'; then
      note "WARN: $deleted files deleted — explicitly opted in (mass-delete-ok)"
    else
      err "this push deletes $deleted files vs origin/main (>3000). Deliberate migration? Add [mass-delete-ok] to the HEAD commit message or set TREE_GUARD_MASS_DELETE_OK=1. Otherwise the branch tree is missing content it never meant to delete (the #1680 failure mode)."
    fi
  fi
fi

if [ "$fail" = 0 ]; then
  note "ok (sentinels + submodule pins + mass-deletion)"
fi
exit "$fail"
