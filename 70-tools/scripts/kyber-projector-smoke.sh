#!/usr/bin/env bash
# Smoke test for kyber-projector (APQC PCF × BPMN 2.0 × OCEL 2.0), ADR-0025.
#
# Preconditions:
#   - kyber ERP (kyb3rerp) + kyber-projector (kyb3proj) deployed
#   - `gftd auth login` completed (or GFTD_TOKEN exported)
#   - $KYBER_APP default = kyb3rerp, $PROJECTOR_APP default = kyb3proj
#
# Flow:
#   1. ERP side: initApqcProjector → follow + bootstrap record
#   2. Projector side: listApqcActors (expect 13 rows, status=active)
#   3. Projector side: listBpmnTasks (expect 28 bindings)
#   4. ERP side: createJournalEntry → triggers reactive projection
#   5. Projector side: getApqcCoverage → expect byL1[9.0].ocelEvents >= 1
#   6. Projector side: runBpmnTask(bpmn-11-risk-assess) → explicit non-reactive
#   7. Projector side: emitApqcEvent(custom) → ad-hoc OCEL write

set -euo pipefail

KYBER_APP="${KYBER_APP:-kyb3rerp}"
PROJECTOR_APP="${PROJECTOR_APP:-kyb3proj}"
TODAY="$(date -u +%Y-%m-%d)"
YEAR="$(date -u +%Y)"

say() { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }
ok()  { printf '  \033[1;32m✓\033[0m %s\n' "$*"; }

say "1. ERP → initApqcProjector (follow + apqcBootstrap record)"
gftd xrpc ai.gftd.apps.kyber.initApqcProjector \
  -d '{"scope":"all"}' \
  --app "$KYBER_APP"
ok "bootstrap dispatched"

say "2. Projector → listApqcActors (expect 13 L1 rows)"
gftd xrpc ai.gftd.kyber.projector.listApqcActors \
  --method GET -q 'limit=20' \
  --app "$PROJECTOR_APP"
ok "L1 actors listed"

say "3. Projector → listBpmnTasks (expect 28 bindings)"
gftd xrpc ai.gftd.kyber.projector.listBpmnTasks \
  --method GET -q 'limit=100' \
  --app "$PROJECTOR_APP"
ok "BPMN catalog listed"

say "4. ERP → createJournalEntry (reactive trigger)"
gftd xrpc ai.gftd.apps.kyber.createJournalEntry \
  -d "{\"date\":\"${TODAY}\",\"memo\":\"smoke: APQC projection test\",\"currency\":\"JPY\",\"lines\":[{\"account\":\"1000\",\"debit\":1000,\"credit\":0},{\"account\":\"4000\",\"debit\":0,\"credit\":1000}]}" \
  --app "$KYBER_APP"
ok "journal emitted → projector.onCommit(bpmn-9-journal-post)"

# Allow PDS fanout + subscribeRepos delivery
sleep 3

say "5. Projector → getApqcCoverage period=${YEAR}"
gftd xrpc ai.gftd.kyber.projector.getApqcCoverage \
  --method GET -q "period=${YEAR}-01-01/${YEAR}-12-31" \
  --app "$PROJECTOR_APP"
ok "coverage retrieved (byL1[9.0].ocelEvents should be >= 1)"

say "6. Projector → runBpmnTask(bpmn-11-risk-assess) non-reactive"
gftd xrpc ai.gftd.kyber.projector.runBpmnTask \
  -d '{"taskId":"bpmn-11-risk-assess","caseId":"smoke-001","input":{"inherentRisk":"medium","controlStrength":"high"}}' \
  --app "$PROJECTOR_APP"
ok "businessRuleTask executed + OCEL emitted"

say "7. Projector → emitApqcEvent (ad-hoc)"
gftd xrpc ai.gftd.kyber.projector.emitApqcEvent \
  -d '{"apqcCode":"12.0","eventType":"regulator.filed","caseId":"smoke-002","objects":[{"id":"filing-2026q1","type":"filing"}],"attributes":{"filingType":"quarterly","regulator":"FSA-JP"}}' \
  --app "$PROJECTOR_APP"
ok "ad-hoc OCEL event written"

say "smoke complete — verify in browser: https://kyber.etzhayyim.com/ → APQC / BPMN tab"
