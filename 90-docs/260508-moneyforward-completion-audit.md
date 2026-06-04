# MoneyForward Replacement Completion Audit

Date: 2026-05-08

Objective: design and implement the remaining MoneyForward replacement coverage
for `kaisya`, `kyber`, and `apqc` assuming LangGraph Server and SpiffWorkflow.

## Success Criteria

- Every MoneyForward contracted module has a corresponding internal actor or
  explicit control ledger.
- Each new write/read surface has schema, lexicon, BPMN binding, Python handler,
  and worker registration where runtime execution is required.
- `kaisya` exposes a finance cockpit that reads the replacement state.
- APQC/Kyber continue to provide classification, BPMN catalog, and OCEL/process
  mining coverage instead of duplicating finance persistence.
- Verification exists without requiring live RisingWave credentials.

## Prompt-To-Artifact Checklist

| Requirement | Evidence |
|---|---|
| 会計 / 会計 Plus | Existing `kaikei` schema + handlers; added statutory/parity control in `moneyforward_ops.py` |
| 請求書 / 請求書 Plus | `seikyu.*` lexicons, BPMN, `issue_invoice`, `send_invoice`, `record_payment_received`, aging API |
| 経費 | `keihi.expense`, `submitExpense`, `approveExpense`, `vertex_atrecord_keihi_expense` |
| Box | `kaisya.registerSaasAsset` with `provider="box"` and `vertex_kaisya_saas_asset` |
| 債務支払 | Existing `kaikei.apBill`; keihi approval and kaikei AP derivation source type |
| 固定資産 | Existing `kaikei.fixedAsset`; statutory report control ledger covers fixed asset reports |
| 個別原価 | `kousuu.*` project/time/burn handlers and `view_kousuu_project_burn` |
| 連結会計 | owner_did multi-entity reporting + statutory/parity control ledger |
| ビジネスカード | Existing `kouza` aggregator and `kaikei.bankTransaction`; keihi expense/card reconciliation ledger |
| 人事管理 | `jinji.employee`, `upsertEmployee`, encrypted T3 employee table |
| 勤怠 | `jinji.recordAttendance`, `vertex_atrecord_jinji_attendance` |
| 給与 | `jinji.completePayrollRun`, encrypted payroll run table, kaikei source type |
| 年末調整 | `jinji.recordYearEndAdjustment`, declaration hash/artifact ledger |
| 社会保険 | Existing EPFO/ESIC kaikei payable handlers plus encrypted payroll aggregate |
| マイナンバー | `jinji.registerMynumberVaultRef`; vault ref encrypted, number not stored in RW |
| 契約 | `keiyaku.*` agreement/signing handlers and active agreements view |
| Admina | `kaisya.registerSaasAsset` with `provider="admina"` |
| MoneyForward dual-run cutover | `kaikei.validateMoneyForwardParity` + cutover runbook |
| LangGraph Server premise | Existing `kaisya-member-assistant` / APQC materializer; no transactional persistence moved into LangGraph |
| SpiffWorkflow premise | BPMN process defs use Spiff-compatible Zeebe taskDefinition extraction; `spiff_moneyforward_worker.py` registers all task types |

## Verification Evidence

- `pytest -q tests/test_moneyforward_ops_pure.py`: 6 passed.
- `python3 -m py_compile` for handlers, worker, tests: passed.
- Added lexicon JSON parse: passed.
- Added BPMN XML parse: passed.
- `30-graph/graph-schema`: `pnpm exec tsc --noEmit --pretty false`: passed.
- kaisya Svelte build: passed.
- `git diff --check`: passed.

## Live Gates Not Executed Here

The local Keychain does not contain `etzhayyim.risingwave/RW_DSN` (security exit
code 44), so live DB migration, Spiff instance smoke, and MoneyForward export
parity execution could not be run from this workspace. The required commands
and pass/fail criteria are captured in
`90-docs/260508-moneyforward-cutover-runbook.md`.
