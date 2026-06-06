# 助 (tasuke) — maturity

**Status**: R0 (design + offline generation) · **ADR**: 2606060900 · **Date**: 2026-06-05

## What is real (R0)

- **Ontology** `00-contracts/schemas/cybercrime-victim-support-ontology.kotoba.edn` with the closed
  structural vocab encoding G1 (fee `[0]`), G2 (`:support/role` no 代理), G3 (`:doc/authored-by`
  `[:member]`), G5 (`:referral/paid` `[false]`), G6 (PII-by-ref), G7 (no-server-key), G9 (draft).
- **6 lexicons** `com.etzhayyim.tasuke.*` (victimIntake / evidenceItem / policeReportDraft /
  platformRequest / recoveryPlan / supportCase).
- **5 cells** (coded state machines; `.solve()` raises at R0): intake_triage / evidence_preservation
  / police_report / platform_abuse / account_recovery.
- **Methods** (stdlib, runnable): `triage.py` (classify + severity + free windows + checklist +
  deadlines), `report_gen.py` (7 member-authored document generators), `evidence.py` (chain-of-
  custody sha256 + PII-by-reference), `analyze.py` (end-to-end, asserts ¥0).
- **Seed**: 5 `:representative` victim cases (one per major scam KIND) + 9 FREE public windows.
- **69 tests green** (12 triage + 7 evidence + 10 report_gen + 17 charter-invariants + 5 analyze +
  5 lexicons + 8 consistency + 13 cells; `./run_tests.sh`).
- **Registered** in INFRA_ACTORS + actor-profile-seed → `did:web:etzhayyim.com:actor:tasuke`
  (resolvable + searchable).

## What is NOT real yet (gated / deferred)

- **No live filing / sending / submission** — every cell `.solve()` raises; `:doc/published` is
  const false. Real 被害届 submission, bank/platform sending, account operations = Council Lv6+ +
  operator (G9).
- **Deterministic classification** — the scam-KIND classifier is keyword-based; Murakumo-only LLM
  refinement of classification + Japanese wording is R1 (G8).
- **`:representative` registry** — windows / 根拠法令 / 法定処理期間 need primary-source
  verification before any live use (G10).
- **No 代理 / no paid counsel ever** — these are not "deferred", they are permanent invariants
  (G2 / G5).

## Roadmap

| Phase | Scope | Gate |
|---|---|---|
| R0 (this) | ontology + lex + cells + methods + seed + tests; offline generation | ADR-2606060900 |
| R1 | live-but-gated intake over the member's own evidence; LLM refinement; registry → :authoritative; "bring this to the police" export | Future ADR + Council Lv6+ + operator |
| R2 | standing free service via toritsugi/kurashimori/tadori/kokoro; multi-jurisdiction registry; member-signed live submission (never 代理) | Future ADR + Council Lv6+ + operator |
