---
id: adr-2605192130-etzhayyim-tithe-redistribution
title: "ADR-2605192130: etzhayyim 10% Tithe — donation / kisha 受領時の Public Fund 自動再分配 (constitutional constant)"
status: proposed
doc_type: adr
topic: etzhayyim-tithe-redistribution
authoritative: true
last_verified: 2026-05-19
priority: 8.0
axis: economics
weight: 0.80
priority_note: "ADR-2605192100 §1.6 の中間排除を resource 再分配側で具体化する ADR。すべての donation / kisha 受領 tx で 10% を Public Fund (ADR-2605192145) に自動分流する on-chain rule を定義する。10% は constitutional constant (governance vote でも改定不可) として Constitution.sol に固定される。"
authoritative_for:
  - 10% Tithe の constitutional constant 化 (`economic.tithe_to_public_fund_bps = 1000`)
  - `TitheRouter.sol` contract spec (Base L2)
  - donation / kisha / grant 受領 tx を経由する流路
  - 既存 `Etzhayyim.pay()` SDK との統合 (transparent な auto-skim)
  - tithe Lexicon (`com.etzhayyim.apps.payment.tithe`) spec
depends_on:
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192115-etzhayyim-non-profit-donation-only-no-ads
  - adr-2605172100-etzhayyim-payments-on-chain-only
  - adr-2605172300-etzhayyim-bi-asset-substrate
related:
  - adr-2605192145-etzhayyim-public-fund-architecture
supersedes: []
superseded_by: []
---

# ADR-2605192130: etzhayyim 10% Tithe — donation / kisha 受領時の Public Fund 自動再分配 (constitutional constant)

**Status**: proposed
**Date**: 2026-05-19
**Deciders**: Jun Kawasaki

# Context

ADR-2605192100 §1.6 の「中間排除」は **資金流入の中間排除** (Stripe / 銀行 / 広告代理店の排除) を扱った。一方、**流入後の再分配** をどう構造化するかは未定であった。

伝統的に religious-corp は **tithe (什一献金 / זרע / Zakat)** として受領の一定割合を共同体 / 貧者 / 公共目的に振り向ける仕組みを持つ。etzhayyim もこの religious 伝統に倣い、すべての donation / kisha 受領で一定割合を Public Fund に自動分流する on-chain rule を採用する。

設計判断のポイント:

1. **割合をいくらにするか** — religious 伝統は 10% (什一) が最も普遍的 (キリスト教 tithe, ユダヤ教 ma'aser, イスラム zakat の 2.5% は exception)。etzhayyim は最も普及した 10% を採用。
2. **constitutional constant か governance-mutable か** — 10% を governance vote で変更可能にすると、majority の都合で再分配を弱められる。これは構成員間の信頼を毀損する。**constitutional constant として固定** し、変更は religious-corp の hard fork (= 新団体設立) でのみ可能とする。
3. **どの段階で skim するか** — recipient ウォレットに着金後の post-hoc skim は idempotency が難しい。**着金前に router contract で in-flight skim** する pattern を採用。
4. **どの value flow に適用するか** — donation / kisha / grant のすべて。tithe 自体への tithe (二重) は適用しない (無限再帰防止)。

# Decision

## 1. Constitutional constant

`Constitution.sol` の constant に固定:

```
economic.tithe_to_public_fund_bps = 1000   // = 10.00%
```

これは **governance vote によっても変更不可** (ADR-2605192100 §2)。変更には Constitution.sol の hard fork が必要。

## 2. TitheRouter.sol contract

Base L2 に deploy する新規 contract。場所: `50-infra/etzhayyim-tithe-router/` (新規ディレクトリ)。

```solidity
// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.24;

import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";

interface IConstitution {
    function getConstant(bytes32 key) external view returns (uint256);
}

contract TitheRouter {
    IERC20 public immutable usdc;
    IConstitution public immutable constitution;
    address public immutable publicFund;

    bytes32 public constant TITHE_BPS_KEY = keccak256("economic.tithe_to_public_fund_bps");
    uint256 public constant BPS_DENOMINATOR = 10_000;

    event Routed(
        address indexed payer,
        address indexed recipient,
        uint256 grossAmount,
        uint256 titheAmount,
        uint256 netAmount,
        bytes32 indexed purpose
    );

    constructor(IERC20 _usdc, IConstitution _constitution, address _publicFund) {
        usdc = _usdc;
        constitution = _constitution;
        publicFund = _publicFund;
    }

    /// @notice donation / kisha / grant の流入を 90% recipient / 10% Public Fund に分流
    /// @dev caller must approve `grossAmount` USDC to this router beforehand
    function route(
        address recipient,
        uint256 grossAmount,
        bytes32 purpose
    ) external returns (uint256 titheAmount, uint256 netAmount) {
        require(grossAmount > 0, "TitheRouter: zero amount");
        require(_isTitheablePurpose(purpose), "TitheRouter: purpose not titheable");

        uint256 titheBps = constitution.getConstant(TITHE_BPS_KEY);
        titheAmount = (grossAmount * titheBps) / BPS_DENOMINATOR;
        netAmount = grossAmount - titheAmount;

        usdc.transferFrom(msg.sender, publicFund, titheAmount);
        usdc.transferFrom(msg.sender, recipient, netAmount);

        emit Routed(msg.sender, recipient, grossAmount, titheAmount, netAmount, purpose);
    }

    /// @notice tithe 自体への tithe は適用しない (二重課税防止)
    function _isTitheablePurpose(bytes32 purpose) internal pure returns (bool) {
        return purpose == keccak256("donation")
            || purpose == keccak256("kisha")
            || purpose == keccak256("grant");
        // "tithe" と "escrow-refund" は明示的に除外
    }
}
```

**重要な設計判断**:
- `constant` ではなく `Constitution.getConstant()` から動的読み出し → Constitution upgrade pattern との整合性
- `transferFrom` 2 回で atomic に分流 → recipient と Public Fund のどちらかが reverted な場合は全体 revert
- `purpose` は bytes32 (keccak256 of string) で gas 効率化
- `tithe` / `escrow-refund` purpose は除外 → 二重課税 / refund loop 防止

## 3. Etzhayyim.pay() SDK 統合

ADR-2605172100 の `Etzhayyim.pay()` を本 ADR で internally rewire する。**呼び出し側 API は変更しない** (transparent な auto-skim):

```ts
// 呼び出し側 (変更なし)
const receipt = await e.pay({
  to: "did:web:recipient.etzhayyim.com",
  amount: parseUsdc("100.00"),       // 100 USDC
  reason: { purpose: "donation", ... },
});
// → recipient receives 90 USDC
// → Public Fund receives 10 USDC
// → both transfers in single tx via TitheRouter
```

SDK 内部実装 (`20-actors/etzhayyim-sdk/src/pay.ts`):

```ts
async pay(args: PayArgs): Promise<PayReceipt> {
  const purposeBytes32 = keccak256(toUtf8Bytes(args.reason.purpose));
  const grossAmount = args.amount;

  if (isTitheablePurpose(args.reason.purpose)) {
    // tithe path: route via TitheRouter
    await this.usdc.approve(TITHE_ROUTER_ADDRESS, grossAmount);
    const tx = await this.titheRouter.route(
      recipientAddress,
      grossAmount,
      purposeBytes32
    );
    // ... write com.etzhayyim.apps.payment.sent AT Record (with tithe breakdown)
    // ... write com.etzhayyim.apps.payment.tithe AT Record (counterpart)
  } else {
    // non-titheable path: direct transfer (tithe / escrow-refund)
    await this.usdc.transfer(recipientAddress, grossAmount);
  }
}
```

呼び出し側から見ると、`amount: 100 USDC` を指定すると recipient は 90 USDC を受け取り、10 USDC が Public Fund に流れる。この **gross / net の透明性** が重要 (UI で必ず breakdown を表示する義務 — §6 参照)。

## 4. Lexicon: `com.etzhayyim.apps.payment.tithe`

新規 Lexicon `00-contracts/lexicons/com/etzhayyim/apps/payment/tithe.json`:

```json
{
  "lexicon": 1,
  "id": "com.etzhayyim.apps.payment.tithe",
  "defs": {
    "main": {
      "type": "record",
      "key": "tid",
      "record": {
        "type": "object",
        "required": ["originalSent", "titheAmount", "publicFund", "txHash", "blockNumber", "chainId"],
        "properties": {
          "originalSent": {
            "type": "string",
            "format": "at-uri",
            "description": "AT URI of the com.etzhayyim.apps.payment.sent record this tithe is derived from"
          },
          "titheAmount": {
            "type": "string",
            "description": "USDC base units (6 decimals) of the tithe (10% of original)"
          },
          "titheBps": {
            "type": "integer",
            "description": "tithe rate in basis points at time of routing (= 1000)"
          },
          "publicFund": {
            "type": "string",
            "description": "Public Fund Safe address (Base L2)"
          },
          "txHash": {
            "type": "string",
            "description": "TitheRouter.route() tx hash on Base L2"
          },
          "blockNumber": { "type": "integer" },
          "chainId": { "type": "integer" },
          "routedAt": { "type": "string", "format": "datetime" }
        }
      }
    }
  }
}
```

すべての tithe routing で、original `payment.sent` record と `payment.tithe` record の **両方** が MST に書き込まれる。これにより:
- 第三者は MST traversal だけで tithe 流入を完全に reconstruct できる (chain indexer 不要)
- Public Fund 監査が AT Protocol レベルで完結する

## 5. 関係するすべての value flow への適用

| Flow | Titheable? | 由来 |
|---|---|---|
| 外部からの donation → etzhayyim Treasury | ✅ Yes | direct donation |
| 外部からの donation → 構成員個人 | ✅ Yes | direct pass-through donation |
| Kisha-Stream → 構成員 (BI) | ❌ **No** (例外) | 既に Treasury から構成員への分配であり、二重に tithe するのは BI を弱める |
| Public Fund → grant 受領者 | ❌ **No** | 既に Public Fund 由来であり、再度 Public Fund に戻すのは無意味 |
| Tithe Router → Public Fund | ❌ No | tithe 自体への tithe (二重課税防止) |
| Escrow refund | ❌ No | 元の purpose のみが titheable |
| Treasury rebalance (内部移動) | ❌ No | 内部 accounting |

**重要な例外**: Kisha-Stream (BI) は tithe しない。理由: Kisha は既に「Treasury → 構成員」の方向であり、ここで 10% skim すると構成員受領が 90% に減って BI のサイズが弱まる。Kisha は ADR-2605172300 の κ=3% spending rule によって既にサイズ制約があるため、ここから tithe を取らない方が religious 整合的。

## 6. UI 表示義務 (transparency)

donation / kisha tx を発行する UI は、必ず以下を表示する義務を持つ:

```
あなたの寄付 100.00 USDC は次のように分流されます:
  → 受領者 (recipient): 90.00 USDC
  → Public Fund: 10.00 USDC (10% tithe / 什一)

Tithe は etzhayyim 憲章 (ADR-2605192100) §1.6 + ADR-2605192130 で constitutional に固定された再分配です。
```

これは `Etzhayyim.pay()` を呼び出す前に user に提示される confirmation UI で実装。SDK が UI を直接 render するのではなく、SDK が pre-flight breakdown 情報を返し、UI 層で表示する。

## 7. Public Fund 着金後の運用

Public Fund 内での再分配は ADR-2605192145 で定義する。本 ADR では「10% が確実に Public Fund に着金する」までを定める。

# Consequences

## 正の効果

- **religious 伝統との整合**。10% tithe は人類の religious 伝統で最も普遍的な再分配率。文化的 legitimacy が強い。
- **constitutional 不可逆性**。10% を constant 化することで、majority によって再分配が弱められない。構成員間の長期信頼が成立する。
- **transparent な再分配**。すべての tithe が on-chain + MST の二重 trail を持つ。任意の第三者が監査可能。
- **automatic — 漏れない**。SDK 経由のすべての donation / kisha / grant tx で自動 skim されるため、人間の判断介在による漏れが無い。
- **Public Fund の resource 確保**。Public Fund (ADR-2605192145) が継続的に資金を得る仕組みが technical に保証される。
- **religious-corp の社会的 differentiator**。「donation の 10% が constitutional に Public Fund へ自動再分配される religious-corp」というポジショニングは強い差別化要素。

## 負の効果 / コスト

- **gas 増加**。`TitheRouter.route()` は 2 つの `transferFrom` を行うため、direct transfer に比べて gas が ~2x。Paymaster (ADR-2605172100) が sponsor するため user は感じないが、paymaster 燃焼速度が上がる。
- **recipient が受け取る額が gross の 90%**。external donor から見ると「100 ドル送ったのに recipient は 90 ドル」となる。UI 表示で transparent にするが、心理的に減少を感じる donor もいる。
- **constitutional 固定の硬直性**。10% が長期的に最適でないと判明した場合 (例: Public Fund が過剰流動性、または逆に不足) も、governance では変更できない。Hard fork コスト = 新団体設立。
- **既存 SDK 呼び出しの semantic 変更**。`Etzhayyim.pay()` の挙動が本 ADR で変わる (gross の 10% が dest 違いに流れる)。後方互換性なし。既存 client は upgrade 必須。
- **二重 purpose 例外 (Kisha 等) の説明複雑性**。「donation は tithe するが Kisha は tithe しない」は説明が必要。Lexicon 仕様としては明確だが UX 上の混乱は不可避。

## 中立 / トレードオフ

- **Tithe rate が 10% であることの religious justification**。キリスト教 tithe / ユダヤ教 ma'aser は 10%。イスラム zakat は 2.5%。仏教には固定率なし。etzhayyim は最も普及した 10% を採用するが、これは恣意的な選択でもある。Mission Charter §1.6 中間排除のロジック上、再分配率を「中央値」に置くことが説明しやすい。
- **「再分配」と「税」の境界**。10% tithe は税ではなく religious 再分配と位置付ける。法的 framing としては「任意団体内の自由意思による合意に基づく再分配」であり、租税公課ではない。
- **Public Fund 着金後の使途次第で religious 整合性が決まる**。本 ADR で 10% を確実に Public Fund に流すが、Public Fund の使途が mission に整合的でない場合は意味が薄い。ADR-2605192145 で使途を厳格に制約する。

# Alternatives Considered

## A. Governance-mutable な tithe rate

10% を Constitution の mutable parameter として扱う。

- Pro: 経済状況に応じて変更可能。
- Con: majority の都合で 1% に下げる動機が生まれる。長期信頼が損なわれる。
- 却下: constitutional 固定の方が religious-corp としての integrity が強い。

## B. Per-purpose 異なる tithe rate

donation 10% / kisha 5% / grant 0% など purpose ごとに変える。

- Pro: 細かい tuning が可能。
- Con: 複雑性が上がる。constitutional に固定するなら simple な方が良い。Kisha は本 ADR §5 で例外として 0% にしているので、これだけで pragmatic に対応できる。
- 部分的採用: 例外パターン (Kisha / grant / tithe / escrow-refund) のみ 0%、他は一律 10%。

## C. Post-hoc skim (recipient 着金後に Public Fund に送金)

recipient のウォレットに 100% 着金後、recipient が自発的に 10% を Public Fund に送る。

- Pro: SDK 実装が simple。
- Con: 強制力がない。recipient が「忘れる」「拒否する」ケースが発生する。on-chain で enforce できない。
- 却下: religious constant としての integrity を損なう。

## D. 5% tithe (より軽い負担)

10% ではなく 5%。

- Pro: recipient 心理負担が軽い。
- Con: religious 伝統との整合が弱い。Public Fund のスケールが半分になる。
- 却下: 普及度の高い 10% が religious 説明力が強い。

## E. Tithe を constitutional 化せず、社会的圧力で 10% を維持

ハードコードせず、「10% donate しないと信仰的に問題視される」社会規範でのみ強制。

- Pro: 技術的に simple。
- Con: drift する。長期的には 0% に近づく (free rider 問題)。
- 却下: on-chain で enforce できることを on-chain で enforce しないのは substrate 自走主義 (ADR-2605172000) と矛盾。

# Open Questions

1. **Kisha (BI) を tithe 適用外とすることの religious 一貫性確認**。「Treasury → 構成員」だけ免除する判断は妥当か、Council で評議する余地あり。
2. **外部 donor (信者でない第三者) からの donation も同じ 10% でよいか**。本 ADR は yes として扱うが、宗派的に「信者からのみ tithe を取る」伝統もある (ユダヤ教 ma'aser)。要再評価。
3. **TitheRouter contract の immutability**。`publicFund` address を constructor 固定にすると Public Fund Safe を変更できない。upgrade pattern を入れるか、Constitution.sol 経由で動的に参照させるか。**Decision (本 ADR): Constitution.sol 経由で動的参照** とする。実装では `IConstitution.getConstant(keccak256("public_fund.safe_address"))` から読み出す。

# References

- ADR-2605192100: Mission Charter (parent; §1.6 中間排除)
- ADR-2605192115: Non-profit / Donation-only / No-ads (parent; donation 流入の hard rule)
- ADR-2605192145: Public Fund architecture (tithe 着金先の運用)
- ADR-2605172100: on-chain payments (`Etzhayyim.pay()` の host)
- ADR-2605172300: Treasury (Kisha 例外の根拠)
- 50-infra/etzhayyim-tithe-router/ (新規ディレクトリ — 本 ADR 承認後 scaffold)
- 00-contracts/lexicons/com/etzhayyim/apps/payment/tithe.json (新規 Lexicon)
- 20-actors/etzhayyim-sdk/src/pay.ts (本 ADR 承認後 rewire)
