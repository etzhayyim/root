---
id: adr-2605201700-yobel-jubilee-shmita-debt-release-actor
title: Yobel — Collective Debt Release Actor (Shmita / Jubilee / Tokusei-rei / Amnesty) under etzhayyim
status: proposed
doc_type: adr
topic: yobel-actor
authoritative: true
last_verified: 2026-05-20
authoritative_for:
  - yobel.etzhayyim.com
  - collective debt release rites
  - etzhayyim religious-corp doctrinal acts
related:
  - 90-docs/adr/0016-legal-cluster-topology.md
  - 90-docs/adr/0074-ethereum-identity-bridge-cacao-webauthn.md
  - adr-2605152100-etzhayyim-github-org-boundary
  - 90-docs/adr/2605172000-etzhayyim-open-telecom-fabric.md
  - adr-2605172400-etzhayyim-vendor-three-axis-split-rule
  - 60-apps/etzhayyim-project-bankruptcy/CLAUDE.md
supersedes: []
superseded_by: []
---

# Context

`bankruptcy.etzhayyim.com` (84 jurisdictions, ~170 process types) は **個別の法的負債清算**を網羅する — Chapter 7/11/13、自己破産、IVA、Restschuldbefreiung、UNCITRAL Model Law。`lawfirm.etzhayyim.com` (ADR-0016) は代理人レイヤを提供する。

**設計空白**: **集合的・教義的・政治的に債務をリセットする儀式 (rite)** を扱う actor は存在しない。具体的には:

| 制度 | 出典 | 周期/契機 | 範囲 |
|---|---|---|---|
| שמיטה (shmita) | Deut 15:1-2 / Lev 25:1-7 | 7 年毎 | 共同体内の負債免除 + 農地休耕 |
| יובל (yobel, Jubilee) | Lev 25:8-13 | 49/50 年毎 | 負債免除 + 土地復帰 + 負債奴隷解放 |
| 徳政令 (tokusei-rei) | 永仁の徳政令 1297 / 嘉吉の徳政令 1441 等 | 政治的契機 (一揆・改元・大火) | 借券無効化 (徳政一揆・大乗院寺社雑事記) |
| Catholic Jubilee (Holy Year) | Boniface VIII 1300 + Unigenitus 1343 | 25/50/100 年 | indulgentia plenaria (霊的負債) + 巡礼免除 |
| Modern Political Amnesty | Tax amnesty / veteran debt cancellation / individual loan amnesty | ad-hoc | **mass amnesty for natural-person debtors** (sovereign/corporate restructuring は scope 外) |

これらは:
1. **法的破産手続 (bankruptcy.etzhayyim.com) と本質的に異なる** — voluntary creditor opt-in / 教義的権威 / 集合的契機
2. **etzhayyim (עץ חיים, 運営宗教法人) の本来的活動領域** — 宗教教義に基づく債務免除は religious-corp の core function
3. **3-axis split rule (ADR-2605172400)**: Liability (教義的責任 → etzhayyim) / Custody (集合記録 → etzhayyim) / Settlement (USDC on Base L2 → etzhayyim 基盤、ADR-2605172000) すべて etzhayyim 側

# Decision

**`yobel.etzhayyim.com`** を新規 actor として設計する。

| 項目 | 値 |
|---|---|
| **Name** | yobel (יובל, ram's horn / Jubilee の語源) |
| **Operating entity** | **etzhayyim** (運営法人。etzhayyim Japan vendor の関与なし) |
| **Destination repo** | `github.com/etzhayyim/root` (Apache 2.0、open religious-corp monorepo) |
| **License** | Apache 2.0 |
| **DID** | `did:web:yobel.etzhayyim.com` (primary) + `did:web:yobel.etzhayyim.com` (federation alias only, AT layer) |
| **Substrate** | AT MST + IPFS + Base L2 (kotoba per ADR-2605172000) |
| **Settlement** | USDC on Base L2 via ERC725 Smart Wallet (ADR-0074) — fiat / Stripe 禁止 |
| **NSID** | `org.etzhayyim.yobel.*` (canonical, etzhayyim/root cutover 後) / `com.etzhayyim.apps.yobel.*` (transitional alias 維持) |
| **Runtime** | TS Native + Lexicon Contract |
| **Profile category** | `religious` |
| **Profile operator** | `etzhayyim` |
| **3-axis classification** | etzhayyim (3/3 axes clean) |

## Rite Catalog

| Rite type | 名称 | 周期/契機 | 教義的根拠 | 範囲 |
|---|---|---|---|---|
| `shmita_7yr` | שמיטה Sabbatical | 7 年毎 (固定 calendar) | Lev 25:1-7 / Deut 15:1-2 | 共同体員間の monetary debt |
| `yobel_50yr` | יובל Jubilee | 49/50 年毎 (7 × shmita) | Lev 25:8-13 | debt + land + bondage release |
| `tokusei_rei` | 徳政令 | 政治契機 (declared) | 室町幕府 / 鎌倉幕府慣行 | 借券無効化 (借金棒引き) |
| `religious_jubilee` | Catholic Holy Year | 25 年毎 (1300 起点) | Unigenitus 1343 + Indulgentiarum doctrina 1967 | spiritual debt + temporal punishment |
| `political_amnesty` | Modern Amnesty | ad-hoc | 主権者宣言 / 議会決議 / 多国間合意 | sovereign / institutional debt |

## Lexicon (`org.etzhayyim.yobel.*`)

| Method | 種別 | 用途 |
|---|---|---|
| `declareRite` | procedure | etzhayyim 主宰者が rite を宣言 (riteType, scope, effectiveDate, expiryDate, doctrinalBasis, jurisdictionNotes) |
| `enrollCreditor` | procedure | 債権者 DID が voluntary に opt-in (creditorDid, debtList[], signedConsent) |
| `enrollDebtor` | procedure | 債務者 DID が opt-in (debtorDid, **debtorEntityType="natural_person"** 必須, eligibilityProof) |
| `verifyEligibility` | query | 債務者の eligibility 判定 (rite 別の条件: shmita = 共同体員 / tokusei = jurisdictionMatch / etc.) |
| `recordRelease` | procedure | 個別 debt の release を記録 (debtId, releaseMethod, baseL2TxHash?) |
| `listRites` | query | rite 一覧 (status / riteType / period filter) |
| `getRite` | query | rite 詳細 (enrolled creditors / debtors / releases count) |
| `listReleases` | query | 個別 release 一覧 (rite scope) |

すべて voluntary opt-in。**強制力なし**。書き込みは AT MST (etzhayyim PDS) + Base L2 anchor (settlement 発生時のみ)。

### Natural-person-only invariant (CRITICAL)

**yobel は自然人 (natural person) のみを債務者として扱う。** 法人 (sovereign / corporate) の債務リストラ・恩赦は scope 外。詳細は etzhayyim ADR-2605201800 §Invariants 参照。

Defense-in-depth:
- Lexicon schema: `enrollDebtor.debtorEntityType` は単一値 enum `["natural_person"]`
- Lexicon schema: `enrollCreditor.debts[].instrument` から `sovereign_bond` / `corporate_bond` を除外
- Cell DMN R14 (最高優先度 short-circuit): 宣言 entityType + CouncilSBT 解決 entityType の両方が `natural_person` でないと拒否
- Cell DMN R13 拡張: `sovereign_bond` / `corporate_bond` を legal-person-only instrument として拒否

Creditor 側は自然人・法人いずれも可 (法人が自然人債務を voluntary に forgive することは Charter §1 mission に整合)。**gate は relief の受け手 (= debtor) の identity に対してのみ適用される。**

`political_amnesty` rite type は **個人債務者に対する集合的恩赦** (例: 国家税滞納の一括恩赦・退役軍人個別債務消除) を扱い、HIPC / Paris Club / Brady Bond のような **国家債務リストラは扱わない** — それは sibling actor `amnesty.etzhayyim.com` (etzhayyim ADR-2605202000) が担当する。両 actor は entityType に基づく symmetric mutual deferral を実装 (yobel R14 が legal_person を受けたら `deferToAmnesty=true`、amnesty A14 が natural_person を受けたら `deferToYobel=true`)。

## Cluster Integration

```
yobel.etzhayyim.com (etzhayyim, voluntary rite)
   ├── falls back to → bankruptcy.etzhayyim.com  (formal legal procedure, jurisdictionally required)
   ├── represented by → lawfirm.etzhayyim.com    (creditor consent letters, court filings)
   ├── eligibility   ← trust.etzhayyim.com       (kyu/dan + Well-Becoming filter, optional)
   ├── settlement    → ERC725 Smart Wallet (ADR-0074) + Base L2 USDC release tx
   ├── audit         → AT MST + IPFS append-only (etzhayyim substrate, no RW)
   └── publication   → app.bsky.feed.post + #shmita / #yobel / #徳政令 / #jubilee tags
```

### Cross-Actor Wire (IMPLEMENTED 2026-05-20)

Vendor-side read-only consumer of etzhayyim/yobel rite state:

| Lexicon | Direction | Purpose |
|---|---|---|
| `com.etzhayyim.apps.bankruptcy.recordYobelRiteReference` | vendor:bankruptcy ← (queries) → etzhayyim/yobel | Attach a yobel rite reference to a formal bankruptcy case. Handler resolves rite state via `YobelRiteRegistry.getRite()` on Base L2 (no trust required — independent chain verification). |

**3-axis split enforced** (vendor ADR-2605172400):
- Vendor stores attachment record; etzhayyim/yobel remains rite SSoT
- Vendor has no write access to `YobelRiteRegistry` contract
- Tax advice delegated to vendor:lawfirm.etzhayyim.com (vendor handles secular tax procedure)
- COD income calculations are vendor's domain; voluntary release attribution is etzhayyim's

**etzhayyim ADR-2605201800** is the destination-side twin (etzhayyim/root). Stack across both repos:

| Layer | Repo | Path |
|---|---|---|
| Lexicons (8 yobel methods) | etzhayyim/root | `00-contracts/lexicons/com/etzhayyim/apps/etzhayyim/yobel/` |
| LangGraph cells (5) + orchestrator | etzhayyim/root | `20-actors/yobel/` |
| Solidity contracts (2) | etzhayyim/root | `50-infra/etzhayyim-yobel-contract/` |
| Web3 ports + EIP-712 verify | etzhayyim/root | `20-actors/yobel/concrete_ports/` |
| Vendor cross-actor lexicon | this repo | `00-contracts/lexicons/com/etzhayyim/apps/bankruptcy/recordYobelRiteReference.json` |
| Vendor cross-actor doc | this repo | `60-apps/etzhayyim-project-bankruptcy/CLAUDE.md` §Cross-Actor |

# Consequences

**Positive**
- etzhayyim religious-corp の core function (教義的債務免除) が actor として実装可能になる
- bankruptcy.etzhayyim.com (mandatory legal) と yobel.etzhayyim.com (voluntary doctrinal) の責務分離が明確
- collective rite (shmita 7-yr, jubilee 50-yr) を append-only audit trail で歴史記録できる
- ERC725 + Base L2 settlement により非営利・on-chain only 経路で完結 (fiat 不要)
- Jubilee 2000 / HIPC 等の modern political amnesty を同一データモデルで記録可能

**Negative / リスク**
- **権威の濫用リスク** — etzhayyim 主宰者が任意に rite を宣言可能 → mitigations: (1) voluntary opt-in 必須、(2) doctrinalBasis 必須 field、(3) PDS commit log で全宣言が public audit、(4) 3rd-party religious-corp が同様の rite 宣言可能 (multi-issuer model)
- **税務影響** — debt forgiveness は jurisdiction によって課税所得を生む (e.g. US IRC §61(a)(11) cancellation-of-debt income)。actor は jurisdiction-specific `jurisdictionNotes` を保持し、warning を返すが、税務 advice は提供しない (→ lawfirm.etzhayyim.com に delegate)
- **法的拘束力の限界** — voluntary opt-in のため secular creditor は無視可能。formal binding が必要な場合は bankruptcy.etzhayyim.com fallback
- **歴史的負債データ整合** — 徳政令の歴史記録 (大乗院寺社雑事記等) を schema に乗せる際、史料 ambiguity が残る (典拠 field + uncertainty tagging で吸収)

**Neutral**
- deps.toml `[[projects]]` 追加
- etzhayyim/root への seed は登記変更後の Step 11 (220-file sed cutover) に合わせて実施。本 repo には scaffolding stub のみ置く
- NSID `org.etzhayyim.yobel.*` を canonical、`com.etzhayyim.apps.yobel.*` を transitional alias とする (ADR-2605152100 GitHub org split に整合)

# Alternatives Considered

**A. Extend bankruptcy.etzhayyim.com with a `voluntary_collective_release` process type** — 却下。bankruptcy actor は**法的強制力ある手続**の intelligence + 代行を扱う。voluntary doctrinal rite を同居させると domain confusion + vendor (etzhayyim Japan) と etzhayyim の責任境界が曖昧になる (3-axis split 違反)。

**B. 4-actor cluster (`shmita.etzhayyim.com` + `yobel.etzhayyim.com` + `tokusei.etzhayyim.com` + `amnesty.etzhayyim.com`)** — 却下。データモデル (debt registration + voluntary opt-in + release tx) はすべて同一。rite type discriminator で 1 actor に統合する方が Shannon-optimal (η 高、operational overhead 低)。

**C. Vendor placement (`com.etzhayyim.apps.yobel.*` only, this repo)** — 却下。user 明示で「非営利 → etzhayyim」。3-axis split: liability (religious doctrine) / custody (collective ritual records) / settlement (USDC on Base L2, no fiat) すべて etzhayyim clean。

**D. RW + Hyperdrive 経由実装** — 却下。ADR-2605172000 etzhayyim substrate boundary により RW は vendor 限定。yobel は AT MST + IPFS + Base L2 のみ。

**E. 既存 etzhayyim NSID `org.etzhayyim.*` を使う** — 却下。canonical rename (ADR-2605152100) で `etzhayyim` を採用済。新規 actor は最初から `org.etzhayyim.*` で書く。

# References

- Leviticus 25:1-13 (BHS) — shmita + yobel 原典
- Deuteronomy 15:1-11 — shmita 拡張規定
- 永仁の徳政令 (1297) / 嘉吉の徳政令 (1441) — 一次史料: 大乗院寺社雑事記 / 建武以来追加
- Boniface VIII, *Antiquorum habet fida relatio* (1300) — Catholic Holy Year 起源
- Indulgentiarum doctrina (Paul VI, 1967) — modern doctrine
- Jubilee 2000 Coalition / HIPC Initiative (IMF/World Bank, 1996) — modern political amnesty
- UNCTAD Sovereign Debt Workout (2015) — secular collective release framework
- ADR-0016 Legal Cluster Topology
- ADR-0074 Ethereum Identity Bridge (ERC725 + Smart Wallet)
- ADR-2605152100 etzhayyim GitHub Org Boundary
- ADR-2605172000 etzhayyim Open Telecom Fabric (substrate boundary)
- ADR-2605172400 etzhayyim/vendor 3-axis Split Rule
- `60-apps/etzhayyim-project-bankruptcy/CLAUDE.md`
