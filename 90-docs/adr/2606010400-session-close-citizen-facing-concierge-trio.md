---
id: adr-2606010400-session-close-citizen-facing-concierge-trio
title: "ADR-2606010400: Session close — citizen-facing concierge trio (toritsugi + moushibumi + kurashimori) R0"
status: active
doc_type: adr
topic: session-close-citizen-facing-concierge-trio
authoritative: true
last_verified: 2026-06-01
priority: 5.0
axis: governance
weight: 0.50
priority_note: "Documentation-only session-closure ADR. Records the 2026-05-31/06-01 session that completed the citizen-facing concierge trio — toritsugi (government procedure) + moushibumi (democratic participation) + kurashimori (consumer protection) — committed as 7ba09ee60 and pushed in 3e9061a2e on branch feat/social-security-for-humanity. No new doctrine; pointer + verification record + the gap-audit verdict (disaster already covered by kazaori)."
authoritative_for:
  - the citizen-facing concierge trio deliverable list + verification state
  - the 2026-05-31 citizen-facing gap-audit verdict
depends_on:
  - "2605312030"
  - "2605312400"
  - "2605312500"
related:
  - adr-2605312130-session-close-toritsugi-government-procedure-concierge
  - adr-2605302130-himotoki-disclosure-request-tier-b-actor-r0
  - adr-2605301600-danjo-public-accountability-oversight-tier-b-actor-r0
  - adr-2605263200-kazaori-disaster-response-tier-b-actor-r0
supersedes: []
superseded_by: []
---

# ADR-2606010400: Session close — citizen-facing concierge trio (toritsugi + moushibumi + kurashimori) R0

**Status**: active
**Date**: 2026-06-01
**Deciders**: Jun Kawasaki

# Context

A run of sessions (2026-05-31 → 06-01) built out a **citizen-facing concierge
family** — actors that stand on the *citizen's* side of an institution, the
service-delivery counterpart to the repo's *passive* watchers (danjo) and
*right-of-access* filers (himotoki). This is the closure record for that family.

The family answers one founding question — *"etzhayyim で LINE のように
自治体・政府手続きを行ってくれる actor は?"* — and then generalizes it across the
three institutions a citizen must deal with: **government** (transact),
**state** (be heard), and **merchant** (be protected).

# Decision

Record the citizen-facing concierge trio as closed at R0, all on branch
`feat/social-security-for-humanity` (trio creation commit **7ba09ee60**, pushed
in **3e9061a2e**).

## The trio (all Tier-B, R0 scaffold, kotoba-EAVT-native, Murakumo-only)

| Actor | ADR | Axis | Critical gate |
|---|---|---|---|
| **取次 toritsugi** | 2605312030 | citizen ↔ **government** (住民票 / 給付 / 申請) | G5 行政書士法 / UPL (no advice + no 作成代理) |
| **申文 moushibumi** | 2605312400 | citizen → **state** (選挙情報 / 請願 / パブコメ) | G3 公職選挙法 + political-neutrality (no campaigning/GOTV; protects §1.12 / 1 SBT = 1 vote) |
| **暮らし守 kurashimori** | 2605312500 | citizen ↔ **merchant** (苦情 / 返金 / クーリングオフ) | G5 UPL/司法書士法/弁護士法 + G9 no claims-buying/no 取立 + G10 non-harassment |

### Shared design pattern (all three)

- **Coded target registry** (`*.procedure` / `*.participationTarget` /
  `*.remedyTarget`) — each entry holds 窓口/organ / channel / 根拠法令 / 様式 /
  期限, seeded `unverified-seed`, gated by G14 (no live action against an
  unverified/stale entry).
- **Member-self-action default (G15)** — guide + draft-assist + the member acts;
  代行 (agent-on-behalf) is the gated R3 exception (per-submission consent +
  行政書士法/司法書士法 clearance + Council Lv7+; structurally double-gated via
  `DAIKOU_R3_GATE_TX`).
- **7 import-raise Pregel cells** each (reuben/gad/naphtali) + per-cell README.
- **PII-encrypted (G6)** — content only in `com.etzhayyim.encrypted.*`
  DID-bound envelopes; moushibumi additionally treats political opinion as APPI
  §2 special-care; kurashimori's cooling-off output is `isLegalOpinion` const
  false (date-computation, never a legal opinion).
- **Two-layer machine enforcement** carried over from toritsugi: pytest
  invariants (toritsugi) + node guard (toritsugi); moushibumi/kurashimori ship
  with the schema-level invariants embedded (const fields + knownValues) and the
  religious-corp lexicon validator green.

## Gap-audit verdict (2026-05-31)

Three citizen-facing gaps were proposed; an Explore pass verified each against
the roster:

1. **Democratic participation (選挙/請願/パブコメ)** → **GAP** → built as moushibumi.
2. **Disaster/emergency citizen support (安否/避難/罹災証明/支援金)** →
   **COVERED** by **kazaori (風折, ADR-2605263200)**, whose civilian-coordination
   scope already routes the citizen-side procedures. **Not built** (no duplicate).
3. **Consumer protection (苦情/返金/クーリングオフ)** → **GAP** → built as kurashimori.

This honest "build 2 of 3, skip the covered one" is the substantive content of
the audit and is recorded here so a future session does not re-propose kazaori's
scope.

# Consequences

- **R0 complete for the trio.** toritsugi reached R0-exhaustion in a prior
  9-iteration loop (closed in ADR-2605312130); moushibumi + kurashimori are
  fresh R0 scaffolds (this session).
- **Verification state** (moushibumi + kurashimori): 13 new lexicons pass
  `validate-religious-corp-lexicons` (0 errors); `lexicon-primary-types` +
  `nsid-lexicon-exists` green; 14 cells (7+7) all import-raise with their
  actor's R0 message; deps.toml valid TOML; docs.json + graph.jsonld regenerated
  (720 entries/nodes); pre-commit + pre-push hooks passed.
- **Registry**: root CLAUDE.md status table (+2 rows; Tier-B count 27→30 — note a
  parallel session's **haraedo** also landed in this window, so the live count
  may read higher), ADR README (+2 rows), deps.toml (+2 `[[adrs]]` blocks).
- **R0 ceiling held** across the family: cells import-raise (no execution), no
  submission/dispatch, no plaintext PII, Murakumo-only, and the
  per-axis reserved-practice boundaries (行政書士法 / 公職選挙法 / 司法書士法・
  弁護士法) are structural, not merely documented.
- **Next maturity is R1-gated** on Council Lv6+ ≥3 ratification of each master
  ADR (post Bootstrap Council Seats 2-5 RFP close 2026-06-19). Deferred to R1+
  uniformly: kotoba KG-seed entries (node-local), fleet.toml cell placement
  (reuben undeployed), and any 代行 path.

# Alternatives Considered

- **Build a disaster citizen-concierge too** — rejected: the gap audit found
  kazaori (ADR-2605263200) already covers the citizen-coordination side; a 4th
  actor would duplicate scope. Recorded as COVERED instead.
- **Fold moushibumi + kurashimori into toritsugi** — rejected: each carries a
  distinct reserved-practice risk (公職選挙法 political-neutrality; 司法書士法 /
  claims-collection) that would contaminate toritsugi's clean 行政手続 boundary.
  Separate actors with their own G3/G9/G10 gates are safer.

# References

- ADR-2605312030 (toritsugi) · ADR-2605312400 (moushibumi) · ADR-2605312500 (kurashimori)
- ADR-2605312130 (toritsugi session-close — prior closure in the family)
- ADR-2605302130 (himotoki) · ADR-2605301600 (danjo) — the passive/right-of-access counterparts
- ADR-2605263200 (kazaori — the COVERED disaster gap)
- ADR-2605181100 (confidentiality) · ADR-2605262130 (kotoba) · ADR-2605215000 (Murakumo-only) · ADR-2605192100 §1.12
- Commits: 7ba09ee60 (trio creation), pushed 3e9061a2e (branch feat/social-security-for-humanity)
