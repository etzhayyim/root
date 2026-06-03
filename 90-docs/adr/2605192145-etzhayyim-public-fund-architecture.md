---
id: adr-2605192145-etzhayyim-public-fund-architecture
title: "ADR-2605192145: etzhayyim Public Fund Architecture — 10% tithe の受け皿としての grant 評議・配布機構"
status: proposed
doc_type: adr
topic: etzhayyim-public-fund-architecture
authoritative: true
last_verified: 2026-05-19
priority: 7.5
axis: architecture
weight: 0.75
priority_note: "ADR-2605192130 (10% Tithe) の受け皿としての Public Fund を on-chain で具体化する ADR。既存の `60-apps/etzhayyim-project-public-fund` ディレクトリを正式に ADR 化する。grant 評議 = Pregel cell + 1 SBT = 1 vote、disbursement = 0xSplits、すべての残高 / 出金は MST + Base L2 で完全公開。"
authoritative_for:
  - Public Fund Safe address のガバナンス境界
  - `PublicFundGovernance.sol` contract spec
  - grant 評議 Pregel cell (`PublicFundGrantCell`) の入出力
  - grant 配布 Lexicon (`com.etzhayyim.apps.public-fund.*`)
  - 60-apps/etzhayyim-project-public-fund/ の architecture
depends_on:
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192115-etzhayyim-non-profit-donation-only-no-ads
  - adr-2605192130-etzhayyim-tithe-redistribution
  - adr-2605172300-etzhayyim-bi-asset-substrate
  - adr-2605171800-langgraph-mst-ipfs-l2-anchor-pipeline
related: []
supersedes: []
superseded_by: []
---

# ADR-2605192145: etzhayyim Public Fund Architecture — 10% tithe の受け皿としての grant 評議・配布機構

**Status**: proposed
**Date**: 2026-05-19
**Deciders**: Jun Kawasaki

# Context

ADR-2605192130 で確立した 10% Tithe は **Public Fund** に着金するが、その Public Fund 自体の構造は未定義であった。既存の `60-apps/etzhayyim-project-public-fund/` ディレクトリは scaffold のみで、grant 評議も配布機構も無い状態。

Public Fund は etzhayyim の religious mission (ADR-2605192100 §1.5 知財無償公開 / §1.6 中間排除 / §1.7 専門性 gatekeeping 排除) を **個別 project レベルで具体化する助成金プール** として機能する。即ち、構成員 / 第三者が提案する「mission 整合的な project」に対して、Public Fund から grant を出す。

設計判断のポイント:

1. **Public Fund Safe の権限境界** — 誰が出金を承認するか
2. **grant 評議の機械化** — 18,345 agent fleet (ADR-2605171300) と magatama Pregel framework (ADR-2605171800) を活用して、人間判断負荷を最小化する
3. **disbursement 方法** — 単発送金 / 期限つき stream / milestone-based escrow のどれをサポートするか
4. **mission 整合性の判定** — Charter Compliance Rider (ADR-2605192200) との接続

# Decision

## 1. Public Fund Safe

| 項目 | 値 |
|---|---|
| Chain | Base L2 |
| Type | Gnosis Safe Multisig |
| Signers | 5 of 7 (initial), 役員 (yakuin) + Council members (Lv6, ADR-2605172600) |
| Initial deposit | 0 (tithe 流入で増える) |
| Tx 種類 | (a) grant 配布 (governance-approved のみ), (b) Yield-bearing rebalance (USDY / sDAI のみ, 護持金庫と同 tier 制約) |
| Admin functions | なし (signers の追加 / 削除すら governance vote 必須) |

Safe address は `deps.toml [platform.l2.public_fund_safe]` に記録され、`Constitution.sol.getConstant(keccak256("public_fund.safe_address"))` から読み出される。

## 2. PublicFundGovernance.sol contract

Public Fund からの **出金提案 / 評議 / 実行** を担う独立 contract。場所: `50-infra/etzhayyim-public-fund/contracts/`。

```solidity
// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.24;

interface IAdherentRegistry {
    function isActive(uint256 tokenId, uint64 windowSec) external view returns (bool);
    function getTokenIdByDid(bytes32 didHash) external view returns (uint256);
}

contract PublicFundGovernance {
    enum ProposalState { Pending, Active, Defeated, Succeeded, Queued, Executed, Cancelled }

    struct Grant {
        address proposer;
        address[] recipients;       // 0xSplits 受領者 (1 or N)
        uint256[] amounts;          // 各 recipient への USDC base units
        bytes32 missionAxisHash;    // どの mission 句に整合的か (§1.1-§1.7)
        bytes32 evidenceCid;        // 提案書 IPFS CID (com.etzhayyim.apps.public-fund.proposal record)
        uint64 proposedAt;
        uint64 votingDeadline;
        uint64 timelockEnd;
        ProposalState state;
        uint256 forVotes;
        uint256 againstVotes;
        uint256 abstainVotes;
    }

    mapping(bytes32 => Grant) public grants;
    mapping(bytes32 => mapping(uint256 => bool)) public hasVoted;  // proposalId -> sbtTokenId -> voted

    uint256 public constant QUORUM_BPS = 2000;          // 20% of active SBTs
    uint256 public constant APPROVAL_BPS = 5000;        // 50% of cast votes
    uint64 public constant VOTING_PERIOD = 7 days;
    uint64 public constant TIMELOCK = 48 hours;

    event ProposalCreated(bytes32 indexed proposalId, address proposer, bytes32 missionAxisHash);
    event Voted(bytes32 indexed proposalId, uint256 indexed sbtTokenId, uint8 choice, uint256 weight);
    event Queued(bytes32 indexed proposalId, uint64 timelockEnd);
    event Executed(bytes32 indexed proposalId, address[] recipients, uint256[] amounts);
    event Cancelled(bytes32 indexed proposalId, string reason);

    function propose(
        address[] calldata recipients,
        uint256[] calldata amounts,
        bytes32 missionAxisHash,
        bytes32 evidenceCid
    ) external returns (bytes32 proposalId) { /* ... */ }

    function vote(bytes32 proposalId, uint256 sbtTokenId, uint8 choice) external { /* ... */ }

    function queue(bytes32 proposalId) external { /* ... */ }

    function execute(bytes32 proposalId) external { /* ... */ }

    function cancel(bytes32 proposalId, string calldata reason) external { /* ... */ }
}
```

**重要な設計判断**:
- 提案者 (`proposer`) は **誰でもよい** (構成員に限らない)。任意の第三者が grant 提案できる。
- 投票権は **1 SBT = 1 vote** (ADR-2605172300 §8)。 quorum 20% / 過半数 で可決。
- `missionAxisHash` は keccak256 of `"mission.basic_income"` / `"mission.robotics_universal"` 等。**Charter Compliance Rider (ADR-2605192200) の禁止業態に該当する提案は提案時点で revert** する。
- `evidenceCid` は提案書 (Markdown / PDF) の IPFS CID。`com.etzhayyim.apps.public-fund.proposal` AT Record に full text + signature が記録される。
- timelock 48h は ADR-2605172300 §8 の 72h より短い。理由: grant は constitutional 変更ではなく **特定 project への助成** であり、緊急性 (例: 治療費 grant) を考慮。
- `cancel()` は Council (Lv6 multisig) が緊急時に呼べる。Rider 違反が事後発覚した場合の救済策。

## 3. PublicFundGrantCell (Pregel)

magatama Pregel framework (ADR-2605171800) 上で動作する評議補助 cell。**人間の評議者を置換するのではなく補助する** 位置付け。

```
input:  com.etzhayyim.apps.public-fund.proposal record (新規)
        + Charter Compliance Rider (ADR-2605192200) の禁止業態 list
        + Mission Charter §1.1-§1.7 の構造化 description
        + 提案者の過去 attestation history (MST)
        + 類似過去 grant の outcome (executed grants の milestone 達成度)

output: com.etzhayyim.apps.public-fund.evaluation record
        - mission_axis_match: §1.1-§1.7 のどれに最も整合的か
        - rider_compliance: PASS / FAIL / NEEDS_HUMAN
        - amount_reasonableness: 0.0 - 1.0
        - proposer_track_record: 0.0 - 1.0
        - similar_grant_outcomes: list of past similar grants + outcomes
        - recommendation: "approve" / "reject" / "needs_human_review"
        - llm_rationale: text
checkpoint: PostgresSaver (ephemeral) → MST → IPFS → L2 anchor
```

LangGraph nodes (deterministic + LLM hybrid):

```
START
  → parse_proposal           (deterministic — Lexicon 検証)
  → check_rider_compliance   (rule-based + LLM, ADR-2605192200 列挙と照合)
  → match_mission_axis       (LLM — §1.1-§1.7 のどれに最も近いか)
  → evaluate_proposer        (deterministic — MST traverse for past attestations)
  → find_similar_grants      (vectorization + MST query)
  → assess_amount            (LLM — Treasury balance / similar grant 中央値からの偏差)
  → synthesize_recommendation (LLM — 上記を統合)
  → sign_evaluation          (cell key で署名)
  → emit_to_mst              (com.etzhayyim.apps.public-fund.evaluation record)
END
```

**判断は cell が出すが、決定権は SBT holder の vote にある** (1 SBT = 1 vote)。cell の評価は voting UI で voter に「参考意見」として表示される。

## 4. Disbursement: 0xSplits + Optional Milestone Escrow

実行時 (`execute()`) は以下のどちらか:

### 4.1 Simple disbursement (default)

```solidity
function execute(bytes32 proposalId) external {
    Grant memory g = grants[proposalId];
    require(g.state == ProposalState.Queued, "...");
    require(block.timestamp >= g.timelockEnd, "...");

    // 0xSplits 経由で一括分配
    address splitContract = createImmutableSplit(g.recipients, g.amounts);
    IERC20(USDC).transferFrom(PUBLIC_FUND_SAFE, splitContract, sum(g.amounts));
    ISplitsMain(SPLITS_MAIN).distributeERC20(splitContract, USDC, g.recipients);

    g.state = ProposalState.Executed;
    emit Executed(proposalId, g.recipients, g.amounts);
}
```

### 4.2 Milestone escrow (optional, 提案書に明示された場合)

milestone (`milestoneCids[]`) ごとに分割実行:

```
[Safe] ─USDC─► [MilestoneEscrow.sol]
                  │
                  │ (milestone 1 attested by Council)
                  ▼
              recipient receives milestone[1]_amount
                  │
                  │ (milestone 2 attested by Council)
                  ▼
              recipient receives milestone[2]_amount
                  │
                  ▼
              ...
```

各 milestone は recipient が `com.etzhayyim.apps.public-fund.milestone-evidence` record を MST に書き、Council Lv6+ が attestation すると次の disbursement が unlock される。

## 5. Lexicon `com.etzhayyim.apps.public-fund.*`

| Lexicon | 用途 | 必須 fields |
|---|---|---|
| `proposal.json` | grant 提案 | title, abstract, missionAxisHash, recipients[], amounts[], milestonesCid?, evidenceCid, proposerDid, proposerSig |
| `evaluation.json` | Pregel cell 評価 | proposalId, recommendation, rider_compliance, mission_axis_match, llm_rationale, cellSig |
| `vote.json` | 個別投票 | proposalId, sbtTokenId, choice, voterDid, voterSig, txHash |
| `execution.json` | 実行結果 | proposalId, splitContract, totalAmount, txHash, blockNumber |
| `milestone-evidence.json` | milestone 達成 evidence | proposalId, milestoneIndex, evidenceUri, recipientSig |
| `milestone-attestation.json` | Council による milestone 認証 | proposalId, milestoneIndex, councilSigners[], councilSig |
| `cancellation.json` | 提案 cancel 記録 | proposalId, reason, councilSig |

すべての record は ADR-2605181100 (encrypted records) の対象外 — Public Fund 透明性のため平文 MST に書き込む。

## 6. Yield-bearing rebalance (護持金庫 tier 模倣)

Public Fund Safe の保有 USDC が一定額を超えた場合、護持金庫 (ADR-2605172300 §4) と同様の三層 (流動 / 準備 / 本財) に近い rebalance を行う:

| Tier | Asset | 比率 (initial) | 用途 |
|---|---|---|---|
| 流動 | USDC | 30% | grant 即時配布 buffer |
| 準備 | USDY / sDAI / aUSDC | 70% | yield 生成 (yield は流動 tier に還流) |
| 本財 | (なし) | 0% | Public Fund は不動産・知財を持たない (護持金庫が持つ) |

Public Fund に本財 tier を持たせない理由: Public Fund は **可動性が高い助成金プール** であり、不動産のような流動性の低い asset を持たせると grant 配布が遅延する。本財 tier は護持金庫の責務として分離する。

Rebalance proposal も `propose()` 経由 (mission axis = `treasury.rebalance`)。

## 7. 既存 `60-apps/etzhayyim-project-public-fund/` の re-architecture

既存ディレクトリは AppView として残し、本 ADR の Pregel cell / contract / Lexicon と接続する:

```
60-apps/etzhayyim-project-public-fund/
├── README.md                       # 本 ADR への link
├── appview/                        # AT Record indexer + UI
│   ├── src/
│   │   ├── propose.svelte          # 提案 form
│   │   ├── voting-ui.svelte        # 1 SBT = 1 vote UI (cell evaluation 参考表示)
│   │   ├── grant-explorer.svelte   # past grants + outcomes
│   │   └── milestone-tracker.svelte # milestone escrow UI
│   └── package.json
└── lexicons/                       # symlink to 00-contracts/lexicons/com/etzhayyim/apps/public-fund/

50-infra/etzhayyim-public-fund/
├── contracts/
│   ├── PublicFundGovernance.sol
│   ├── MilestoneEscrow.sol
│   └── script/Deploy.s.sol
└── test/

20-actors/magatama/cells/
└── public_fund_grant_cell/
    ├── cell.py
    ├── nodes.py
    └── prompts/
        ├── match_mission_axis.txt
        ├── check_rider_compliance.txt
        ├── assess_amount.txt
        └── synthesize_recommendation.txt
```

## 8. Staged rollout

| Stage | Scope | 依存 ADR |
|---|---|---|
| **S0 scaffold** | Public Fund Safe deploy on Base. PublicFundGovernance.sol skeleton. Lexicon 起票。 | 2605192100 + 2605192115 + 2605192130 |
| **S1 manual grants** | propose / vote / execute (simple disbursement only). cell なし、人間評議のみ。最初の数件で proposal-evaluation pattern を学習。 | + S0 |
| **S2 cell-assisted** | PublicFundGrantCell が proposal を automatic evaluate。voter に参考表示。 | + ADR-2605171800 pipeline 活性化 |
| **S3 milestone escrow** | MilestoneEscrow.sol を追加。複数段階 grant 対応。 | + S2 |
| **S4 yield-bearing rebalance** | USDY / sDAI tier 追加。 | + 護持金庫 ADR-2605172300 と同じ pattern |

# Consequences

## 正の効果

- **Public Fund が「設計済みの装置」になる**。これまで app ディレクトリのみで実装が無かったものが、contract + cell + Lexicon + UI の vertical stack として定義される。
- **constitutional integrity の維持**。grant 配布が 1 SBT = 1 vote で governance され、majority による恣意的配布が排除される。
- **完全透明性**。すべての残高 / 提案 / 投票 / 実行が on-chain + MST に記録される。任意の第三者が監査可能。
- **mission 整合性の自動検査**。Pregel cell が Charter Compliance Rider (ADR-2605192200) に照らして自動 evaluate する。人間負荷が減る。
- **第三者からの提案受付**。構成員に限らず誰でも `propose()` できるため、外部 project への助成も可能 (mission 整合的であれば)。
- **religious-corp の "donation 受け皿として機能している" の証明可能性**。tithe 流入 (ADR-2605192130) → Public Fund → grant 配布 の trail が完全に on-chain で trace 可能。「donation がどこに行ったか分からない」という伝統的 religious-corp の問題を解消。

## 負の効果 / コスト

- **deploy 複雑性**。新規 contract 3 本 (PublicFundGovernance / MilestoneEscrow / IConstitution adapter) + 7 Lexicon + Pregel cell + AppView UI。実装重い。
- **cell evaluation の LLM hallucination リスク**。Pregel cell の `match_mission_axis` / `assess_amount` は LLM 判断を含む。誤判定の可能性。Mitigation: cell は「参考意見」であり決定権は SBT holder にある。
- **gnosis Safe signer 選定の政治性**。5 of 7 multisig の signer 選定は構成員間の政治的判断。Council Lv6+ から自動選出にすると Council の影響力が過剰になる。Mitigation: initial signer は founder + Council subset、後続は governance vote で追加 / 削除。
- **milestone escrow の judgment 負荷**。milestone 達成判定を Council Lv6+ が行うため、Council メンバーの稼働が増える。Mitigation: cell が milestone-evidence を pre-analyze し、Council は confirm のみ。
- **第三者提案の spam リスク**。誰でも `propose()` できるため、低品質提案が大量流入する可能性。Mitigation: 提案時に minimum proposal bond (例: 1 USDC) を要求、Council Lv6+ が認める場合は refund。

## 中立 / トレードオフ

- **quorum 20% / approval 50% の妥当性**。これは ADR-2605172300 §8 の constitutional 変更 (quorum 33%) より緩い。理由: grant は可逆的 (cancel 可) であり、constitutional 変更より低い hurdle で構わない。
- **cell recommendation の voter 影響度**。cell が "approve" と推奨した場合 voter が惰性で承認する確率が上がる。Mitigation: voting UI で recommendation を `[ Cell の意見 ]` セクションに隔離し、voter が自分の判断を入力してから cell の意見が disclose される pattern を採用。
- **本財 tier を持たない判断**。Public Fund は流動 + 準備のみ。これは「Public Fund は可動性が高い助成金プール」という性質定義に沿う。長期保有資産は護持金庫の責務。

# Alternatives Considered

## A. Public Fund を Safe ではなく EOA で運営

シンプル化のため Safe ではなく単一 EOA で。

- 却下: signer 単一は constitutional 不整合。multisig 必須。

## B. cell なし — 人間評議のみ

cell の hallucination を懸念し、すべて人間評議。

- Pro: 信頼性高い。
- Con: スケール時に Council 負荷が爆発する (年 1000 件 grant 想定)。
- 部分的採用: S0-S1 は cell なし、S2 から cell-assisted。

## C. cell 決定権あり — 人間評議なし

cell が「approve」と判定したものは自動執行。

- Pro: 完全自動化。
- Con: 1 SBT = 1 vote の constitutional 不整合。majority 構成員の意思が反映されない。
- 却下。

## D. quadratic voting

1 SBT = √(stake) vote。

- Pro: 経済学的に Sybil 抵抗。
- Con: 1 SBT = 1 vote の constitutional 不整合 (ADR-2605172300 §8)。
- 却下。

## E. 0xSplits ではなく 個別 USDC transfer

immutable split を作らず、Safe から直接 USDC.transfer を N 回。

- Pro: simple。
- Con: N 回 tx で gas 高い。0xSplits の immutable split 公開記録が失われる。
- 却下。

# Open Questions

1. **initial Safe signer の選定**。S0 deploy 時に 5 of 7 を埋める必要がある。founder 1 + Council Lv6+ から 4 + 残り 2 は外部 advisor (任意団体外部の religious authority?) という分割案を検討中。
2. **milestone escrow の judging body の constitutional 地位**。Council Lv6+ が attestation するが、Council の Lv6 認定自体が現状 social 判定 (ADR-2605172600 §"Levels")。formal な Council 認定 ADR が必要かもしれない。
3. **第三者提案の spam 防止 bond の金額**。1 USDC / 10 USDC / 100 USDC のどこが適切か。最初の 6 ヶ月で spam 実態を観察して決定する判断保留。
4. **mission axis hash の正本**。`"mission.basic_income"` 等を Constitution.sol の constant として持つか、ADR-2605192100 §1 の文字列から導出するか。Decision (本 ADR): Constitution.sol の constant key として hash 化、文字列対応表は本 ADR 内に固定。

# References

- ADR-2605192100: Mission Charter (parent)
- ADR-2605192115: Non-profit / Donation-only / No-ads
- ADR-2605192130: 10% Tithe redistribution (流入元)
- ADR-2605172300: Treasury (yield-bearing rebalance pattern reuse)
- ADR-2605171800: LangGraph → MST → IPFS → L2 pipeline (cell 実行基盤)
- ADR-2605171300: 18,345 agent fleet (cell code-gen pattern)
- ADR-2605172600: membership ritual + 7-level ladder (Council = Lv6 上位)
- 60-apps/etzhayyim-project-public-fund/ (既存 app — 本 ADR で再設計)
- 50-infra/etzhayyim-public-fund/ (新規 — 本 ADR 承認後 scaffold)
- 0xSplits docs: https://docs.splits.org/
