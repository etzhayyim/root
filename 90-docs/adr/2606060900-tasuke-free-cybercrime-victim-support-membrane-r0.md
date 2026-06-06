---
id: adr-2606060900-tasuke-free-cybercrime-victim-support-membrane-r0
title: "ADR-2606060900: 助 (tasuke) — free cybercrime-victim-support membrane R0"
status: proposed
doc_type: adr
topic: tasuke-cybercrime-victim-support
authoritative: true
last_verified: 2026-06-05
priority: 5.0
axis: architecture
weight: 0.50
priority_note: ""
authoritative_for:
  - tasuke-cybercrime-victim-support-membrane
  - free-victim-relief-document-generation
depends_on:
  - adr-2605231525-server-side-signing-capability-boundary
  - adr-2605312345-kotoba-datom-first-class-canonical-state
  - adr-2605181100-etzhayyim-confidential-records-encryption
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
related:
  - adr-2605301400-tadori-onchain-tx-tracing
  - adr-2605312500-kurashimori-consumer-protection-concierge
  - adr-2605312030-toritsugi-government-procedure-concierge
  - adr-2605302130-himotoki-active-disclosure-request-filer
  - adr-2605262700-chigiri-legal-procedure-substrate
supersedes: []
superseded_by: []
---

# ADR-2606060900: 助 (tasuke) — free cybercrime-victim-support membrane R0

**Status**: proposed
**Date**: 2026-06-05
**Deciders**: Jun Kawasaki

# Context

The question: *「日本でサイバー犯罪被害に遭った時に対応サポートする actor は設計されているか?
弁護士はつなげず、お金がかからず すべて無料で。申請フォーマットも。警察側の手続き・書面・警察内で
そのまま使える報告書・レポートの作成も。」*

The honest answer before this ADR: **no dedicated actor exists.** Eight adjacent actors each cover
one slice — tadori (on-chain trace), kurashimori (事業者 consumer disputes), himotoki (disclosure),
chigiri (legal procedure), toritsugi (gov procedure), warifu/karakuri (payments/accounts), danjo
(oversight) — but **no single actor walks a cybercrime victim from 相談 to recovery**, and none
GENERATES the relief documents the victim brings to the police, their bank, or a platform.

The user's constraints are sharp and they map cleanly onto existing Charter invariants:

- **すべて無料** → cash≡0 / 非営利 / donation-only (ADR-2605301020). A fee would itself be a Charter
  violation, so "free" is not a feature, it is the only representable state.
- **弁護士へつながない** → no paid-counsel routing. (NB: this does **not** remove the UPL boundary —
  弁護士法72条 / 行政書士法19条 still forbid 代理作成・代理提出 for non-licensees. The clean path is
  the toritsugi/kurashimori/chigiri G5 pattern: 案内 + 本人作成支援 + 本人提出, never 代理.)
- **申請フォーマット + 警察側書面 + そのまま使えるレポート** → document generation. The one
  interpretive choice that shapes the whole design: 助 generates **the victim's own 申告書類**
  (被害届・被害状況報告書・証拠目録・被害額算定書), formatted so an officer can work straight from
  them — but it does **not** author police-officer-name 公文書 (that would be 公文書偽造). "そのまま
  使える" = the officer/bank uses it as the basis of their own work, not that 助 forged an official
  record.

# Decision

Build **助 (tasuke)**, a Tier-B actor: a **free** cybercrime-victim-support membrane. 助 (たすけ) is
the in-kind 助け a 信者/member receives when hit by online crime. It is the charter-clean inverse of
a paid "詐欺被害回復" business (which would charge fees and/or buy claims): a non-profit relief
membrane that **drafts but never bills, never adjudicates, never represents, and never forges**.

## The pipeline

```
intake_triage → evidence_preservation → ┌ police_report      被害届 / 被害状況報告書 / 証拠目録 / 被害額算定書
(同意・無料・分類)  (暗号化参照 + hash)       ├ platform_abuse     銀行組戻し(振り込め詐欺救済法) / プラットフォーム依頼
                                          └ account_recovery   アカウント復旧手順(本人実行)
                                                  → FREE public windows (#9110 / 188 / NCCC / …)
```

## The structural invariants (the heart)

Following the nusa `:thc-class` / tazuna `:weaponizable` / kamado `:fossil-virgin-crude` / ake
`:impersonate` pattern, the user's three hard constraints are made **unrepresentable** in THREE
places each (schema `:db/allowed`/enum + lexicon `:const`/`:enum` + Python `ValueError`):

- **G1 全て無料 (cash≡0)** — `:support/cost-jpy :db/allowed [0]`; `supportCostJpy const 0`;
  `triage.SUPPORT_COST_JPY = 0`. A fee/charge/subscription cannot be expressed. `analyze.run()`
  asserts the total victim cost across every case is ¥0.
- **G2 本人作成・本人提出** — `:support/role :db/allowed {:guide :draft-assist :self-submit}`;
  `:represent`/`:proxy-submit`/`:agent-file` absent; every generated doc carries
  `needsMemberSignature const true`. 助 drafts; the member authors, signs, and submits
  (行政書士法/弁護士法 独占業務不踏).
- **G3 警察authored不可** — `:doc/authored-by :db/allowed [:member]`; `authoredBy const "member"`;
  `report_gen._doc` hard-wires `:member`. `:police`/`:official`/`:server` are unrepresentable — a
  generated filing is the victim's own 申告書類 (公文書偽造を構造的に排除).

Plus: **G4** non-adjudicating (a scam KIND is a routing label; `:case/verdict` does not exist —
danjo/chigiri boundary) · **G5** no paid counsel (`:referral/paid :db/allowed [false]`; free public
windows only — 弁護士へつながない) · **G6** PII-by-reference (evidence in
`com.etzhayyim.encrypted.*`; a plaintext-PII field raises — ADR-2605181100) · **G7** no-server-key
(member signs every submission — ADR-2605231525) · **G8** Murakumo-only (ADR-2605215000) · **G9**
outward-gated (`:doc/published const false`; `.solve()` raises; live filing = Council Lv6+ +
operator) · **G10** sourcing-honesty (the window/procedure registry is `:representative`).

## Why "そのまま使える" without forging anything

The generated police-side documents are exactly what a victim has the right to prepare and bring:
a 被害届 下書き addressed to the 警察署長, a 時系列の被害状況報告書, a 証拠目録 with chain-of-custody
hashes, a 被害額算定書. They are complete enough that the receiving officer can use them as the basis
of the official intake and 聴取 — which is the real friction 助 removes — **without** 助 ever
producing the officer's own 公文書 (供述調書・受理書類 remain police-authored, by construction). The
bank-side 組戻し・口座凍結依頼 leans on the **振り込め詐欺救済法** (free, bank-administered, no lawyer
needed); the platform-side requests lean on each service's abuse 条項; the recovery plan is a
self-help procedure the member executes (助 never logs into the member's account).

# Consequences

- **Positive**: a real, free, end-to-end path for a Japanese cybercrime victim; the relief documents
  generated ready-to-use; UPL/公文書/料金 the three sharpest legal risks made *structurally*
  impossible rather than policy-promised; composes with tadori (crypto trace), kurashimori
  (consumer), toritsugi (surface), kokoro (psychosocial), chigiri/danjo (the adjudication boundary).
- **Honest R0 limits**: design + offline generation only. No live filing/sending/account-operation
  (G9). Deterministic keyword classifier (LLM refinement = R1, G8). The window/根拠法令/法定期限
  registry is `:representative` and needs primary-source verification (G10). 訴訟代理 is out of scope
  (助 does not route to paid counsel; it points to free public consultation windows).
- **Zero invariant amendments** — 助 STRENGTHENS cash≡0, no-server-key (ADR-2605231525),
  encrypted-records (ADR-2605181100), kotoba-canonical-state (ADR-2605312345), and the non-profit /
  donation-only Charter.

## Artifacts

- Ontology `00-contracts/schemas/cybercrime-victim-support-ontology.kotoba.edn`
- 6 lexicons `20-actors/tasuke/lex/*.edn` (`com.etzhayyim.tasuke.*`)
- 5 cells `20-actors/tasuke/cells/*` (coded state machines; `.solve()` raises at R0)
- Methods `20-actors/tasuke/methods/{triage,report_gen,evidence,analyze}.py`
- Seed `20-actors/tasuke/data/seed-cybercrime-cases.kotoba.edn` (5 cases + 9 free windows)
- 69 tests green (`20-actors/tasuke/run_tests.sh`)
- Registered: `INFRA_ACTORS` + `actor-profile-seed.kotoba.edn` → `did:web:etzhayyim.com:actor:tasuke`

## Non-goals

N1 not a 代理人 (G2) · N2 not a generator of official police documents (G3) · N3 not an adjudicator
(G4) · N4 not a paid service / no paid-counsel routing (G1/G5) · N5 not debt collection / 取立 /
自力救済 · N6 no server-signed submission (G7) · N7 not surveillance (G6).
