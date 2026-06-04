# Staging Monitoring Setup — PR #1032 Deployment

**Date**: 2026-04-17  
**Purpose**: Real-time visibility during migration apply (Phase 2)  
**Duration**: 6 hours (active monitoring window)

---

## Part 1: Health Check Queries (RisingWave)

Run these in `psql` every 5–15 minutes during deploy. Copy into `/tmp/health_checks.sql`:

```sql
-- 1. MIGRATION PROGRESS
SELECT COUNT(*) as total_migrations FROM kysely_migration WHERE migration LIKE '202604%';
SELECT migration FROM kysely_migration WHERE migration LIKE '202604%' ORDER BY executed_at DESC LIMIT 5;

-- 2. CLUSTER CONNECTIVITY TEST
SELECT version() as risingwave_version;
SELECT current_database(), current_user, now() as check_time;

-- 3. TABLE CREATION VERIFICATION
SELECT COUNT(*) as new_tables FROM pg_tables 
WHERE schemaname = 'public' 
  AND tablename IN ('vertex_orbital_system', 'vertex_orbital_body', 'vertex_maps_job', 'vertex_flight_offer');

-- 4. ROW COUNT BASELINE (should match seed data)
SELECT 'vertex_orbital_system' as table_name, COUNT(*) as rows FROM vertex_orbital_system
UNION ALL
SELECT 'vertex_orbital_body', COUNT(*) FROM vertex_orbital_body
UNION ALL
SELECT 'vertex_maps_job', COUNT(*) FROM vertex_maps_job
UNION ALL
SELECT 'vertex_flight_offer', COUNT(*) FROM vertex_flight_offer;

-- 5. INDEX CREATION CHECK
SELECT schemaname, tablename, indexname FROM pg_indexes 
WHERE tablename LIKE 'vertex_orbital%' OR tablename LIKE 'vertex_maps%' OR tablename LIKE 'vertex_flight%'
ORDER BY tablename;

-- 6. ACTIVE JOBS (MV backfills)
SHOW JOBS;

-- 7. MATERIALIZED VIEW HEALTH
SELECT mviewname, schemaname FROM pg_matviews 
WHERE mviewname LIKE 'mv_world%' OR mviewname LIKE 'mv_flight%'
ORDER BY mviewname;

-- 8. RECENT ERRORS (if any)
SELECT name, state, error_message FROM rw_catalog.rw_ddl_progress WHERE state = 'Failed';

-- 9. RESOURCE USAGE
SELECT current_setting('work_mem') as work_mem, 
       current_setting('maintenance_work_mem') as maint_mem,
       current_setting('shared_buffers') as shared_buffers;
```

### Auto-check script (run every 5 min):

```bash
cat > /tmp/monitor_health.sh << 'EOF'
#!/bin/bash

DB_URL="postgresql://etzhayyim_user:${RW_STAGING_PASSWORD}@risingwave-staging.etzhayyim.com:4566/etzhayyim"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

echo "=== Health Check: $TIMESTAMP ===" >> /tmp/migration_health.log

# Migration count
migration_count=$(psql "$DB_URL" -tc "SELECT COUNT(*) FROM kysely_migration WHERE migration LIKE '202604%';" 2>/dev/null)
echo "Migrations applied: $migration_count/40" >> /tmp/migration_health.log

# Table creation check
tables_created=$(psql "$DB_URL" -tc "SELECT COUNT(*) FROM pg_tables WHERE tablename IN ('vertex_orbital_system', 'vertex_maps_job');" 2>/dev/null)
echo "Key tables created: $tables_created/2" >> /tmp/migration_health.log

# Active jobs
active_jobs=$(psql "$DB_URL" -tc "SHOW JOBS;" 2>/dev/null | grep -c RUNNING)
echo "Active background jobs: $active_jobs" >> /tmp/migration_health.log

# Cluster health (connectivity)
if psql "$DB_URL" -c "SELECT 1;" > /dev/null 2>&1; then
  echo "Cluster: RESPONSIVE" >> /tmp/migration_health.log
else
  echo "Cluster: ⚠ UNRESPONSIVE" >> /tmp/migration_health.log
fi

echo "" >> /tmp/migration_health.log
EOF

chmod +x /tmp/monitor_health.sh

# Run in background (every 5 min)
while true; do
  /tmp/monitor_health.sh
  sleep 300
done &

echo "Health check monitoring started (logs to /tmp/migration_health.log)"
```

---

## Part 2: Kubernetes Cluster Monitoring

Monitor RisingWave compute/storage pods in parallel terminal:

### CPU & Memory Watch (every 30s)

```bash
watch -n 30 'echo "=== $(date) ===" && \
  kubectl top pod -n risingwave -l role=compute 2>/dev/null | head -10 && \
  echo "---" && \
  kubectl top node -n risingwave 2>/dev/null | head -10'
```

**Expected during apply**:
- Compute CPU: 30-60% (spikes OK during migration apply)
- Memory: 60-75% (should NOT exceed 85%)
- If memory hits 90%+ → **ABORT**, increase cluster memory

### RisingWave Logs (watch for errors)

```bash
kubectl logs -n risingwave -l role=compute -f --tail=100 2>&1 | \
  grep -E "ERROR|WARN|timeout|checkpoint|write_part" | \
  tee /tmp/rw_errors.log
```

**Alert triggers**:
- `write_part timeout` → S3 Hummock bottleneck (normal, expected)
- `OOM` → **CRITICAL**, stop migration
- `connection refused` → **CRITICAL**, cluster down

### Pod Restart Detection

```bash
kubectl get events -n risingwave -w 2>&1 | \
  grep -E "compute|Restart|Failed" | \
  tee /tmp/pod_events.log
```

---

## Part 3: PDS Health Checks

Run every 2 minutes in separate terminal:

```bash
cat > /tmp/pds_health.sh << 'EOF'
#!/bin/bash

TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
PDS_URL="https://atproto.etzhayyim.com"

echo "=== PDS Health: $TIMESTAMP ===" >> /tmp/pds_health.log

# Test server availability
if response=$(curl -s -w "\n%{http_code}" "$PDS_URL/xrpc/com.atproto.server.describeServer"); then
  http_code=$(echo "$response" | tail -1)
  body=$(echo "$response" | head -n -1)
  
  if [ "$http_code" = "200" ]; then
    echo "PDS Status: ✓ UP (HTTP 200)" >> /tmp/pds_health.log
    echo "Response: $(echo "$body" | jq -c '.did // .appid' 2>/dev/null)" >> /tmp/pds_health.log
  else
    echo "PDS Status: ⚠ HTTP $http_code" >> /tmp/pds_health.log
  fi
else
  echo "PDS Status: ✗ UNREACHABLE" >> /tmp/pds_health.log
fi

# Test latency (p95)
latency=$(curl -s -o /dev/null -w "%{time_total}" "$PDS_URL/xrpc/com.atproto.server.describeServer" | awk '{print $1 * 1000 "ms"}')
echo "Latency: $latency" >> /tmp/pds_health.log

echo "" >> /tmp/pds_health.log
EOF

chmod +x /tmp/pds_health.sh

while true; do
  /tmp/pds_health.sh
  sleep 120
done &

echo "PDS health checks started (logs to /tmp/pds_health.log)"
```

---

## Part 4: S3 Hummock Write Latency

Track S3 write performance (indicator of backfill pressure):

```bash
cat > /tmp/s3_latency.sh << 'EOF'
#!/bin/bash

TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Query RW metrics (if exposed via Prometheus)
echo "=== S3 Latency: $TIMESTAMP ===" >> /tmp/s3_latency.log

# Check RW logs for write_part timing (rough estimate)
latest_write=$(kubectl logs -n risingwave -l role=compute --tail=500 2>/dev/null | \
  grep -i "write_part\|checkpoint" | tail -1)

if [ -n "$latest_write" ]; then
  echo "Latest write event: $latest_write" >> /tmp/s3_latency.log
else
  echo "No recent S3 writes detected" >> /tmp/s3_latency.log
fi

echo "" >> /tmp/s3_latency.log
EOF

chmod +x /tmp/s3_latency.sh

while true; do
  /tmp/s3_latency.sh
  sleep 180
done &

echo "S3 latency monitoring started"
```

---

## Part 5: Email Notifications

Configure email alerts during migration:

### 5.1 Email Configuration

Set environment variables:

```bash
export NOTIFICATION_EMAIL="platform-team@etzhayyim.com"
export SMTP_SERVER="smtp.gmail.com"  # or your mail server
export SMTP_PORT="587"
export SMTP_USER="<your-email>"
export SMTP_PASSWORD="<app-password>"
```

### 5.2 Milestone Email Notifications

Send email updates every 10 migrations:

```bash
cat > /tmp/email_notifier.sh << 'EOF'
#!/bin/bash

RECIPIENT="$1"
MIGRATION_NUM="$2"
STATUS="$3"  # "success" or "failed"
SMTP_SERVER="${SMTP_SERVER:-smtp.gmail.com}"
SMTP_PORT="${SMTP_PORT:-587}"
SMTP_USER="${SMTP_USER}"
SMTP_PASSWORD="${SMTP_PASSWORD}"

TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

if [ "$STATUS" = "success" ]; then
  SUBJECT="✅ PR #1032 Staging Deployment — Migrations $((MIGRATION_NUM-9))-$MIGRATION_NUM Complete"
  BODY="Deployment Progress Report

Status: SUCCESS
Progress: $MIGRATION_NUM / 40 migrations
Timestamp: $TIMESTAMP

All migrations applied successfully so far.
No errors detected in RisingWave cluster.

Next milestone: Migrations $((MIGRATION_NUM+1))-$((MIGRATION_NUM+10))

Logs: /tmp/migration_health.log
"
else
  SUBJECT="❌ PR #1032 Staging Deployment — FAILED at Migration #$MIGRATION_NUM"
  BODY="Deployment Failure Alert

Status: FAILED
Failed at migration: $MIGRATION_NUM / 40
Timestamp: $TIMESTAMP

ERROR DETECTED — Rollback initiated automatically.

Check logs:
- /tmp/migration_apply_*.log
- /tmp/rw_errors.log
- /tmp/pod_events.log

Action required: Review logs and restart staging after investigation.
"
fi

# Send email via sendmail (simple method)
{
  echo "To: $RECIPIENT"
  echo "Subject: $SUBJECT"
  echo "From: deployment-bot@etzhayyim.com"
  echo "MIME-Version: 1.0"
  echo "Content-Type: text/plain; charset=UTF-8"
  echo ""
  echo "$BODY"
} | sendmail -v "$RECIPIENT" 2>/dev/null

if [ $? -eq 0 ]; then
  echo "[$(date)] Email sent to $RECIPIENT" >> /tmp/notification.log
else
  echo "[$(date)] ⚠ Email send FAILED" >> /tmp/notification.log
fi
EOF

chmod +x /tmp/email_notifier.sh

# Usage during migration:
# /tmp/email_notifier.sh "platform-team@etzhayyim.com" 10 success
# /tmp/email_notifier.sh "platform-team@etzhayyim.com" 20 success
# /tmp/email_notifier.sh "platform-team@etzhayyim.com" 25 failed
```

### 5.3 Alternative: Using Mailgun API

If sendmail is not available:

```bash
cat > /tmp/email_notifier_mailgun.sh << 'EOF'
#!/bin/bash

RECIPIENT="$1"
MIGRATION_NUM="$2"
STATUS="$3"
MAILGUN_DOMAIN="${MAILGUN_DOMAIN:-mg.etzhayyim.com}"
MAILGUN_API_KEY="${MAILGUN_API_KEY}"

if [ -z "$MAILGUN_API_KEY" ]; then
  echo "Error: MAILGUN_API_KEY not set"
  exit 1
fi

TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

if [ "$STATUS" = "success" ]; then
  SUBJECT="✅ PR #1032 Staging — Migrations $((MIGRATION_NUM-9))-$MIGRATION_NUM OK"
  TEXT="Progress: $MIGRATION_NUM/40 migrations applied successfully at $TIMESTAMP"
else
  SUBJECT="❌ PR #1032 Staging — FAILED at Migration #$MIGRATION_NUM"
  TEXT="Deployment failed at migration $MIGRATION_NUM at $TIMESTAMP. Rollback initiated."
fi

curl -s --user "api:${MAILGUN_API_KEY}" \
  "https://api.mailgun.net/v3/${MAILGUN_DOMAIN}/messages" \
  -F "from=deployment@etzhayyim.com" \
  -F "to=${RECIPIENT}" \
  -F "subject=${SUBJECT}" \
  -F "text=${TEXT}" > /dev/null

echo "[$(date)] Email sent to $RECIPIENT" >> /tmp/notification.log
EOF

chmod +x /tmp/email_notifier_mailgun.sh
```

---

## Part 6: Dashboard Configuration (Optional: Grafana/Prometheus)

If you have Grafana access, create dashboard with these panels:

### Panel 1: Migration Progress
```
Title: Migration Apply Progress
Query: 
  SELECT COUNT(*) FROM kysely_migration WHERE migration LIKE '202604%'
Refresh: 30s
Alert: If < expected_count for >10 min
```

### Panel 2: RW Cluster Health
```
Title: RW CPU & Memory
Source: Prometheus (via kube-state-metrics)
Metrics:
  - container_cpu_usage_seconds_total{pod=~".*compute.*"}
  - container_memory_usage_bytes{pod=~".*compute.*"}
Refresh: 15s
Alert: If memory > 85%
```

### Panel 3: PDS Latency
```
Title: PDS Response Time
Query: Synthetic check every 2m
Target: https://atproto.etzhayyim.com/xrpc/com.atproto.server.describeServer
Alert: If latency > 500ms for >5 min
```

### Panel 4: RW Logs (Error aggregation)
```
Title: RisingWave Errors
Source: Loki (log aggregation)
Query: 
  {job="risingwave",level=~"ERROR|WARN"} 
  |= "write_part" or |= "timeout" or |= "OOM"
Alert: Any ERROR level
```

---

## Part 7: Log Archival (Post-Deploy)

Save all logs for post-mortem analysis:

```bash
mkdir -p /tmp/migration_logs_$(date +%Y%m%d)

# Collect logs
cp /tmp/migration_health.log /tmp/migration_logs_*/
cp /tmp/pds_health.log /tmp/migration_logs_*/
cp /tmp/rw_errors.log /tmp/migration_logs_*/
cp /tmp/pod_events.log /tmp/migration_logs_*/
cp /tmp/migration_apply_*.log /tmp/migration_logs_*/

# Upload to S3
aws s3 sync /tmp/migration_logs_$(date +%Y%m%d) \
  s3://etzhayyim-staging-logs/migrations/$(date +%Y/%m/%d)/

echo "Logs archived to S3"
```

---

## Part 8: Live Dashboard (All-in-One)

Create a single terminal dashboard aggregating all metrics:

```bash
cat > /tmp/live_dashboard.sh << 'EOF'
#!/bin/bash

while true; do
  clear
  echo "╔════════════════════════════════════════════════════════════════╗"
  echo "║         PR #1032 Staging Deployment — Live Dashboard           ║"
  echo "║                     $(date '+%Y-%m-%d %H:%M:%S')                       ║"
  echo "╚════════════════════════════════════════════════════════════════╝"
  echo ""
  
  # Migration progress
  echo "📊 MIGRATION PROGRESS:"
  migration_count=$(psql -h risingwave-staging.etzhayyim.com -U etzhayyim_user -d etzhayyim -tc "SELECT COUNT(*) FROM kysely_migration WHERE migration LIKE '202604%';" 2>/dev/null || echo "?")
  echo "   Migrations applied: $migration_count / 40"
  echo ""
  
  # RW Cluster health
  echo "🖥️  CLUSTER HEALTH:"
  if psql -h risingwave-staging.etzhayyim.com -U etzhayyim_user -d etzhayyim -c "SELECT 1;" > /dev/null 2>&1; then
    cpu=$(kubectl top pod -n risingwave -l role=compute --no-headers 2>/dev/null | awk '{sum+=$2} END {print sum "m"}' || echo "?")
    mem=$(kubectl top pod -n risingwave -l role=compute --no-headers 2>/dev/null | awk '{sum+=$3} END {print sum "Mi"}' || echo "?")
    echo "   Status: ✓ RESPONSIVE"
    echo "   CPU: $cpu  Memory: $mem"
  else
    echo "   Status: ✗ UNRESPONSIVE ⚠️"
  fi
  echo ""
  
  # PDS health
  echo "🌐 PDS STATUS:"
  pds_code=$(curl -s -o /dev/null -w "%{http_code}" https://atproto.etzhayyim.com/xrpc/com.atproto.server.describeServer 2>/dev/null || echo "???")
  if [ "$pds_code" = "200" ]; then
    echo "   Status: ✓ UP (HTTP 200)"
  else
    echo "   Status: ⚠ HTTP $pds_code"
  fi
  echo ""
  
  # Error summary
  echo "⚠️  RECENT ERRORS (last 3):"
  tail -3 /tmp/rw_errors.log 2>/dev/null | sed 's/^/   /' || echo "   (none)"
  echo ""
  
  # Next refresh
  echo "Next refresh in 30s... (Ctrl+C to exit)"
  sleep 30
done
EOF

chmod +x /tmp/live_dashboard.sh

# Start dashboard
/tmp/live_dashboard.sh
```

---

## Setup Instructions (Quick Start)

### Before Deploy (T-30 min):

```bash
export RW_STAGING_PASSWORD="<staging-password>"
export NOTIFICATION_EMAIL="platform-team@etzhayyim.com"

# Terminal 1: Health checks (5-min polling)
/tmp/monitor_health.sh &
tail -f /tmp/migration_health.log

# Terminal 2: K8s pod monitoring
watch -n 30 'kubectl top pod -n risingwave -l role=compute'

# Terminal 3: RW error logs
kubectl logs -n risingwave -l role=compute -f --tail=100 | grep -i error

# Terminal 4: PDS health (2-min checks)
/tmp/pds_health.sh &
tail -f /tmp/pds_health.log

# Terminal 5: Live dashboard (optional, nice-to-have)
/tmp/live_dashboard.sh
```

**Email notifications** will be sent automatically to `$NOTIFICATION_EMAIL` at migration milestones (every 10 migrations).

### During Deploy:

1. Execute migration apply (Terminal 6)
2. Watch terminals 1–5 for anomalies
3. Send Slack notifications every 10 migrations
4. If any **CRITICAL** alert → **STOP and ROLLBACK**

### After Deploy:

1. Run health checks 5 more times (next 25 min)
2. Archive logs: `aws s3 sync /tmp/migration_logs_* s3://...`
3. Generate post-deploy report

---

## Alert Thresholds

| Metric | Warning | Critical | Action |
|--------|---------|----------|--------|
| RW Memory | >75% | >85% | Reduce backfill parallelism OR increase cluster memory |
| PDS Latency | >200ms | >1000ms | Check network; may be unrelated to migration |
| Migration apply time | >30 min per migration | >60 min | **STOP and ROLLBACK** |
| Cluster unresponsive | >1 min | >2 min | **STOP and ROLLBACK** |
| S3 write timeouts | 1–3 per minute | >5 per minute | Reduce checkpoint frequency (system param) |
| Active errors in logs | 1–5 | >10 | Investigate; may be transient |

---

## Emergency Stop Procedure

If any **CRITICAL** threshold triggered:

```bash
# 1. Stop migration apply script
pkill -f apply_migrations.sh

# 2. Wait 10s, check cluster health
psql "$DATABASE_URL" -c "SELECT 1;"

# 3. If still unresponsive, initiate rollback
/tmp/rollback.sh "$DATABASE_URL"

# 4. Alert team via email
/tmp/email_notifier.sh "$NOTIFICATION_EMAIL" 0 failed
```

---

**Document Owner**: Platform Team  
**Created**: 2026-04-17  
**Last Updated**: 2026-04-17
