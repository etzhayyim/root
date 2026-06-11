---
id: adr-2605201800-etzhayyim-yobel-debt-release-actor
title: "ADR-2605201800: Yobel — Collective Debt Release Actor (Shmita / Jubilee / Tokusei-rei / Amnesty)"
status: proposed
doc_type: adr
topic: etzhayyim-yobel-debt-release-actor
authoritative: true
last_verified: 2026-05-20
priority: 7.5
axis: doctrine-runtime
weight: 0.75
priority_note: "etzhayyim Mission Charter §1 (構造的労働解放) の **金銭的負債** 局面における doctrinal runtime。bankruptcy.etzhayyim.com (vendor, mandatory legal procedure intelligence) と相補的に、religious-corp 主導の voluntary 集合債務免除 rite を AT MST + Base L2 USDC で実装する。SBT-gated eligibility + Council Lv6+ ratification + transparent on-chain settlement の三条件下で運用される。"
authoritative_for:
  - org.etzhayyim.yobel.* lexicon family (transitional NSID: com.etzhayyim.apps.etzhayyim.yobel.*)
  - shmita / yobel / tokusei-rei / Catholic Jubilee / political amnesty rite catalog
  - voluntary creditor opt-in + signedConsent invariant
  - USDC-on-Base-L2 settlement boundary (no fiat)
  - cross-actor fallback to bankruptcy.etzhayyim.com (vendor side, mandatory legal)
depends_on:
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192115-etzhayyim-non-profit-donation-only-no-ads
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
  - adr-2605192230-etzhayyim-three-tier-enforcement-implementation
  - adr-2605192415-etzhayyim-religious-corp-daemon-architecture
related:
  - adr-2605201700-yobel-jubilee-shmita-debt-release-actor
  - vendor:60-apps/etzhayyim-project-bankruptcy/CLAUDE.md
  - vendor:90-docs/adr/0016-legal-cluster-topology.md
  - vendor:90-docs/adr/0074-ethereum-identity-bridge-cacao-webauthn.md
supersedes: []
superseded_by: []
---

# ADR-2605201800: Yobel — Collective Debt Release Actor (Shmita / Jubilee / Tokusei-rei / Amnesty)

**Status**: proposed
**Date**: 2026-05-20
**Deciders**: Jun Kawasaki

# Context

etzhayyim Mission Charter (ADR-2605192100) は **構造的労働解放** を最終目的とする。労働強制の主要な原動力は **負債** (monetary / agrarian / sovereign) であり、人類史は周期的な **集合的債務リセット rite** で当該強制を解除してきた:

| 制度 | 出典 | 周期/契機 | 範囲 |
|---|---|---|---|
| שמיטה (shmita) | Lev 25:1-7 / Deut 15:1-2 | 7 年毎 | 共同体内負債免除 + 農地休耕 |
| יובל (yobel, Jubilee) | Lev 25:8-13 | 49/50 年毎 | 負債 + 土地復帰 + 負債奴隷解放 |
| 徳政令 (tokusei-rei) | 永仁 1297 / 嘉吉 1441 | 政治契機 | 借券無効化 |
| Catholic Holy Year | Boniface VIII 1300 / Indulgentiarum doctrina 1967 | 25 年毎 | indulgentia plenaria |
| Modern Political Amnesty | HIPC 1996 / Jubilee 2000 / Paris Club | ad-hoc | sovereign debt |

**設計空白**: vendor 側 `bankruptcy.etzhayyim.com` (84 jurisdictions, ~170 法定手続) は **個別・法的強制力ある手続** の intelligence + 代行を扱う。これに対し本 ADR が扱う rite は:

1. **voluntary opt-in** — 強制力なし、creditor 同意必須
2. **教義的権威に基づく宣言** — etzhayyim religious-corp doctrinal act (Charter §1 mission の直接実装)
3. **集合的契機** — 周期 (shmita / yobel) or 政治的判断 (tokusei / amnesty)
4. **自然人 (natural person) のみ対象** — yobel は個人債務者の救済のみ扱う。法人 (sovereign / corporate) 債務のリストラ・恩赦は scope 外

これらは vendor の domain ではなく **etzhayyim の core function** — Charter Rider v2 §2(b) で禁止する "speculative finance + predatory lending" の **antithesis** であり、§1.5 "free release of new technology to charter-aligned others" の中核に位置する。

# Decision

**`yobel`** actor を etzhayyim/root 配下に新規設計する。

| 項目 | 値 |
|---|---|
| **Name** | yobel (יובל, ram's horn / Jubilee 語源) |
| **Operating entity** | etzhayyim (vendor 関与なし、3-axis split 全 clean) |
| **License** | Apache-2.0 + Charter Compliance Rider v2.0 |
| **DID** | `did:web:yobel.etzhayyim.com` (primary) |
| **Substrate** | AT MST + IPFS + Base L2 (RW-free — vendor の Kotoba/Datomic は使わない) |
| **Settlement** | USDC on Base L2 via ERC725 Smart Wallet。fiat / Stripe / 銀行決済 禁止 |
| **NSID (current)** | `com.etzhayyim.apps.etzhayyim.yobel.*` (kuniUmi precedent と整合) |
| **NSID (canonical, future)** | `org.etzhayyim.yobel.*` (post-org-rename cutover) |
| **Runtime** | TS Native + Lexicon Contract |
| **Charter alignment** | Mission §1 (構造的労働解放) の monetary-debt 局面における doctrinal runtime |
| **Eligibility gate** | SBT membership (Council Lv1+) + rite type 別追加条件 |
| **Ratification gate** | rite declaration は Council Lv6+ ratification (§2 enforcement tier 3 と同等の重要性) |

## Rite Catalog

| Rite type | 名称 | 周期/契機 | 教義的根拠 | 範囲 |
|---|---|---|---|---|
| `shmita_7yr` | שמיטה Sabbatical | 7 年毎 | Lev 25:1-7 / Deut 15:1-2 | 共同体員間 monetary debt |
| `yobel_50yr` | יובל Jubilee | 49/50 年毎 | Lev 25:8-13 | debt + land tenure + bondage |
| `tokusei_rei` | 徳政令 | 政治契機 | 室町/鎌倉幕府慣行 | 借券無効化 |
| `religious_jubilee` | Catholic Holy Year | 25 年毎 | Boniface VIII 1300 + Paul VI 1967 | spiritual / temporal punishment |
| `political_amnesty` | Modern Amnesty | ad-hoc | 主権者宣言 / 議会決議 | **mass amnesty for natural-person debtors** (e.g. national tax delinquency pardon, post-conflict veteran debt cancellation, individual loan amnesty). NOT sovereign/corporate debt restructuring — that is handled by the sibling [`amnesty.etzhayyim.com`](/90-docs/adr/2605202000-etzhayyim-amnesty-legal-person-debt-actor.md) actor (ADR-2605202000). |

## Invariants (NON-NEGOTIABLE)

### Natural-person-only (debtor side) — CRITICAL

yobel releases debt for **natural persons (自然人) only**. Legal-person debt (sovereign / corporate restructuring, partnerships, government entities) is **out of scope**. Creditors may be either natural or legal persons — a corporation voluntarily forgiving an individual's debt is a legitimate creditor enrollment; what is gated is the **identity of the recipient of relief**.

Enforcement is **schema- and runtime-defense-in-depth**:

| Layer | Mechanism |
|---|---|
| Lexicon schema | `enrollDebtor.debtorEntityType` is a single-value enum `["natural_person"]` — caller cannot encode any other value |
| Lexicon schema (creditor side) | `enrollCreditor.debts[].instrument` enum excludes `sovereign_bond` + `corporate_bond` — legal-person debt instruments unrepresentable |
| Cell DMN R14 | `debtor_enrollment` cell short-circuits to ineligible if either declared `debtorEntityType` or resolved CouncilSBT `entityType` claim is not `natural_person`. Highest-priority rule, fires before R12 (SBT) or R13 (instrument) |
| Cell DMN R13 | extended to reject `sovereign_bond` / `corporate_bond` as legal-person-only instruments (in addition to Charter Rider §2(b) `liquidation` / `margin_call` / `seizure`) |
| Solidity contracts | no `entityType` field on-chain — invariant lives at cell-level governance for amendability via ADR rather than redeploy. EVM-level `OneWayViolation` revert remains the §2(b) hard gate |

### `political_amnesty` rite scope (clarified per this amendment)

Political amnesty rites under yobel handle **mass amnesty for individual debtors under sovereign decree**. Examples in scope:

- National tax delinquency pardon programs (e.g. periodic tax amnesty laws for individual taxpayers)
- Post-conflict / post-civil-unrest debt cancellation for affected individuals
- Veteran debt cancellation acts
- Individual loan amnesty under sovereign decree

Examples **out of yobel scope but in [amnesty.etzhayyim.com](/90-docs/adr/2605202000-etzhayyim-amnesty-legal-person-debt-actor.md) scope** (sibling actor, ADR-2605202000):

- HIPC / Paris Club sovereign debt restructuring (state-to-state) → `amnesty.sovereign_multilateral` / `amnesty.sovereign_bilateral`
- Corporate Chapter 11 amnesty (legal person) → `amnesty.corporate_chapter_11`
- Brady Bond restructuring (sovereign + commercial creditor renegotiation) → `amnesty.sovereign_multilateral`
- Sovereign debt jubilee movements at the institutional level (Jubilee 2000 etc. — at the level of debt CLAIM ownership, individuals were the ultimate beneficiaries; but the YOBEL release is recorded against the natural-person debtor, not the sovereign issuer; institutional-level cases go to amnesty)
- Debt-for-nature swaps (sovereign debt cancellation ↔ conservation commitment) → `amnesty.debt_for_nature_swap`

The actor pair (yobel + amnesty) provides symmetric coverage with mutual deferral: yobel returns `deferToAmnesty=true` when entityType=legal_person; amnesty returns `deferToYobel=true` when entityType=natural_person.

Where the line gets fuzzy (e.g. a sole-proprietor's business debt where the proprietor IS the legal entity), default to natural-person treatment if the debtor's CouncilSBT `entityType=natural_person` claim holds.


## Lexicon (8 methods)

| Method | 種別 | 用途 |
|---|---|---|
| `declareRite` | procedure | rite 宣言 (Council Lv6+ ratification 必須) |
| `enrollCreditor` | procedure | 債権者 voluntary opt-in + signedConsent (ERC725 EIP-712 or DPoP) |
| `enrollDebtor` | procedure | 債務者 opt-in + eligibilityProof |
| `verifyEligibility` | query | rite type 別 eligibility 判定 + jurisdictional warnings |
| `recordRelease` | procedure | 個別 debt release (Base L2 tx hash 含む) |
| `listRites` | query | pagination 付き rite 一覧 |
| `getRite` | query | rite 詳細 + 集計 metrics |
| `listReleases` | query | pagination 付き release 一覧 |

詳細 schema: `00-contracts/lexicons/com/etzhayyim/apps/etzhayyim/yobel/*.json`

## Cluster Integration

```
etzhayyim/yobel (this repo — voluntary, doctrinal, USDC on Base L2)
   ├── fallback to    → vendor:bankruptcy.etzhayyim.com   (mandatory legal, 84 jurisdictions)
   ├── represented by → vendor:lawfirm.etzhayyim.com      (creditor consent letters, court filings)
   ├── eligibility    ← council SBT registry        (Lv1+ membership gate)
   ├── ratification   ← council Lv6+                (rite declaration approval)
   ├── settlement     → ERC725 Smart Wallet + Base L2 USDC
   ├── audit          → AT MST + IPFS append-only   (Charter §1.3 transparent)
   ├── anchor         → MstCheckpointSaver + AnchorBridge (ADR-2605171800)
   └── publication    → app.bsky.feed.post (#shmita / #yobel / #徳政令 / #jubilee)
```

vendor 境界 (3-axis split, vendor ADR-2605172400):
- **Liability** = religious doctrine (etzhayyim) — secular law 抵触時は vendor:bankruptcy 経路を併用
- **Custody** = AT MST + IPFS (etzhayyim substrate)
- **Settlement** = USDC on Base L2 (etzhayyim substrate)

vendor (etzhayyim Japan) は **意思決定権なし**。本 actor の出力 (release 記録) を読み取って bankruptcy.etzhayyim.com の case management に紐付ける逆方向参照は許容 (vendor → etzhayyim の read-only consumer)。

# Consequences

**Positive**
- Mission §1 (構造的労働解放) を金銭債務局面で具現化する最初の actor。Charter doctrine → 実行可能 lexicon contract の path が確立
- bankruptcy.etzhayyim.com (mandatory legal) と yobel.etzhayyim.com (voluntary doctrinal) の責務分離が明確化
- shmita 7-yr / yobel 50-yr の周期的 rite を append-only audit trail で歴史記録できる
- Charter Rider §2(b) speculative finance 禁止の **正反対** = 構造的 anti-predatory-lending として CR v2 の正当性を強化
- HIPC / Jubilee 2000 / Paris Club 等の現代政治 amnesty を同一データモデルで記録可能、religious-corp が中立 record-keeper として機能可能
- SBT-gated eligibility により Charter §1.13 (SBT-based identity) と直結

**Negative / Risk**
- **権威の濫用リスク** — 主宰者が任意に rite 宣言可能 → Council Lv6+ ratification + voluntary opt-in 必須 + PDS commit log 全 public audit + 3rd-party religious-corp も同様の rite 宣言可能 (multi-issuer)
- **税務影響** — debt forgiveness は jurisdiction によって課税所得 (e.g. US IRC §61(a)(11) COD income)。`jurisdictionNotes` field で warning、税務 advice は vendor:lawfirm.etzhayyim.com に delegate
- **法的拘束力の限界** — voluntary opt-in のため secular creditor は無視可能。formal binding が必要な場合 vendor:bankruptcy.etzhayyim.com fallback
- **Charter Rider §2(b) 抵触可能性** — もし actor 自身が利息計算 / leverage / arbitrage を行えば自身が SPECULATIVE FINANCE に該当しうる → **本 actor は debt forgiveness one-way のみ。新規貸付 / 利息計算 / margin / liquidation を持たない** invariant を schema レベルで担保
- **歴史データ ambiguity** — 徳政令の史料 (大乗院寺社雑事記 等) を schema に乗せる際の uncertainty → `doctrinalBasis` free-text で吸収

**Neutral**
- deps.toml `[[projects]]` 追加 (登記後の cutover で vendor:deps.toml entry は archive)
- 実装 scaffolding (`kotodama.jsonld` / `src/app.ts`) は本 PR 後の follow-up
- vendor 側 (`vendor:60-apps/etzhayyim-project-yobel/CLAUDE.md`) は marker stub として残置、cross-reference 用

# Alternatives Considered

**A. vendor:bankruptcy.etzhayyim.com を拡張して `voluntary_collective_release` process type を追加** — 却下。voluntary doctrinal rite と mandatory legal procedure を同 actor に同居させると 3-axis split (vendor:ADR-2605172400) 違反 (liability axis = doctrine vs. secular law が混在)。

**B. 5 actor cluster (shmita / yobel / tokusei / jubilee / amnesty を分離)** — 却下。データモデル (debt registration + voluntary opt-in + release tx) はすべて同一。rite type discriminator で 1 actor に統合する方が Shannon-optimal。

**C. vendor 配置 (`com.etzhayyim.apps.yobel.*`)** — 却下。3-axis split: liability (religious doctrine) / custody (collective ritual records) / settlement (USDC on Base L2, no fiat) すべて etzhayyim clean。

**D. RW + Hyperdrive 経由実装** — 却下。vendor:ADR-2605172000 etzhayyim substrate boundary により RW は vendor 限定。

**E. canonical NSID で `org.etzhayyim.yobel.*` を本 repo に最初から使う** — 却下 (transitional)。`kuniUmi` precedent が `com.etzhayyim.apps.etzhayyim.kuniUmi.*` を使っているため、整合性のため transition 期間は `com.etzhayyim.apps.etzhayyim.yobel.*` で書き、登記後の org-rename cutover で `org.etzhayyim.*` に一括 sed する (220-file cutover script に乗せる)。

**F. SBT 不要、誰でも opt-in 可能** — 却下。Charter §1.13 SBT-based identity invariant と整合させるため `enrollDebtor` / `enrollCreditor` は SBT 保有 DID 限定 (verifyEligibility で gate)。

# References

**Doctrinal sources**:
- Leviticus 25:1-13 (BHS) — shmita + yobel 原典
- Deuteronomy 15:1-11 — shmita 拡張規定
- 永仁の徳政令 (1297) / 嘉吉の徳政令 (1441) — 大乗院寺社雑事記 / 建武以来追加
- Boniface VIII, *Antiquorum habet fida relatio* (1300)
- Indulgentiarum doctrina (Paul VI, 1967)
- Jubilee 2000 Coalition + HIPC Initiative (IMF/World Bank, 1996)
- UNCTAD Sovereign Debt Workout Framework (2015)

**etzhayyim/root ADRs (depends_on)**:
- ADR-2605192100 etzhayyim Mission Charter
- ADR-2605192115 etzhayyim Tithe + Public Fund
- ADR-2605192200 etzhayyim IP Free Release Charter Rider
- ADR-2605192230 etzhayyim Three-Tier Enforcement Implementation
- ADR-2605192415 etzhayyim Religious-Corp Daemon Architecture

**Vendor cross-references**:
- vendor ADR-2605201700 yobel jubilee shmita debt release actor (twin design ADR)
- vendor ADR-0016 Legal Cluster Topology
- vendor ADR-0074 ERC725 Identity Bridge (CACAO + WebAuthn)
- vendor ADR-2605172000 etzhayyim Open Telecom Fabric (substrate boundary)
- vendor ADR-2605172400 etzhayyim/vendor 3-axis Split Rule
- vendor `60-apps/etzhayyim-project-bankruptcy/CLAUDE.md`
- vendor `60-apps/etzhayyim-project-lawfirm/CLAUDE.md`
