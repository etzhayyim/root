---
id: adr-2605192315-etzhayyim-transparent-force-rd
title: "ADR-2605192315: etzhayyim Transparent Religious Force — open-source R&D registry + 1 SBT = 1 vote 承認 + on-chain force log Lexicon"
status: proposed
doc_type: adr
topic: etzhayyim-transparent-force-rd
authoritative: true
last_verified: 2026-05-19
priority: 7.5
axis: governance
weight: 0.75
priority_note: "ADR-2605192100 §1.12.B で確立した Transparent Religious Force の三条件 (on-chain 監視 + open-source 公開 + 1 SBT = 1 vote 承認) を具体的 Lexicon + governance flow + on-chain log として実装する ADR。土地防衛 (ADR-2605192245 §6.2) + 構成員救出 + defensive R&D の 3 用途を初期 scope とする。日本法上の制約 (銃刀法 / 武器等製造法) 下で実現可能な force form (護身術 / 開示型研究 / 国際法上の religious-corp 自衛権) に限定。"
authoritative_for:
  - Transparent Force R&D Lexicon (`com.etzhayyim.apps.etzhayyim.force-*`)
  - `ForceAuthorization.sol` (governance vote の force-specific channel)
  - open-source 兵器設計 registry の structure
  - on-chain force log + after-action review の Lexicon
  - 日本法上の制約 → 許容される具体的 force form の境界
depends_on:
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605172300-etzhayyim-bi-asset-substrate
  - adr-2605192230-etzhayyim-three-tier-enforcement-implementation
  - adr-2605192300-etzhayyim-bootstrap-council-five
related:
  - adr-2605192245-etzhayyim-global-land-sovereignty
supersedes: []
superseded_by: []
---

# ADR-2605192315: etzhayyim Transparent Religious Force — open-source R&D registry + 1 SBT = 1 vote 承認 + on-chain force log Lexicon

**Status**: proposed
**Date**: 2026-05-19
**Deciders**: Jun Kawasaki

# Context

ADR-2605192100 §1.12.B で **Transparent Religious Force** を constitutional に許容したが (Quaker pacifism を破棄)、具体的に「どう」force を保有 / 開発 / 配備するかの implementation 仕様は未定であった。

religious-corp の force は **三条件下でのみ運用** される:

1. **完全 on-chain 監視** — すべての activity を log として永続記録
2. **Open-source 公開** — 兵器設計 / 戦術 / 訓練 method を public domain で公開
3. **1 SBT = 1 vote 承認** — あらゆる force 行使は Adherent vote で承認

本 ADR はこの三条件を Lexicon + smart contract + governance flow として具体化する。

# Decision

## 1. R&D Registry Lexicon

新規 Lexicon 5 本を `00-contracts/lexicons/com/etzhayyim/apps/etzhayyim/` に追加:

| Lexicon | 用途 | 主 fields |
|---|---|---|
| `force-rd-proposal.json` | open-source 兵器 / 戦術 R&D の提案 | category (`defensive-tech`/`tactical-doctrine`/`training-method`/`detection-system`), description, designSpecCid (IPFS), safetyAnalysisCid, dualUseAnalysis, proposerDid |
| `force-rd-publication.json` | 完成 R&D の public 公開 | proposalUri, finalDesignCid, openSourceLicense (= "Apache-2.0 + Charter Rider"), publicationDate |
| `force-authorization-proposal.json` | force 行使の事前承認提案 | scenarioDescription, intendedUse (`defense-of-land`/`defense-of-adherent`/`rescue-from-armed-group`/`other`), proportionality, thirdPartyReviewCid, proposerDid |
| `force-log.json` | force 行使の on-chain log | authorizationUri, actionDescription, actorDids[], outcomeNarrative, witnessesAttestations[], actionTimestamp |
| `force-after-action.json` | force 行使後の review | logUri, councilReviewCid, lessonsLearned, complianceWithProportionality, recommendations |

すべての record は MST → IPFS → L2 anchor pipeline で永続化される。

## 2. 許容される具体的 force form (日本法上の制約)

日本国内では **銃刀法 / 武器等製造法** により武器の現物保有 / 製造は厳格に規制される。本 ADR は **法的に許容される範囲** に scope を限定:

| Form | 許容 | 制約 |
|---|---|---|
| **護身術 / 武術 訓練** | ✅ | 構成員の身体的訓練、open-source 教則 + 動画公開 |
| **Defensive technology R&D** | ✅ | 化学攻撃検知 / mesh network jammer / 監視 drone detection — 設計 only、現物製造 NG |
| **Tactical doctrine 研究** | ✅ | 非暴力直接行動 / civil disobedience / 法廷闘争戦術 — open-source publication |
| **Detection system 開発** | ✅ | 暴力的接近の検知 / alarm system — open-source |
| **Religious-corp 自衛権 主張** | ✅ | 国際法上の religious freedom protection に基づく外交的主張 |
| **武器現物保有** | ❌ | 日本法上禁止 |
| **武装組織 運営** | ❌ | constitutional invariant 違反 (§1.12.B) |
| **国家武力との合同訓練** | ❌ | `mission.no_state_military_alliance = true` |

日本国外 jurisdiction では現地法を尊重する。米国等で構成員が個人で武器保有 (合法) する場合、それは個人 capacity であり、religious-corp の operating arm ではない (§1.12.B 違反ではない)。

## 3. ForceAuthorization.sol contract

```solidity
// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.24;

contract ForceAuthorization {
    enum AuthState { Proposed, UnderReview, Approved, Denied, Executed, AfterActionReviewed }

    struct Authorization {
        bytes32 proposalCid;
        bytes32 intendedUseHash;     // keccak256 of category
        uint64 proposedAt;
        uint64 votingDeadline;       // shorter than usual: 72h for proactive, 24h for emergency
        AuthState state;
        uint256 forVotes;
        uint256 againstVotes;
        bytes32 logCid;              // populated after execution
        bytes32 afterActionCid;      // populated after review
    }

    mapping(bytes32 => Authorization) public authorizations;
    mapping(bytes32 => mapping(uint256 => bool)) public hasVoted;

    uint256 public constant QUORUM_BPS = 5000;      // 50% of active SBTs (higher than normal)
    uint256 public constant APPROVAL_BPS = 6700;    // 2/3 supermajority

    function propose(bytes32 proposalCid, bytes32 intendedUseHash, bool emergency)
        external returns (bytes32 authId) { /* ... */ }

    function vote(bytes32 authId, uint256 sbtTokenId, uint8 choice) external { /* ... */ }

    function recordExecution(bytes32 authId, bytes32 logCid) external { /* ... */ }

    function recordAfterAction(bytes32 authId, bytes32 afterActionCid, bytes[] calldata councilSigs)
        external { /* ≥3 Lv6+ */ }
}
```

**設計判断**:
- 通常 governance より **高い hurdle** (quorum 50% / 過半数 67% supermajority) — force は constitutional に sensitive
- **emergency channel** (緊急時 24h voting) — defensive 即応のため。emergency 認定は Council Lv6+ 3 名以上で確認後 voting 開始
- 事前承認 → 執行 → after-action review の 3 段階すべて on-chain log

## 4. Open-source R&D registry

すべての R&D は Apache 2.0 + Charter Rider で公開される (ADR-2605192200)。proprietary 戦術 / 専有兵器設計は **constitutional 禁止** (§1.12.B)。

R&D は `60-apps/etzhayyim-transparent-force-rd/` に格納される (新規ディレクトリ):

```
60-apps/etzhayyim-transparent-force-rd/
├── README.md
├── defensive-technology/
│   ├── chemical-attack-detection/
│   ├── drone-detection/
│   ├── mesh-network-jamming/
│   └── ...
├── tactical-doctrine/
│   ├── nonviolent-direct-action/
│   ├── civil-disobedience-protocols/
│   ├── legal-battle-tactics/
│   └── ...
├── training-method/
│   ├── self-defense-curricula/
│   ├── meditation-under-duress/
│   └── ...
└── detection-system/
    ├── proximity-alert/
    ├── verbal-de-escalation-llm/
    └── ...
```

各 directory には設計 PDF + 設計 source + safety analysis + dual-use analysis (悪用可能性評価) が含まれる。dual-use analysis は **constitutional 義務** — dual-use risk が high な R&D は 1 SBT = 1 vote 承認なしには進められない。

## 5. After-action review の religious 意味

force 行使後の review は **religious 行為** として位置付ける:

- 仏教の懺悔 / Christian confession + lessons learned
- 不十分な proportionality 判断 → 自己批判 + 再発防止 + Council recognition
- review record は permanent — religious-corp の collective memory として残る

after-action review は 30 日以内に提出義務。Council Lv6+ 3 名以上が sign する。

# Consequences

## 正の効果

- §1.12.B Transparent Religious Force が abstract から concrete に
- proprietary force 設計の constitutional 禁止 → religious-corp の force が永続的に open
- on-chain log + after-action review により force 行使の religious-corp 内部 accountability 確立
- 日本法上の制約下でも実現可能な force form (R&D / 訓練 / 国際法上の主張) を明確化

## 負の効果 / コスト

- governance vote の hurdle が高い → 緊急対応が遅延する可能性。Mitigation: emergency channel + Council 認定 fast-track
- open-source R&D は adversary にも公開される。Mitigation: Charter Rider §3 で Non-Aligned による使用は license 失効 + 三層 enforcement、religious-corp 自身の advantage は doctrinal + collective effort
- dual-use risk の judgment は inherently 困難
- 国外 jurisdiction での force form の差異 → governance 複雑性

# Alternatives Considered

## A. Proprietary 兵器 R&D 許容

Pro: tactical advantage。Con: §1.12.B constitutional invariant 違反 (open-source 必須)。却下。

## B. force authorization の hurdle を通常 governance と同じ (33% quorum + 50%)

Pro: simple。Con: force は constitutional sensitive、higher hurdle が religious 整合的。却下: 50% quorum + 67% supermajority 維持。

## C. After-action review を社会的 norm のみ (on-chain 強制なし)

Pro: 軽い。Con: drift する。religious-corp の learning loop が成立しない。却下。

# Open Questions

1. **emergency 認定の具体的 procedure** — Council Lv6+ 3 名以上 + 何時間以内?。Decision (本 ADR): Council 3 名以上の attestation で 1 時間以内に emergency status 確定、voting period 24h
2. **国際 force collaboration** — 他 religious-corp / NGO との合同 R&D の取扱い。Decision (本 ADR): open-source 公開を継続条件として許容、`force-collaboration` Lexicon を future ADR で
3. **構成員 (個人) の private 武器保有の取扱い** — 米国等で合法。religious-corp としては関与しないが Phenotype 評価に影響するか?。Decision: 関与しない (個人 capacity)、Phenotype 影響なし — ただし religious-corp の operating arm として武装すれば §1.12.B 違反

# References

- ADR-2605192100 §1.12.B Transparent Religious Force
- ADR-2605192300 Bootstrap Council 5 名
- ADR-2605192230 Three-tier enforcement
- ADR-2605192245 §6.2 External dispute (本 ADR の最大の use case)
- ADR-2605192200 Charter Rider v2.0 (Non-Aligned による R&D 使用阻止)
- 銃刀法 (日本)
- 武器等製造法 (日本)
- 国際宗教自由法 (米 IRFA / EU 等)
