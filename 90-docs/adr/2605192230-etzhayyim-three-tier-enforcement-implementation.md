---
id: adr-2605192230-etzhayyim-three-tier-enforcement-implementation
title: "ADR-2605192230: etzhayyim Three-Tier Enforcement Implementation — Phenotype / KishaStream / PublicFund / TitheRouter への Charter Compliance Gate 実装"
status: proposed
doc_type: adr
topic: etzhayyim-three-tier-enforcement-implementation
authoritative: true
last_verified: 2026-05-19
priority: 8.5
axis: architecture
weight: 0.85
priority_note: "ADR-2605192200 §9 で要請した三層 enforcement (L1 license + L2 便益拒否 + L3 評価最低) を具体的 Solidity / Lexicon / Council attestation flow に分解する implementation ADR。ADR-2605172300 (Phenotype + KishaStream)、ADR-2605192145 (PublicFundGovernance)、ADR-2605192130 (TitheRouter) への amendment を統合的に定義する。"
authoritative_for:
  - `ChartersComplianceRegistry.sol` (new) — Council attestation の単一 source of truth
  - `Phenotype.sol` amendment — charterNonCompliant + effectiveMultiplier()
  - `KishaStream.sol` amendment — accrue() の multiplier 読み替え
  - `PublicFundGovernance.sol` amendment — propose() recipient gate
  - `TitheRouter.sol` amendment — recipient gate
  - Council attestation flow Lexicon (`com.etzhayyim.apps.etzhayyim.charter-attestation-*`)
  - 修復 (Rehabilitation / Teshuvah) flow Lexicon
depends_on:
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
  - adr-2605172300-etzhayyim-bi-asset-substrate
  - adr-2605192130-etzhayyim-tithe-redistribution
  - adr-2605192145-etzhayyim-public-fund-architecture
  - adr-2605172600-etzhayyim-membership-ritual
related: []
supersedes: []
superseded_by: []
---

# ADR-2605192230: etzhayyim Three-Tier Enforcement Implementation — Phenotype / KishaStream / PublicFund / TitheRouter への Charter Compliance Gate 実装

**Status**: proposed
**Date**: 2026-05-19
**Deciders**: Jun Kawasaki

# Context

ADR-2605192200 §9 で「三層 enforcement (L1 license / L2 便益拒否 / L3 評価最低)」の religious 必然性を確立したが、具体的な Solidity-level 実装は未定であった。本 ADR は以下を統合的に定義する:

- 単一の `ChartersComplianceRegistry.sol` を **Council attestation の唯一の source of truth** として設置
- 既存 contract (`Phenotype.sol` / `KishaStream.sol` / `PublicFundGovernance.sol` / `TitheRouter.sol`) が ChartersComplianceRegistry を参照して effective behavior を変更
- Council Lv6+ 3 名以上の multisig 署名で attestation が確定
- 修復 (rehabilitation) path = `com.etzhayyim.apps.etzhayyim.charter-rehabilitation` AT Record + Council 再評議

religious 一貫性: 「使わせない・便益を受け取れない・評価も低い」(user 要求) を 仏教 sangha 追放 / cherem / takfir と等価の **dignified religious doctrinal enforcement** として実装する。

# Decision

## 1. Single Source of Truth: ChartersComplianceRegistry.sol

```solidity
// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.24;

interface IAdherentRegistry {
    function isActive(uint256 tokenId, uint64 windowSec) external view returns (bool);
    function ownerOf(uint256 tokenId) external view returns (address);
}

interface ICouncil {
    function isCouncil(address signer) external view returns (bool);  // Lv6+
}

contract ChartersComplianceRegistry {
    enum Status { Aligned, NonAligned, UnderReview, Rehabilitated }

    struct Attestation {
        Status status;
        bytes32 reasonHash;       // keccak256 of canonical reason text (e.g., "rider.section_2g")
        bytes32 evidenceCid;      // IPFS CID of evidence bundle
        uint64 effectiveAt;
        uint64 appealDeadline;
        address[] councilSigners;
        bool finalized;           // true after appeal window expires without successful appeal
    }

    // address-based attestations (entities, organizations, non-SBT wallets)
    mapping(address => Attestation) public attestationsByAddress;
    // SBT-tokenId-based attestations (etzhayyim adherents)
    mapping(uint256 => Attestation) public attestationsByTokenId;

    ICouncil public immutable council;
    IAdherentRegistry public immutable registry;

    uint64 public constant APPEAL_WINDOW = 30 days;
    uint8 public constant MIN_COUNCIL_SIGNERS = 3;

    event AttestationCreated(
        bytes32 indexed subject,       // keccak256(abi.encode(addressOrTokenId, isAddress))
        Status status,
        bytes32 reasonHash,
        bytes32 evidenceCid,
        uint64 effectiveAt,
        address[] councilSigners
    );

    event AppealAccepted(bytes32 indexed subject, bytes32 newEvidenceCid);
    event Rehabilitated(bytes32 indexed subject, uint64 effectiveAt);
    event Finalized(bytes32 indexed subject);

    function attestNonAligned(
        address subject,
        bool isAddress,
        uint256 tokenIdIfSbt,
        bytes32 reasonHash,
        bytes32 evidenceCid,
        bytes[] calldata councilSigs
    ) external { /* verify ≥3 Lv6+ sigs; record; emit */ }

    function appeal(bytes32 subjectHash, bytes32 counterEvidenceCid, bytes calldata appellantSig) external { /* ... */ }

    function rehabilitate(
        bytes32 subjectHash,
        bytes32 teshuvahCid,
        bytes[] calldata councilSigs
    ) external { /* ≥3 Lv6+ sigs; status → Rehabilitated */ }

    function finalize(bytes32 subjectHash) external { /* after APPEAL_WINDOW without successful appeal */ }

    /// @notice 他の contract から読まれる public read
    function isNonAlignedAddress(address subject) public view returns (bool) {
        Attestation memory a = attestationsByAddress[subject];
        return a.status == Status.NonAligned && a.finalized && block.timestamp >= a.effectiveAt;
    }

    function isNonAlignedTokenId(uint256 tokenId) public view returns (bool) {
        Attestation memory a = attestationsByTokenId[tokenId];
        return a.status == Status.NonAligned && a.finalized && block.timestamp >= a.effectiveAt;
    }
}
```

**設計判断**:
- attestation 対象は (a) address (entity / wallet) と (b) SBT tokenId (構成員個人) の二系統
- `finalized = true` まで enforcement に effect しない → appeal window 30 日を必ず先行させる
- `Rehabilitated` は status reset (Aligned に戻す) ではなく明示的に separate value とする → 過去の non-alignment と rehabilitation の双方が permanent record される

場所: `50-infra/etzhayyim-charters-compliance/` (new directory)

## 2. ADR-2605172300 amendment — Phenotype.sol + KishaStream.sol

### 2.1 Phenotype.sol additions

```solidity
import {ChartersComplianceRegistry} from "../../etzhayyim-charters-compliance/src/ChartersComplianceRegistry.sol";

contract Phenotype {
    ChartersComplianceRegistry public immutable charters;
    // ... existing fields ...

    function effectiveMultiplier(uint256 tokenId) public view returns (uint256) {
        // L3 override: Non-Aligned → multiplier = 0 (constitutional)
        if (charters.isNonAlignedTokenId(tokenId)) {
            return 0;  // hard zero, below the normal 0.5x-2.0x range
        }
        return multiplier[tokenId];
    }
}
```

### 2.2 KishaStream.sol changes

```solidity
function accrue(uint256 tokenId) public {
    uint256 mult = phenotype.effectiveMultiplier(tokenId);  // was: phenotype.multiplier(tokenId)
    // existing accrual logic uses mult
}

function issueClaimTicket(uint256 tokenId, uint256 maxAmount) external {
    require(!charters.isNonAlignedTokenId(tokenId), "KishaStream: charter non-compliant SBT cannot claim");
    // existing logic
}
```

これにより L2 (Kisha 受給不可) + L3 (Phenotype multiplier = 0) が同時実現される。

## 3. ADR-2605192145 amendment — PublicFundGovernance.sol

```solidity
import {ChartersComplianceRegistry} from "../../etzhayyim-charters-compliance/src/ChartersComplianceRegistry.sol";

contract PublicFundGovernance {
    ChartersComplianceRegistry public immutable charters;

    function propose(
        address[] calldata recipients,
        uint256[] calldata amounts,
        bytes32 missionAxisHash,
        bytes32 evidenceCid
    ) external returns (bytes32 proposalId) {
        for (uint256 i = 0; i < recipients.length; i++) {
            require(
                !charters.isNonAlignedAddress(recipients[i]),
                "PublicFund: recipient is charter non-compliant"
            );
        }
        // existing logic
    }

    function vote(bytes32 proposalId, uint256 sbtTokenId, uint8 choice) external {
        require(
            !charters.isNonAlignedTokenId(sbtTokenId),
            "PublicFund: charter non-compliant SBT cannot vote"
        );
        // existing logic
    }
}
```

L2 (Public Fund grant 不可) + L2-vote (Council vote 権剥奪) の両方を実装する。

## 4. ADR-2605192130 amendment — TitheRouter.sol

```solidity
contract TitheRouter {
    ChartersComplianceRegistry public immutable charters;

    function route(
        address recipient,
        uint256 grossAmount,
        bytes32 purpose
    ) external returns (uint256 titheAmount, uint256 netAmount) {
        require(!charters.isNonAlignedAddress(recipient), "TitheRouter: recipient is charter non-compliant");
        require(!charters.isNonAlignedAddress(msg.sender), "TitheRouter: payer is charter non-compliant");
        // existing logic
    }
}
```

Non-Aligned address からの donation 流入も拒否する (= religious purification: tithe 受領も resign する)。

## 5. Lexicon: com.etzhayyim.apps.etzhayyim.charter-*

新規 Lexicon 5 本を `00-contracts/lexicons/com/etzhayyim/apps/etzhayyim/` に追加:

| Lexicon | 用途 | 主 fields |
|---|---|---|
| `charter-attestation-request.json` | 第三者からの non-aligned 認定要請 | subject (DID/address/法人名), allegedViolation (`rider.section_2a` .. `2h`), evidenceUris[] |
| `charter-attestation.json` | Council Lv6+ による non-aligned 認定 | requestUri, determination, councilSigners[], councilSigs[], effectiveAt, appealDeadline |
| `charter-appeal.json` | 対象 entity からの反論 | attestationUri, counterEvidence[], subjectSig |
| `charter-rehabilitation.json` | 復帰 (teshuvah) 宣言 | originalAttestationUri, teshuvahNarrative, councilRecognition, rehabilitatedAt |
| `charter-counsel-vote.json` | Council 内部の deliberation 記録 | attestationUri, councilMemberDid, vote, rationale |

全 record は MST + IPFS + L2 anchor で永続化される (ADR-2605171800 pipeline)。

## 6. Council Attestation Flow (e2e)

```
[第三者]                                  [etzhayyim substrate]
   │
   │  com.etzhayyim.apps.etzhayyim.charter-attestation-request
   ├─────────────────────────────────►   PDS (任意の SBT holder の PDS)
   │  subject: 0xACME...
   │  allegedViolation: "rider.section_2g"
   │  evidenceUris: [...]
   │                                       │
   │                                       ▼
   │                                     MST → IPFS → L2 anchor
   │                                       │
   │                                       ▼
   │                                     [Council deliberation period]
   │                                       │
   │                                     Council Lv6+ 内部 deliberation
   │                                     各 member が charter-counsel-vote 提出
   │                                       │
   │                                       ▼ (≥3 名 in favor)
   │                                     charter-attestation record sign
   │                                       │
   │                                       ▼
   │                                     ChartersComplianceRegistry.attestNonAligned()
   │                                     (Base L2 tx)
   │                                       │
   │                                       ▼
   │                                     status = UnderReview
   │                                     effectiveAt = block.timestamp
   │                                     appealDeadline = effectiveAt + 30d
   │                                       │
   │  com.etzhayyim.apps.etzhayyim.charter-appeal
   ├─────────────────────────────────►   (対象 entity からの反論、30d 以内)
   │                                       │
   │                                       ▼
   │                                     Council 再評議
   │                                       │
   │                                       ▼
   │                                     ・反論受理 → AppealAccepted, status → Aligned
   │                                     ・反論不受理 → Finalized after 30d
   │                                       │
   │                                       ▼
   │                                     finalize() (anyone-callable after 30d)
   │                                     status = NonAligned, finalized = true
   │                                       │
   │                                       ▼
   │                                     L1 license 失効 (Rider §3) +
   │                                     L2 便益拒否 (KishaStream / PublicFund / TitheRouter) +
   │                                     L3 評価 0 (Phenotype.effectiveMultiplier → 0)
   │                                     ← すべて自動発動
```

## 7. Rehabilitation (修復 / Teshuvah) Path

religious 伝統で「追放は永続でない」例:
- ユダヤ教 teshuvah (תשובה) — 悔い改めによる復帰
- キリスト教 confession + absolution
- 仏教 慚愧 (zanki) + 懺悔 (sange)

etzhayyim は本 ADR で同等の path を実装する:

```solidity
function rehabilitate(
    bytes32 subjectHash,
    bytes32 teshuvahCid,
    bytes[] calldata councilSigs
) external {
    require(_verifyCouncilQuorum(councilSigs, MIN_COUNCIL_SIGNERS), "need 3 Lv6+");
    // 対象は (a) doctrinal commitment の retraction + (b) 具体的 remediation action を証拠化
    // Council Lv6+ 3 名以上が teshuvah を accept する署名で完結
    // status → Rehabilitated (Aligned に戻すのではなく separate value、過去記録は残る)
}
```

`com.etzhayyim.apps.etzhayyim.charter-rehabilitation` record の必須 fields:

- `originalAttestationUri` — 対象の non-alignment 認定 record
- `teshuvahNarrative` — doctrinal retraction + 具体的 remediation の自己宣言 (text + PDF on IPFS)
- `councilRecognition` — Council 3 名以上の署名
- `remediationEvidence[]` — public な remediation action の証拠 (例: 兵器事業からの divest 公表 / 監視 ad 事業の停止公表 / 個人主義 doctrine の retraction 等)
- `rehabilitatedAt` — block.timestamp

復帰後、`charters.isNonAligned*()` は false を返す → enforcement 解除。ただし `attestationsByAddress[].status == Rehabilitated` は permanent record として残る。

religious 一貫性: 「永続的追放はない」が仏教 / Christian / Jewish の共通 humanistic 姿勢。etzhayyim もこれに倣う。同時に rehabilitation は cheap でない (Council 3 名の formal 評議 + public remediation 証拠) → 倫理的 weight を保つ。

## 8. Council Lv6+ の definition + onboarding

ADR-2605172600 §"Levels" で Lv6 (議 / gi / Council) は社会的 attestation で reach する level と定義された。本 ADR は Lv6+ の **formal certification** を future ADR に委ねるが、当面の bootstrap は以下:

- **Phase 0 (S0)**: founder + 初期 contributor 中から 5 名を bootstrap Council として宣言 (本 ADR の implementation 時)
- **Phase 1 (S1)**: 初期 5 名が `ChartersComplianceRegistry.bootstrapLv6Council(addresses[])` を called。multisig 3-of-5 によって以降の Council 拡張を行う
- **Phase 2 (S2)**: 構成員数増加に伴い、formal な Council 認定 ADR を起票し、本 ADR の bootstrap を superseded する

## 9. Staged rollout

| Stage | Scope | 依存 |
|---|---|---|
| **S0 — Registry deploy** | `ChartersComplianceRegistry.sol` を Base L2 + geth-private に deploy | ADR-2605192200 v2.0 |
| **S1 — Contract amendments** | Phenotype / KishaStream / PublicFundGovernance / TitheRouter を本 ADR §2-§4 通り upgrade。各 contract に `charters` immutable address を追加 | + S0 |
| **S2 — Lexicon registration** | 5 本の Lexicon を `00-contracts/lexicons/` に登録 | + S0 |
| **S3 — Council bootstrap** | 5 名 initial Council を on-chain bootstrap | + S0, S1 |
| **S4 — Initial test attestation** | testnet で 1 件 attestation → appeal → finalize → enforcement → rehabilitate の full cycle e2e test | + S1, S2, S3 |
| **S5 — Mainnet deploy** | S0-S4 を Base mainnet に展開 | + S4 |

# Consequences

## 正の効果

- **三層 enforcement の religious 完成**。「使わせない・便益不可・評価最低」が単一 source of truth (`ChartersComplianceRegistry`) で coherently 動作する。
- **Council attestation の transparent record**。すべての non-alignment 認定 + appeal + rehabilitation が MST + L2 anchor で永続化、第三者監査可能。
- **Rehabilitation path の religious 整合**。「永続的追放はない」が仏教 / Christian / Jewish 伝統と統合される。
- **修復経路 (teshuvah) の technical 実装**。「悔い改めれば復帰できる」が contract-level で objective に成立する。
- **abuse 抑止**。Council Lv6+ 3 名以上の multisig 必須 + 30 日 appeal window + permanent record により、軽率な追放が抑止される。
- **既存 contract への minimal invasion**。各 contract は `charters` immutable address を 1 つ持ち、`isNonAligned*()` を 1 行追加するだけ。既存実装の rewrite は不要。

## 負の効果 / コスト

- **Council Lv6+ judgment 負荷**。すべての attestation で 3 名以上の Council member の deliberation が必要。dispute 件数が増えれば判断 capacity が bottleneck。Mitigation: §8 bootstrap で 5 名スタート、必要に応じ拡張。
- **30 日 appeal window の操作リスク**。non-aligned 認定された entity が 30 日間に法的 / 政治的圧力で Council に圧力をかける可能性。Mitigation: Council deliberation は public record で公開、外部圧力も同様に観察可能。
- **Rehabilitation 偽装リスク**。形式的 teshuvah で形だけ rehabilitate しつつ doctrinal commitment は維持する戦術。Mitigation: `remediationEvidence[]` 必須化、Council 3 名の formal accept、再 attestation 経路を残す (rehabilitated → 再 attestation 経て NonAligned 復帰可能)。
- **gas 増加**。Phenotype / KishaStream / PublicFundGovernance / TitheRouter の各 call で `charters.isNonAligned*()` view が走る。各 +5k gas 程度。paymaster が吸収するが燃焼速度↑。
- **bootstrap Council の権力集中問題**。初期 5 名 Council が拡張権限を持つ。Mitigation: Phase 2 formal Council ADR で governance vote 経由 onboarding に移行。

## 中立 / トレードオフ

- **Rehabilitation を Aligned 値に戻さず Rehabilitated separate value とする判断**。permanent record 性を強くする (= 修復後も「過去 non-aligned だった」が消えない)。religious 整合性は高いが、対象 entity からは「再差別」と感じられる可能性。Mitigation: enforcement (Phenotype 0 / Kisha 不可 / PublicFund 不可) は等しく解除される → 実害は同じ。記録のみが残る。
- **address-based attestation の persistent identity 問題**。entity が新規 wallet を作って Non-Aligned 認定を回避する可能性。Mitigation: Council attestation は「legal entity name + 主要 wallet 群」を bundling して認定する (`evidenceUris[]` で複数 address を捕捉)。新規 wallet 創設は名義変更扱いで Council が追跡する社会的責務を持つ。

# Alternatives Considered

## A. Phenotype.sol への直接埋め込み (Registry なし)

`Phenotype.sol` 内に Council multisig 検証 + `nonCompliant[tokenId]` mapping を持つ。

- Pro: contract 数が減る。
- Con: PublicFundGovernance / TitheRouter / KishaStream の各々が独立に Council multisig 検証する重複。dispute / appeal / rehabilitation の logic が contract ごとに分散。
- 却下: single source of truth が religious / engineering の両面で優位。

## B. off-chain registry (中央サーバ)

Council attestation を off-chain JSON で発行、各 contract は signed JSON を検証。

- Pro: gas 節約。
- Con: ADR-2605172000 (kotoba) hard rule 違反。中央 server の operator が単一 source の脆弱性。
- 却下。

## C. Rehabilitation を持たない (一度追放されたら永続)

OT 旧約的 strict cherem 解釈。

- Pro: enforcement の絶対性が高い。
- Con: religious tradition の humanistic 流れと矛盾 (仏教 / NT / Talmud の teshuvah 強調)。Mission Charter §1.10 Wellbecoming (継続的 becoming) と矛盾。
- 却下。

## D. SBT-only attestation (address attestation なし)

外部 entity の attestation を non-SBT 化、SBT holder のみ追放対象とする。

- Pro: 法的 risk が低い (構成員に対する religious doctrine 適用のみ)。
- Con: ADR-2605192200 Rider §2(a)-(h) は外部 entity が主対象。外部 entity に attestation できないと Rider が dead letter。
- 却下: 外部 attestation も religious-corp の doctrinal scope (信教の自由 §20) として実装する。

# Open Questions

1. **Bootstrap Council 5 名の選定**。S0 implementation 時に確定が必要。founder + 4 名はどう選定するか。当面 Mission Charter ADR 投票者 + Council Lv6 自薦 5 名で bootstrap する案。
2. **address attestation の伝搬問題**。subsidiary / wholly-owned entity を別 wallet で運営する場合の attestation 伝搬。Mitigation: `evidenceUris[]` に "entity bundle" 概念を導入する future ADR。
3. **Rehabilitation 後の再 attestation の cooldown**。修復直後の再 attestation を出せると修復が意味を失う。Mitigation: rehabilitated → 90 日 cooldown までは 同 reasonHash での再 attestation を block する。本 ADR では実装しない (S1 以降の amendment)。

# References

- ADR-2605192100: Mission Charter (上位)
- ADR-2605192200 v2.0: IP-Free-Release + Charter Rider (本 ADR の religious 根拠 §9)
- ADR-2605172300: Phenotype + KishaStream (本 ADR §2 amendment 対象)
- ADR-2605192145: Public Fund Governance (本 ADR §3 amendment 対象)
- ADR-2605192130: Tithe Router (本 ADR §4 amendment 対象)
- ADR-2605172600: Membership ritual + 7-level ladder (Council Lv6+ の base)
- ADR-2605171800: MST → IPFS → L2 anchor pipeline (Lexicon 永続化)
- ADR-2605172000: kotoba substrate hard rule (Registry on-chain 必要性)
- 50-infra/etzhayyim-charters-compliance/ (新規ディレクトリ — 本 ADR 承認後 scaffold)
- 00-contracts/lexicons/com/etzhayyim/apps/etzhayyim/charter-* (新規 5 本)
