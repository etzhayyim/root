#!/usr/bin/env bash
# yatabase-deploy.sh — deploy yatabase Worker with CF Cron Triggers preserved.
#
# `gftd deploy` rewrites wrangler.jsonc from magatama.jsonld + bindings,
# stripping any `triggers.crons` block that was hand-edited. This script:
#   1. Runs `gftd deploy` normally
#   2. Patches the freshly-generated wrangler.jsonc to re-add `triggers.crons`
#   3. Calls `npx wrangler deploy` once more so the cron metadata lands
#   4. Restores the gftd-generated wrangler.jsonc as the on-disk source of truth
#
# Until P28 (extending the gftd CLI itself to honor `crons` in magatama.jsonld)
# lands, ALL yatabase deploys MUST go through this script. Bare `gftd deploy`
# will silently drop the lead-source scraper schedule.
#
# Usage:  ./70-tools/scripts/yatabase-deploy.sh
# From:   any directory (script cd's to the project itself)

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/../../60-apps/ai-gftd-project-yatabase" && pwd)"
cd "$PROJECT_DIR"

# Comma-separated cron schedules. Defaults are:
#   0 */6 * * *   — HN scraper (top-of-funnel)
#   30 */6 * * *  — domain enrichment (fills contact_email + tech_stack)
#   45 */6 * * *  — GitHub stargazers scraper (durable second source)
# scheduled() in src/app.ts dispatches by event.cron prefix.
#
# The BMC iteration cron (`15 */6 * * *`) was removed 2026-05-12 when
# lg-yatabase Granian pod took ownership of the loop. It now runs from
# `lg/langgraph.json crons[].schedule = "0 7 * * *"` inside the pod —
# Worker only forwards on-demand /xrpc/ai.gftd.apps.yata.bmcIterate.
CRON_SCHEDULES="${YATA_CRON_SCHEDULES:-0 */6 * * *,30 */6 * * *,45 */6 * * *}"

echo "▸ gftd deploy (will strip cron triggers)"
gftd deploy

echo "▸ patching wrangler.jsonc with triggers.crons + kv_namespaces"
python3 - <<PY
import json, re, os
schedules = [s.strip() for s in os.environ.get('CRON_SCHEDULES', '$CRON_SCHEDULES').split(',') if s.strip()]
with open('wrangler.jsonc') as f:
    raw = f.read()
stripped = re.sub(r'^\s*//.*$', '', raw, flags=re.M)
stripped = re.sub(r',(\s*[}\]])', r'\1', stripped)
data = json.loads(stripped)
data['triggers'] = {'crons': schedules}
# KV binding for auth-cache fallback (P62, 2026-05-12). Used when RW
# durability is degraded — Worker resolves sk_live_yata_* from KV
# without round-tripping to lg-yatabase pod / RisingWave.
kv_bindings = data.setdefault('kv_namespaces', [])
if not any(b.get('binding') == 'YATABASE_AUTH_CACHE' for b in kv_bindings):
    kv_bindings.append({
        'binding': 'YATABASE_AUTH_CACHE',
        'id': 'fbb9ca096633432486a7daee53e8cfd9',
    })
# P82 (2026-05-12): CF native rate-limit binding for synchronous edge
# burst protection. 100 req per 10s per orgDid. Layers on top of the
# KV daily meter (which handles billing-day caps).
unsafe = data.setdefault('unsafe', {})
unsafe_bindings = unsafe.setdefault('bindings', [])
if not any(b.get('name') == 'YATA_BURST_LIMITER' for b in unsafe_bindings):
    unsafe_bindings.append({
        'name': 'YATA_BURST_LIMITER',
        'type': 'ratelimit',
        'namespace_id': '1001',
        'simple': { 'limit': 100, 'period': 10 },
    })
with open('wrangler.jsonc.cron', 'w') as f:
    json.dump(data, f, indent=2)
PY

mv wrangler.jsonc wrangler.jsonc.gftd
mv wrangler.jsonc.cron wrangler.jsonc

echo "▸ npx wrangler deploy (re-attaches cron trigger)"
npx wrangler deploy

# Restore gftd-managed wrangler.jsonc so subsequent `gftd deploy` runs
# work from a clean baseline. The CF-side cron remains attached to the
# Worker version because the Cloudflare API is idempotent on triggers.
mv wrangler.jsonc wrangler.jsonc.cron-applied
mv wrangler.jsonc.gftd wrangler.jsonc
rm -f wrangler.jsonc.cron-applied

echo "✓ yatabase deployed with cron schedules: $CRON_SCHEDULES"
