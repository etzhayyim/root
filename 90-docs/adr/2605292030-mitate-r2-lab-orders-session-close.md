---
id: adr-2605292030-mitate-r2-lab-orders-session-close
title: "Session close — ADR-2605281950 mitate R2 general lab orders + iyashi phlebotomy R0 scaffold (allergy + blood test gap arc)"
status: active
doc_type: adr
topic: session-close
authoritative: true
last_verified: 2026-05-29
priority: 3.0
axis: session-record
weight: 0.20
priority_note: "Two-commit closure record for the 2026-05-28→29 single-question arc: gap question → R0 scaffold landed → session-close annotation. Pure retrospective; no constitutional decisions."
authoritative_for:
  - Session-close record for ADR-2605281950 R0 scaffold arc
  - Deferred-item list referencing the R1 / R2 / R3 prerequisites surfaced by the R0 scaffold
depends_on:
  - adr-2605281950-mitate-r2-general-lab-orders-and-iyashi-phlebotomy
related:
  - 90-docs/adr/2605281950-mitate-r2-general-lab-orders-and-iyashi-phlebotomy.md
supersedes: []
superseded_by: []
---

# ADR-2605292030: Session close — mitate R2 general lab orders + iyashi phlebotomy R0 scaffold arc

**Status**: active
**Date**: 2026-05-29
**Deciders**: Jun Kawasaki

# Context

Single-question session: 「アレルギー検査、血液検査の actor, agent は設計されている?」 (2026-05-28).

Audit answered the question in two parts:

1. **Already designed at R0** (per ADR-2605260115): specific IgE panel (`orderType=ige-panel-39` / `ige-panel-perennial-only`) + nasal-smear eosinophil cytology — both rhinitis-domain-scoped.
2. **Gap** (closed by ADR-2605281950 R0 scaffold): general blood / clinical-chemistry / urinalysis lab orders; religious-corp internal phlebotomy (iyashi R2+); per-order 要配慮個人情報 移管 consent receipt (APPI 第2条第3項 / GDPR Art. 9).

# Decision

Pure retrospective record (no constitutional decisions; ADR-2605281950 carries all the substantive content):

## D1 — Commit chain

| Commit | Scope |
|---|---|
| `4ff94642c` | R0 scaffold — ADR-2605281950 + 2 NEW lexicons (`mitate.diagnosticConsentReceipt` + `iyashi.phlebotomyAttestation`) + `mitate.diagnosticOrder` extension (+16 orderType / +18 conditionContext / +`orderRoutingTarget` enum) + 4 cell paths reserved with `(reserved)` markers + 1 `[[adrs]]` + 6 `[[modules]]` in deps.toml + mitate/iyashi lexicon README index bumps |
| `76b04ac30` (parallel session — kotoba arc) | Absorbed my `deps.toml` status_note update from `proposed` → `proposed-r0-landed` + the front-matter changes (status, `last_verified: 2026-05-29`) during that session's batched commit |
| `4eec496a8` | Session-close annotation — `R0 Landing Record` body section append on ADR-2605281950 (final alignment with HEAD front-matter state) |

## D2 — Hook-gate clearance

All 15 pre-commit hooks pass on the final tree state. One mid-commit fix was required: `validate-religious-corp-lexicons` initially failed on two AT Protocol Lexicon discipline violations in `phlebotomyAttestation.json`:

| Violation | Fix |
|---|---|
| `tubesCollected.items` was inline `type=object` | Extracted to `#tubeRecord` def; array now uses `{"type": "ref", "ref": "#tubeRecord"}` |
| `volumeMl` was `type=number` (float) | Renamed `volumeMlTenths` and converted to `type=integer` with implied units (5..200 representing 0.5..20.0 mL); avoids floating-point storage drift per spec |

## D3 — Registry audit (5 PR-gate axes all EXIT 0)

| Axis | State at session close |
|---|---|
| `deps.toml`-paths | 586/605 resolve + 19 accepted-reserved + 0 drift |
| docs.json freshness | 676 entries in sync |
| graph.jsonld freshness | 676 nodes in sync |
| docs+graph schemas | valid |
| kotodama manifests | 42/42 valid |

## D4 — Deferred items (each becomes its own R1+ ADR)

Cell activation is constitutionally gated on **Bootstrap Council Seat 2-5 RFP close 2026-06-19** (per ADR-2605192300). Until that date, only design / playbook work can land:

1. **R1 ADR** — `mitate_diagnostic_consent_orchestrator` cell activation + chigiri annual template review path (dry-run-only consent surface, no patient ordering). Prerequisites: Bootstrap Council Seat 2-5 RFP close + ADR-2605181100 envelope production deploy + ≥1 licensed MD on Council medical advisory + chigiri R1 active.
2. **R2 ADR** — `mitate_diagnostic_order_general` + `mitate_diagnostic_result_ingest` + `iyashi_internal_phlebotomy` cell activation; first 3 external clinical lab vendor allowlist entries (Council Lv6+ ≥3 + Charter Rider §2(a)-(h) scan per vendor); ≤200-patient pilot. Requires GB external lab vendor onboarding playbook landing first.
3. **R3 ADR** — Multi-clinic + in-clinic centrifuge + basic-chemistry analyzer at iyashi (reduce external lab dependence); cross-jurisdictional consent receipt translation matrix; up to ≤25,000 patient capacity.
4. **GB external lab vendor onboarding playbook** — operator-facing runbook for Charter Rider §2(a)-(h) per-vendor scan procedure (Council-independent; unblocks vendor due-diligence for R2 pilot).
5. **N1..N12 escalation** (out of R2/R3 scope) — Genetic / DTC / NIPT (N1/N2/N3) require Council Lv7+ unanimity; oncology markers (N4) require oncology-trained MD on Council; fertility (N5) requires musubi cross-doctrinal consult; STI (N6) requires chigiri data_privacy co-design; in-vivo skin prick (N11) requires iyashi acute_first_line R3-mature.

## D5 — Session-question resolution

The actor surface answering 「アレルギー検査、血液検査」 is:

- **mitate** — issues `diagnosticOrder` (licensed-MD attestor required at R2+); receives `diagnosticResult`; routes to `treatmentPlan` / Rx referral
- **iyashi R2+** — performs internal phlebotomy when `orderRoutingTarget=iyashi-internal`; emits `phlebotomyAttestation`
- **External clinical lab vendors** — Council-attested allowlist (GB §2 scan); paid via toritate from Public Fund Safe Council Lv6+ ≥4
- **chigiri** — owns the consent template registry; reviews annually
- **No new actor introduced**

# Consequences

**Positive**

- Single-session arc: gap question → R0 scaffold → session-close annotation in ~3 commits
- Project convention preserved (session-close ADR pattern matches ADR-2605281000 / 2605290000 / 2605290900)
- All R1/R2/R3 work-ahead is gated on Bootstrap Council Seat 2-5 ratification, not blocked by missing design

**Negative / costs**

- One mid-session lexicon-spec correction (inline-object + `type=number`); should be added to the `validate-religious-corp-lexicons` violation catalog so future lexicon authors hit it earlier (CI rather than commit time)
- `deps.toml` `status_note` was racing with a parallel session; commit `76b04ac30` absorbed my edit cleanly but the order-of-operations was not deterministic

# Alternatives Considered

**Alt-1: Skip a separate session-close ADR; rely on the R0 Landing Record body section in ADR-2605281950.** Rejected — project convention is to write a closure ADR for any multi-commit arc (cf. ADR-2605271100 / 2605271200 closure pattern, ADR-2605290000 / 2605290900 / 2605291700 today). Keeps the ADR index navigable.

**Alt-2: Bundle this session-close into ADR-2605281950 final commit.** Rejected for the same reason — body-section sprawl on a substantive R0 charter is less navigable than a small dedicated retrospective.

# References

- ADR-2605281950 (mitate R2 general lab orders R0 scaffold — substantive content; this session-close annotates it)
- ADR-2605260115 (allergic rhinitis perennial — IgE panel reference; pre-existing design)
- ADR-2605263000 (iyashi R0 — internal_phlebotomy cell added at R2 in ADR-2605281950)
- ADR-2605262700 (chigiri G14 — consent template stewardship + UPL boundary preserved)
- ADR-2605192300 (Bootstrap Council Seat 2-5 RFP — R1 activation gate)
- Commits `4ff94642c` + `76b04ac30` + `4eec496a8`
