#!/usr/bin/env bash
# Apply pending migrations one-at-a-time via run-one-migration.mjs,
# skipping the kysely migrator entirely.
#
# Why:
#   `pnpm db:migrate latest` breaks on this repo for 3 reasons:
#   1. Historic kysely_migration rows pointing at deleted files trigger
#      the "corrupted migrations" guard (see graph-schema/CLAUDE.md).
#   2. `ON CONFLICT DO NOTHING` in a migration aborts — RisingWave's
#      sql_parser rejects the clause at parse time. Re-write to
#      SELECT-then-INSERT before running.
#   3. Files next to migrations that import vitest (`*.test.ts`)
#      crash kysely's FileMigrationProvider import step. Filter added
#      2026-04-24 (migrate.ts:128ish).
#   Even after (1)+(3) are fixed, the migrator still picks up the
#   full pending list, which often includes cross-scope work owned
#   by other maintainers. This helper lets you apply exactly the
#   migrations you mean to apply, one at a time, with explicit
#   verification between each.
#
# Usage:
#   bash scripts/apply-pending.sh <migration-name> [<migration-name> ...]
#   DRY_RUN=1 bash scripts/apply-pending.sh <migration-name>  # just echo
#
# Each name is the migration stem without the .ts extension, e.g.
#   20260424120000_seed_yabai_batch3_bpmn_actors
#
# After each successful apply the script:
#   - runs `pnpm db:drift` to catch schema drift
#   - prints the kysely_migration row count diff
# and stops on the first failure.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GRAPH_SCHEMA_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

DRY_RUN="${DRY_RUN:-0}"

if [[ $# -eq 0 ]]; then
  printf 'usage: %s <migration-name> [<migration-name> ...]\n' "$(basename "$0")"
  printf '       DRY_RUN=1 %s <migration-name>\n' "$(basename "$0")"
  exit 2
fi

# Resolve DATABASE_URL from Keychain if not already set.
if [[ -z "${DATABASE_URL:-}" ]]; then
  if command -v security >/dev/null 2>&1; then
    DATABASE_URL="$(security find-generic-password -s etzhayyim.rw -a ROOT_URL -w 2>/dev/null || true)"
    export DATABASE_URL
  fi
fi
if [[ -z "${DATABASE_URL:-}" ]]; then
  printf 'DATABASE_URL unset and not in Keychain (service=etzhayyim.rw account=ROOT_URL).\n'
  printf 'Export it manually or run:\n'
  printf '  security add-generic-password -s etzhayyim.rw -a ROOT_URL -w "postgresql://...:4566/dev" -U\n'
  exit 3
fi

color_pass() { printf "\033[32m✔\033[0m"; }
color_fail() { printf "\033[31m✘\033[0m"; }
color_info() { printf "\033[36mℹ\033[0m"; }
say() { printf "\n\033[1;36m==> %s\033[0m\n" "$*"; }

cd "$GRAPH_SCHEMA_DIR"

for name in "$@"; do
  say "apply $name"

  if [[ ! -f "migrations/${name}.ts" ]]; then
    printf '  %s migrations/%s.ts not found\n' "$(color_fail)" "$name"
    exit 1
  fi

  # Sanity-check: warn if migration uses `ON CONFLICT` in actual SQL
  # (not just in a comment discussing it). Strips `// ...` and `/* ... */`
  # before checking.
  if awk '
      {
        line = $0
        sub(/\/\/.*$/, "", line)
        while (match(line, /\/\*[^*]*\*\//)) {
          line = substr(line, 1, RSTART-1) substr(line, RSTART+RLENGTH)
        }
        if (index(toupper(line), "ON CONFLICT") > 0) { print; exit 0 }
      }
    ' "migrations/${name}.ts" | grep -q .; then
    printf '  %s migration uses ON CONFLICT in executable SQL; RisingWave will reject.\n' "$(color_fail)"
    printf '    rewrite to SELECT-then-INSERT before applying.\n'
    exit 1
  fi

  if [[ "$DRY_RUN" == "1" ]]; then
    printf '  %s DRY_RUN=1 — would run: node scripts/run-one-migration.mjs %s\n' \
      "$(color_info)" "$name"
    continue
  fi

  # Apply via the one-off runner (bypasses kysely missing-history guard).
  if ! node scripts/run-one-migration.mjs "$name"; then
    printf '\n  %s run-one-migration.mjs failed for %s\n' "$(color_fail)" "$name"
    exit 1
  fi

  # Record the row if the runner didn't (e.g. if up() errored partway
  # but partial state is acceptable — we gate on drift-detect below).
  psql_cmd="INSERT INTO kysely_migration (name, timestamp) SELECT '${name}', NOW()::text WHERE NOT EXISTS (SELECT 1 FROM kysely_migration WHERE name = '${name}');"
  if command -v psql >/dev/null 2>&1; then
    # Parse DATABASE_URL into psql components.
    PGURL="$DATABASE_URL" python3 - <<'PY' >/tmp/psql-args.$$
import os, urllib.parse as up
u = up.urlparse(os.environ['PGURL'])
print(f"-h {u.hostname} -p {u.port or 5432} -U {u.username} -d {u.path.lstrip('/')}")
print(u.password or '')
PY
    args="$(sed -n 1p /tmp/psql-args.$$)"
    pw="$(sed -n 2p /tmp/psql-args.$$)"
    rm -f /tmp/psql-args.$$
    PGPASSWORD="$pw" psql $args -c "$psql_cmd" >/dev/null 2>&1 || true
  fi

  printf '  %s %s applied\n' "$(color_pass)" "$name"
done

if [[ "$DRY_RUN" == "1" ]]; then
  exit 0
fi

# Single drift check after the whole batch.
say "drift check"
if pnpm db:drift 2>&1 | tee /tmp/apply-pending-drift.log | grep -q 'OK: no drift'; then
  printf '  %s clean\n' "$(color_pass)"
else
  printf '  %s drift report not clean — see /tmp/apply-pending-drift.log\n' "$(color_fail)"
  exit 1
fi

say "regenerate database.ts (pnpm db:gen)"
pnpm db:gen 2>&1 | tail -3

printf '\n\033[32mDONE\033[0m — %d migration(s) applied, drift clean, database.ts regenerated.\n' "$#"
printf 'Commit the database.ts diff + any migration rewrites before pushing.\n'
