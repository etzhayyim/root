# MoneyForward Replacement Cutover Runbook

Date: 2026-05-08

This runbook is the live verification path for ADR-0076 after the remaining
implementation landed.

## Preconditions

- `KOTOBA_URL` or `DATABASE_URL` is available to the operator.
- SpiffWorkflow engine host is deployed and `/readyz` returns ready.
- `pymagatama` image includes `pymagatama.spiff_moneyforward_worker`.
- MoneyForward exports for the dual-run period are stored in encrypted vault/B2
  and referenced by CID.

## Apply

```bash
cd 30-graph/graph-schema
DATABASE_URL="$KOTOBA_URL" pnpm db:migrate
DATABASE_URL="$KOTOBA_URL" pnpm db:gen
DATABASE_URL="$KOTOBA_URL" pnpm db:drift
```

Expected migration objects:

- `vertex_atrecord_seikyu_payment_received`
- `vertex_atrecord_seikyu_credit_note`
- `vertex_atrecord_seikyu_recurring_schedule`
- `vertex_atrecord_keiyaku_counterparty`
- `vertex_atrecord_keiyaku_signing_flow`
- `vertex_atrecord_keiyaku_amendment`
- `vertex_atrecord_keiyaku_obligation`
- `vertex_atrecord_kousuu_task`
- `vertex_atrecord_kousuu_project_cost`
- `vertex_atrecord_keihi_expense`
- `vertex_atrecord_jinji_employee`
- `vertex_atrecord_jinji_attendance`
- `vertex_atrecord_jinji_payroll_run`
- `vertex_kaikei_statutory_report`
- `vertex_kaikei_moneyforward_parity_run`
- `vertex_kaisya_saas_asset`
- `vertex_atrecord_jinji_year_end_adjustment`
- `vertex_atrecord_jinji_mynumber_vault_ref`

## Deploy Worker

```bash
kubectl apply -f 50-infra/k8s/moneyforward-ops-worker/deployment.yaml
kubectl -n mitama-udf rollout status deploy/moneyforward-ops-spiff-worker --timeout=120s
kubectl -n mitama-udf logs deploy/moneyforward-ops-spiff-worker --tail=80
```

Expected log contains task types such as:

```text
seikyu.issueInvoice
keiyaku.draftAgreement
kousuu.recordTimeEntry
keihi.approveExpense
jinji.completePayrollRun
kaikei.validateMoneyForwardParity
kaisya.registerSaasAsset
```

## Spiff Smoke

Start one instance per actor and verify `vertex_spiff_instance.status` reaches
`completed`:

```bash
kubectl -n mitama-udf port-forward svc/bpmn-engine-host 8080:80 &
curl -fsS -X POST http://localhost:8080/v1/instance \
  -H 'content-type: application/json' \
  -d '{"processId":"kousuu_create_project","variables":{"owner":"works","projectCode":"SMOKE","projectName":"Smoke","startDate":"2026-05-08"}}'
curl -fsS -X POST http://localhost:8080/v1/instance \
  -H 'content-type: application/json' \
  -d '{"processId":"kaisya_register_saas_asset","variables":{"owner":"works","provider":"box","assetType":"folder","externalId":"smoke","displayName":"Smoke"}}'
```

## Dual-Run Parity Gate

Run after every MoneyForward export period:

```bash
curl -fsS -X POST https://kaikei.etzhayyim.com/xrpc/com.etzhayyim.apps.kaikei.validateMoneyForwardParity \
  -H 'content-type: application/json' \
  -d '{"owner":"works","periodFrom":"2026-04-01","periodTo":"2026-04-30","mfExportCid":"bafy...","mfTotal":0}'
```

Cutover is blocked unless every owner/period returns `status="matched"` or the
delta has a documented manual adjustment row.

## Cutover Criteria

- All schema migrations applied and `db:drift` is clean.
- Spiff smoke for `seikyu`, `keiyaku`, `kousuu`, `keihi`, `jinji`, `kaikei`,
  and `kaisya` succeeds.
- `kaisya.etzhayyim.com/finance` renders invoice aging, contract, project burn,
  expense, payroll, statutory, parity, SaaS, year-end, and My Number sections.
- MoneyForward parity status is `matched` for Works, Japan, and Labo or an
  exception note is filed.
- Tax advisor signs off statutory reports.
- MoneyForward remains read-only until one closed accounting period passes.
