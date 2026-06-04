---
id: adr-2604281400-oss-contribution-royalty-gcc-redistribution
title: "ADR-2604281400: OSS/データコントリビューター GCC ロイヤルティ自動再分配"
status: proposed
doc_type: adr
topic: oss-contribution-royalty
authoritative: true
last_verified: 2026-04-28
authoritative_for:
  - oss-contribution-royalty
related:
  - adr-0074-ethereum-identity-bridge-cacao-webauthn
  - adr-0056-bpmn-as-actor
  - adr-2604261100-rego-dmn-policy-decision-layers
---

# ADR-2604281400: OSS/データコントリビューター GCC ロイヤルティ自動再分配

**Status**: proposed
**Date**: 2026-04-28
**Context**: ADR-0074 (ERC725 root identity), GCC Phase 2-A contracts, ADR-0056 (BPMN-as-actor)

---

## 問題

いらすとや / irasutoya（無料クリップアート）・GitHub OSS ライブラリ・HuggingFace モデル・参照データセットなど、platform actor の成果物の基盤となったコントリビューターが現状ゼロ補償。Platform が成長するにつれ、これらの一次資産が生む価値が外部に漏れ続ける。

**設計ゴール**: actor が成果物を生成するたびに、その成果物が依存したコントリビューションソースの保有者へ GCC が自動配分される仕組みをオンチェーン＋グラフ＋BPMN の 3 層で構築する。

---

## アーキテクチャ概観

```
Actor (inference / render / deploy)
  │  usage emit  (vertex_contribution_usage)
  ▼
RisingWave MV (mv_contribution_royalty_daily)
  │  daily batch
  ▼
Zeebe BPMN (contributionRoyaltyDistribute.bpmn  R/PT24H)
  │  ContributionRoyaltyRegistry.credit()
  ▼
On-chain ContributionRoyaltyRegistry (chainId 260425)
  │  claim()
  ▼
Contributor smart-account (GCC balance +)
```

---

## コンポーネント詳細

### 1. オンチェーン: ContributionRoyaltyRegistry

新規 Solidity コントラクト。GCC をプールし、コントリビューターが `claim()` で引き出す。

```solidity
// src/ContributionRoyaltyRegistry.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.23;

import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {Ownable2Step} from "@openzeppelin/contracts/access/Ownable2Step.sol";

contract ContributionRoyaltyRegistry is Ownable2Step {
    IERC20 public immutable gcc;
    address public oracle;  // sealer EOA / BPMN worker key

    // keccak256(canonical_id) → contributor smart-account address
    mapping(bytes32 => address) public contributors;
    // contributor address → accumulated earned GCC (wei)
    mapping(address => uint256) public earned;
    // unclaimed mapping: keccak256("github:{handle}") → wei
    // used when contributor not yet registered on platform
    mapping(bytes32 => uint256) public pendingEarned;

    event SourceRegistered(bytes32 indexed sourceHash, address indexed contributor);
    event Credited(address indexed contributor, uint256 amount);
    event PendingCredited(bytes32 indexed sourceHash, uint256 amount);
    event Claimed(address indexed contributor, uint256 amount);
    event PendingClaimed(bytes32 indexed sourceHash, address indexed contributor, uint256 amount);

    constructor(address _gcc, address _oracle, address _owner) {
        gcc = IERC20(_gcc);
        oracle = _oracle;
        _transferOwnership(_owner);
    }

    // Safe governance: register source → contributor mapping
    function registerSource(bytes32 sourceHash, address contributor) external onlyOwner {
        contributors[sourceHash] = contributor;
        emit SourceRegistered(sourceHash, contributor);
    }

    // Oracle (BPMN worker / sealer) credits batched earnings
    function credit(
        bytes32[] calldata sourceHashes,
        uint256[] calldata amounts
    ) external {
        require(msg.sender == oracle, "not oracle");
        require(sourceHashes.length == amounts.length, "length mismatch");
        uint256 total;
        for (uint256 i = 0; i < sourceHashes.length; i++) {
            address c = contributors[sourceHashes[i]];
            if (c != address(0)) {
                earned[c] += amounts[i];
                emit Credited(c, amounts[i]);
            } else {
                pendingEarned[sourceHashes[i]] += amounts[i];
                emit PendingCredited(sourceHashes[i], amounts[i]);
            }
            total += amounts[i];
        }
        require(gcc.transferFrom(msg.sender, address(this), total), "transfer failed");
    }

    // Contributor withdraws their GCC
    function claim() external {
        uint256 amount = earned[msg.sender];
        require(amount > 0, "nothing to claim");
        earned[msg.sender] = 0;
        require(gcc.transfer(msg.sender, amount), "transfer failed");
        emit Claimed(msg.sender, amount);
    }

    // When a contributor registers post-hoc, claim pending balance
    function claimPending(bytes32 sourceHash) external {
        require(contributors[sourceHash] == msg.sender, "not registered contributor");
        uint256 amount = pendingEarned[sourceHash];
        require(amount > 0, "nothing pending");
        pendingEarned[sourceHash] = 0;
        require(gcc.transfer(msg.sender, amount), "transfer failed");
        emit PendingClaimed(sourceHash, msg.sender, amount);
    }

    function setOracle(address _oracle) external onlyOwner {
        oracle = _oracle;
    }
}
```

**デプロイ先**: `contracts/src/ContributionRoyaltyRegistry.sol` + `script/DeployContributionRegistry.s.sol`
**オーナー**: Safe `0xc0C2…`
**オラクル**: sealer EOA (将来は dedicated BPMN bot key)
**初期 GCC 供給**: Safe から `gcc.transfer(registry, 10_000e18)` で 10,000 GCC をプールに入金

---

### 2. グラフ層: RisingWave テーブル + MV

```sql
-- コントリビューションソース登録表 (オンチェーンの mirror + 追加メタデータ)
CREATE TABLE vertex_contribution_source (
    vertex_id        VARCHAR PRIMARY KEY,
    -- keccak256(canonical_id) — オンチェーン sourceHash と一致
    source_hash      VARCHAR(66) NOT NULL,
    -- 正規化された識別子
    -- 形式: "{type}:{namespace}/{id}"
    -- 例: "oss:github.com/encode/httpx"
    --      "media:irasutoya.com/illustrator"
    --      "model:huggingface.co/mistralai/Mixtral-8x7B-Instruct-v0.1"
    --      "dataset:huggingface.co/datasets/HuggingFaceH4/ultrachat_200k"
    canonical_id     VARCHAR NOT NULL,
    source_type      VARCHAR NOT NULL,     -- oss | media | model | dataset | api
    contributor_did  VARCHAR,              -- platform DID (nullable — 未登録者は pending)
    contributor_addr VARCHAR,              -- smart-account / EOA address
    royalty_bps      INT DEFAULT 100,      -- basis points (100 = 1%)
    description      VARCHAR,
    license          VARCHAR,              -- MIT, Apache-2.0, CC-BY-4.0, etc.
    created_at       VARCHAR NOT NULL,
    actor_did        VARCHAR NOT NULL,
    org_did          VARCHAR NOT NULL DEFAULT 'anon'
);

-- 使用イベント (actor が毎回 emit)
CREATE TABLE vertex_contribution_usage (
    vertex_id        VARCHAR PRIMARY KEY,
    source_hash      VARCHAR(66) NOT NULL,
    consumer_did     VARCHAR NOT NULL,     -- 使用した actor の DID
    usage_type       VARCHAR NOT NULL,     -- inference | render | deploy | query | embed
    -- GCC 換算の使用価値 (wei decimal string)。
    -- 0 = 無料利用でも使用ログは記録する
    gcc_value_wei    VARCHAR DEFAULT '0',
    used_at          VARCHAR NOT NULL,
    actor_did        VARCHAR NOT NULL,
    org_did          VARCHAR NOT NULL DEFAULT 'anon'
);

-- 日次ロイヤルティ集計 MV
CREATE MATERIALIZED VIEW mv_contribution_royalty_daily AS
SELECT
    cs.source_hash,
    cs.contributor_did,
    cs.contributor_addr,
    DATE_TRUNC('day', used_at::TIMESTAMP) AS distribution_date,
    COUNT(*)                              AS usage_count,
    SUM(
        CAST(cu.gcc_value_wei AS NUMERIC) * cs.royalty_bps / 10000
    )                                     AS earned_wei
FROM vertex_contribution_usage cu
JOIN vertex_contribution_source cs USING (source_hash)
GROUP BY
    cs.source_hash,
    cs.contributor_did,
    cs.contributor_addr,
    DATE_TRUNC('day', used_at::TIMESTAMP);
```

**インデックス**: `source_hash` + `used_at` on `vertex_contribution_usage`
**フレッシュネス**: streaming MV (<100ms)

---

### 3. BPMN: 日次ロイヤルティ配分ワーカー

```xml
<!-- etzhayyim-root/00-contracts/bpmn/com/etzhayyim/contribution/contributionRoyaltyDistribute.bpmn -->
<!-- Timer-start R/PT24H — distributes yesterday's accrued royalties -->
```

ステップ:
1. `generic.db.select` — 昨日の `mv_contribution_royalty_daily` を取得
2. `generic.llm.json` — contributor_addr ごとに合算 (複数ソースが同じ contributor を持てる)
3. `contribution.distributeRoyalties` — 専用 pyzeebe ハンドラ:
   - GCC を sealer key で `approve(registry, total)`
   - `ContributionRoyaltyRegistry.credit(sourceHashes[], amounts[])` を `cast send` で呼ぶ
   - トランザクション txHash を `vertex_contribution_usage` に back-fill
4. `generic.audit.emit` — OCEL 配分イベント記録

---

### 4. 使用イベントの emit パターン

#### 4-A. Murakumo 推論 (自動)

`MurakumoEscrow.settleJob()` が settle されるたびに、BPMN ハンドラ or pyzeebe が使用した `modelId` を `vertex_contribution_usage` に INSERT する。

```python
# 20-actors/magatama/py/src/pymagatama/primitives/contribution_usage.py
async def emit_contribution_usage(
    db, source_hash: str, consumer_did: str,
    usage_type: str, gcc_value_wei: str
):
    vertex_id = f"at://did:web:contribution.etzhayyim.com/com.etzhayyim.apps.contribution.usage/{generate_tid()}"
    await db.execute("""
        INSERT INTO vertex_contribution_usage
            (vertex_id, source_hash, consumer_did, usage_type, gcc_value_wei, used_at, actor_did, org_did)
        VALUES (%s, %s, %s, %s, %s, NOW()::TEXT, %s, 'anon')
    """, [vertex_id, source_hash, consumer_did, usage_type, gcc_value_wei, consumer_did])
```

#### 4-B. `etzhayyim deploy` での依存解析 (自動)

`etzhayyim deploy` 実行時に `package.json` / `requirements.txt` / `go.mod` を解析し、既知の OSS パッケージを `vertex_contribution_usage` に記録する。

```go
// 70-tools/etzhayyim/etzhayyim/contribution_attr.go
func EmitDeployDependencies(deps []string, consumerDid string) error {
    for _, dep := range deps {
        sourceHash := keccak256("oss:" + dep)
        // INSERT INTO vertex_contribution_usage ...
    }
}
```

#### 4-C. 画像レンダリング (BPMN / actor 側で手動)

BPMN タスクの `input` に `contribution_source_id: "media:irasutoya.com/illustrator"` を設定する規約を設ける。generic.db.insert step で自動 emit。

---

### 5. コントリビューター登録フロー

#### 5-A. Platform ユーザー (既登録 DID)

```
authz.etzhayyim.com/xrpc/com.etzhayyim.authz.registerContributionSource
  body: {
    canonicalId: "oss:github.com/myname/mylib",
    sourceType: "oss",
    license: "MIT"
  }
  → Safe governance (owner) が承認 → registerSource(sourceHash, contributor.smartAccount) on-chain
```

#### 5-B. GitHub OSS 作者 (未登録)

1. contributor が etzhayyim.com で sign-up
2. `linkGithub` (OAuth) → GitHub handle を `linked_auth_methods` に登録
3. `com.etzhayyim.authz.claimContributionPending` を呼ぶ
4. authz が `pendingEarned[keccak256("github:{handle}")]` を lookup → `registerSource` + `claimPending` on-chain

#### 5-C. いらすとや (免責・自動)

Platform 運営 (etzhayyim) が代表して登録:
- `canonicalId = "media:irasutoya.com/illustrator"`
- `contributor_addr` = platform treasury (Safe) — creator が未参加の間、treasury に蓄積
- 作者が参加した際に treasury が資金を転送 (社内政策)

---

### 6. ロイヤルティ率設定

| ソースタイプ | デフォルト royalty_bps | 根拠 |
|---|---|---|
| **oss** (ライブラリ/フレームワーク) | 50 (0.5%) | per-transaction ではなく per-deploy のため低率 |
| **model** (推論ベースモデル) | 200 (2%) | 推論コスト比に対して意味のある補償 |
| **media** (画像・音声・動画) | 100 (1%) | レンダリング毎課金 |
| **dataset** (学習データ) | 100 (1%) | モデル訓練利用時 |
| **api** (データフィード) | 50 (0.5%) | API 呼び出し単価ベース |

Safe (multisig) が `royalty_bps` を個別ソースごとに変更できる (authz Worker の governance endpoint 経由)。

---

### 7. 実装ロードマップ

| Phase | 内容 | 前提 |
|---|---|---|
| **P1 (今日〜1 週)** | ContributionRoyaltyRegistry デプロイ + 初期 10K GCC 入金 + RisingWave 2 テーブル作成 | 既存 GCC + Safe |
| **P2 (1〜2 週)** | Murakumo 推論 usage emit (modelId → source_hash lookup) + BPMN distributionWorker | ADR-0056 BPMN |
| **P3 (2〜3 週)** | `etzhayyim deploy` 依存解析 + `com.etzhayyim.authz.registerContributionSource` XRPC + pending claim 機能 | authz Worker |
| **P4 (3〜4 週)** | yoro UI: `/credits` にコントリビューター残高 + claim ボタン | authz getActorTokenBalance |

---

### 8. セキュリティ考慮

- `ContributionRoyaltyRegistry.credit()` は oracle (sealer EOA) のみ呼び出し可能。将来は dedicated BPMN bot key + Safe 承認に昇格
- `registerSource()` は Safe multisig のみ。未審査ソースの自己登録は禁止 (スパム防止)
- `pendingEarned` の自動 credit は未審査のまま蓄積するが引き出しは `claimPending` が `contributors[hash] == msg.sender` を要求する
- 日次配分の総額は `mv_contribution_royalty_daily` の earned_wei 合計であり、registry の GCC 残高を超えた場合は BPMN がアラートを上げ配分を延期する

---

### 9. 既存コントラクト変更なし

GCCStablecoin / etzhayyimActorRegistry / etzhayyimRootIdentityRegistry は無変更。新規コントラクト 1 本 + グラフテーブル 2 本 + BPMN 1 本の加法追加。

---

## 決定

- **ContributionRoyaltyRegistry** を chainId 260425 に新規デプロイ (P1)
- 使用イベントは `vertex_contribution_usage` グラフに記録、MV で日次集計
- BPMN `R/PT24H` で `credit()` バッチ送信、コントリビューターは `claim()` で引き出し
- 未登録コントリビューター分は `pendingEarned` に蓄積、登録後に `claimPending` で回収
- `royalty_bps` は Safe governance で変更可能 (デフォルト: model 2%, media 1%, oss 0.5%)
