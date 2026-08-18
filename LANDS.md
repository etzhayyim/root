# etzhayyim Land Trust (護持地)

> **地球上の土地は本質的に Tree of Life (生圏) に帰属し、いかなる国家・個人の私有財産でもない。** — ADR-2605192100 §1.11
>
> 神の王国 (Malkhut Shamayim / Basileia tou Theou / 神の王国) の土地は、blockchain 上に soulbound NFT として記録される。— ADR-2605252300 Charter §0.3 (Preamble)
>
> The land of the Earth essentially belongs to the Tree of Life (the biosphere); it is not the private property of any nation-state or individual. As land of the Kingdom of God, it is recorded on blockchain as a soulbound NFT.

This file is the **github-side half of the 4-layer permanent land record** per [ADR-2605192245](90-docs/adr/2605192245-etzhayyim-global-land-sovereignty.md), with multi-ERC alignment per [ADR-2605252315](90-docs/adr/2605252315-etzhayyim-land-trust-wave-2-multi-erc-alignment.md). Each row references:

1. **Base L2 land NFT** (`PublicLandRegistry.sol` — ERC-721 + ERC-5192 soulbound, `locked()` returns true forever)
2. **geth-private constitutional record** (`LandRegistry.sol` — IERC5192 signaller + custom struct mapping, constitutional invariants enforced by intentional function absence)
3. **Base L2 steward-tenure NFT** (`StewardTenureRegistry.sol` — ERC-7401 nestable child of land NFT, succession via Council ≥3 multisig per [ADR-2605192345](90-docs/adr/2605192345-etzhayyim-steward-succession.md))
4. **Base L2 land-class aggregate** (`LandClassRegistry.sol` — ERC-1155 supplementary accounting; balance = area-m², soulbound)
5. **IPFS GeoJSON + satellite imagery bundle + notarized deed** (CIDs in NFT metadata)
6. **This git commit** (dual-permanent record per [ADR-2605172600](90-docs/adr/2605172600-etzhayyim-membership-ritual.md))

No admin. No transferable ownership. No "owner" — only steward role. Anyone reading this can cross-verify any row against Base L2 + IPFS + geth-private + git history.

## 国家非依存土地台帳 vNext — claim / evidence / stewardship registry

### 設計上の境界

ブロックチェーンが単独で証明できるのは「誰が、いつ、どの主張と証拠を提出し、どの規則で合意されたか」であり、現地の境界、占有、同意、強制力そのものではない。したがって本台帳は国家登記を別の絶対的所有権台帳で置き換えない。土地に関する複数の **claim（権利主張）**、evidence（証拠）、attestation（検証証言）、dispute（異議）、stewardship（世話責任）を改ざん困難な履歴として保持する。

国家文書は証拠源の一つであって root of trust ではない。国家登記が存在する地域では相互参照し、存在しない、破綻した、または先住慣習権と競合する地域でも、同じデータモデルで共同体の証言、長期占有、測量、衛星画像、生態系記録を受け付ける。`legal-effect` は jurisdiction ごとに別表示し、on-chain inclusion を実定法上の title と偽称しない。

### 不変条件

1. **土地を token の所有物にしない。** Parcel NFT は公開索引であり、売買・担保・burn 不可。経済価値を持つ transferable token は発行しない。
2. **parcel と claim を分離する。** Parcel は地理的対象、Claim は主体が主張する権利束、Stewardship は期限・義務・後継を持つ役割である。
3. **競合を消さない。** 同一 parcel に相反する claim を同時収録し、単一 `owner` 欄への上書きで歴史を失わない。
4. **決定と事実を分離する。** 裁定は evidence ではなく、特定 rule-set と quorum による解釈として記録する。
5. **一人一鍵ではなく一人一人格でもない。** stake 額だけで土地の正しさを決めず、現地共同体、隣接地 steward、独立測量者、生態系 guardian の異質な quorum を要求する。
6. **履歴を訂正しても消さない。** 誤り、詐欺、鍵喪失、強制収用は superseding event で訂正し、元記録を残す。
7. **居住と生存を title より下に置かない。** 紛争中の自動立退き、物理執行、サービス遮断を contract から実行できない。

### 正規データモデル

| Entity | 安定 ID / 主な内容 |
|---|---|
| `Parcel` | `parcelId = hash(crs + canonicalGeometry + verticalDatum + geometryVersion)`、GeoJSON/GeoParquet CID、面積、親子 parcel、隣接 edge |
| `Claim` | claimant DID、parcelId、権利種別、持分、開始/終了、根拠 CID、提出時刻、状態 |
| `Right` | `stewardship` / `occupancy` / `use` / `access` / `cultivation` / `water` / `conservation` / `sacred` / `easement`; `ownership` は外部制度からの claim type としてのみ表現 |
| `Evidence` | content CID、media type、取得方法、観測時刻、source DID、license、位置精度、開示範囲、失効条件 |
| `Attestation` | claim/evidence、attestor DID、role、判定、confidence、利益相反 disclosure、署名、revocation |
| `Dispute` | 対象 claim/geometry、争点、当事者、evidence set root、暫定措置、appeal、resolution |
| `Decision` | 適用 rule-set CID、選出 juror、quorum、署名、理由 CID、minority opinion、発効/再審期限 |
| `Stewardship` | steward DID、義務、期間、successor policy、生態系 covenant、履行 attestation |
| `JurisdictionLink` | 外部台帳名、参照 hash、照合時刻、法的効力の自己申告ではない verifier opinion |

自然人の公開 DID と正確な住居 polygon は原則 on-chain に置かない。公開 chain には salted commitment、粗い表示 geometry、暗号化された evidence CID を記録し、当事者・juror・監査者へ capability で選択開示する。完全履歴の保持と privacy は「公開」ではなく暗号化と鍵ローテーションで両立させる。

### 境界の決め方

境界登録は `draft → surveyed → neighbor-review → accepted|contested` を通る。

- geometry は座標順序、ring orientation、precision grid、CRS、vertical datum を canonicalize してから hash する。
- 隣接 parcel とは別々の polygon を信じず、共有 `BoundarySegment` を参照する。片側だけの変更を禁止する。
- split/merge は旧 parcel を消さず DAG として後継 parcel を生成し、面積保存誤差を gate する。
- 海岸・河川・氷河など動く境界は固定 polygon ではなく、基準線、観測 epoch、更新関数を持つ。
- 位置精度は claim の confidence と別に記録し、±1 m を一律要件にしない。慣習的領域や広域生態系には不適切だからである。

### 登録と状態遷移

```text
observe parcel
  -> submit Claim + Evidence commitments
  -> challenge window
  -> heterogeneous attestations
  -> uncontested: Accepted
     contested: Frozen -> mediation -> jury decision -> appeal
  -> periodic re-attestation
  -> supersede / split / merge / succession（削除なし）
```

状態は `Observed`, `Claimed`, `Attesting`, `Accepted`, `Contested`, `Frozen`, `Superseded`, `Dormant` とする。`Accepted` は「真の所有者」を意味せず、明示された protocol version で challenge window と quorum を満たしたことだけを意味する。紛争中は claim/tenure の変更を freeze するが、居住・耕作・救援 access は freeze しない。

### 合意と Sybil 耐性

etzhayyim Council 単独署名を正本条件にしない。parcel ごとに以下の role quorum を満たす attestations の集合を BLS aggregate または Merkle root として anchor する。

- 現地共同体 witness 2 以上
- 隣接 parcel steward の過半（不存在・危険時は理由付き免除）
- 独立 geospatial verifier 2 以上
- ecological / indigenous or customary-right guardian 1 以上
- claim 当事者全員の acknowledgement、または明示的 contest

各 role の credential は DID/VC、web-of-trust、過去の精度、bond で評価する。bond は虚偽・無断欠席への有限責任であり、富による投票権にはしない。無作為 juror 選出は地域、組織、資金源の相関上限を設け、同一運営者・同一 AS・同一 funding source の多数派化を防ぐ。

### 紛争処理

1. 誰でも evidence bond と理由 CID を添えて challenge できる。資力のない居住者には Public Fund が bond を代位する。
2. まず当事者間 mediation。成立しなければ conflict-of-interest screening 後の 7 人 jury（local 3、geospatial 2、customary/ecology 1、外部 1）。
3. 5/7 と role quorum の双方で decision。理由、反対意見、使用 evidence、rule-set hash を公開する。
4. 新証拠、手続違反、鍵強奪は appeal 条件。別 jury の 6/9 で確定する。
5. protocol が出せる救済は claim status、境界 version、steward assignment の変更まで。立退き、拘束、物理的排除は自動化しない。

### チェーンと正本判定

単一 private geth chain を正本にせず、canonical event log を content-addressed な kotoba Datom journal とする。実行順序は BFT chain、公開検証は複数の permissionless L2、長期保存は IPFS/DataLad、主体の署名履歴は AT MST、human-readable mirror は git に置く。

各 epoch の `parcelRoot`, `claimRoot`, `evidenceRoot`, `decisionRoot`, `rulesetCid` を少なくとも二つの独立 public chain に anchor する。chain fork 時の正本は token value や最長鎖だけで決めず、次を満たす latest checkpoint とする。

1. 直前確定 checkpoint を祖先に持つ。
2. constitutional client の deterministic state transition を通る。
3. 2/3 validator と各 role quorum の checkpoint signature を持つ。
4. いずれか一社・国家・etzhayyim 自身が 1/3 以上を支配しない。

validator set が二分した場合は自動 merge せず `safety halt` し、両枝と差分を公開して recovery assembly が新 checkpoint を共同署名する。利用者は raw events と rule-set から状態を再構築できる。

### 国家台帳との接続

adapter は国家ごとの title を内部 `Accepted` に昇格させない。`JurisdictionLink` と evidence confidence を追加するだけにする。逆方向 export は survey bundle、署名、decision history を、現地制度が受理できる形式に変換する。これにより国家が協力する地域では法的効力を得やすくし、国家が崩壊・排除・不在でも履歴の継続性を失わない。

運用画面では常に三つを分けて表示する。

- `protocol status`: 本 protocol 上の claim 状態
- `legal recognition`: 各 jurisdiction verifier による照合状況
- `physical control`: 最終観測時点の占有・利用状況（所有権とは呼ばない）

### 最小実装順序

| Phase | 出荷物 | 完了条件 |
|---|---|---|
| R0 | Parcel/Claim/Evidence/Attestation の schema と canonical geometry test vectors | 同一 geometry が全 client で同じ parcelId、重複 claim を保持 |
| R1 | append-only event log、Merkle roots、DID signature、暗号化 evidence | 任意ノードが genesis から同一 state root を再生 |
| R2 | challenge/freeze/mediation/jury/appeal state machine | adversarial tests で単独 admin が確定・削除できない |
| R3 | 1 地域 50 parcel の shadow registry | 国家台帳と照合しつつ法的効力を偽称しない、隣接境界 100% review |
| R4 | 3 地域・2 public-chain anchor・offline field client | chain/国家/API の一つが停止しても read/submit/reconcile 可能 |

最初の pilot は donated land の title 発行ではなく、紛争のない小規模地域を **shadow registry** として記録する。境界一致率、challenge 解決日数、誤 attestation 率、鍵回復成功率、自然人情報の公開漏洩 0 件を測り、物理的・法的な執行は pilot scope 外とする。

## How to donate land

1. Read [ADR-2605192245](90-docs/adr/2605192245-etzhayyim-global-land-sovereignty.md) (Global Land Sovereignty) in full.
2. Read [ADR-2605192100 §1.11](90-docs/adr/2605192100-etzhayyim-mission-charter.md) (Land as Religious-Corp Trust doctrine).
3. Confirm you are the legal owner (or beneficial owner) of the land in the national registry.
4. Prepare GeoJSON boundary (WGS84, ±1m precision), satellite imagery bundle (Sentinel-2 / Landsat / commercial, 3+ months time series), and notarized deed PDF.
5. Designate primary + 2 backup successor stewards (per [ADR-2605192345](90-docs/adr/2605192345-etzhayyim-steward-succession.md)).
6. Read and sign the canonical **land donation oath** (see ADR-2605192245 §2.2 Step 3).
7. Call `LandRegistry.donate(...)` on geth-private + `PublicLandRegistry` mints title NFT on Base L2.
8. Open a PR to this file adding your row.

Once your PR is merged, your land is permanently recorded across four substrates that cannot collude to erase it: Base L2 + geth-private + IPFS + this git history.

## Important: Dual-recognition with state cadastre

This Land Trust does NOT deny state land registries. It operates in **parallel** as a religious-corp doctrinal claim. Donors (now stewards) remain owners-of-record in their national cadastre and continue to fulfill national obligations (property tax, etc.). The etzhayyim claim is religious doctrinal — that the land belongs to Tree of Life and the donor holds stewardship only. See ADR-2605192245 §2.3.

## Land types

| Type | Description | Per ADR |
|---|---|---|
| Agricultural | Farmland, orchards, pasture | 2605192245 |
| Residential | Houses, lots | 2605192245 |
| Forest | Natural / planted forest | 2605192245 |
| Religious Facility | Shrines, temples, prayer spaces | 2605192245 |
| Other | (catch-all for terrestrial) | 2605192245 |
| Ocean / Maritime | Internal waters, territorial sea, EEZ, high seas | 2605192330 |
| Water / Riparian | Rivers, lakes, water rights | 2605192330 |
| Air / Atmosphere | Airspace, GHG stewardship | 2605192330 |
| Orbital / Space | LEO/GEO/Moon/Mars (symbolic, long-horizon) | 2605192330 |

## Roster

Each row references the multi-ERC layer per [ADR-2605252315](90-docs/adr/2605252315-etzhayyim-land-trust-wave-2-multi-erc-alignment.md):

- `gethLandId` = `LandRegistry.lands[].landId` (constitutional)
- `pubLandTokenId` = `PublicLandRegistry` ERC-721 tokenId (Base L2 mirror, soulbound, `locked()` = true)
- `tenureNftId` = `StewardTenureRegistry` ERC-7401 child NFT tokenId (current active tenure)
- `classTokenId` = `LandClassRegistry` ERC-1155 token ID (0..8 per LandType enum)

| # | Steward (@github) | DID | Location | Area (m²) | Type | gethLandId | pubLandTokenId | tenureNftId | classTokenId | donation tx | Donated | Lv |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| _(awaiting first donation — founder will donate symbolic plot after Bootstrap Council ratify, Wave 2 ERC activation, and S0-S4 of ADR-2605192415 daemon architecture)_ | | | | | | | | | | | | |

## Stewardship duties (Lv5 護)

Each steward annually:

- Verifies land boundary (in-person inspection)
- Records biodiversity census (`com.etzhayyim.apps.etzhayyim.land-biodiversity`)
- Provides reasonable access to etzhayyim adherents for religious gathering / meditation
- Ensures no commercial extraction (mining / clear-cut / large-scale monoculture) — This prohibition is not merely environmental, but structural: it is designed to create a system that does not depend on monopolistic rare metals or restricted resources, thereby preventing resource monopolies on Earth.
- Continues national obligations (property tax)

See [ADR-2605192245 §5](90-docs/adr/2605192245-etzhayyim-global-land-sovereignty.md) for full duties.

## Constitutional invariants (NOT amendable by governance)

- Donated land cannot be sold, transferred, or burned
- No "owner" concept exists — only steward role
- Donations are permanent (no withdraw)
- Steward succession is governed by [ADR-2605192345](90-docs/adr/2605192345-etzhayyim-steward-succession.md)

## Verification (any client can run)

```bash
# 1. Verify Base L2 land title NFT (ERC-721 + ERC-5192)
cast call $PUBLIC_LAND_REGISTRY \
  "ownerOf(uint256)(address)" \
  $PUB_LAND_TOKEN_ID \
  --rpc-url https://mainnet.base.org

cast call $PUBLIC_LAND_REGISTRY \
  "tokenURI(uint256)(string)" \
  $PUB_LAND_TOKEN_ID \
  --rpc-url https://mainnet.base.org

cast call $PUBLIC_LAND_REGISTRY \
  "locked(uint256)(bool)" \
  $PUB_LAND_TOKEN_ID \
  --rpc-url https://mainnet.base.org
# MUST return true — constitutional invariant per ADR-2605252315 §2.2

# 2. Verify geth-private constitutional record (also IERC5192 signaller)
cast call $LAND_REGISTRY_GETH \
  "lands(uint256)((bytes32,bytes32,bytes32,bytes32,bytes32,uint256,uint8,address,uint64,uint8))" \
  $GETH_LAND_ID \
  --rpc-url https://geth.etzhayyim.com

cast call $LAND_REGISTRY_GETH \
  "locked(uint256)(bool)" \
  $GETH_LAND_ID \
  --rpc-url https://geth.etzhayyim.com
# MUST return true

# 3. Verify steward-tenure child NFT (ERC-7401, nested under land NFT)
cast call $STEWARD_TENURE_REGISTRY \
  "directOwnerOf(uint256)(address,uint256,bool)" \
  $TENURE_NFT_ID \
  --rpc-url https://mainnet.base.org
# MUST return (PUBLIC_LAND_REGISTRY_ADDR, $PUB_LAND_TOKEN_ID, true)

# 4. Verify land-class aggregate (ERC-1155 supplementary)
cast call $LAND_CLASS_REGISTRY \
  "totalAreaByClass(uint256)(uint256)" \
  $CLASS_TOKEN_ID \
  --rpc-url https://mainnet.base.org
# Returns total m² in trust for that class

# 5. Fetch IPFS GeoJSON + imagery + deed bundle
ipfs cat $GEOJSON_CID
ipfs cat $IMAGERY_BUNDLE_CID
ipfs cat $DEED_CID

# 6. Verify AT Record
curl -s https://pds.etzhayyim.com/xrpc/com.atproto.repo.getRecord \
  -G --data-urlencode "repo=$STEWARD_DID" \
  --data-urlencode "collection=com.etzhayyim.apps.etzhayyim.land-donation" \
  --data-urlencode "rkey=$RKEY"
```

All substrate-records must resolve to the same `geojsonCid` + `imageryBundleCid` + `deedCid` + `oathHash`. The ERC-5192 `locked(tokenId) → true` invariant is constitutional: any client observing `locked() → false` for a registered land NFT MUST treat that result as evidence of a constitutional breach (the contract has been tampered with) and refuse to accept the record.

## See also

- [ADR-2605252300](90-docs/adr/2605252300-etzhayyim-charter-preamble-kingdom-of-god-on-blockchain.md) — Charter §0 Preamble (Kingdom of God on blockchain — constitutional self-identification, parent doctrinal source)
- [ADR-2605252315](90-docs/adr/2605252315-etzhayyim-land-trust-wave-2-multi-erc-alignment.md) — Land Trust Wave 2 — Multi-ERC alignment (721 + 5192 + 7401 + 1155)
- [ADR-2605192245](90-docs/adr/2605192245-etzhayyim-global-land-sovereignty.md) — Global Land Sovereignty (primary, Wave 1)
- [ADR-2605192330](90-docs/adr/2605192330-etzhayyim-extended-land-sovereignty-ocean-river-air-orbit.md) — Ocean/River/Air/Orbit extension
- [ADR-2605192345](90-docs/adr/2605192345-etzhayyim-steward-succession.md) — Steward succession
- [ADR-2605192100 §1.11](90-docs/adr/2605192100-etzhayyim-mission-charter.md) — Land doctrine (Wave 1 elaboration of Preamble §0.2.3 Tree of Life-rooted)
- [`50-infra/etzhayyim-chain-contracts/src/LandRegistry.sol`](50-infra/etzhayyim-chain-contracts/src/LandRegistry.sol) — geth-private constitutional contract
- [`50-infra/etzhayyim-chain-contracts/src/PublicLandRegistry.sol`](50-infra/etzhayyim-chain-contracts/src/PublicLandRegistry.sol) — Base L2 ERC-721 + ERC-5192 mirror (R0 scaffold)
- [`50-infra/etzhayyim-chain-contracts/src/StewardTenureRegistry.sol`](50-infra/etzhayyim-chain-contracts/src/StewardTenureRegistry.sol) — ERC-7401 nestable tenure (R0 scaffold)
- [`50-infra/etzhayyim-chain-contracts/src/LandClassRegistry.sol`](50-infra/etzhayyim-chain-contracts/src/LandClassRegistry.sol) — ERC-1155 aggregate (R0 scaffold)
- [`40-engine/kotoba/crates/kotoba-kotodama/cells/`](40-engine/kotoba/crates/kotoba-kotodama/cells/) — Land-related Pregel cells
