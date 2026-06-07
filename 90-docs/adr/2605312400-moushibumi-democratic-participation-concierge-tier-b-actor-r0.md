---
id: adr-2605312400-moushibumi-democratic-participation-concierge-tier-b-actor-r0
title: "ADR-2605312400: 申文 (moushibumi) — citizen democratic-participation concierge (election info + 請願 + パブリックコメント) Tier-B actor (R0)"
status: proposed
doc_type: adr
topic: moushibumi-democratic-participation-concierge
authoritative: true
last_verified: 2026-05-31
priority: 5.0
axis: architecture
weight: 0.50
priority_note: ""
authoritative_for:
  - moushibumi-democratic-participation-concierge
depends_on:
  - "2605312030"
  - "2605262700"
  - "2605302130"
  - "2605181100"
  - "2605262130"
  - "2605192100"
  - "2605192200"
  - "2605192300"
  - "2605215000"
related:
  - "2605301600"
  - "2605302130"
  - "2605192315"
supersedes: []
superseded_by: []
---

# ADR-2605312400: 申文 (moushibumi) — citizen democratic-participation concierge (R0)

**Status**: proposed
**Date**: 2026-05-31
**Deciders**: Jun Kawasaki

# Context

The toritsugi audit (ADR-2605312030) closed the citizen-facing **government-
procedure** gap (住民票 / 給付 / 申請). A sibling gap remains: **democratic
participation** — helping a citizen *be heard by* and *participate in* the
organs of the state, as opposed to merely transacting with them. No actor
covers it:

- **danjo (弾正, ADR-2605301600)** *watches* the state (国会会議録 / 予算 /
  調達); passive oversight, never citizen-facing.
- **himotoki (繙き, ADR-2605302130)** files **disclosure** requests (DSAR/FOIA);
  pulls data out, does not convey the citizen's voice in.
- **toritsugi (取次, ADR-2605312030)** runs **administrative procedures**;
  explicitly NOT election / 請願 / パブリックコメント (its N-list defers them).

So the three channels by which a citizen feeds their voice *into* governance —
**informed voting**, **petition (請願 / 陳情)**, and **public comment
(パブリックコメント / 意見公募手続)** — have no concierge. This ADR creates one:
**申文 (moushibumi)**.

> **申文** = a Heian-era formal written submission of one's case/request *to
> authority*. The name deliberately parallels danjo (弾正台, the Heian
> censorate): danjo is the state-watching *eye*, moushibumi is the citizen's
> *voice* submitted upward. Provisional; Council may rename.

The sharp constitutional risk here is **公職選挙法 (Public Offices Election
Act) + political neutrality**. A religious body that steers votes becomes a
political machine — flatly incompatible with the §1.12 Transparent Religious
Force discipline (1 SBT = 1 vote, no coercion) and with the anti-individualist,
non-partisan covenant. moushibumi therefore handles **information + procedure
only**, never campaigning, endorsement, or vote solicitation.

# Decision

Create **申文 moushibumi** as a Tier-B actor at
`did:web:moushibumi.etzhayyim.com` (`20-actors/moushibumi/`), kotoba-EAVT-native
(ADR-2605262130; no Kotoba/Datomic), Murakumo-only inference (ADR-2605215000),
atproto/MST-native for member-facing channels. It mirrors the toritsugi pattern
(coded target registry + member-self-submission default + gated 代行).

## §1 Scope

Three citizen→state participation channels, each member-initiated + consent-bound:

1. **選挙情報 (informed participation, INFO-ONLY)** — when/where to vote, the
   mechanics of 期日前投票 / 不在者投票, neutral candidate/issue *reference*
   (official 選挙公報 pointers only). **Never** campaigning, endorsement,
   ranking, GOTV targeting, or vote solicitation (G3 political neutrality).
2. **請願 / 陳情 (petition)** — assist drafting a 請願書 (請願法) / 陳情 to a
   議会 (Diet / 地方議会), with a 紹介議員 pointer where 請願法 requires one;
   the **member submits** (or gated 代行).
3. **パブリックコメント (public comment, 行政手続法 §39 意見公募手続)** — assist
   drafting + submitting an opinion on a 命令等 proposal during its comment
   window.

Default mode = **案内 + 起草補助 + 本人提出**; **代行 (本人同意ベース)** is the
gated R3 exception (parallels toritsugi G15). JP-first; jurisdiction-generic.

## §2 Coded participation-target registry

Analogue of toritsugi's procedure registry. Each target is an
`com.etzhayyim.moushibumi.participationTarget` record holding the **organ
(議会 / 行政機関 / 選管) / channel (窓口 / portal / 郵送) / 根拠法令 / 提出様式 /
期限 (comment window / 会期) / 紹介議員-required flag** so a cell can route +
(eventually) file procedurally. Seed at `registry/targets.seed.json` (5 entries,
all `unverified-seed`): 国会 請願 (衆/参) · 地方議会 陳情 template · 国 パブコメ
(e-Gov 意見募集) · 自治体 パブコメ template · 選挙情報 (総務省/選管) template.
G14 verification gate identical to toritsugi: no live submission against an
`unverified-seed` / stale target.

## §3 Cells (7 Pregel cells, R0 path-reserved; import-time RuntimeError)

| Cell | Node | Phase | I/O |
|---|---|---|---|
| `moushibumi_target_registry` | reuben | continuous | maintain + resolve the coded `participationTarget` catalog; enforce G14 |
| `moushibumi_voter_info` | reuben | continuous | NEUTRAL election-mechanics info (dates / 期日前 / official 選挙公報 pointers); G3 no partisanship |
| `moushibumi_opportunity_match` | reuben | event | consenting member's interest/locale (OWN) → `participationMatch` ("a comment window / petition route is open") — neutral, aggregate |
| `moushibumi_intake` | gad | event | member consent + DID/SBT → `participationSession` |
| `moushibumi_compose` | gad | event | pull chigiri template + target → drafted 請願書 / 意見 (`voiceDraft`; G5 drafting-assist, no legal advice) |
| `moushibumi_submit` | naphtali | event | **only active-outbound** — default hands draft back for member self-submit; 代行 only under G14+G15+R3 → `submissionRecord` |
| `moushibumi_status_track` | naphtali | continuous | petition/comment receipt + 議会 採択/不採択 + agency 考え方 公示 tracking |

## §4 Constitutional gates (G1–G15, immutable; Council Lv6+ + new ADR to amend)

- **G1** Charter Rider §2(a)–(h) scan on every authored artifact + outbound action.
- **G2** kotoba attestation lineage on every record (EAVT; no RW).
- **G3** **公職選挙法 + political-neutrality boundary (CRITICAL)** — INFO +
  procedure ONLY. **No** campaigning / canvassing (§138 戸別訪問) / candidate or
  party endorsement / ranking / scoring / vote solicitation / GOTV targeting /
  partisan steering. The religious-corp never directs votes; election content is
  neutral reference to official sources only. (Protects §1.12 / 1 SBT = 1 vote.)
- **G4** **Consent-gated + own-voice-only** — every petition/comment is member-
  initiated with consent + Adherent-SBT/DID binding and is the **member's own**
  voice; never files on behalf of a non-consenting person; never a third party's.
- **G5** **行政書士法 / UPL-equivalent** — drafting-assist + 案内 only; renders
  **no legal advice**; legal characterization + appeal route to **chigiri +
  licensed counsel**.
- **G6** **PII confidentiality** — member PII / political-opinion content (a
  special-care category under APPI §2) lands ONLY in `com.etzhayyim.encrypted.*`
  DID-bound envelopes (ADR-2605181100); never plaintext on MST. Political-belief
  data is collected only with explicit consent and the minimum necessary.
- **G7** Murakumo-only inference (ADR-2605215000).
- **G8** **Non-fabrication** — never invent a 期限 / 様式 / 根拠法令 / 紹介議員
  requirement; every target cites 根拠法令 + `provenance`; the member confirms
  before any submission.
- **G9** **Non-partisan + non-commercial** — non-profit; no paid lobbying / no
  lobbying-for-hire; no resale of participation or member-opinion data;
  organisationally non-partisan (no party affiliation, donation, or PAC).
- **G10** **Lawful-channel-only** — the only external mutation is a lawful
  submission through an official channel with member authorization.
- **G11** **Transparent Religious Force discipline** (§1.12) — voice + submit +
  track only; no coercion / extra-legal pressure; aggregate-first publication;
  1 SBT = 1 vote governs any internal aggregation.
- **G12** **Scope / data-minimization** — collect only what the specific
  participation act requires; no political profiling, no opinion-bank building.
- **G13** `stateAlignedFlag` pass-through into derived records.
- **G14** **Verified-target-only submission** — `moushibumi_submit` refuses any
  target whose `verificationStatus` is `unverified-seed` or stale.
- **G15** **Member-self-submission default** — guide-the-member-to-submit is the
  default; 代行 active-outbound is the gated R3 exception (per-submission consent
  + 行政書士法 clearance + Council Lv7+).

## §5 Non-goals (N1–N13)

N1 NOT a political party / PAC / campaign org / candidate-support body ·
N2 NOT a lobbying-for-hire firm · N3 NOT a vote-direction / GOTV / get-out-the-
vote-targeting machine · N4 NOT a partisan endorser or candidate ranker ·
N5 NOT a 行政書士/弁護士 firm (drafting-assist only; advice → chigiri + licensed)
· N6 NOT a replacement for the member's own civic right (assists, not supplants)
· N7 NOT a political-opinion-profiling / surveillance system · N8 NOT a data-
broker of participation or opinion data · N9 NOT a pretext / impersonation tool
· N10 NOT a plaintext-PII / plaintext-political-belief store · N11 NOT a mass-
filing / assembly-flooding tool · N12 NOT Japan-exclusive (JP-first R0) ·
N13 NOT an oversight actor (that is danjo — opposite posture).

## §6 Lexicons (6, `com.etzhayyim.moushibumi.*`)

`participationTarget` (election/petition/public-comment target registry;
`verificationStatus`) · `participationMatch` (neutral open-opportunity match for
a consenting member) · `participationSession` (member-facing guide session) ·
`voiceDraft` (drafted 請願書 / 意見; `assistMode` = `drafting-assist` only) ·
`submissionRecord` (`member-self-submit` | `agent-on-behalf` gated) ·
`statusTrack` (receipt + 採択/考え方 outcome).

## §7 Cross-actor boundaries

- **chigiri (ADR-2605262700)**: chigiri = templates + legal characterization +
  作成代理 + appeal (UPL); moushibumi pulls templates, renders no advice.
- **danjo (ADR-2605301600)**: opposite posture — danjo watches the state's
  output; moushibumi conveys the citizen's input. A petition's *subject matter*
  may cite danjo's published observations (member's choice), but moushibumi never
  adjudicates.
- **himotoki (ADR-2605302130)**: sibling pattern — himotoki files 開示請求 (data
  out); moushibumi files 請願/意見 (voice in). Shared dispatch discipline.
- **toritsugi (ADR-2605312030)**: sibling — administrative procedures vs
  democratic participation; same registry + G15 self-submit pattern.
- **`com.etzhayyim.encrypted.*` (ADR-2605181100)**: the only home for member PII
  + political-opinion content.
- **kotoba EAVT (ADR-2605262130)**: target catalog + session/draft/submission
  lifecycle datoms; no Kotoba/Datomic.

## §8 Roadmap

- **R0 (this ADR)** — scaffold only: ADR + actor dir + 6 lexicon skeletons +
  target seed (5, all `unverified-seed`) + 7 import-raise cells + registry rows.
  No submission, no live guide.
- **R1** (Council Lv6+ ≥3) — `target_registry` + `voter_info` + `opportunity_
  match` + `intake` + `compose` build artifacts; 案内 + 起草補助 only.
- **R2** (+30-day public comment) — member **self-submits** petitions/comments;
  `status_track` live.
- **R3** (+Council Lv7+ + 行政書士法 clearance) — gated 代行 submission.

# Consequences

- **Positive**: closes the democratic-participation gap with the proven
  toritsugi pattern; the 公職選挙法 / neutrality risk is structurally contained
  (G3 INFO-only floor, no campaigning representable; 代行 gated; political-belief
  PII encrypted + minimized).
- **Negative / honest limits**: the neutrality line is a *policy* discipline as
  much as a schema one — `voter_info` content must be reviewed for partisanship;
  G3 is enforced by content discipline + (future) a guard, not by schema alone.
  Petition 紹介議員 requirements and 議会 routing vary; the seed is best-effort.
- **Constitutional**: no invariant amended. Non-profit / non-partisan /
  Murakumo-only / kotoba-native / encrypted-PII / no-platform-key all hold.

# Alternatives Considered

- **Fold into toritsugi** — rejected: election/petition carry a distinct
  公職選挙法 + political-neutrality risk that would contaminate toritsugi's clean
  行政手続 boundary. A separate actor with its own G3 neutrality gate is safer.
- **Include any campaigning / endorsement / GOTV** — rejected outright:
  incompatible with §1.12 (no vote direction) and non-partisanship. Hence G3/N1–N4.
- **Guidance-only, never submit** — considered; rejected as too thin (same as
  toritsugi): self-submit is the floor, 代行 the gated ceiling.

# References

- This ADR: `/90-docs/adr/2605312400-moushibumi-democratic-participation-concierge-tier-b-actor-r0.md`
- Actor: `/20-actors/moushibumi/` · Lexicons: `/00-contracts/lexicons/com/etzhayyim/moushibumi/`
- ADR-2605312030 (toritsugi — sibling pattern) · ADR-2605302130 (himotoki) · ADR-2605301600 (danjo) · ADR-2605262700 (chigiri)
- ADR-2605181100 (confidentiality) · ADR-2605262130 (kotoba) · ADR-2605192100 §1.12 (Transparent Force / 1 SBT = 1 vote) · ADR-2605192315 (Transparent Force authorization)
- ADR-2605192200 (Charter Rider) · ADR-2605192300 (Council) · ADR-2605215000 (Murakumo-only)
