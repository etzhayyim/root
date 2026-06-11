#!/usr/bin/env bash
# γ2 legacy-trust daily observation probe — appended to by the LaunchAgent
# `com.etzhayyim.legacy-trust-tally.plist`. Mirrors the Claude session cron
# c79292b9 logic but runs on the OS cron so it survives across sessions
# and isn't capped at 7 days.
#
# Runbook: 90-docs/260424-legacy-trust-headers-cutover-runbook.md §2
# Gate: 0 `[trust][legacy] hit` events per 24h for 14 consecutive days.

set -euo pipefail

REPO_ROOT="${REPO_ROOT:-/Users/junkawasaki/github/etzhayyim-root}"
TALLY_LOG="${REPO_ROOT}/90-docs/260424-legacy-trust-tally.log"
WORKER_NAME="${WORKER_NAME:-etzhayyim-appview}"
SAMPLE_SECS="${SAMPLE_SECS:-60}"

# Seed the log with a header the first time we write.
if [[ ! -f "$TALLY_LOG" ]]; then
  printf '# ADR-2604241038 Phase γ2 legacy-trust observation tally — one row per daily sample.\n' > "$TALLY_LOG"
  printf '# runbook: 90-docs/260424-legacy-trust-headers-cutover-runbook.md\n' >> "$TALLY_LOG"
  printf '# pass: 0 hits per 24h for 14 consecutive days → safe to flip LEGACY_TRUST_HEADERS=off\n\n' >> "$TALLY_LOG"
fi

timestamp="$(date '+%Y-%m-%d %H:%M')"

# Path to wrangler — most setups have it under pnpm's global dir or in
# the worker's node_modules. Fall back to PATH.
WRANGLER="${WRANGLER_BIN:-}"
if [[ -z "$WRANGLER" ]]; then
  if command -v wrangler >/dev/null 2>&1; then
    WRANGLER="$(command -v wrangler)"
  elif [[ -x "${REPO_ROOT}/50-infra/cloudflare/workers/appview/node_modules/.bin/wrangler" ]]; then
    WRANGLER="${REPO_ROOT}/50-infra/cloudflare/workers/appview/node_modules/.bin/wrangler"
  else
    printf '%s  ERROR=wrangler_not_found  window=%ss\n' "$timestamp" "$SAMPLE_SECS" >> "$TALLY_LOG"
    exit 0
  fi
fi

cd "${REPO_ROOT}/50-infra/cloudflare/workers/appview"

# Stream wrangler tail for SAMPLE_SECS then kill + parse.
tmp="$(mktemp)"
trap 'rm -f "$tmp"' EXIT

"$WRANGLER" tail --format=json "$WORKER_NAME" 2>/dev/null > "$tmp" &
tail_pid=$!
sleep "$SAMPLE_SECS"
kill "$tail_pid" 2>/dev/null || true
wait "$tail_pid" 2>/dev/null || true

matched_true="$(jq -r '
  (.logs // []) as $logs
  | ($logs[]?.message? // [])
  | if type == "array" then .[] else . end
  | strings
  | select(test("\\[trust\\]\\[legacy\\] hit .* matched=true"))
' "$tmp" 2>/dev/null | wc -l | tr -d ' ')"

matched_false="$(jq -r '
  (.logs // []) as $logs
  | ($logs[]?.message? // [])
  | if type == "array" then .[] else . end
  | strings
  | select(test("\\[trust\\]\\[legacy\\] hit .* matched=false"))
' "$tmp" 2>/dev/null | wc -l | tr -d ' ')"

printf '%s  matched_true=%s  matched_false=%s  window=%ss\n' \
  "$timestamp" "$matched_true" "$matched_false" "$SAMPLE_SECS" >> "$TALLY_LOG"
