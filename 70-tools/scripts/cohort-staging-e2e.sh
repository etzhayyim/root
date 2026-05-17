#!/usr/bin/env bash
# cohort-staging-e2e.sh — ADR-0026 Phase A→B→C end-to-end smoke test.
# Spec: 90-docs/260415-cohort-fission-staging-runbook.md
#
# Usage:
#   PDS_URL=https://atproto.etzhayyim.com ./cohort-staging-e2e.sh
#   (requires `gftd auth login` already done)
#
# Exits 0 on success, non-zero on any failure.

set -euo pipefail

PDS_URL="${PDS_URL:-https://atproto.etzhayyim.com}"
SEED_PCFL1="${SEED_PCFL1:-3-market-sell}"
SEED_ROLE="${SEED_ROLE:-salesRep}"
SEED_LOCALE="${SEED_LOCALE:-jp}"
EVIDENCE_COUNT="${EVIDENCE_COUNT:-50}"

log() { printf "\033[36m[cohort-e2e]\033[0m %s\n" "$*" >&2; }
fail() { printf "\033[31m[cohort-e2e FAIL]\033[0m %s\n" "$*" >&2; exit 1; }
ok() { printf "\033[32m[cohort-e2e OK]\033[0m %s\n" "$*" >&2; }

command -v gftd >/dev/null || fail "gftd CLI not on PATH"
command -v jq >/dev/null || fail "jq required"

# ── Step 0: baseline ──
log "Step 0: baseline dashboard"
gftd cohort dashboard --pds "$PDS_URL"

# ── Step 1: Phase A seed ──
log "Step 1: Phase A — seed cohort (pcfL1=$SEED_PCFL1, role=$SEED_ROLE, locale=$SEED_LOCALE)"
SEED_TOKEN=$(gftd agent-token --lxm ai.gftd.cohort.seed --ttl 600)
SEED_OUT=$(GFTD_TOKEN="$SEED_TOKEN" gftd cohort gen \
  --pcfL1 "$SEED_PCFL1" --role "$SEED_ROLE" --locale "$SEED_LOCALE" \
  --k 50 --json --pds "$PDS_URL")
COHORT_DID=$(echo "$SEED_OUT" | jq -r .did)
[ -z "$COHORT_DID" ] || [ "$COHORT_DID" = "null" ] && fail "seed returned no did: $SEED_OUT"
ok "seeded $COHORT_DID"

# ── Step 2: Phase B emit evidence ──
log "Step 2: Phase B — emit $((EVIDENCE_COUNT - 1)) ambient + 1 fission-ready evidence"
EMIT_TOKEN=$(gftd agent-token --lxm ai.gftd.cohort.emitEvidence --ttl 600)
for i in $(seq 1 $((EVIDENCE_COUNT - 1))); do
  GFTD_TOKEN="$EMIT_TOKEN" gftd cohort emit \
    --cohort "$COHORT_DID" \
    --signal-kind "behavior.observation" \
    --payload "obs-$i" \
    --posterior 0.4 --judge=false \
    --pds "$PDS_URL" >/dev/null
done
GFTD_TOKEN="$EMIT_TOKEN" gftd cohort emit \
  --cohort "$COHORT_DID" \
  --signal-kind "identity.confirm" \
  --payload "judge-confirmed" \
  --posterior 0.97 --judge=true \
  --pds "$PDS_URL" >/dev/null
ok "emitted $EVIDENCE_COUNT evidence rows"

# ── Step 2b: verify evidence MV ──
log "Step 2b: wait 5s for streaming MV, then verify fission-ready count"
sleep 5
EVIDENCE_OUT=$(GFTD_TOKEN="$EMIT_TOKEN" gftd cohort evidence \
  --cohort "$COHORT_DID" --min-posterior 0.95 --judge true --json --pds "$PDS_URL")
READY_COUNT=$(echo "$EVIDENCE_OUT" | jq '.evidence | length')
[ "$READY_COUNT" = "1" ] || fail "expected 1 fission-ready evidence, got $READY_COUNT"
ok "fission-ready count = 1"

# ── Step 3: Phase C fission ──
log "Step 3: Phase C — fire fission"
EVIDENCE_URI=$(echo "$EVIDENCE_OUT" | jq -r '.evidence[0].evidenceHash // ""')
[ -z "$EVIDENCE_URI" ] && fail "no evidence hash from listEvidence"
FISSION_TOKEN=$(gftd agent-token --lxm ai.gftd.cohort.fission --ttl 60)
FISSION_OUT=$(GFTD_TOKEN="$FISSION_TOKEN" gftd cohort fission \
  --cohort "$COHORT_DID" \
  --posterior 0.97 --judge=true \
  --evidence "at://placeholder/ai.gftd.cohort.evidence/$EVIDENCE_URI" \
  --json --pds "$PDS_URL")
INDIVIDUAL_DID=$(echo "$FISSION_OUT" | jq -r .individualDid)
[ -z "$INDIVIDUAL_DID" ] || [ "$INDIVIDUAL_DID" = "null" ] && fail "fission returned no individualDid"
ok "fissioned to $INDIVIDUAL_DID"

# ── Step 3b: verify lineage ──
log "Step 3b: verify lineage chain (2 hop expected)"
LINEAGE_OUT=$(GFTD_TOKEN="$FISSION_TOKEN" gftd cohort lineage \
  --did "$INDIVIDUAL_DID" --json --pds "$PDS_URL")
HOPS=$(echo "$LINEAGE_OUT" | jq 'length')
[ "$HOPS" = "2" ] || fail "expected 2-hop lineage, got $HOPS"
ok "lineage chain = 2 hop"

# ── Step 4: drift audit ──
log "Step 4: lineage drift audit"
LINEAGE_STATS=$(GFTD_TOKEN="$FISSION_TOKEN" gftd cohort lineage-stats \
  --pcfL1 "$SEED_PCFL1" --min-children 1 --json --pds "$PDS_URL")
CHILDREN=$(echo "$LINEAGE_STATS" | jq '.rows[0].directChildren // 0')
[ "$CHILDREN" -ge 1 ] || fail "expected direct_children >= 1, got $CHILDREN"
ok "mv_cohort_lineage_depth.direct_children = $CHILDREN"

# ── Summary ──
log "all 4 steps passed"
echo
echo "== E2E SUCCESS =="
echo "cohort:     $COHORT_DID"
echo "fissioned:  $INDIVIDUAL_DID"
echo
echo "Cleanup (staging only):"
echo "  psql \$STAGING_HYPERDRIVE_URL -c \"DELETE FROM vertex_cohort_actor WHERE cohort_did IN ('$COHORT_DID', '$INDIVIDUAL_DID');\""
