#!/usr/bin/env bash
# ADR 2605081200 — pre-cluster-apply preflight for bpmn-engine-host.
# Runs read-only checks. No kubectl apply, no DDL, no docker push.
# Exit non-zero on any RED finding so the operator can stop.
#
# Usage (from repo root):
#     bash 50-infra/k8s/bpmn-engine-host/preflight.sh
set -u
RED=0
ok()   { printf '\033[32m[ OK ]\033[0m %s\n' "$1"; }
warn() { printf '\033[33m[WARN]\033[0m %s\n' "$1"; }
bad()  { printf '\033[31m[FAIL]\033[0m %s\n' "$1"; RED=1; }

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$REPO_ROOT"

echo "── Pre-flight: bpmn-engine-host (ADR 2605081200) ──"
echo "Repo root: $REPO_ROOT"
echo

# 1. Required CLI tools
for cmd in kubectl psql docker python3 security pnpm; do
  if command -v "$cmd" >/dev/null 2>&1; then
    ok "$cmd available"
  else
    case "$cmd" in
      docker) warn "$cmd missing (only needed for image build)" ;;
      psql)   warn "$cmd missing (only for DDL verification)" ;;
      *)      bad "$cmd missing (required)" ;;
    esac
  fi
done
echo

# 2. Files exist
must_exist=(
  "30-graph/graph-schema/sql_migrations/20260509110000_vertex_spiff_runtime.up.sql"
  "30-graph/graph-schema/sql_migrations/20260509110000_vertex_spiff_runtime.down.sql"
  "30-graph/graph-schema/alembic/current_versions/r_20260509110000_vertex_spiff_runtime.py"
  "50-infra/k8s/bpmn-engine-host/engine.py"
  "50-infra/k8s/bpmn-engine-host/main.py"
  "50-infra/k8s/bpmn-engine-host/Dockerfile"
  "50-infra/k8s/bpmn-engine-host/deployment.yaml"
  "50-infra/k8s/bpmn-engine-host/requirements.txt"
  "50-infra/k8s/bpmn-engine-host/tests/smoke.py"
  "50-infra/k8s/open-lei-mcp/spiff_worker.py"
  "50-infra/k8s/open-lei-mcp/deployment-spiff-worker.yaml"
  "20-actors/magatama/py/src/pymagatama/spiff_worker/client.py"
  "20-actors/magatama/py/src/pymagatama/spiff_worker/types.py"
)
for f in "${must_exist[@]}"; do
  if [[ -f "$f" ]]; then ok "file: $f"; else bad "missing: $f"; fi
done
echo

# 3. Migration chain head — new revision must point to a known parent
HEAD_FILE="30-graph/graph-schema/alembic/current_versions/r_20260509110000_vertex_spiff_runtime.py"
PARENT="$(grep -m1 '^down_revision' "$HEAD_FILE" 2>/dev/null | sed 's/.*= *"\(.*\)".*/\1/')"
if [[ -n "$PARENT" ]]; then
  if [[ -f "30-graph/graph-schema/alembic/current_versions/${PARENT}.py" ]]; then
    ok "migration parent exists: ${PARENT}"
  else
    bad "migration parent NOT found: ${PARENT} (broken chain)"
  fi
else
  bad "could not parse down_revision from $HEAD_FILE"
fi
echo

# 4. Schema collision: ensure NEW SQL only creates vertex_spiff_*
NEW_SQL="30-graph/graph-schema/sql_migrations/20260509110000_vertex_spiff_runtime.up.sql"
if grep -qE "CREATE TABLE.*vertex_bpmn_(instance|job|timer|history)\b" "$NEW_SQL"; then
  bad "$NEW_SQL still creates vertex_bpmn_* runtime tables (Zeebe collision)"
else
  ok "no vertex_bpmn_* runtime CREATE TABLE in new migration"
fi
if grep -qE "CREATE TABLE.*vertex_spiff_(instance|job|timer|history)" "$NEW_SQL" && \
   grep -q "CREATE MATERIALIZED VIEW.*mv_spiff_ready_jobs" "$NEW_SQL"; then
  ok "new migration creates expected vertex_spiff_* + mv_spiff_ready_jobs"
else
  bad "new migration missing one of vertex_spiff_{instance,job,timer,history} or mv_spiff_ready_jobs"
fi
echo

# 5. Spec layer dependency present (required by engine ProcessRegistry._load)
if grep -rq "CREATE TABLE.*vertex_bpmn_process_def" \
     30-graph/graph-schema/migrations/ 30-graph/graph-schema/sql_migrations/ 2>/dev/null; then
  ok "vertex_bpmn_process_def schema present (engine spec source)"
else
  bad "vertex_bpmn_process_def schema NOT found — engine cannot load BPMN XML"
fi
echo

# 6. Python syntax (no deps required for py_compile)
if python3 -m py_compile \
    50-infra/k8s/bpmn-engine-host/engine.py \
    50-infra/k8s/bpmn-engine-host/main.py \
    50-infra/k8s/bpmn-engine-host/tests/smoke.py \
    50-infra/k8s/open-lei-mcp/spiff_worker.py \
    20-actors/magatama/py/src/pymagatama/spiff_worker/client.py \
    20-actors/magatama/py/src/pymagatama/spiff_worker/types.py \
    20-actors/magatama/py/src/pymagatama/spiff_worker/__init__.py \
    20-actors/magatama/py/src/pymagatama/spiff_worker/decorator.py 2>/dev/null; then
  ok "Python syntax: all engine/worker/shim files compile"
else
  bad "Python syntax error in one of the engine/worker files"
fi
echo

# 7. RW_DSN reachable (operator should have it in keychain)
if security find-generic-password -s "etzhayyim.risingwave" -a "RW_DSN" -w >/dev/null 2>&1; then
  ok "RW_DSN found in macOS Keychain (etzhayyim.risingwave / RW_DSN)"
else
  warn "RW_DSN NOT in macOS Keychain — Step 3 secret provisioning will need a manual value"
fi
echo

# 8. mitama-udf namespace + open-lei namespace exist
if kubectl get ns mitama-udf >/dev/null 2>&1; then
  ok "namespace mitama-udf exists"
else
  warn "namespace mitama-udf missing — apply will create"
fi
if kubectl get ns open-lei >/dev/null 2>&1; then
  ok "namespace open-lei exists"
else
  warn "namespace open-lei missing — apply will create"
fi
echo

# 9. Existing Zeebe broker presence (informational; not a blocker)
if kubectl -n mitama-udf get deploy zeebe-gateway >/dev/null 2>&1; then
  warn "Zeebe broker still deployed — coexists during transition (Phase 2 retires)"
else
  ok "no Zeebe broker deploy in mitama-udf"
fi
echo

# 10. seed BPMN (lawfirm_intake_funnel) needed for smoke
if grep -rq "lawfirm_intake_funnel" 30-graph/graph-schema/migrations/ 2>/dev/null; then
  ok "seed reference for lawfirm_intake_funnel present in migrations"
else
  warn "no migration seeds lawfirm_intake_funnel — smoke will fail unless RW already has the row"
fi
echo

# Summary
echo "─────────────────────────────────────────"
if [[ $RED -eq 0 ]]; then
  echo "$(printf '\033[32m')PRE-FLIGHT: PASS$(printf '\033[0m') — proceed with RUNBOOK.md Step 1"
  exit 0
else
  echo "$(printf '\033[31m')PRE-FLIGHT: FAIL$(printf '\033[0m') — fix [FAIL] items before applying"
  exit 1
fi
