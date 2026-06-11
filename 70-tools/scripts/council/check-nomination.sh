#!/usr/bin/env bash
# Council Seat 2-5 nomination structural-eligibility check.
#
# Reads the PR diff between $BASE..HEAD on COUNCIL.md + COUNCIL-BOOTSTRAP-RFP.md,
# extracts proposed nominee rows (lines starting with "+|" in markdown tables),
# and validates the structural fields: Seat number ∈ {2,3,4,5}, DID format,
# wallet format, name non-empty.
#
# Substantive checks (SBT held, Charter affirmation, Rider §2 compliance) are
# explicitly out of scope — those are Council human review.
#
# Exit codes:
#   0 — at least one structurally-valid nomination found, OR diff contains no
#       nomination row (the PR may touch council files for other reasons)
#   1 — at least one nomination row failed structural validation
#
# Usage (from repo root):
#   BASE="origin/main" ./70-tools/scripts/council/check-nomination.sh
#
# Active-inference cycle 05 (2026-05-22).

set -euo pipefail

BASE="${BASE:-origin/main}"
DIFF=$(git diff "$BASE...HEAD" -- COUNCIL.md COUNCIL-BOOTSTRAP-RFP.md 2>/dev/null || true)

if [[ -z "$DIFF" ]]; then
  echo "no council-file diff vs $BASE — nothing to check"
  exit 0
fi

# Extract added lines that look like markdown table rows:
#   +| 3 | someone | did:web:example.org | 0xabc...123 | candidate | n/a |
ADDED_ROWS=$(echo "$DIFF" | awk '/^\+\|/ && !/^\+\| *Seat/ && !/^\+\|---/ { print substr($0, 2) }' || true)

if [[ -z "$ADDED_ROWS" ]]; then
  echo "no added table rows in COUNCIL files — PR may touch prose only; skipping"
  exit 0
fi

echo "Found $(echo "$ADDED_ROWS" | wc -l | tr -d ' ') added table row(s):"
echo

EXIT=0
ROW_NUM=0
while IFS= read -r row; do
  ROW_NUM=$((ROW_NUM + 1))
  echo "--- Row $ROW_NUM ---"
  echo "  raw: $row"

  # Tokenize: split on |, trim whitespace, drop leading/trailing empties.
  IFS='|' read -r -a CELLS <<<"$row"
  TRIMMED=()
  for c in "${CELLS[@]}"; do
    t=$(echo "$c" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
    [[ -n "$t" ]] && TRIMMED+=("$t")
  done

  if [[ ${#TRIMMED[@]} -lt 4 ]]; then
    echo "  ✘ row has fewer than 4 non-empty cells — not a valid roster row"
    EXIT=1
    continue
  fi

  SEAT="${TRIMMED[0]}"
  NAME="${TRIMMED[1]}"
  DID="${TRIMMED[2]}"
  WALLET="${TRIMMED[3]}"

  # Seat: extract digit
  SEAT_DIGIT=$(echo "$SEAT" | grep -oE '[0-9]+' | head -n1 || echo "")
  if [[ -z "$SEAT_DIGIT" ]] || (( SEAT_DIGIT < 2 || SEAT_DIGIT > 5 )); then
    echo "  ✘ seat number '$SEAT' not in {2,3,4,5} (Seat 1 founder is confirmed; cannot be re-nominated)"
    EXIT=1
  else
    echo "  ✓ seat: $SEAT_DIGIT"
  fi

  # Name
  if [[ -z "$NAME" || "$NAME" == "TBD" ]]; then
    echo "  ✘ name is empty or TBD"
    EXIT=1
  else
    echo "  ✓ name: $NAME"
  fi

  # DID format
  if [[ "$DID" =~ ^did:(web|plc|key): ]]; then
    echo "  ✓ DID format: $DID"
  elif [[ "$DID" == "TBD" || "$DID" == "n/a" ]]; then
    echo "  ✘ DID is TBD/n/a — Council members MUST operate a religious DID per RFP §3"
    EXIT=1
  else
    echo "  ✘ DID format '$DID' — required: did:web:* / did:plc:* / did:key:*"
    EXIT=1
  fi

  # Wallet format (0x + 40 hex), TBD permitted during bootstrap window
  if [[ "$WALLET" =~ ^0x[0-9a-fA-F]{40}$ ]]; then
    echo "  ✓ smart wallet: $WALLET"
  elif [[ "$WALLET" == "TBD" ]]; then
    echo "  ~ smart wallet: TBD (acceptable during 30-day RFP window; must resolve before confirmation)"
  else
    echo "  ✘ smart wallet '$WALLET' — required: 0x + 40 hex, or 'TBD' during bootstrap"
    EXIT=1
  fi

  echo
done <<<"$ADDED_ROWS"

if (( EXIT == 0 )); then
  echo "Structural check: PASS ($ROW_NUM nomination row(s))."
  echo
  echo "Reminder: substantive eligibility (Adherent SBT / Charter affirmation /"
  echo "Rider §2 clearance) is Council human review per COUNCIL-BOOTSTRAP-RFP.md."
else
  echo "Structural check: FAIL — fix the rows above and re-push."
fi

exit $EXIT
