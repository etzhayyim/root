# MoneyForward Remaining Implementation Plan

Date: 2026-05-08

This is the implementation ledger for completing the MoneyForward replacement
surface after ADR-0076.

## Target Coverage

| MoneyForward module | Internal actor | Runtime surface |
|---|---|---|
| 会計 / 会計 Plus | kaikei | existing GL handlers + reporting MVs |
| 請求書 / 請求書 Plus | seikyu | Spiff task handlers + invoice aging view |
| 契約 | keiyaku | Spiff task handlers + active agreements view |
| 個別原価 | kousuu | Spiff task handlers + project burn view |
| 経費 / 債務支払 / ビジネスカード | keihi + kaikei | expense approval and AP derivation |
| 人事管理 / 勤怠 / 給与 / 年末調整 / 社会保険 / マイナンバー | jinji | T3 encrypted employee/payroll records |
| 固定資産 | kaikei | fixed asset table, depreciation task binding |
| 連結会計 | kaikei | owner_did multi-entity reporting + parity/statutory control ledger |
| Box / Admina | kaisya | SaaS asset inventory via `registerSaasAsset` |

## Runtime Boundary

- BPMN durable orchestration: SpiffWorkflow engine host (`vertex_spiff_*`).
- Task handlers: `kotodama.ingest.moneyforward_ops`.
- Legacy coexistence: `zeebe_worker_main.py` registers the same task types until
  Zeebe is fully retired.
- Cognitive coordination: LangGraph remains for `kaisya-member-assistant` and
  APQC materialization, not for transactional persistence.

## Delivery Checklist

- Schema: add remaining record tables for seikyu, keiyaku, kousuu, keihi, jinji.
- Lexicons: add Phase 3 keihi/jinji procedure and record contracts.
- BPMN: one single-service-task process per XRPC operation.
- Seed migration: register process definitions and lexicon bindings.
- Python handlers: implement read/write task functions idempotently.
- Spiff worker entrypoint: register all task types through `SpiffWorker`.
- Legacy worker registration: register task types in the shared pyzeebe worker.
- Control ledger: statutory report rows, MoneyForward dual-run parity rows,
  SaaS asset inventory rows, year-end adjustment hashes, and My Number vault refs.
