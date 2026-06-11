---
id: adr-2605192345-etzhayyim-steward-succession
title: "ADR-2605192345: etzhayyim Steward Succession — donor 死亡時の steward 継承手続き + 多世代 stewardship continuity"
status: proposed
doc_type: adr
topic: etzhayyim-steward-succession
authoritative: true
last_verified: 2026-05-19
priority: 7.0
axis: governance
weight: 0.70
priority_note: "ADR-2605192245 §"Open Question 2" で要請した steward 死亡時継承 procedure を formal 化する ADR。donation 時の事前指定 + 国家 inheritance 法との整合 + fallback path (指定者拒否 / 死亡時無指定 / 全候補拒否) を定義。多世代 stewardship continuity (§1.9) の technical 実装の核。"
authoritative_for:
  - donation 時の successor steward 事前指定 procedure (`com.etzhayyim.apps.etzhayyim.steward-succession-declaration`)
  - donor 死亡時の succession trigger + activation flow (`com.etzhayyim.apps.etzhayyim.steward-succession-event`)
  - 国家 inheritance 法との dual-recognition pattern
  - fallback paths (4 種)
  - Council Lv6+ による succession 認定
depends_on:
  - adr-2605192245-etzhayyim-global-land-sovereignty
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192300-etzhayyim-bootstrap-council-five
  - adr-2605172600-etzhayyim-membership-ritual
related: []
supersedes: []
superseded_by: []
---

# ADR-2605192345: etzhayyim Steward Succession — donor 死亡時の steward 継承手続き + 多世代 stewardship continuity

**Status**: proposed
**Date**: 2026-05-19
**Deciders**: Jun Kawasaki

# Context

ADR-2605192245 で steward role (Lv5 護) を定義したが、**donor 死亡時の継承** procedure は未定。これは:

- §1.9 多世代 stewardship continuity の technical 実装で最重要
- 国家 inheritance 法 (相続) と religious-corp 内継承の境界調整
- 寄付土地が steward 死亡で「捨て地」化することの防止
- Lv5 護 → 次世代 steward への transmission を formal 化

# Decision

## 1. Donation 時の Successor 事前指定 (Required)

ADR-2605192245 の Land Donation Ritual に **Step 4.5: Successor Designation** を必須追加する。

寄付者は寄付完了時に以下を含む successor 指定 record (`com.etzhayyim.apps.etzhayyim.steward-succession-declaration`) を作成:

```json
{
  "$type": "com.etzhayyim.apps.etzhayyim.steward-succession-declaration",
  "landId": 1234,
  "primarySuccessor": {
    "did": "did:web:successor1.example",
    "sbtTokenId": 5678,
    "relationship": "child" | "spouse" | "trusted-adherent" | "council-appointed",
    "preAcceptanceCid": "ipfs://..."   // primary successor 自身の事前承諾 signed record
  },
  "backupSuccessors": [
    { "did": "...", "sbtTokenId": ..., "preAcceptanceCid": "..." },
    { "did": "...", "sbtTokenId": ..., "preAcceptanceCid": "..." }
  ],
  "fallbackPath": "council-appointed",  // primary + backup all decline 時
  "donorSig": "...",
  "declaredAt": "2026-05-19T..."
}
```

### 1.1 Requirements

- **Primary successor** + **backup successor 2 名以上** (合計 3 名以上の指定)
- 各 successor は事前に `com.etzhayyim.apps.etzhayyim.steward-succession-pre-acceptance` で承諾 sign 済み
- 各 successor は active etzhayyim Adherent SBT holder (Lv5+ 推奨)
- fallback path として `council-appointed` (= 全候補拒否時に Council Lv6+ が任命) または `corpus-direct` (= religious-corp 直接 stewardship、構成員 collective stewardship) を指定

### 1.2 Successor 更新

donor (steward) は alive 中に successor 指定を更新可能。`steward-succession-declaration` の 新 version を MST に書き、最新のものが有効になる。

## 2. Succession Trigger Events

steward role は以下のいずれかで自動的に successor へ移譲される:

| Trigger | Detection | Council 認定 |
|---|---|---|
| **死亡** | 公的死亡記録 + Council 認定 | 必須 (Lv6+ ≥3) |
| **昏睡 / 重大疾患** | 医師 attestation + Council 認定 | 必須 (Lv6+ ≥3) |
| **長期消息不明 (>1 年)** | Council attestation + heartbeat 不在 | 必須 (Lv6+ ≥3) |
| **自発的 step-down** | steward 自身の signed step-down record | Council 認定 (簡略, ≥1) |
| **三層 enforcement (Non-Aligned 認定)** | ChartersComplianceRegistry status = NonAligned (finalized) | 自動 |

### 2.1 Succession Event Lexicon

`com.etzhayyim.apps.etzhayyim.steward-succession-event`:

```json
{
  "$type": "com.etzhayyim.apps.etzhayyim.steward-succession-event",
  "landId": 1234,
  "previousSteward": "did:web:previous.example",
  "newSteward": "did:web:successor1.example",
  "trigger": "death" | "incapacitation" | "absence" | "step-down" | "non-aligned",
  "triggerEvidenceCid": "ipfs://...",
  "successionDeclarationUri": "at://...",
  "councilAttestationUris": ["at://...", "at://...", "at://..."],
  "activatedAt": "2026-05-19T..."
}
```

## 3. National Inheritance Law との Dual-Recognition

steward role は **religious-corp 内 role** であり、国家 inheritance 法 (相続) の対象ではない。しかし donor は国家 registry 上では引き続き土地所有者として記載されており、**国家相続 と religious-corp succession は parallel process** として両立する:

| 観点 | 国家 相続 | etzhayyim Steward Succession |
|---|---|---|
| 法的対象 | donor の private property (土地 + 動産) | religious-corp role (土地所有権ではない) |
| 受益者 | 法定 / 遺言相続人 | steward succession declaration の successor |
| 課税 | 相続税 | n/a (role 移譲のみ) |
| 期間 | 数ヶ月 - 数年 | Council 認定後即時 |
| Conflict 時 | 国家 court | Council Lv6+ + 国家 court parallel |

**国家相続人と religious-corp successor が異なる人物の場合**:

- 土地の国家 registry 上の名義は国家相続人へ移転 (国家法に従う)
- religious-corp 内では successor が新 steward
- 双方が並立 → 国家相続人は名義人だが religious-corp doctrine 上「土地は Tree of Life のもの」を尊重する義務 (= donor の oath が継承される)
- 国家相続人が doctrine を拒否し売却を試みる場合 → ADR-2605192245 §2.3 の constitutional inalienability (売買不可) と国家法の整合が問題 → Council Lv6+ + 法務闘争

### 3.1 Pre-emptive 対策

donor は生前に以下を実行することで国家相続との conflict を最小化:

1. **遺言書** で「本土地は etzhayyim religious-corp に寄進済み、相続人は steward 指定を尊重」を明記
2. **国家 registry に restrictive covenant** (例: 信託登記、地役権設定) を可能な範囲で記載
3. **国家相続人と religious-corp successor を同一人物に指定** (例: 自分の子が両方の役割を負う)
4. **遺言執行者** に Council Lv6+ を指定 (religious-corp と国家手続きの整合役)

## 4. Fallback Paths (4 種)

primary + backup successor が全員 decline / 不適格な場合:

### 4.1 `council-appointed`

Council Lv6+ が SBT holder の中から後継 steward を任命:

```
Council 3-of-Lv6+ multisig
  → 候補 SBT holder の同意 (signed)
  → LandRegistry.reassignSteward(landId, newSteward, councilSigs)
```

### 4.2 `corpus-direct`

religious-corp 直接 stewardship。土地は具体的 individual steward を持たず、構成員 collective が stewardship duty を分担:

- 年次 attestation は Council Lv6+ + Lv5 護 holders の中から rotation で実施
- biodiversity / boundary 維持は地域近隣の Adherent collective
- これは 入会地 (commons) pattern と同じ

### 4.3 `community-trust`

土地を周辺地域の non-etzhayyim community に長期 lease (50 年 lease 等) — religious-corp は overall stewardship を維持しつつ実務的 land use を地域 community に委ねる:

- religious-corp 形式は dual-recognition 維持
- 地域 community は lease 期間 use rights + stewardship duty 一部
- 適用例: 寄付者死亡後、地域 community が religious-corp と協働で土地を共同管理

### 4.4 `dissolution-to-corpus`

donor の指定があれば: religious-corp の 護持金庫 corpus tier に統合し、個別土地としての identity を解消 (= 集合 corpus の一部として運用):

- 個別 stewardship → 集合 stewardship
- ただし constitutional inalienability は維持

## 5. Council Verification Flow

```
[死亡 / トリガー event]
  → com.etzhayyim.apps.etzhayyim.steward-succession-event record 起票
  → triggerEvidence (死亡証明 / 医師 attestation / 不在 attestation 等) を Council Lv6+ がレビュー
  → Council 3-of-Lv6+ が承認 signature
  → LandRegistry.reassignSteward(landId, newSteward, councilSigs)
  → Land record update + AT Record + AnchorBridge.commitRoot
  → 新 steward 通知 (PDS + email if registered)
```

## 6. Special Case: Multi-generational Succession Plan

donor は寄付時に **3 世代以上の succession plan** を declare 可能:

```
Gen 1 (donor) → Gen 2 (子) → Gen 3 (孫) → ...
```

各 generation の successor が事前承諾 record を sign し、世代を超えた continuity を doctrinal に確立する。Gen N 時点で Gen N+1 が未生 (= 子孫が未だ生まれていない) 場合は `pre-accept-future` flag で予約。

これは §1.9 多世代 priority + Mission Charter §1.11 (多世代 stewardship continuity) と完全整合。

# Consequences

## 正の効果

- §1.9 多世代 stewardship continuity が technical に成立
- 寄付土地の「捨て地」化を防止
- 国家相続との dual-recognition が pre-emptive 対策込みで明示
- 4 種 fallback により corner case が全カバー
- 多世代 succession plan が long-horizon stewardship を encode

## 負の効果 / コスト

- donor の事前負担増 (successor 3 名指定 + 事前承諾収集)
- Council Lv6+ judgment 負荷増 (succession 認定毎に 3 名 deliberation)
- 国家相続との conflict が顕在化するリスク
- successor 全員死亡 / decline の極端 case → fallback paths でカバーするが complex

## 中立 / トレードオフ

- successor 事前承諾を donation 時 required にすると寄付の hurdle が上がるが、長期 stewardship 確保には不可欠
- multi-generational plan は long-horizon だが Gen N+1 未生 case の practical 取扱いは Council 判断に依存

# Alternatives Considered

## A. successor は default 国家相続人

Pro: simple。Con: religious-corp doctrine と国家 inheritance が conflate される。doctrinal independence が失われる。却下。

## B. successor 1 名のみ required (backup なし)

Pro: 軽い。Con: 1 名 decline で fallback に直行、流動性が低い。却下: 3 名以上 required。

## C. Council 直接 reassign (donor 指定なし)

Pro: governance 集中。Con: donor の wish が反映されない、religious autonomy 低下。却下: donor 事前指定を優先。

# Open Questions

1. **「死亡」認定の権威** — 国家公的記録 vs Council Lv6+ attestation のどちらを primary とするか。Decision (本 ADR): 国家公的記録を primary、Council はそれを accept する形
2. **Gen N+1 未生時の succession plan の有効性** — 未生児への signing は法的には void。Decision: doctrinal record として残す、Gen N+1 出生 + Adherent SBT 取得時に formal 承諾を再収集
3. **国家相続人による religious-corp 拒否** — 国家相続人が doctrine を拒否し land を売却した場合の救済 path。Decision: ADR-2605192245 §6.2 三段階対応に従う、最悪 case は Status = RehabReversal

# References

- ADR-2605192245 Global Land Sovereignty (Land Trust の host)
- ADR-2605192100 §1.9 多世代 priority + §1.11 Land doctrine
- ADR-2605192300 Bootstrap Council 5名 (Council Lv6+ host)
- ADR-2605172600 Membership ritual (Lv5 護 = Steward の根拠)
- 民法 (相続) — 日本
