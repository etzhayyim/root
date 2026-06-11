---
id: adr-2605312500-kurashimori-consumer-protection-concierge-tier-b-actor-r0
title: "ADR-2605312500: 暮らし守 (kurashimori) — citizen consumer-protection concierge (苦情 + 返金 + クーリングオフ) Tier-B actor (R0)"
status: proposed
doc_type: adr
topic: kurashimori-consumer-protection-concierge
authoritative: true
last_verified: 2026-05-31
priority: 5.0
axis: architecture
weight: 0.50
priority_note: ""
authoritative_for:
  - kurashimori-consumer-protection-concierge
depends_on:
  - "2605312030"
  - "2605302130"
  - "2605262700"
  - "2605263500"
  - "2605181100"
  - "2605262130"
  - "2605192100"
  - "2605192200"
  - "2605192300"
  - "2605215000"
related:
  - "2605312400"
  - "2605302000"
  - "2605263400"
supersedes: []
superseded_by: []
---

# ADR-2605312500: 暮らし守 (kurashimori) — citizen consumer-protection concierge (R0)

**Status**: proposed
**Date**: 2026-05-31
**Deciders**: Jun Kawasaki

# Context

toritsugi (ADR-2605312030) covers citizen↔**government** procedures; moushibumi
(ADR-2605312400) covers citizen→**state** participation. A third citizen-facing
gap remains: citizen↔**merchant** disputes — the 国民生活センター /
消費生活センター role. No actor covers it:

- **himotoki (繙き, ADR-2605302130)** files **disclosure** requests (own data),
  not consumer complaints / refunds.
- **chigiri (契, ADR-2605262700)** is the UPL-bound procedure/template substrate
  (government procedure + dispute *mediation mechanics*), not a consumer advocate.
- **toritate / toritsugi / warifu** are accounting / gov-procedure / payments.

So a member facing **unfair billing, fraud, a defective product, or a
high-pressure 訪問販売 contract** has no concierge to help with **苦情
(complaint), 返金 (refund), or クーリングオフ (cooling-off withdrawal)**. This
ADR creates one: **暮らし守 (kurashimori)**.

> **暮らし守** = "guardian of everyday life." The name parallels shidemori
> (死出守, memorial guardian) and frames the actor as protecting the member's
> ordinary consumer life. Provisional; Council may rename.

The sharp risk is the same UPL boundary as toritsugi/chigiri **plus** the
specific Japanese consumer-law reserve: 適格消費者団体 (qualified consumer org)
status and 司法書士法/弁護士法 reserves on representation. kurashimori is a
**self-help + drafting-assist concierge**, never a representative advocate or a
claims-collection business.

# Decision

Create **暮らし守 kurashimori** at `did:web:kurashimori.etzhayyim.com`
(`20-actors/kurashimori/`), kotoba-EAVT-native (ADR-2605262130; no Kotoba/Datomic),
Murakumo-only (ADR-2605215000), atproto/MST-native, mirroring the toritsugi
pattern (coded registry + member-self-action default + gated 代行).

## §1 Scope

Three citizen↔merchant self-help channels, member-initiated + consent-bound:

1. **クーリングオフ (cooling-off)** — detect whether a contract is within a
   statutory cooling-off window (特定商取引法 — 訪問販売 8日 / 連鎖販売 20日
   等), assist drafting the 書面 (or 電子) 通知, the **member sends** (or gated
   代行). The cleanest, most deterministic channel.
2. **返金 / 苦情 (refund / complaint)** — assist drafting a complaint / refund
   demand to the merchant; track the merchant's response; on stall, route to the
   appropriate **public** channel (消費生活センター / 消費者ホットライン 188).
3. **エスカレーション routing** — when self-help stalls, route the member to the
   lawful external forum: 消費生活センター, ADR (指定紛争解決機関), or — for
   legal characterization / representation — **chigiri + licensed counsel**.
   kurashimori never represents the member before a tribunal.

Default = **診断 + 起草補助 + 本人送付**; **代行 (本人同意ベース)** is the gated
R3 exception. JP-first; jurisdiction-generic.

## §2 Coded remedy registry

Each remedy/route is an `com.etzhayyim.kurashimori.remedyTarget` record holding
the **remedy kind / 根拠法令 / statutory window (日数) / required 書面 form /
delivery channel (内容証明 / 電子 / portal) / escalation forum**. Seed at
`registry/targets.seed.json` (5 entries, all `unverified-seed`): 訪問販売
クーリングオフ (特商法) · 通信販売 返品特約 · 連鎖販売 クーリングオフ ·
消費生活センター / 188 escalation template · 適格消費者団体 / ADR escalation
template. G14 verification gate identical to toritsugi.

## §3 Cells (7 Pregel cells, R0 path-reserved; import-time RuntimeError)

| Cell | Node | Phase | I/O |
|---|---|---|---|
| `kurashimori_remedy_registry` | reuben | continuous | maintain + resolve the coded `remedyTarget` catalog; enforce G14 |
| `kurashimori_intake` | reuben | event | member consent + DID/SBT + the consumer matter (OWN) → `complaintSession` |
| `kurashimori_cooloff_check` | reuben | event | contract date + type → cooling-off eligibility (`coolingOffAssessment`; INFORMATIONAL, not legal advice — G5) |
| `kurashimori_compose` | gad | event | pull chigiri template + remedy → drafted 通知/苦情 (`remedyDraft`; drafting-assist, G5) |
| `kurashimori_send` | naphtali | event | **only active-outbound** — default hands draft back for member self-send; 代行 only under G14+G15+R3 → `dispatchRecord` |
| `kurashimori_status_track` | naphtali | continuous | merchant response / refund / window-expiry clock; stall → escalation route |
| `kurashimori_escalation` | gad | event | self-help stalled → route to 消費生活センター / ADR / chigiri+counsel (`escalationReferral`) |

## §4 Constitutional gates (G1–G15, immutable; Council Lv6+ + new ADR to amend)

- **G1** Charter Rider §2(a)–(h) scan on every authored artifact + outbound action.
- **G2** kotoba attestation lineage on every record (EAVT; no RW).
- **G3** **Consent-gated + own-matter-only** — every complaint/cooling-off is
  member-initiated with consent + Adherent-SBT/DID binding and concerns the
  **member's own** consumer matter; never on behalf of a non-consenting person;
  never a third party's matter.
- **G4** **Transparent + non-pretextual** — the member is the named complainant;
  no impersonation; kurashimori identifies itself as an *unofficial* assistant,
  never as 消費生活センター or a public body.
- **G5** **UPL / 司法書士法 / 弁護士法 boundary (CRITICAL)** — self-help
  diagnosis + drafting-assist + 案内 only; renders **no legal advice**, performs
  **no representation** (代理), and makes **no legal determination** of rights;
  legal characterization + representation route to **chigiri + licensed
  counsel**; the cooling-off "eligibility" output is an informational date
  computation, explicitly NOT a legal opinion.
- **G6** **PII confidentiality** — member PII + contract/complaint content land
  ONLY in `com.etzhayyim.encrypted.*` DID-bound envelopes (ADR-2605181100);
  never plaintext on MST.
- **G7** Murakumo-only inference (ADR-2605215000).
- **G8** **Non-fabrication** — never invent a 根拠法令 / 日数 / 様式; every
  remedy cites 根拠法令 + `provenance`; the member confirms before any send.
- **G9** **No commercialization / no claims-buying** — non-profit; no
  contingency fee; no purchase or assignment of the member's claim; no
  debt/claims-collection business; no resale of complaint data (Charter Rider §2(e)).
- **G10** **Lawful-channel-only + non-harassment** — the only external action is
  a lawful, proportionate communication to the merchant through a legitimate
  channel with member authorization; never threats / harassment / 威迫;
  cooling-off and demands use lawful means only.
- **G11** **Transparent Religious Force discipline** (§1.12) — assist + send +
  track + escalate only; no coercion / extra-legal pressure; escalation via
  lawful public fora.
- **G12** **Scope / data-minimization** — collect only what the specific matter
  requires.
- **G13** `stateAlignedFlag` pass-through into derived records.
- **G14** **Verified-remedy-only send** — `kurashimori_send` refuses any remedy
  whose `verificationStatus` is `unverified-seed` or stale (statutory windows
  drift; a wrong 日数 is harmful).
- **G15** **Member-self-action default** — the member sends/withdraws by default;
  代行 active-outbound is the gated R3 exception (per-submission consent +
  司法書士法/行政書士法 clearance + Council Lv7+).

## §5 Non-goals (N1–N13)

N1 NOT a 弁護士/司法書士 firm or representative advocate (drafting-assist only;
representation → chigiri + licensed) · N2 NOT a claims-collection / debt-
collection / 取立 business · N3 NOT a contingency-fee or claims-buying operation
· N4 NOT a 適格消費者団体 substitute (no group/class representation) · N5 NOT a
harassment / 威迫 / pressure tool against merchants · N6 NOT a replacement for
the member's own right (assists, does not supplant) · N7 NOT a merchant-
blacklist / review-bombing / reputation-attack system · N8 NOT a data-broker of
complaint or contract data · N9 NOT a pretext / impersonation tool · N10 NOT an
official 消費生活センター (unofficial assistant) · N11 NOT a plaintext-PII store
· N12 NOT Japan-exclusive (JP-first R0) · N13 NOT a legal-opinion / rights-
determination engine (informational date-computation only).

## §6 Lexicons (7, `com.etzhayyim.kurashimori.*`)

`remedyTarget` (coded remedy/route registry; `verificationStatus`) ·
`complaintSession` (member-facing session) · `coolingOffAssessment` (informational
window computation; `isLegalOpinion` const false) · `remedyDraft` (drafted
通知/苦情; `assistMode` = `drafting-assist` only) · `dispatchRecord`
(`member-self-send` | `agent-on-behalf` gated) · `statusTrack` (merchant response
+ refund + window clock) · `escalationReferral` (route to 消費生活センター / ADR /
chigiri+counsel).

## §7 Cross-actor boundaries

- **chigiri (ADR-2605262700)**: chigiri = legal characterization + 作成代理 +
  representation + ADR/dispute procedure (UPL); kurashimori pulls templates +
  escalates to chigiri, renders no advice.
- **himotoki (ADR-2605302130)**: sibling — himotoki files 開示請求 (data out);
  kurashimori files 苦情/通知 (consumer remedy). Shared dispatch discipline.
- **toritsugi (ADR-2605312030) / moushibumi (ADR-2605312400)**: sibling citizen-
  facing concierges (government procedure / democratic participation); same
  registry + G15 self-action pattern.
- **wakai (和会, ADR-2605263500)**: if a member's consumer loss is irrecoverable,
  the mutual-aid pool (NOT insurance) may be the member's relief path — kurashimori
  routes, wakai absorbs (its own gates).
- **warifu (割符, ADR-2605302000)**: a disputed card charge may have a warifu-side
  chargeback/refund path; kurashimori coordinates the consumer-side demand.
- **`com.etzhayyim.encrypted.*` (ADR-2605181100)**: only home for member PII +
  contract/complaint content.
- **kotoba EAVT (ADR-2605262130)**: registry + session/draft/dispatch lifecycle
  datoms; no Kotoba/Datomic.

## §8 Roadmap

- **R0 (this ADR)** — scaffold: ADR + actor dir + 7 lexicon skeletons + remedy
  seed (5, all `unverified-seed`) + 7 import-raise cells + registry rows. No
  send, no live diagnosis.
- **R1** (Council Lv6+ ≥3) — registry + intake + cooloff_check + compose build
  artifacts; 診断 + 起草補助 only.
- **R2** (+30-day public comment) — member **self-sends**; status_track +
  escalation live.
- **R3** (+Council Lv7+ + 司法書士法/行政書士法 clearance) — gated 代行 send.

# Consequences

- **Positive**: closes the consumer-protection gap with the proven toritsugi
  pattern; the UPL / 司法書士法 / claims-collection risks are structurally
  contained (G5 no-advice/no-representation, G9 no claims-buying/no-contingency,
  G10 non-harassment, cooling-off output is date-computation not legal opinion,
  代行 gated).
- **Negative / honest limits**: statutory cooling-off windows + return-policy law
  drift and vary by transaction type; a wrong 日数 is harmful, so G14 + G8 are
  load-bearing and the seed is best-effort (`unverified-seed`). The line between
  "informational eligibility" and "legal advice" is a content discipline as much
  as a schema one (`isLegalOpinion` const false anchors it).
- **Constitutional**: no invariant amended. Non-profit / Murakumo-only / kotoba-
  native / encrypted-PII / no-platform-key all hold.

# Alternatives Considered

- **Fold into toritsugi** — rejected: consumer↔merchant disputes carry distinct
  司法書士法/claims-collection/harassment risks foreign to toritsugi's gov-
  procedure boundary. A separate actor with G9/G10 is safer.
- **Allow contingency-fee or claims-buying** — rejected outright: incompatible
  with non-profit + 弁護士法 §72/債権回収 reserves. Hence G9/N2/N3.
- **Represent the member in ADR/court** — rejected: representation is a licensed
  reserve; kurashimori escalates to chigiri + counsel instead (G5/N1).
- **Diagnosis-only, never send** — considered; rejected as too thin: self-send is
  the floor, 代行 the gated ceiling.

# References

- This ADR: `/90-docs/adr/2605312500-kurashimori-consumer-protection-concierge-tier-b-actor-r0.md`
- Actor: `/20-actors/kurashimori/` · Lexicons: `/00-contracts/lexicons/com/etzhayyim/kurashimori/`
- ADR-2605312030 (toritsugi — sibling pattern) · ADR-2605312400 (moushibumi — sibling) · ADR-2605302130 (himotoki)
- ADR-2605262700 (chigiri — escalation + UPL) · ADR-2605263500 (wakai — mutual-aid relief) · ADR-2605302000 (warifu — chargeback coordination)
- ADR-2605181100 (confidentiality) · ADR-2605262130 (kotoba) · ADR-2605192100 §1.12 · ADR-2605192200 (Charter Rider) · ADR-2605192300 (Council) · ADR-2605215000 (Murakumo-only)
