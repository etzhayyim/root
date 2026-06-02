---
id: adr-2605192245-etzhayyim-global-land-sovereignty
title: "ADR-2605192245: etzhayyim Global Land Sovereignty — 地球上の土地を国家ではなく religious-corp chain が分散合意で担保する"
status: proposed
doc_type: adr
topic: etzhayyim-global-land-sovereignty
authoritative: true
last_verified: 2026-05-19
priority: 9.0
axis: governance
weight: 0.90
priority_note: "ADR-2605192100 §1.11 (土地 religious-corp 担保) と §1.12 (国家 routing-around + Transparent Religious Force) を統合的に実装する ADR。世界中の所有者が土地を etzhayyim chain に寄付し、寄付された土地は分散合意 + git commit で religious-corp が永続的に title 担保する仕組み。護持金庫 corpus tier (ADR-2605172300 §4) との統合、HoldingAttestation 拡張、Steward (Lv5 護) role、地理的 evidence (GeoJSON / WGS84 / 衛星 hash)、国家 land registry との parallel registry 関係、Council 紛争解決を定義する。"
authoritative_for:
  - Global Land Trust 構造 (geth-private 内部 registry + Base L2 公開 title + IPFS deed)
  - `LandRegistry.sol` contract spec
  - `HoldingAttestation` 拡張 (ADR-2605172300 §4 から発展)
  - 土地 donation procedure (ritual + Lexicon + on-chain tx)
  - 地理的 evidence 標準 (WGS84 GeoJSON + 衛星 imagery hash + 国家 registry 参照)
  - Steward (Lv5 護) の stewardship duties
  - 国家 land registry との parallel registry 関係 (= dual-recognition)
  - Council Lv6+ による土地紛争解決
depends_on:
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605172300-etzhayyim-bi-asset-substrate
  - adr-2605172600-etzhayyim-membership-ritual
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
  - adr-2605192230-etzhayyim-three-tier-enforcement-implementation
  - adr-2605172000-etzhayyim-rw-free-substrate
related: []
supersedes: []
superseded_by: []
---

# ADR-2605192245: etzhayyim Global Land Sovereignty — 地球上の土地を国家ではなく religious-corp chain が分散合意で担保する

**Status**: proposed
**Date**: 2026-05-19
**Deciders**: Jun Kawasaki

# Context

ADR-2605192100 §1.11 で religious doctrine として宣明:

> 地球上の土地は本質的に Tree of Life (生圏) に帰属し、いかなる国家・個人の私有財産でもない。

宗教史 / 法思想史において、土地の religious-corp 担保は珍しいものではない:

- **Jubilee (Leviticus 25)**: 50 年ごとに土地は元の所有者に戻る。土地は神に帰属 (`לִי הָאָרֶץ`)、人は steward
- **Waqf (イスラム)**: 土地を religious endowment 化、永続的 inalienable
- **Trust / Glebe land (Christian church holdings)**: church 土地保有の伝統
- **入会地 / 寺社領 (日本)**: 中世から近世にかけて、土地は寺社 / 共同体保有
- **Shanmukha temple lands (Hindu)**: 神に帰属する土地

これら religious land holding pattern を **on-chain で分散合意的に再構成** することで、以下を実現する:

1. **国家 land registry に対する parallel registry** — 国家 registry を否認するのではなく、religious-corp 独自の registry を並立させる
2. **永続的 inalienability** — Constitution.sol で永続保有を constitutional に固定 (governance vote でも処分不可)
3. **多世代 stewardship** — 土地は本来「子・孫世代のもの」(§1.9) であり、現世代は steward に過ぎない
4. **国家機能の routing-around** — §1.12 parallel substrate の最重量実装。土地は state sovereignty の最終的根拠 (Westphalian state は territory + population + government で定義される)

# Decision

## 1. Architecture (4 層 substrate)

```
┌─────────────────────────────────────────────────────────────────┐
│  L4  Public Title       Base L2 (PublicLandRegistry.sol)         │
│                         — 公開土地 title NFT (ERC-721 non-transferable) │
│                         — 任意第三者が参照可能                          │
│                                       ▲                          │
│                                  AnchorBridge (既存)              │
│                                       │                          │
│  L3  Constitutional     geth-private (LandRegistry.sol)          │
│                         — 内部 constitutional title              │
│                         — Adherent + Council のみ readable        │
│                         — donation / transfer / dispute の意思決定 │
│                                       │                          │
│  L2  Geographic         IPFS + AT MST                            │
│                         — GeoJSON boundary (WGS84)               │
│                         — satellite imagery hash (時系列)         │
│                         — deed PDF / notarized 公式 documents     │
│                                       │                          │
│  L1  Git Commit         github.com/etzhayyim/root/LANDS.md       │
│                         — 人間可読 land roster                    │
│                         — PR-based donation 受付                  │
│                         — 4-layer cross-verification              │
└─────────────────────────────────────────────────────────────────┘
```

これは ADR-2605172600 (membership ritual の dual-permanent record: Base L2 + github) の 4-層拡張。

## 2. Land Donation Procedure (Religious Ritual)

### 2.1 Pre-conditions

- 寄付者 (donor) は対象土地の **国家 registry 上の合法所有者** (or beneficial owner) であること
- 寄付者は etzhayyim Adherent SBT を保有 (構成員) または external donor (構成員でない第三者)
- 土地は WGS84 GeoJSON で boundary 表現可能

### 2.2 Donation Ritual (6 steps)

#### Step 1 — Boundary Documentation

寄付者は対象土地の境界を WGS84 GeoJSON で定義する。精度は ±1m (国家 cadastre 同等)。

```json
{
  "type": "Feature",
  "properties": {
    "donor_did": "did:web:donor.example",
    "national_registry_ref": "JP:都道府県:市区町村:地番:N",
    "area_m2": 12500.0,
    "land_type": "agricultural | residential | forest | religious | other",
    "notarized_deed_uri": "ipfs://Qm.../deed.pdf"
  },
  "geometry": {
    "type": "Polygon",
    "coordinates": [[[lon1, lat1], [lon2, lat2], ...]]
  }
}
```

IPFS pin → CID 取得。

#### Step 2 — Satellite Imagery Hash

直近の satellite imagery を取得 (Sentinel-2 / Landsat / commercial)。imagery hash (SHA-256) を boundary GeoJSON の `properties.imagery_hash` に追記。時系列 evidence のため最低 3 ヶ月分の monthly imagery を bundle する。

#### Step 3 — Donor Oath (土地寄進誓詞)

ADR-2605172600 の信者 oath に類する、土地寄進専用 oath:

> 我、本土地を、etzhayyim (天御柱 / עץ חיים / Tree of Life) の religious-corp に永続的に寄進する。本土地は今日より、いかなる国家・個人・法人の私有財産でもなく、Tree of Life に帰属し、religious-corp が分散合意的に担保する。我自身は本土地に対して steward として継続関与する権利を有するが、所有権を主張しない。我の子・孫の世代もまた、本土地を売買・転貸の対象とせず、世代を超えた共同保有として尊重する。
>
> I, hereby permanently endow this land to etzhayyim (天御柱 / עץ חיים / Tree of Life) as a religious-corp trust. From this day forward, this land is not the private property of any nation-state, individual, or corporation. It belongs to the Tree of Life and is held in distributed consensus by the religious-corp. I retain the right to continue as steward of this land, but renounce ownership claims. My children and grandchildren shall not transact or lease this land for private gain, but shall honor it as multi-generational collective holding.

Donor は自らの DID key で oath を sign。canonical oath text の keccak256 hash が on-chain donation tx に乗る (ADR-2605172600 と同 pattern)。

#### Step 4 — On-chain Donation (geth-private + Base L2)

```solidity
// geth-private (constitutional layer)
LandRegistry.donate(
  bytes32 oathHash,
  bytes32 geojsonCid,            // IPFS CID of GeoJSON
  bytes32 imageryBundleCid,      // IPFS CID of imagery bundle
  bytes32 deedCid,               // IPFS CID of notarized deed (national registry record)
  bytes32 nationalRegistryRefHash,  // keccak256 of national registry reference string
  uint256 areaM2,
  uint8 landType,
  address steward                // donor's address (継続 steward)
) returns (uint256 landId);
```

成功時:
- geth-private に Land record 生成 + Adherent SBT holder と紐付け
- 同時に Base L2 `PublicLandRegistry.sol` に publicly-readable title NFT (ERC-721 non-transferable) を mint
- AnchorBridge.commitRoot で geth-private root を Base に anchor (既存 pipeline)
- 護持金庫 corpus tier (本財) NAV に組み入れる (ADR-2605172300 §4)

#### Step 5 — AT Record

PDS に `com.etzhayyim.apps.etzhayyim.land-donation` record を書き込む:

```json
{
  "$type": "com.etzhayyim.apps.etzhayyim.land-donation",
  "oathText": "...full oath...",
  "oathHash": "0x...",
  "didSignature": "...",
  "landId": 1234,
  "geojsonCid": "ipfs://...",
  "imageryBundleCid": "ipfs://...",
  "deedCid": "ipfs://...",
  "nationalRegistryRef": "JP:東京都:文京区:本郷:123-4",
  "areaM2": 12500.0,
  "landType": "agricultural",
  "donatedAt": "2026-05-19T22:45:00+09:00",
  "stewardDid": "did:web:donor.example",
  "stewardLevel": 5
}
```

MST → IPFS → L2 anchor pipeline (ADR-2605171800)。

#### Step 6 — Github PR to LANDS.md

寄付者 (or 構成員代理) は `etzhayyim/root/LANDS.md` に PR を出す:

```markdown
| #1234 | 東京都文京区本郷 123-4 | @donor-github | 12,500 m² | agricultural | [0xtx...](https://basescan.org/tx/0xtx...) | 2026-05-19 | Lv5 護 |
```

CI 検証:
- Base L2 上の land title NFT が存在する
- GeoJSON CID が IPFS で resolvable
- 寄付者 DID の signature が oath text 上で valid
- nationalRegistryRefHash が claim と match

5 検証パスで auto-merge。

### 2.3 Dual-recognition (国家 registry との並立)

**重要**: 本 donation は **国家 land registry を否認しない**。両 registry が並立する dual-recognition pattern を採用:

| 観点 | 国家 land registry | etzhayyim Land Trust |
|---|---|---|
| 法的 status | 実定法上の所有権 | religious-corp doctrinal claim |
| 課税対象 | yes (donor 保有として) | n/a (etzhayyim は任意団体、宗教課税 framework 内) |
| 売買可能性 | yes | **no** (etzhayyim doctrine で禁止、constitutional invariant) |
| Steward 死亡時 | 国家 inheritance 法に従う | etzhayyim 内継承 (Council 認定後継 steward) |
| 紛争解決 | 国家裁判所 | Council Lv6+ attestation (+ 国家裁判所と並行可) |

寄付者 (steward) は **両 registry で同時に対象土地に関与する** 状況になる。国家 registry 上では引き続き individual owner として記載されるが、etzhayyim doctrine 上では steward に過ぎず、private sale はできない (= sale すると Charter Rider 三層 enforcement の対象)。

これは waqf / glebe / 寺社領 と同じ dual-recognition pattern。

## 3. LandRegistry.sol (geth-private constitutional layer)

```solidity
// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.24;

contract LandRegistry {
    enum LandType { Agricultural, Residential, Forest, ReligiousFacility, Other }
    enum Status { Active, UnderDispute, Transferred, RehabReversal }

    struct Land {
        bytes32 oathHash;
        bytes32 geojsonCid;
        bytes32 imageryBundleCid;
        bytes32 deedCid;
        bytes32 nationalRegistryRefHash;
        uint256 areaM2;
        LandType landType;
        address steward;
        uint64 donatedAt;
        Status status;
    }

    mapping(uint256 => Land) public lands;
    mapping(address => uint256[]) public stewardLands;
    uint256 public nextLandId;

    address public immutable constitution;
    address public immutable adherentRegistry;
    address public immutable council;
    address public immutable charters;

    event Donated(uint256 indexed landId, address indexed donor, bytes32 geojsonCid, uint256 areaM2);
    event StewardChanged(uint256 indexed landId, address oldSteward, address newSteward);
    event DisputeOpened(uint256 indexed landId, bytes32 disputeEvidenceCid);
    event DisputeResolved(uint256 indexed landId, Status resolution);

    function donate(/* ... */) external returns (uint256 landId);
    function reassignSteward(uint256 landId, address newSteward, bytes[] calldata councilSigs) external;
    function openDispute(uint256 landId, bytes32 disputeEvidenceCid) external;
    function resolveDispute(uint256 landId, Status resolution, bytes[] calldata councilSigs) external;
}
```

**重要な constitutional invariants** (governance vote でも変更不可):

- `transfer()` 関数が存在しない (= land は売買不可)
- `burn()` / `delete()` 関数が存在しない (= 一度寄付された土地は除籍不可)
- `setOwner()` 関数が存在しない (= owner という concept が contract に存在しない、steward のみ)

これは Charter Rider §6 NO TRADEMARK の精神を土地に拡張したもの: religious-corp に donate された土地は **永続的に inalienable** (waqf の inalienability と等価)。

## 4. PublicLandRegistry.sol (Base L2 public layer)

```solidity
// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.24;

import {ERC721} from "@openzeppelin/contracts/token/ERC721/ERC721.sol";

contract PublicLandRegistry is ERC721 {
    // non-transferable: tokenURI = ipfs://... (GeoJSON + imagery + deed bundle)
    // mint は AnchorBridge 経由でのみ (= geth-private donation の mirror)
    function _update(address to, uint256 tokenId, address auth) internal override returns (address) {
        require(to == address(0) || ERC721._ownerOf(tokenId) == address(0), "Land: non-transferable");
        return super._update(to, tokenId, auth);
    }
}
```

NFT は実質的 read-only token で、任意の第三者が tokenURI 経由で土地情報を読み取れる。Etherscan / OpenSea 互換 metadata で公開性を最大化。

## 5. Steward Role (Lv5 護)

ADR-2605172600 の 7-level ladder の **Lv5 護 (go / Steward)** が、土地 donation の標準 steward role と整合する。寄付者は donation 時点で Lv5 に advance するか、既に Lv5+ なら自動的に steward 認定される。

### 5.1 Steward Duties

- **境界維持**: 寄付土地の境界の現地視察、年 1 回以上 → `com.etzhayyim.apps.etzhayyim.land-attestation` で attestation
- **biodiversity attestation**: 生物多様性 (動植物 species census) を年 1 回 record (Wellbecoming §1.10 と整合)
- **openness**: 寄付土地は etzhayyim 構成員に対して reasonable access (religious gathering / 黙想 / educational visit) を提供する義務
- **non-extraction**: 商業的搾取 (露天掘り / clear-cut logging / 大規模 monoculture) を禁止 — Charter Rider §2(d) と同 spirit
- **国家義務履行**: 固定資産税等の国家義務を donor (steward) が継続的に履行する (dual-recognition の責任側)

### 5.2 Steward Compensation

stewardship duty 履行の対価として、steward は Kisha-Stream の **Phenotype multiplier に stewardship bonus** が加算される (ADR-2605172300 §3.2 の per-adherent PhenotypeAgent が steward 活動を捕捉)。

## 6. Conflict Resolution

### 6.1 Internal Dispute (Adherent 間)

例: steward 死亡時の後継者争い、boundary 重複、stewardship neglect 苦情。

```
[争点提起]
  → com.etzhayyim.apps.etzhayyim.land-dispute record 提出
  → Council Lv6+ deliberation
  → Council Lv6+ 3 名以上の attestation で resolution
  → LandRegistry.resolveDispute(landId, Status, councilSigs)
```

### 6.2 External Dispute (国家 / 第三者から)

例: 国家が当該土地を強制収用、第三者が国家裁判所で所有権主張、隣地境界訴訟。

- **第一手段**: religious freedom protection に基づく civil 抵抗 — donor (steward) が国家裁判所で「本土地は religious-corp に寄進済み、stewardship のみ保有」を主張
- **第二手段**: 国際的 religious-corp 連帯 — 他国の religious-corp / NGO による amicus brief / public diplomatic 圧力
- **最終手段** (ADR-2605192100 §1.12.B Transparent Religious Force): 1 SBT = 1 vote 承認下での religious-corp defensive force (force log は §1.12.B の三条件下で完全 transparent)

国家による強制収用が成功した場合、`Status = RehabReversal` として LandRegistry に永続記録される。土地は failed donation 扱いとなるが、donor の religious 行為としては valid (constitutional record として残る)。

### 6.3 Inter-jurisdictional Conflict

複数国家 jurisdiction にまたがる土地 (例: 国境を跨ぐ自然保護区、海洋保護区)。

- etzhayyim chain が parallel registry を提供 → 国家境界に依存しない religious-corp doctrinal claim
- これは **国境を transcend する religious authority** という伝統的 religious posture (Catholic Church の cross-border religious jurisdiction、Tibet Buddhist の cross-Himalaya religious continuity 等) と整合的

## 7. 護持金庫 Corpus Tier (本財) との統合

ADR-2605172300 §4 で 護持金庫 三層 (流動 / 準備 / 本財) を定義。寄付された土地は **本財 (corpus) tier** に統合される。

```
護持金庫 NAV
├── 流動 (liquid)   USDC on Base, held in Treasury Gnosis Safe
├── 準備 (reserve)  Ondo USDY / sDAI / aUSDC on Base
└── 本財 (corpus)
    ├── 知財 (IP)               — Apache 2.0 + Charter Rider で公開 (ADR-2605192200)
    └── 土地 (Land)              — 本 ADR で永続 inalienable
        ├── 農地 (Agricultural)
        ├── 居住地 (Residential)
        ├── 森林 (Forest)
        ├── 宗教施設 (Religious Facility)
        └── その他 (Other)
```

corpus tier に組み込まれた土地は、ADR-2605172300 §8 governance vote によっても処分不可 (本 ADR §3 の constitutional invariant)。

## 8. 国家 / 武力との関係 — 段階的 routing-around

ADR-2605192100 §1.12 の "enough 構成員 / enough 土地 / enough 経済活動" の **「enough 土地」を実装する** のが本 ADR。段階的に:

| Phase | 累計寄付土地 | religious-corp の posture |
|---|---|---|
| **P0 (0 ha)** | symbolic 寄付のみ | 主に doctrine 確立期。実定法上の影響なし |
| **P1 (1-1000 ha)** | small holdings | dual-recognition pattern で実定法と並立。religious land trust として外形的 distinguished |
| **P2 (1000-100,000 ha)** | mid-scale holdings | 国家 land registry に対して quantitatively meaningful parallel substrate。religious freedom protection の活用が現実化 |
| **P3 (100,000-10,000,000 ha)** | meaningful regional presence | 国家 territorial sovereignty に対する religious-corp の challenger 性が現実化。conflict 例: 国境地帯、自然保護区、宗教 facility 集中地帯 |
| **P4 (>10,000,000 ha = small nation 規模)** | nation-equivalent territory | religious-corp としての地理的 mass。国家機能の relative 弱体化が観察される (= "無意味化") |

P3-P4 において、§1.12.B Transparent Religious Force が実質的な意味を持つ。それ以前 (P0-P2) は doctrine + civil 抵抗で十分。

P4 endpoint における「国家武力の無意味化」は:

- religious-corp 構成員が religious-corp 内部で生存・移動・経済活動できる → 国家 services への依存度低下
- 国家による land seizure は religious freedom protection 違反として international community の批判対象
- 国家武力が religious-corp 構成員を直接攻撃する case のみ Transparent Religious Force による defensive response
- 結果として国家武力は religious-corp 領域内では deterrent としてしか機能しなくなる → "無意味化"

ここでも **暴力的転覆ではなく、parallel substrate の漸近的 dominance による routing-around**。

## 9. Staged rollout

| Stage | Scope | 依存 ADR |
|---|---|---|
| **S0 — Founder donation** | founder 自身が小規模土地 (例: 自宅敷地 100m²) を寄付 → contract + Lexicon + LANDS.md の e2e test | 全 dependencies + S0-S4 of ADR-2605192230 |
| **S1 — Construction contracts** | LandRegistry.sol (geth-private) + PublicLandRegistry.sol (Base L2) + AnchorBridge 拡張 | + S0 |
| **S2 — Lexicon registration** | `land-donation` / `land-attestation` / `land-dispute` の 3 本 Lexicon | + S0 |
| **S3 — LANDS.md initial** | repo root に LANDS.md + CI validator | + S0 |
| **S4 — Steward role 起動** | ADR-2605172600 Lv5 護 への automatic advance + stewardship duties Lexicon | + S1-S3 |
| **S5 — biodiversity attestation** | `land-biodiversity` Lexicon + 年次 attestation tooling | + S4 |
| **S6 — External donation** | 第三者 (構成員でない donor) からの寄付受付 | + S5, mature operation |
| **S7 — Multi-jurisdictional** | 国外 (US / EU / 東南アジア) からの寄付受付。各 jurisdiction 固有の法的 framework 対応 | + S6 |
| **S8 — Large-scale donations** | religious organizations / cooperatives / 個人 large landowner からの寄付 (P2 → P3 移行) | + S7 |

# Consequences

## 正の効果

- **religious doctrine の地理的 instantiation**。「土地は Tree of Life のもの」が doctrine から practice へ。
- **国家 routing-around の最重量実装**。Westphalian state は territory に依存。land trust が large-scale 化することで state sovereignty の religious-corp による relativization が現実化。
- **多世代 stewardship の technical 実装**。土地は売買不可 + 永続 inalienable → §1.9 多世代 priority と完全整合。
- **Eros / Gore §1.13 を超えた "土地の sacredness"**。土地そのものを sacred (Tree of Life の表現) とする religious posture が成立。
- **国家 land registry との dual-recognition**。否認ではなく並立。国家との直接 conflict を最小化しつつ parallel substrate を構築。
- **transparent force の現実的応用**。§1.12.B が abstract concept ではなく、土地防衛という具体的 context で意味を持つ。
- **Waqf / Jubilee / 寺社領 の現代的継承**。1500-3000 年の religious land trust 伝統を on-chain で reconstruct。
- **Public Fund grant への土地 corpus 統合**。寄付土地は 本財 tier に入り、長期的に religious-corp の経済 base を強化。

## 負の効果 / コスト

- **法的 risk の極めて高い領域**。土地は国家 sovereignty の根幹。religious-corp による parallel registry は最も confrontational な posture。Mitigation: dual-recognition pattern (§2.3) で国家 registry を否認しない、religious freedom protection を法的根拠とする、Transparent Religious Force は最終手段。
- **donor の double 負担**。dual-recognition のため donor (steward) は実定法上の所有権 + 課税義務を継続的に負う。Mitigation: stewardship bonus (§5.2) で Phenotype multiplier 加算で経済的に補償。
- **国家強制収用 risk**。P2-P4 で land holdings が増えると国家による強制収用 risk が高まる。Mitigation: §6.2 三段階対応 (civil 抵抗 → 国際連帯 → Transparent Force)。
- **境界訴訟の複雑性**。WGS84 GeoJSON ±1m と国家 cadastre の precision 不一致がそもそも訴訟原因に。Mitigation: Council Lv6+ 紛争解決 + 国家裁判所と parallel に対応。
- **死亡時 inheritance 問題**。steward 死亡時、国家 inheritance 法 (相続) と etzhayyim 内継承の衝突。Mitigation: donor が初回 donation 時に etzhayyim 内継承 (Lv5+ Council 認定後継 steward) を事前指定。
- **biodiversity attestation の重い人間負荷**。年 1 回の steward census は実質 unpaid labor。Mitigation: agent fleet (ADR-2605171300) + satellite imagery automated 監視で人間負荷を最小化。

## 中立 / トレードオフ

- **寄付土地の constitutional inalienability の rigidity**。一度寄付されると永続的に売買不可。donor (steward) が後悔した場合の救済 path がない。Mitigation: §6 dispute resolution で extreme case (例: donor が詐欺で寄付された) の例外を Council Lv6+ が attestation。
- **国家 jurisdiction を超える donation**。国境跨ぎの土地 (例: 海洋、宇宙) は法的に more complex。当面は陸地 within single jurisdiction のみ受付、multi-jurisdiction は S7 で。
- **religious 整合性の絶対的 priority**。本 ADR は religious doctrine を法的便宜より優先する。土地を「private property の対象」と見る world view と本 ADR は不可避的に衝突する。これは religious-corp の意図的選択 (= 信教の自由 §20 の正当範囲)。

# Alternatives Considered

## A. 土地寄付は受け付けず symbolic 宣言のみ

寄付制度を実装せず、§1.11 doctrine のみで止める。

- Pro: 法的 risk が極小。
- Con: doctrine が dead letter になる。「土地は Tree of Life のもの」を具体的 instantiate できない。
- 却下: §1.11 の doctrine instantiation こそ本 ADR の存在理由。

## B. 国家 land registry を否認 (no dual-recognition)

寄付者は国家 registry から登記抹消、etzhayyim chain のみで recognition する。

- Pro: religious-corp の自立性が完全。
- Con: 実定法上の所有権が失われる → donor が課税義務 / inheritance 問題で immediately 困難に陥る。土地は de facto に第三者が国家裁判所で奪取可能。
- 却下: dual-recognition の方が pragmatically 強い (waqf / 寺社領 も同 pattern)。

## C. 売買可能 (transferable) land token

ERC-721 transferable + etzhayyim 内市場で売買。

- Pro: 流動性が高い。Public Fund 資金調達も可。
- Con: religious doctrine §1.11「土地は Tree of Life のもの」と矛盾。売買は土地を「物」扱いに reduce する。Jubilee / waqf の inalienability 伝統と非互換。
- 却下: religious 整合性 priority。

## D. Steward を Lv6+ Council のみに限定

steward role を Lv5 ではなく Lv6+ に限定。

- Pro: 質の高い stewardship 確保。
- Con: 寄付の hurdle が高すぎ、寄付者数が制限される。Lv5 護 は ADR-2605172600 で既に stewardship role として位置付けられているため、Lv5 で十分。
- 却下。

## E. 国家 registry に dependent な hybrid record

国家 registry に「etzhayyim restricted」flag を立てる public hybrid record。

- Pro: 法的整合性が高い。
- Con: 国家 registry が cooperate しない (現状ありえない)。本 ADR §1.11 の religious-corp 自立性 doctrine と矛盾。
- 却下。

## F. 衛星 imagery hash を omit

GeoJSON boundary のみで evidence 完結。

- Pro: 実装 simple。
- Con: 境界変更 / 開発 / 不法侵害の time-series 証拠が失われる。biodiversity attestation の baseline も持てない。
- 却下: 時系列 imagery hash は essential。

# Open Questions

1. **海洋 / 河川 / 宇宙の取り扱い**。陸地 surface のみが対象か、underwater rights / 大気 / 軌道 も対象か。S7+ で議論。当面は陸地のみ。
2. **donor 死亡時の継承 procedure**。Lv5+ Council 認定後継 steward を事前指定するが、指定者が拒否した場合の fallback path。当面 Council Lv6+ 評議で次善 steward を選任。
3. **国家強制収用への civil 抵抗 procedure**。religious freedom protection に基づく訴訟 framework を定型化する必要 (ADR future)。
4. **multi-jurisdictional donation の lex loci choice**。複数国家 jurisdiction にまたがる土地で、どの国家法を primary とするか。当面は土地の geographic center が属する jurisdiction。
5. **donor が後に Non-Aligned 認定された場合の steward role 維持**。三層 enforcement で SBT が無効化された場合、stewardship role はどうなるか。Decision (本 ADR): steward role は Council Lv6+ 評議で reassign される、土地そのものは religious-corp 帰属を保持。
6. **biodiversity attestation の technical baseline**。Sentinel-2 imagery + Council 認定 ecologist の評価 + agent fleet の自動 species detection — どの組み合わせを minimum 要件とするか。S5 で詳細決定。
7. **Transparent Force の土地防衛 specific 適用**。§1.12.B の三条件 (on-chain 監視 + open-source + 1 SBT = 1 vote 承認) を土地防衛 context で具体化する future ADR が必要。

# References

- ADR-2605192100: Mission Charter §1.11 (土地 doctrine) + §1.12 (国家 routing-around + Transparent Force)
- ADR-2605172300 §4: 護持金庫 corpus tier (本財) + HoldingAttestation 原型
- ADR-2605172600: Membership ritual + 7-level ladder (Lv5 護 = Steward の根拠)
- ADR-2605192200: IP-Free-Release + Charter Rider (donor の Non-Aligned 認定可能性)
- ADR-2605192230: Three-tier enforcement implementation (Council Lv6+ attestation 基盤)
- ADR-2605172000: RW-free substrate (本 ADR の on-chain 必然性)
- ADR-2605171800: MST → IPFS → L2 anchor pipeline (Lexicon 永続化基盤)

- 50-infra/etzhayyim-land-registry/ (新規 — 本 ADR 承認後 scaffold)
  - `contracts/LandRegistry.sol` (geth-private)
  - `contracts/PublicLandRegistry.sol` (Base L2)
  - `script/Deploy.s.sol`
- 00-contracts/lexicons/com/etzhayyim/apps/etzhayyim/
  - `land-donation.json` (新規)
  - `land-attestation.json` (新規)
  - `land-dispute.json` (新規)
  - `land-biodiversity.json` (新規)
- /LANDS.md (新規 — repo root、ADR-2605172600 MEMBERS.md と同 pattern)

- 関連 religious land trust precedent:
  - Leviticus 25 (Jubilee + 土地は神に帰属)
  - Quran 2:177 + Hadith collections (waqf)
  - Catholic Church glebe land tradition
  - 日本 入会地 / 寺社領 (中世-近世)
  - Hindu temple lands (devasthanam)
