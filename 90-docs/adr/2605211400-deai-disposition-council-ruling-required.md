---
id: adr-2605211400-deai-disposition-council-ruling-required
title: "ADR-2605211400: deai disposition — Council Lv6+ ruling required (PII + research vs etzhayyim charter)"
status: proposed
doc_type: adr
topic: deai-disposition
authoritative: true
last_verified: 2026-05-21
authoritative_for:
  - deai.etzhayyim.com (vendor) → ? (etzhayyim move target | SPLIT | vendor confirmed) disposition
  - Council Lv6+ ruling agenda item
related:
  - adr-2605172000-etzhayyim-rw-free-substrate
  - adr-2605172400-etzhayyim-vendor-three-axis-split-rule
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605211335-tranche-f-session-closure-category-a-split
depends_on:
  - adr-2605172400-etzhayyim-vendor-three-axis-split-rule
  - adr-2605192100-etzhayyim-mission-charter
supersedes: []
superseded_by: []
---

# ADR-2605211400: deai disposition — Council Lv6+ ruling required

**Status**: proposed (awaiting Council Lv6+ ruling)
**Date**: 2026-05-21
**Deciders**: Bootstrap Council Lv6+ (per ADR-2605192100 Charter §1.2 + §1.13 referral)

# Context

`deai.etzhayyim.com` is a vendor project (etzhayyim/etzhayyim-root) that landed 2026-05-17 (post-Tranche-F catalog freeze). Its `kotodama.jsonld` declares `profile.operator = "etzhayyim"` but the project lives in vendor 60-apps, not etzhayyim/root.

The 2026-05-21 post-freeze 3-axis audit (vendor PR #1339 `tranche-f-post-freeze-7-actors-audit-2026-05-21`) flagged deai for **Council Lv6+ ruling** because the 3-axis OR-test verdict and the kotodama-declared operator contradict.

## Project shape

- **Primary purpose** (per vendor `CLAUDE.md`): Spirit-in-Physics 研究データ収集 frontend + 出会い・マッチングアプリ
- **Inputs**: Hume biometric scores, emotion assessments (Spirit Type: Hero / Sage / Lover / Caregiver), word-response reaction times, physiological JSON
- **Output**: Match recommendations + research dataset → `spirit-in-physics.com/api` (research SSoT)
- **Research basis**: Jun Kawasaki et al. "Spirit in Physics: Spirit as a Thermodynamic Information Quantity"
- **7 lexicons** at `vendor/00-contracts/lexicons/com/etzhayyim/apps/deai/`:
  - `startAssessment` / `submitResponse` / `getProfile` / `createCheckin` / `listMatches` / `sendMessage` / `listMessages`

## 3-axis verdict (per ADR-2605172400)

| Axis | Evaluation | Verdict |
|---|---|---|
| Liability | PII + research ethics liability. Hume biometric scoring requires IRB-equivalent oversight. Operator bears liability for participant safety (matching algorithm fairness, dating-app abuse vectors, regulatory privacy compliance). | **HIT** |
| Custody | Heavy PII (emotion data, biometric scores, Spirit Type assessment, message content). Data flows to external research SSoT (spirit-in-physics.com). | **HIT** |
| Settlement | Participation incentive (no fiat billing visible in current spec). | clean |

**Default verdict per ADR-2605172400 rules**: 2 of 3 HIT → vendor confirmed. The `operator: etzhayyim` declaration in kotodama.jsonld is **inconsistent with the default verdict** and triggers Council escalation.

# Decision

**No code-side disposition without Council Lv6+ ruling.**

This ADR is filed as `status: proposed` and remains so until the Bootstrap Council (per ADR-2605192300) issues a ruling on which of three dispositions applies. No scaffold mirror, no lexicon copy, no `60-apps/etzhayyim-project-deai/` creation in etzhayyim/root pending the ruling.

## Three possible dispositions

### Disposition A — Full move (etzhayyim assumes operator)

etzhayyim takes over as operator-of-record. Project moves to etzhayyim/root per public-malak (PR #226) / ransomwatch (PR #233) pattern. PII custody clearance requires:

1. Charter compatibility ruling: deai's research-data collection + matching-app surface is compatible with etzhayyim charter §1.13 (Wellbecoming + Eros 許容 per ADR-2605192100 + ADR-2605192400) AND §1.4 (非営利のみ / Donation 流入のみ — confirms no fiat billing vector).
2. PII handling under religious-corp framework: explicit informed-consent flow + IRB-equivalent ethics body + retention/erasure rights per GDPR Art 7 + Art 17 + JP 個人情報保護法 v2.
3. Data SSoT redirection: `spirit-in-physics.com/api` is either (a) re-homed under `did:web:etzhayyim.com` subdomain, or (b) kept third-party with explicit cross-border data-transfer consent UI.

**Implies**: vendor sunset of deai per Lane B (public-malak) / Lane E1 (open-jpn-mynumber) pattern.

### Disposition B — SPLIT (lexicons → etz, runtime → vendor)

Like dougaka SPLIT pattern (ADR-2605172400 C-group). Lexicons + spec land in etzhayyim as the open contract; PII handling stays vendor under Stripe/GDPR/IRB compliance regime. Kotodama `operator` field corrected to `etzhayyim.com`. etzhayyim references deai lexicons in catalog but does not run the actor.

**Implies**: lexicon copy to etzhayyim + vendor kotodama operator field correction. No runtime move.

### Disposition C — Vendor confirmed (correct the kotodama declaration)

Treat the `operator: etzhayyim` declaration as a misconfiguration. Apply default 3-axis verdict (2 HIT → vendor). Correct vendor kotodama to `operator: etzhayyim.com`. Add Tranche F per-actor classification entry locking deai to vendor.

**Implies**: vendor kotodama amendment + Tranche F entry. No etzhayyim-side artifact.

## Council questions to rule on

1. Is dating + matching service compatible with etzhayyim charter? (Eros 許容 §1.13 + Wellbecoming §1.0 vs addictive-design prohibition §2(g))
2. Can research data collection happen under religious-corp non-profit framework? (vs IRB requirement)
3. Is `spirit-in-physics.com` a third-party SSoT acceptable under Custody axis, or must it move to etzhayyim infra?
4. Does the project's per-participant data export include any commercial-purpose vector (data sale, ad targeting, premium tier) that would violate §1.4 (Donation 流入のみ + 広告排除)?
5. Which disposition (A / B / C) applies?

## Decision-rule reference

Per ADR-2605192100 Mission Charter:
- §1.4 (非営利のみ): only Donation inflow. No fiat-billed deai premium tier permissible.
- §1.13 (Wellbecoming + Eros 許容): dating-app surface conditional on charter §2(g) addictive-design prohibition compliance.
- §2(g) prohibited categories: addictive-design surface (which dating apps inherit by default). Requires explicit anti-addiction design audit.

Per ADR-2605172400 Re-judgment triggers:
- "Project takes on fiat billing" → re-judge as vendor
- "Project takes on PII custody" → re-judge as vendor (already hit)
- "Project's operator declaration changes" → file Council referral entry (this ADR)

# Consequences

## If Disposition A (full move)

- etzhayyim takes on PII handling + research-ethics liability
- IRB-equivalent ethics body needs constitutional definition
- spirit-in-physics.com data-flow disposition needs separate ADR
- Vendor sunset follows public-malak Phase 4 timeline

## If Disposition B (SPLIT)

- Vendor retains all PII handling + research-data forwarding
- etzhayyim catalog gains 7 lexicons (open spec)
- Kotodama `operator` field corrected to `etzhayyim.com`
- No runtime change

## If Disposition C (vendor confirmed)

- Kotodama `operator` field corrected to `etzhayyim.com`
- Add to vendor `tranche-f-vendor-confirmed-actors-closure-*` next bulk closure
- No etzhayyim-side artifact

## Default (no ruling within 30 days)

If Council does not rule by 2026-06-20, default to Disposition C (vendor confirmed, kotodama correction). This preserves vendor liability shielding and matches the 3-axis default verdict. The ruling can later upgrade to A or B if charter clarification lands.

# Alternatives Considered

## Alternative D — preemptive scaffold mirror

Land etzhayyim scaffold for deai as if Disposition A were chosen, marked AWAITING_COUNCIL. Rejected because:
- premature commitment to etzhayyim operator-of-record liability
- if Council rules B or C, the scaffold needs reverting
- the scaffold itself implies organizational claim that hasn't been ratified

## Alternative E — defer entirely (no ADR)

Don't file this ADR; let deai sit in vendor with mismatched kotodama declaration. Rejected because:
- the contradiction will surface again at next audit cycle
- Council has no visibility into pending dispositions without a referral document
- Tranche F closure (ADR-2605211335) needs a hanging-question pointer

# References

- ADR-2605172000 — etzhayyim RW-free substrate (Custody constraints)
- ADR-2605172400 — vendor 3-axis split rule (Re-judgment triggers)
- ADR-2605192100 — etzhayyim Mission Charter (§1.4 / §1.13 / §2(g))
- ADR-2605192300 — Bootstrap Council (Lv6+ ruling authority)
- ADR-2605192400 — Eros 許容 / Gore 禁止 (Wellbecoming boundary)
- ADR-2605211335 — Tranche F session closure (post-freeze audit)
- vendor PR #1339 — post-freeze 7-actor audit (verdict source)
- vendor `60-apps/etzhayyim-project-deai/CLAUDE.md` — project shape
- vendor `00-contracts/lexicons/com/etzhayyim/apps/deai/*.json` — 7 lexicons
- Bootstrap Council Seat 2-5 RFP closes 2026-06-19 (per `etzhayyim/root/COUNCIL-BOOTSTRAP-RFP.md`)
