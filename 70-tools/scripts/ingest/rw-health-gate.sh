#!/usr/bin/env bash
# rw-health-gate.sh — RisingWave 3-point health probe for bulk ingest actors
#
# SSoT: deps.toml [[conventions]] rw-health-gate-before-ingest
# Incident that motivated this: 50-infra/vultr/risingwave/deps.toml
#                               [risingwave_vultr.incident_2026_04_25]
#
# Exit codes:
#   0  healthy             — safe for the requested purpose
#   0  degraded-write      — ingest may continue with lower dml_rate_limit
#   1  degraded            — hard stop; stage/pre-fetch only
#   2  probe-failed        — could not determine state (kubectl/psql missing)
#
# Usage in an ingest script:
#   if ! 70-tools/scripts/ingest/rw-health-gate.sh; then
#     echo "RW degraded — staging SPARQL result to disk and exiting"
#     curl ... > /tmp/staging/${RUN_ID}.jsonl
#     exit 0
#   fi
#
# Usage in BPMN `rw.health.probe` primitive (Python LangServer worker):
#   result = subprocess.run(["rw-health-gate.sh"], capture_output=True)
#   if result.returncode != 0:
#     return {"healthy": False, "reason": result.stdout.decode().strip()}
#
# Environment variables (all optional, shown with defaults):
#   RW_DSN                  REDACTED_USE_DATABASE_URL_ENV
#   RW_NAMESPACE            risingwave
#   COMPUTE_SELECTOR        risingwave.risingwavelabs.com/component=compute
#   META_SELECTOR           risingwave.risingwavelabs.com/component=meta
#   MIN_COMPUTE_READY       1      (2026-04-30 license-safe recovery floor)
#   MIN_COMPUTE_AGE_SEC     0      (pod-age gate disabled; rely on recovery/log gates)
#   RW_GATE_PURPOSE          ingest (ingest | ddl | scaling)
#   RW_COLD_START_POLICY     degraded-write (degraded-write | block)
#   SELECT1_TIMEOUT_SEC     5
#   SLOWDOWN_WINDOW_SEC     60
#   SLOWDOWN_MAX            10     (events in window; above = degraded)
#   VERBOSE                 0 / 1

set -u

RW_DSN="${RW_DSN:-REDACTED_USE_DATABASE_URL_ENV"
RW_NAMESPACE="${RW_NAMESPACE:-risingwave}"
COMPUTE_SELECTOR="${COMPUTE_SELECTOR:-risingwave.risingwavelabs.com/component=compute}"
META_SELECTOR="${META_SELECTOR:-risingwave.risingwavelabs.com/component=meta}"
MIN_COMPUTE_READY="${MIN_COMPUTE_READY:-1}"
# Pod-age gating is disabled by default. The live recovery gate now relies on
# rw_recovery_info plus recent object-store/recovery logs; set this env var
# explicitly for a temporary warmup floor during an incident.
MIN_COMPUTE_AGE_SEC="${MIN_COMPUTE_AGE_SEC:-0}"
RW_GATE_PURPOSE="${RW_GATE_PURPOSE:-ingest}"
RW_COLD_START_POLICY="${RW_COLD_START_POLICY:-degraded-write}"
SELECT1_TIMEOUT_SEC="${SELECT1_TIMEOUT_SEC:-5}"
SLOWDOWN_WINDOW_SEC="${SLOWDOWN_WINDOW_SEC:-60}"
SLOWDOWN_MAX="${SLOWDOWN_MAX:-10}"
VERBOSE="${VERBOSE:-0}"

log() { [ "$VERBOSE" = 1 ] && echo "[rw-health-gate] $*" >&2; }

command -v psql    >/dev/null 2>&1 || { echo "psql missing"    >&2; exit 2; }
command -v kubectl >/dev/null 2>&1 || { echo "kubectl missing" >&2; exit 2; }

psql_with_timeout() {
  sql="$1"
  tmp_out="$(mktemp)"
  psql "$RW_DSN" -tAc "$sql" >"$tmp_out" 2>&1 &
  psql_pid=$!
  elapsed=0
  while kill -0 "$psql_pid" >/dev/null 2>&1; do
    if [ "$elapsed" -ge "$SELECT1_TIMEOUT_SEC" ]; then
      kill "$psql_pid" >/dev/null 2>&1 || true
      wait "$psql_pid" >/dev/null 2>&1 || true
      cat "$tmp_out"
      rm -f "$tmp_out"
      return 124
    fi
    sleep 1
    elapsed=$((elapsed + 1))
  done
  wait "$psql_pid"
  status=$?
  cat "$tmp_out"
  rm -f "$tmp_out"
  return "$status"
}

# ── Probe 1 ── meta-plane + recovery catalog with timeout ────────────────
log "probe 1/5: SELECT 1 with ${SELECT1_TIMEOUT_SEC}s timeout"
t0=$(date +%s)
out=$(psql_with_timeout "SELECT 1;")
select_status=$?
t_select=$(( $(date +%s) - t0 ))
if [ "$select_status" -ne 0 ] || [ "$out" != "1" ]; then
  echo "degraded: meta-plane probe failed (status=${select_status} duration=${t_select}s output=${out})"
  exit 1
fi
log "  ok (${t_select}s)"

log "probe 2/5: rw_recovery_info all RUNNING and not global recovering"
recovery_bad=$(psql_with_timeout "SELECT count(*) FROM rw_recovery_info WHERE recovery_state <> 'RUNNING' OR in_global_recovering;")
recovery_status=$?
if [ "$recovery_status" -ne 0 ]; then
  echo "degraded: recovery catalog probe failed (status=${recovery_status} output=${recovery_bad})"
  exit 1
fi
recovery_bad=$(echo "$recovery_bad" | tr -d '[:space:]')
if [ "${recovery_bad:-1}" != "0" ]; then
  echo "degraded: rw_recovery_info has ${recovery_bad} non-running/recovering database(s)"
  exit 1
fi
log "  ok"

# ── Probe 2b ── DDL/barrier queue must be empty before more DDL/scaling ───
if [ "$RW_GATE_PURPOSE" = "ddl" ] || [ "$RW_GATE_PURPOSE" = "scaling" ]; then
  log "probe 2b/5: SHOW JOBS has no pending foreground DDL"
  jobs_out=$(psql_with_timeout "SHOW JOBS;")
  jobs_status=$?
  if [ "$jobs_status" -ne 0 ]; then
    echo "degraded: SHOW JOBS probe failed (status=${jobs_status} output=${jobs_out})"
    exit 1
  fi
  pending_jobs=$(echo "$jobs_out" | grep -E '\|FOREGROUND\|' || true)
  if [ -n "$pending_jobs" ]; then
    echo "degraded: pending foreground DDL jobs block ${RW_GATE_PURPOSE}:"
    echo "$pending_jobs" | sed 's/^/  /'
    exit 1
  fi
  log "  ok"
fi

# ── Probe 3 ── compute pod count + optional age floor ─────────────────────
log "probe 3/5: ${MIN_COMPUTE_READY}+ compute pods Running; age threshold=${MIN_COMPUTE_AGE_SEC}s"
compute_rows=$(kubectl get pod -n "$RW_NAMESPACE" -l "$COMPUTE_SELECTOR" \
  -o jsonpath='{range .items[*]}{.metadata.name}{" "}{.status.phase}{" "}{.status.containerStatuses[0].state.running.startedAt}{"\n"}{end}' 2>/dev/null)
if [ -z "$compute_rows" ]; then
  echo "degraded: no compute pods found for selector ${COMPUTE_SELECTOR}"
  exit 1
fi

ready_count=0
youngest_age=999999999
not_ready=""
while read -r pod_name phase started_at; do
  [ -z "${pod_name:-}" ] && continue
  if [ "$phase" != "Running" ] || [ -z "${started_at:-}" ]; then
    not_ready="${not_ready}${pod_name}:${phase} "
    continue
  fi
  ready_count=$((ready_count + 1))
# Portable epoch parse (GNU date + BSD date)
  if date -u -d "${started_at}" +%s >/dev/null 2>&1; then
    started_epoch=$(date -u -d "${started_at}" +%s)
  else
    started_epoch=$(date -u -j -f "%Y-%m-%dT%H:%M:%SZ" "${started_at}" +%s 2>/dev/null || \
                    date -u -j -f "%Y-%m-%dT%H:%M:%S%z" "${started_at%%.*}Z" +%s 2>/dev/null || echo 0)
  fi
  now_epoch=$(date -u +%s)
  age=$(( now_epoch - started_epoch ))
  [ "$age" -lt "$youngest_age" ] && youngest_age="$age"
done <<EOF
$compute_rows
EOF

if [ "$ready_count" -lt "$MIN_COMPUTE_READY" ]; then
  echo "degraded: only ${ready_count}/${MIN_COMPUTE_READY} compute pods Running (${not_ready})"
  exit 1
fi
if [ -n "$not_ready" ]; then
  echo "degraded: compute pod(s) not Running: ${not_ready}"
  exit 1
fi
degraded_write_reason=""
if [ "$youngest_age" -lt "$MIN_COMPUTE_AGE_SEC" ]; then
  if [ "$RW_GATE_PURPOSE" = "ingest" ] && [ "$RW_COLD_START_POLICY" = "degraded-write" ]; then
    degraded_write_reason="youngest compute pod age ${youngest_age}s < threshold ${MIN_COMPUTE_AGE_SEC}s"
  else
    echo "degraded: youngest compute pod age ${youngest_age}s < threshold ${MIN_COMPUTE_AGE_SEC}s (Foyer cold)"
    exit 1
  fi
fi
log "  ok (${ready_count} ready; youngest=${youngest_age}s)"

# ── Probe 4 ── object-store/recovery log rate ─────────────────────────────
log "probe 4/5: object-store/recovery errors < ${SLOWDOWN_MAX} events / ${SLOWDOWN_WINDOW_SEC}s"
compute_errors=$(kubectl logs -n "$RW_NAMESPACE" -l "$COMPUTE_SELECTOR" \
                   --since="${SLOWDOWN_WINDOW_SEC}s" --all-containers=true 2>/dev/null \
                 | grep -E -c 'SlowDown|RateLimited|NoSuchUpload|write part timeout|cluster is under recovering|DML is not permitted during cluster recovery' || true)
meta_errors=$(kubectl logs -n "$RW_NAMESPACE" -l "$META_SELECTOR" \
                --since="${SLOWDOWN_WINDOW_SEC}s" --all-containers=true 2>/dev/null \
              | grep -E -c 'SlowDown|RateLimited|NoSuchUpload|write part timeout|failed to complete epoch|failed to sync|cluster is under recovering|DML is not permitted during cluster recovery' || true)
sd_count=$((compute_errors + meta_errors))
if [ "$sd_count" -ge "$SLOWDOWN_MAX" ]; then
  echo "degraded: object-store/recovery errors ${sd_count} events in last ${SLOWDOWN_WINDOW_SEC}s (compute=${compute_errors} meta=${meta_errors} >= ${SLOWDOWN_MAX})"
  exit 1
fi
log "  ok (${sd_count} events; compute=${compute_errors} meta=${meta_errors})"

# ── All green ──────────────────────────────────────────────────────────────
if [ -n "$degraded_write_reason" ]; then
  [ "$VERBOSE" = 1 ] && echo "degraded-write: ${degraded_write_reason}; use lower dml_rate_limit, smaller batches, no FLUSH" >&2
  echo "degraded-write: ${degraded_write_reason}"
  exit 0
fi
[ "$VERBOSE" = 1 ] && echo "healthy: select=${t_select}s ready=${ready_count} youngest_age=${youngest_age}s object_store_errors=${sd_count}" >&2
echo "healthy"
exit 0
