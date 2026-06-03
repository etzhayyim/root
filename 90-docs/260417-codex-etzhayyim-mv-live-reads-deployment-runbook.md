# Deployment Runbook: PR #1032 (codex/etzhayyim-mv-live-reads)

**Date**: 2026-04-17
**Branch**: `codex/etzhayyim-mv-live-reads`
**PR**: #1032
**Scope**: 41 graph migrations, 8+ app features, 15+ lexicon definitions, 649 concordance systems
**Risk Level**: **MEDIUM** (MV backfill concurrency, out-of-band migration records)

---

## Part A: Staging Deployment

### Phase 0: Pre-Flight Checks (1h, 1 person)

**Timeline**: T-24h before staging deploy

#### 0.1 Code Verification

```bash
# Verify all migration files exist and are valid TypeScript
cd 30-graph/graph-schema/migrations
ls -1 20260415*.ts 20260416*.ts 20260417*.ts | wc -l
# Expected: 41 files

# Syntax check (compile, don't run)
pnpm tsc --noEmit migrations/*.ts

# Verify down() functions are present
grep -l "export async function down" migrations/20260415*.ts migrations/20260416*.ts migrations/20260417*.ts | wc -l
# Expected: 41 files (all should have down functions)
```

#### 0.2 Lexicon & App Manifest Validation

```bash
cd /repo

# Verify all new lexicon JSONs are syntactically valid
for f in 00-contracts/lexicons/com/etzhayyim/apps/{legalEntity,hospitality,maps,ongakuka,onion,openBanking,openIsic,openJpnGov}/*.json; do
  jq . "$f" > /dev/null || echo "INVALID: $f"
done

# Check that all NSIDs in magatama.jsonld have corresponding lexicon files
# (sample 3 app manifests)
for app in legal-entity maps ongakuka; do
  manifest="20-actors/$app/actor-manifest.jsonld"
  if [ -f "$manifest" ]; then
    echo "=== $app manifest routes ==="
    jq '.handles[] | .handles[]' "$manifest" 2>/dev/null | head -5
  fi
done
```

#### 0.3 Rust Build Check (Kami WASM)

```bash
cd 40-engine/kami-engine/kami-map

# Verify Cargo.toml is valid and dependencies resolve
cargo check 2>&1 | head -50

# Build WASM (pre-compile to catch errors)
wasm-pack build --target bundler 2>&1 | tail -20

# Verify output files exist
ls -lh pkg/kami_map.{js,wasm,d.ts} 2>/dev/null || echo "ERROR: WASM build failed"
```

#### 0.4 Migration Dependency Check

```bash
cd 30-graph/graph-schema

# Identify which migrations were applied out-of-band (manual psql)
# by checking for migrations not in kysely_migration table (after apply)
cat > /tmp/check_manual_migrations.sql << 'EOF'
SELECT migration FROM kysely_migration
WHERE migration LIKE '202604%'
ORDER BY migration DESC
LIMIT 50;
EOF

psql $DATABASE_URL -f /tmp/check_manual_migrations.sql > /tmp/applied_migrations.txt

# Cross-reference with file system
ls -1 migrations/202604*.ts | sed 's/.*\///' | sed 's/\.ts$//' > /tmp/fs_migrations.txt

# Find missing (manually applied)
comm -23 <(sort /tmp/fs_migrations.txt) <(sort /tmp/applied_migrations.txt) | tee /tmp/manual_migrations.txt
echo "---"
echo "Manual migrations found (should match CLAUDE.md list):"
cat /tmp/manual_migrations.txt | wc -l
```

---

### Phase 1: Staging Environment Preparation (2h)

**Prerequisites**: Access to RisingWave staging cluster, kubectl, psql client

#### 1.1 Backup Current State

```bash
# Take snapshot of current schema
RW_HOST=risingwave-staging.etzhayyim.com
RW_PORT=4566
DATABASE_URL="postgresql://etzhayyim_user:${RW_PASSWORD}@${RW_HOST}:${RW_PORT}/etzhayyim"

# Dump current migration state
psql "$DATABASE_URL" -c "\copy kysely_migration TO /tmp/kysely_migration_backup_$(date +%Y%m%d_%H%M%S).csv CSV"

# Snapshot key table row counts (pre-migration baseline)
psql "$DATABASE_URL" << 'EOF' > /tmp/row_counts_before.txt
SELECT schemaname, tablename, n_live_tup FROM pg_stat_user_tables
WHERE tablename LIKE 'vertex_%' OR tablename LIKE 'edge_%' OR tablename LIKE 'mv_%'
ORDER BY tablename;
EOF

echo "Backed up to /tmp/kysely_migration_backup_*.csv and /tmp/row_counts_before.txt"
```

#### 1.2 Configure RisingWave System Parameters (Stability Tuning)

```bash
# Apply MV backfill safety tuning (persistent across restarts)
psql "$DATABASE_URL" << 'EOF'
ALTER SYSTEM SET barrier_interval_ms = 5000;
ALTER SYSTEM SET checkpoint_frequency = 30;
ALTER SYSTEM SET enable_locality_backfill = true;

-- Confirm
SHOW barrier_interval_ms;
SHOW checkpoint_frequency;
SHOW enable_locality_backfill;
EOF

echo "✓ System parameters configured for large MV backfills"
```

#### 1.3 Pre-Stage Migration Code

```bash
cd /repo
git fetch origin codex/etzhayyim-mv-live-reads
git checkout codex/etzhayyim-mv-live-reads

# Verify 41 new migrations are present
new_migration_count=$(git diff main --name-only -- 30-graph/graph-schema/migrations/202604*.ts | wc -l)
echo "New migrations detected: $new_migration_count (expected: 41)"

# Build migration runner
cd 30-graph/graph-schema
pnpm install
pnpm build  # or tsc
```

---

### Phase 2: Staged Migration Apply (Staging) — 4h

**Operator Role**: 1 person watching terminal; Slack channel on alert
**Rollback**: If any migration fails, revert to Phase 1 backup and investigate

#### 2.1 Pre-Migration Cluster Health Check

```bash
# Check RW cluster state (should show "Running")
kubectl -n risingwave get pods -o wide | grep risingwave-

# Check compute memory usage
kubectl top pod -n risingwave | grep compute

# Confirm Hyperdrive connection is alive
psql "$DATABASE_URL" -c "SELECT version();"
# Expected: "RisingWave X.Y.Z"
```

#### 2.2 Apply Migrations **Serially** (Critical for stability)

```bash
cd 30-graph/graph-schema

export DATABASE_URL="postgresql://etzhayyim_user:${RW_PASSWORD}@risingwave-staging.etzhayyim.com:4566/etzhayyim"
export MIGRATION_DIR="./migrations"

# Create a wrapper script to apply one migration at a time
cat > /tmp/apply_migrations.sh << 'EOF'
#!/bin/bash
set -e

DB_URL="$1"
MIGRATIONS_DIR="$2"

# Get list of new migrations (202604*.ts)
migrations=$(ls -1 "$MIGRATIONS_DIR"/202604*.ts | sed 's/.*\///' | sed 's/\.ts$//' | sort)

applied_count=0
failed_migration=""

for mig in $migrations; do
  echo ""
  echo "=========================================="
  echo "Applying migration: $mig"
  echo "Time: $(date)"
  echo "=========================================="

  # Run migration
  if pnpm kysely migrate --up --limit 1 2>&1 | tee /tmp/migration_${mig}.log; then
    applied_count=$((applied_count + 1))
    echo "✓ Success: $mig"

    # Wait 10s for RW to stabilize between migrations
    echo "Waiting 10s for cluster stabilization..."
    sleep 10

    # Check cluster health
    if ! psql "$DB_URL" -c "SELECT 1;" > /dev/null 2>&1; then
      echo "⚠ WARNING: Cluster unresponsive after $mig. Checking..."
      sleep 30
      if ! psql "$DB_URL" -c "SELECT 1;" > /dev/null 2>&1; then
        echo "✗ FATAL: Cluster offline. Manual intervention required."
        exit 1
      fi
    fi
  else
    echo "✗ FAILED: $mig"
    failed_migration="$mig"
    break
  fi
done

echo ""
echo "=========================================="
echo "Migration Summary"
echo "=========================================="
echo "Applied: $applied_count / ${#migrations[@]} migrations"
if [ -z "$failed_migration" ]; then
  echo "Status: ✓ ALL SUCCESSFUL"
else
  echo "Status: ✗ FAILED AT: $failed_migration"
  exit 1
fi
EOF

chmod +x /tmp/apply_migrations.sh

# Run with monitoring
/tmp/apply_migrations.sh "$DATABASE_URL" "$MIGRATION_DIR" 2>&1 | tee /tmp/migration_apply_$(date +%Y%m%d_%H%M%S).log
```

#### 2.3 Monitor During Apply

**In parallel terminal** (watch cluster health):

```bash
# Watch RW cluster CPU/memory
watch -n 5 'kubectl top pod -n risingwave | grep -E "compute|NAME" | head -5'

# Watch checkpoint progress (every 2 min)
watch -n 120 "psql postgresql://etzhayyim_user:\${RW_PASSWORD}@risingwave-staging.etzhayyim.com:4566/etzhayyim -c 'SHOW jobs;' | head -30"

# Monitor S3 write timeouts (in RW logs)
kubectl logs -n risingwave -l role=compute -f 2>&1 | grep -i "timeout\|error\|write"
```

#### 2.4 Post-Migration Verification

```bash
# Confirm all 41 migrations are in kysely_migration
migration_count=$(psql "$DATABASE_URL" -c "SELECT COUNT(*) FROM kysely_migration WHERE migration LIKE '202604%';" | grep -o '[0-9]*' | head -1)
echo "Migrations applied: $migration_count / 41"

if [ "$migration_count" -eq 41 ]; then
  echo "✓ All migrations present"
else
  echo "⚠ WARNING: Expected 41, got $migration_count. Check /tmp/manual_migrations.txt for manual rows."
fi

# Verify key tables created
tables_to_check=(
  "vertex_orbital_system"
  "vertex_orbital_body"
  "vertex_maps_job"
  "vertex_flight_offer"
  "vertex_ongakuka"
)

for tbl in "${tables_to_check[@]}"; do
  count=$(psql "$DATABASE_URL" -c "SELECT count(*) FROM $tbl LIMIT 1;" 2>&1 | grep -o '[0-9]*' | tail -1)
  echo "✓ $tbl: $count rows"
done

# Check row counts changed (should show new vertex tables)
psql "$DATABASE_URL" -c "SELECT schemaname, tablename, n_live_tup FROM pg_stat_user_tables WHERE tablename LIKE 'vertex_orbital%' OR tablename LIKE 'vertex_maps%' OR tablename LIKE 'vertex_flight%';"
```

#### 2.5 Test New Endpoints (App Layer)

```bash
# Test 3 sample endpoints with new schema
endpoints=(
  "com.etzhayyim.apps.maps.getJobStatus"
  "com.etzhayyim.legalEntity.companyFact"
  "com.etzhayyim.ongakuka.listTracks"
)

for nsid in "${endpoints[@]}"; do
  echo "Testing: $nsid"

  # Call via XRPC (example; adjust for your test harness)
  curl -s "https://atproto.etzhayyim.com/xrpc/$nsid?limit=1" \
    -H "Authorization: Bearer $etzhayyim_TEST_TOKEN" | jq . | head -10

  echo "---"
done
```

---

### Phase 3: Staging Validation (2h)

#### 3.1 Coverage Metrics

```bash
psql "$DATABASE_URL" << 'EOF'
-- Check new world coverage (expected: 461 domains)
SELECT COUNT(*) as domain_count FROM dim_world_domain;

-- Sample coverage by domain
SELECT domain, collected, world_total, ROUND(100.0 * collected / NULLIF(world_total, 0), 2) as coverage_pct
FROM mv_world_coverage_live
WHERE domain IN ('maps', 'legal-entity', 'flight_offer', 'ongakuka', 'orbital_system')
ORDER BY collected DESC;

-- Check for newly populated vertex tables
SELECT tablename, n_live_tup
FROM pg_stat_user_tables
WHERE tablename IN ('vertex_orbital_body', 'vertex_maps_job', 'vertex_flight_offer')
ORDER BY n_live_tup DESC;
EOF
```

#### 3.2 MV Stability Check

```bash
# Ensure all new MVs are healthy (no stalled backfills)
psql "$DATABASE_URL" -c "SHOW JOBS;" | grep -E "BACKGROUND|mv_" | head -20

# Check materialized view dependencies (should show no orphans)
psql "$DATABASE_URL" << 'EOF'
SELECT mview_name, source_table
FROM (
  SELECT matviewname as mview_name, NULL as source_table FROM pg_matviews
) mv
WHERE mview_name LIKE 'mv_world%' OR mview_name LIKE 'mv_flight%'
ORDER BY mview_name;
EOF
```

#### 3.3 App Integration Test (Maps Collection)

```bash
# Assuming maps-collection-control-plane is running in staging
curl -s "https://maps-collection-staging.etzhayyim.com/_app/meta" | jq .

# Test job listing (should use new vertex_maps_job schema)
curl -s "https://maps-collection-staging.etzhayyim.com/jobs/list?status=active&limit=10" \
  -H "Authorization: Bearer $etzhayyim_TEST_TOKEN" | jq '.jobs[] | {id, status, progress_pct}'
```

#### 3.4 Performance Sanity Check

```bash
# Sample query performance (should be <100ms)
psql "$DATABASE_URL" \
  -c "EXPLAIN ANALYZE SELECT * FROM vertex_maps_job WHERE status = 'active' LIMIT 10;" | tail -20
```

**Expected**: Seq Scan or Index Scan, ~<100ms

---

## Part B: Production Deployment

### Phase 4: Production Pre-Staging (1h)

**Timeline**: T-2h before prod deploy

#### 4.1 Prod Backup & Baseline

```bash
export DATABASE_URL="postgresql://etzhayyim_user:${RW_PROD_PASSWORD}@risingwave.etzhayyim.com:4566/etzhayyim"

# Full schema backup
pg_dump -s "$DATABASE_URL" > /tmp/schema_backup_$(date +%Y%m%d_%H%M%S).sql

# Migration state snapshot
psql "$DATABASE_URL" -c "\copy kysely_migration TO /tmp/prod_migrations_backup.csv CSV"

# Row count baseline
psql "$DATABASE_URL" << 'EOF' > /tmp/prod_row_counts_before.txt
SELECT tablename, n_live_tup FROM pg_stat_user_tables
WHERE tablename LIKE 'vertex_%' OR tablename LIKE 'mv_%'
ORDER BY tablename;
EOF

# Store backups securely
aws s3 cp /tmp/schema_backup_*.sql s3://etzhayyim-backups/risingwave/$(date +%Y/%m/%d)/
aws s3 cp /tmp/prod_migrations_backup.csv s3://etzhayyim-backups/risingwave/$(date +%Y/%m/%d)/

echo "✓ Backups uploaded to S3"
```

#### 4.2 Prod Cluster Health (Go/No-Go)

```bash
# Check RW cluster state
kubectl -n risingwave get pods -o wide | grep -E "compute|NAME"

# Check PDS & AppView are responding
curl -s https://atproto.etzhayyim.com/xrpc/com.atproto.server.describeServer | jq '.availableUserDomains | length'
curl -s https://appview.etzhayyim.com/_app/meta | jq '.appid'

# Confirm Hyperdrive is healthy
psql "$DATABASE_URL" -c "SELECT COUNT(*) as table_count FROM information_schema.tables WHERE table_schema='public';" | grep -o '[0-9]*'
# Expected: >200 tables

if [ $? -eq 0 ]; then
  echo "✓ GO for production deploy"
else
  echo "✗ ABORT: Production cluster unhealthy"
  exit 1
fi
```

---

### Phase 5: Production Migration Apply (Prod) — 5h

**Operator Role**: 2 people (one applies, one monitors)
**Runbook**: Same as Staging (Phase 2), but slower pacing

#### 5.1 Pre-Migration Health Broadcast

```bash
# Announce to team
cat > /tmp/deploy_announcement.txt << 'EOF'
🚀 DEPLOYING: PR #1032 (codex/etzhayyim-mv-live-reads)

Timeline:
- Start: $(date)
- Expected Duration: 5 hours
- Risk: MEDIUM (MV backfill)

Changes:
- 41 graph migrations (orbital, flight, legal-entity, etc.)
- 8 new app features
- 649 concordance systems

Monitoring:
- RW cluster: https://monitoring.etzhayyim.com/risingwave
- PDS health: https://atproto.etzhayyim.com/xrpc/com.atproto.server.describeServer
- Alerts: Slack #platform-deploys

Rollback: If migration fails, reverting to backup (EST 30 min)
EOF

# Post to Slack
slack --channel platform-deploys < /tmp/deploy_announcement.txt
```

#### 5.2 Apply Migrations (Using Same Serial Script)

```bash
export DATABASE_URL="postgresql://etzhayyim_user:${RW_PROD_PASSWORD}@risingwave.etzhayyim.com:4566/etzhayyim"

cd /repo
git fetch origin codex/etzhayyim-mv-live-reads
git checkout codex/etzhayyim-mv-live-reads
cd 30-graph/graph-schema

# Apply (verbose logging)
/tmp/apply_migrations.sh "$DATABASE_URL" "./migrations" 2>&1 | tee /tmp/prod_migration_$(date +%Y%m%d_%H%M%S).log

# Alert team on each milestone
echo "Migrations 1-10 complete ✓" | slack --channel platform-deploys
sleep 30
echo "Migrations 11-20 complete ✓" | slack --channel platform-deploys
sleep 30
# ... etc
```

#### 5.3 Parallel Monitoring (Operator 2)

```bash
# Terminal 1: Watch RW logs
kubectl logs -n risingwave -l role=compute -f 2>&1 | tee /tmp/rw_logs_$(date +%Y%m%d_%H%M%S).log | grep -i "error\|timeout\|checkpoint"

# Terminal 2: Query health checks every 30 sec
for i in {1..600}; do
  echo "=== Check $i ($(date)) ==="
  psql postgresql://etzhayyim_user:${RW_PROD_PASSWORD}@risingwave.etzhayyim.com:4566/etzhayyim \
    -c "SELECT COUNT(*) as migrations_applied FROM kysely_migration WHERE migration LIKE '202604%';"

  # Check PDS responding
  curl -s https://atproto.etzhayyim.com/xrpc/com.atproto.server.describeServer > /dev/null 2>&1 && echo "PDS: OK" || echo "PDS: UNREACHABLE ⚠"

  sleep 30
done
```

#### 5.4 Rollback Trigger (If Things Go Wrong)

```bash
# If any of these fail, **STOP and ROLLBACK**:
# - Migration fails
# - RW cluster becomes unresponsive (>2 min)
# - PDS health checks fail for >1 min
# - MV backfill causing CPU/memory spike

# Rollback script:
cat > /tmp/rollback.sh << 'EOF'
#!/bin/bash
set -e

DB_URL="$1"

echo "⚠ INITIATING ROLLBACK"
echo "Reverting to pre-migration state..."

# Get last successful migration before our batch
last_good_migration=$(psql "$DB_URL" -c "SELECT migration FROM kysely_migration WHERE migration < '20260415' ORDER BY migration DESC LIMIT 1;" | tail -1)

echo "Reversing migrations back to: $last_good_migration"

# Roll back one by one
pnpm kysely migrate --down --steps 41

echo "✓ Rollback complete"
echo "Restoring migration table..."
psql "$DB_URL" -c "\COPY kysely_migration FROM /tmp/prod_migrations_backup.csv CSV HEADER;"

echo "✓ ROLLBACK SUCCESSFUL - Cluster restored to pre-deploy state"
EOF

chmod +x /tmp/rollback.sh

# To execute:
# /tmp/rollback.sh "$DATABASE_URL"
```

---

### Phase 6: Production Post-Deploy Verification (1h)

#### 6.1 Verify Migrations Applied

```bash
psql "$DATABASE_URL" << 'EOF'
-- Confirm count
SELECT COUNT(*) FROM kysely_migration WHERE migration LIKE '202604%';
-- Expected: 41

-- List all new migrations
SELECT migration, executed_at FROM kysely_migration WHERE migration LIKE '202604%' ORDER BY migration;
EOF
```

#### 6.2 Sanity Test Production Endpoints

```bash
# Test each new app
test_cases=(
  "com.etzhayyim.apps.maps.getJobStatus?jobId=test-job-1"
  "com.etzhayyim.legalEntity.listCompanies?limit=1"
  "com.etzhayyim.ongakuka.listTracks?limit=1"
)

for endpoint in "${test_cases[@]}"; do
  echo "Testing: $endpoint"
  curl -s "https://atproto.etzhayyim.com/xrpc/${endpoint}" \
    -H "Authorization: Bearer $etzhayyim_PROD_TOKEN" | jq '.error // .records | length' | head -5
  echo "---"
done
```

#### 6.3 Production Coverage Report

```bash
psql "$DATABASE_URL" << 'EOF'
-- Sample world coverage (5 domains)
SELECT domain, collected, world_total,
  ROUND(100.0 * collected / NULLIF(world_total, 0), 1) as pct
FROM mv_world_coverage_live
WHERE domain IN ('maps', 'legal-entity', 'orbital_system', 'flight_offer', 'ongakuka')
ORDER BY pct DESC;

-- Check new lexicon usage
SELECT collection, COUNT(*) as record_count
FROM vertex_repo_record
WHERE collection LIKE 'com.etzhayyim.apps.%'
  AND (collection LIKE '%.orbital%'
    OR collection LIKE '%.flight%'
    OR collection LIKE '%.company%')
GROUP BY collection
ORDER BY record_count DESC;
EOF
```

#### 6.4 Alert Team (Success)

```bash
slack --channel platform-deploys << 'EOF'
✅ PR #1032 DEPLOYED TO PRODUCTION

- 41 migrations applied ✓
- All endpoints responding ✓
- Coverage metrics: 461 domains (expected)
- Rollback capability: Maintained

Performance:
- Avg migration time: ~5 min
- RW cluster health: Nominal
- PDS latency: <100ms

Next: Monitor for 24h, check log aggregation for errors
EOF
```

---

## Part C: Rollback & Recovery

### If Deploy Fails

| Symptom | Action |
|---------|--------|
| **Migration fails on step 15** | Stop apply, run `/tmp/rollback.sh $DATABASE_URL` |
| **RW cluster unresponsive** | Wait 2 min; if no recovery, kill apply process and rollback |
| **MV backfill stalled >15 min** | Cancel job: `CANCEL JOB <job_id>`, revert to backup |
| **PDS health failing** | Rollback immediately; investigate separately |

### Post-Rollback Investigation

```bash
# Get failed migration logs
cat /tmp/migration_${failed_migration}.log

# Check RW compute logs for errors
kubectl logs -n risingwave <compute-pod> --tail=200 | grep -i error

# Verify cluster recovered
psql "$DATABASE_URL" -c "SELECT COUNT(*) FROM kysely_migration;"
# Should match pre-deploy count

# File incident + post-mortem
echo "Incident: Deploy PR #1032 rolled back at migration #15" > /tmp/incident.txt
cat /tmp/migration_*.log >> /tmp/incident.txt
aws s3 cp /tmp/incident.txt s3://etzhayyim-incidents/$(date +%Y/%m/%d)/
```

---

## Part D: Post-Deploy Runbook (24h Monitoring)

### Hour 0-4 (Immediate)

- [ ] Every 15 min: Check RW cluster CPU/memory (should be normal)
- [ ] Every 30 min: Sample XRPC endpoints (latency <100ms)
- [ ] Monitor S3 write latency (Hummock backlog)
- [ ] Watch log aggregation for migration errors

### Hour 4-24 (Ongoing)

- [ ] Verify MV materialization is complete (no BACKGROUND jobs pending)
- [ ] Spot-check 10 random world coverage queries
- [ ] Confirm maps-collection app is using new `vertex_maps_job` schema correctly
- [ ] Verify all PDS commits are being collected into new vertex tables

### Day 1-7 (Weekly)

- [ ] Run data quality report on new tables
- [ ] Check for stale TLE data in `vertex_orbital_body` (ISS ephemeris)
- [ ] Monitor flight offer feed for freshness
- [ ] Verify legal-entity ingest is populating correctly

---

## Appendix: Configuration Reference

### Environment Variables Required

```bash
# Staging
export DATABASE_URL="postgresql://etzhayyim_user:${RW_STAGING_PASSWORD}@risingwave-staging.etzhayyim.com:4566/etzhayyim"
export RW_HOST=risingwave-staging.etzhayyim.com
export etzhayyim_TEST_TOKEN="<staging-bearer-token>"

# Production
export DATABASE_URL="postgresql://etzhayyim_user:${RW_PROD_PASSWORD}@risingwave.etzhayyim.com:4566/etzhayyim"
export RW_HOST=risingwave.etzhayyim.com
export etzhayyim_PROD_TOKEN="<prod-bearer-token>"
```

### Critical RW System Params (Already Set in Phase 1.2)

```sql
barrier_interval_ms = 5000        -- Reduce checkpoint frequency (default 1000)
checkpoint_frequency = 30         -- Every 30×barrier (default 1)
enable_locality_backfill = true   -- Reduce data shuffle during MV backfill
force_two_phase_agg = true        -- Already set system-wide (safe default)
```

### Monitoring Dashboards

- RW Cluster: https://monitoring.etzhayyim.com/risingwave
- PDS Health: https://monitoring.etzhayyim.com/pds
- AppView: https://monitoring.etzhayyim.com/appview
- Alerts: Slack `#platform-alerts`

---

## Sign-Off Checklist

- [ ] Staging deployment complete & verified (Phase 0–3)
- [ ] Code review signed off (critical issues resolved)
- [ ] Prod backups taken & stored in S3 (Phase 4.1)
- [ ] Team notified of deployment window
- [ ] 2 operators assigned (apply + monitor)
- [ ] Rollback script tested in staging
- [ ] All endpoints sample-tested post-deploy
- [ ] 24h post-deploy monitoring plan assigned

---

**Document Owner**: Platform Team
**Last Updated**: 2026-04-17
**Version**: 1.0
