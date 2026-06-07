---
id: adr-2605312130-session-close-toritsugi-government-procedure-concierge
title: "ADR-2605312130: Session close — 取次 (toritsugi) citizen-facing government-procedure concierge R0 + 9-iteration maturity loop (2026-05-31)"
status: active
doc_type: adr
topic: session-close-toritsugi-government-procedure-concierge
authoritative: true
last_verified: 2026-05-31
priority: 5.0
axis: governance
weight: 0.50
priority_note: "Documentation-only session-closure ADR. Records the 2026-05-31 session that created Tier-B actor 取次 (toritsugi) — the citizen-facing government-procedure concierge answering the 'LINE で自治体・政府手続き' audit — and matured it through a 9-iteration 30-min /loop, committed as fa3dee231 on branch feat/social-security-for-humanity. No new doctrine beyond ADR-2605312030; pointer + verification record only."
authoritative_for:
  - the 2026-05-31 toritsugi session deliverable list + verification state
  - commit fa3dee231 provenance
depends_on:
  - ADR-2605312030 (toritsugi master)
related:
  - adr-2605312030-toritsugi-government-procedure-concierge-tier-b-actor-r0
  - adr-2605302130-himotoki-disclosure-request-tier-b-actor-r0
  - adr-2605262700-chigiri-legal-procedure-tier-b-actor-r0
  - adr-2605262900-toritate-accounting-audit-tier-b-actor-r0
  - adr-2605301600-danjo-public-accountability-oversight-tier-b-actor-r0
  - adr-2605302357-etzhayyim-social-security-for-humanity
supersedes: []
superseded_by: []
---

# ADR-2605312130: Session close — 取次 (toritsugi) government-procedure concierge R0 + 9-iteration maturity loop

**Status**: active
**Date**: 2026-05-31
**Deciders**: Jun Kawasaki

# Context

The 2026-05-31 session answered the audit *"etzhayyim で LINE のように自治体や
政府手続きを行ってくれる actor は設計されているか?(atproto ベースで)"*. The
finding: **no citizen-facing government-procedure concierge existed** — every
government-touching actor faces the *state*, not the *citizen* (danjo watches,
himotoki files disclosure requests, chigiri is the UPL-bound legal-procedure
substrate, gov-municipality is project-level permits, the §1.16 ubusuna
pipeline delivers etzhayyim's *own* social security). This session created the
missing actor — **取次 (toritsugi)** — under ADR-2605312030, then matured it
through a self-paced `/loop` (30-min cadence, 9 iterations) until R0 was
exhausted.

This is a **documentation-only session-closure ADR**: it records the
deliverable list, the iteration log, the verification state, and what is
honestly deferred to R1+. No new doctrine beyond the master ADR-2605312030.

# Decision

Record the session as closed with the following committed deliverable
(commit **fa3dee231**, branch `feat/social-security-for-humanity`, 36 files,
+2,500/-2).

## Deliverables (init + 9 maturity-loop iterations)

- **Master ADR-2605312030** — 取次 toritsugi, `did:web:toritsugi.etzhayyim.com`,
  Tier-B, R0 scaffold. Service-delivery counterpart to danjo (watches) and
  himotoki (right of access). Scope: default 案内+伴走+本人提出支援 (member
  self-submits, 行政書士法-safe); gated R3 本人同意ベース提出代行 (Council Lv7+ +
  行政書士法 clearance, OFF at R0). 15 gates G1..G15, 14 non-goals.
- **Actor dir** `20-actors/toritsugi/` — manifest.jsonld + README + CLAUDE.md +
  MATURITY ledger + registry/{procedures.seed.json, VERIFICATION.md, SCALING.md}.
- **6 Lexicons** `com.etzhayyim.toritsugi.*` (procedure / benefitMatch /
  procedureGuide / applicationDraft / submissionRecord / statusTrack).
- **7 path-reserved Pregel cells** `kotodama.cells.toritsugi_*` (import-raise)
  + per-cell READMEs (tsukuroi parity).
- **Bidirectional cross-actor boundary** added to chigiri / himotoki / toritate
  manifests (toritsugi side was authored in the master ADR).
- **Two-layer machine enforcement**: pytest invariants
  (`70-tools/scripts/audit/test_toritsugi_invariants.py`, 10 tests) + node
  standalone guard (`70-tools/scripts/lint/toritsugi-procedure-gates.mjs`,
  6 checks).
- **Two operational docs**: `VERIFICATION.md` (G14 tiering workflow, 10-point
  per-field checklist) + `SCALING.md` (1,741-自治体 two-tier template/binding
  curation plan, demand-driven, ぴったりサービス pivot).
- **Registry rows**: root CLAUDE.md status table, ADR README, deps.toml.

## Iteration log (maturity ledger — `20-actors/toritsugi/MATURITY.md`)

| iter | item | result |
|---|---|---|
| init | ADR + manifest + 6 lexicons + seed + registry rows | ✅ |
| 1 | 7 cell scaffold (import-RuntimeError) | ✅ |
| 2 | pytest invariants test (→10 cases) | ✅ |
| 3 | bidirectional cross-actor boundary (chigiri/himotoki/toritate) | ✅ |
| 4 | per-cell READMEs (#13); #11 KG-seed found node-local → deferred | ✅ / 🚫 |
| 5 | node guard `toritsugi-procedure-gates.mjs` (6 checks) | ✅ |
| 6 | lexicon validator green pinned (id↔namespace test 3b) | ✅ |
| 7 | procedure seed audit + VERIFICATION.md (G14 workflow) | ✅ |
| 8 | #14 fleet.toml found premature (reuben undeployed) → R1 deferred | 🚫 |
| 9 | SCALING.md (1,741-自治体 two-tier plan) | ✅ |

# Consequences

- **R0 complete.** 12 of 15 maturity items ✅; 3 honestly deferred:
  - **#11 kotoba KG seed** — the SoT (`kg-seed-v1.ndjson`) is a node-local,
    git-external artifact (ADR-2605301030); not committable here.
  - **#14 fleet.toml cell placement** — R1-premature: `reuben` (the cells'
    proposed node) is undeployed, and no R0 Tier-B actor has cells in
    fleet.toml yet (only the 15 live governance cells). R1 will remap
    reuben → a deployed tribe (asher failover is the overflow candidate).
  - **municipalBinding lexicon** (from SCALING.md) — R2+; creating it now ships
    an unused schema.
- **Verification state**: `python3 -m pytest test_toritsugi_invariants.py` →
  10 passed; `node toritsugi-procedure-gates.mjs` → clean; pre-commit lefthook
  (incl. `validate-religious-corp-lexicons`) → all pass. One validator catch
  during commit (`procedureGuide.checklist.items` inline object) was fixed to a
  `#checklistEntry` def-ref per the danjo/maps convention before landing.
- **R0 constitutional ceiling held throughout**: cells import-raise (no
  execution), no submission/dispatch, no plaintext PII (G6), Murakumo-only
  (G7), 行政書士法/UPL boundary (G5), G14 verified-procedure-only, G15
  member-self-submission default (代行 structurally double-gated via
  `DAIKOU_R3_GATE_TX`).
- **Next maturity is R1-gated** on Council Lv6+ ≥3 ratification of
  ADR-2605312030 (post Bootstrap Council Seats 2-5 RFP close 2026-06-19). The
  self-paced `/loop` was stopped at session close (no remaining R0-committable
  work).

# Alternatives Considered

- **Keep the loop running past R0 exhaustion** — rejected: every remaining item
  is R1-gated; continuing would only risk over-implementation (unused schemas,
  premature infra edits). Stopped the loop instead.
- **Commit the deferred items as scaffolds anyway** — rejected: would put
  import-unreachable fleet config / unused lexicons / node-local data into the
  tree, violating the R0 ceiling and the "no over-implementation" discipline.

# References

- ADR-2605312030 (取次 toritsugi master)
- `20-actors/toritsugi/MATURITY.md` — full 9-iteration ledger
- `20-actors/toritsugi/registry/VERIFICATION.md` · `SCALING.md`
- ADR-2605302130 (himotoki) · ADR-2605262700 (chigiri) · ADR-2605262900 (toritate) · ADR-2605301600 (danjo)
- Commit: fa3dee231 (branch `feat/social-security-for-humanity`)
