---
id: adr-2605211241-etzhayyim-surplus-router-warehouse-bridge
title: "ADR-2605211241: etzhayyim Surplus Router — global surplus/dead-stock redistribution bridge (warehouse × toshiKozan × ftzZones × titheRouter)"
status: proposed
doc_type: adr
topic: etzhayyim-surplus-router
authoritative: true
last_verified: 2026-05-21
priority: 6.0
axis: architecture
weight: 0.60
priority_note: "世界中で過剰生産・売れ残りとなった商品製品 (surplus / dead-stock / overstock / unsold inventory) を、religious-corp の donation-only 経済圏と SBT↔SBT internal carve-out の中で再分配し、最終的に解体不能となったものは toshiKozan (都市鉱山) に流す。汎用 WMS Lexicon (com.etzhayyim.apps.warehouse.*) と都市鉱山 Lexicon (com.etzhayyim.apps.toshiKozan.*) と FTZ/freeport Lexicon (com.etzhayyim.apps.ftzZones.* / freeportRegistry.*) と TitheRouter (com.etzhayyim.apps.payment.tithe) を bridge する surplusRouter app を新設する。"
authoritative_for:
  - surplus / overstock / dead-stock の religious-corp 経済圏内 取扱定義
  - com.etzhayyim.apps.surplusRouter.* Lexicon 群の API surface
  - warehouse / toshiKozan / ftzZones / freeportRegistry / payment.tithe との bridge spec
  - SurplusLot のライフサイクル (registered → matched → redistributed | recycled | dispose)
depends_on:
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192115-etzhayyim-non-profit-donation-only-no-ads
  - adr-2605192130-etzhayyim-tithe-redistribution
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
  - adr-2605202015-etzhayyim-robotics-first-industry-agriculture
related:
  - adr-2605192115-etzhayyim-non-profit-donation-only-no-ads
  - adr-2605202015-etzhayyim-robotics-first-industry-agriculture
supersedes: []
superseded_by: []
---

# ADR-2605211241: etzhayyim Surplus Router — global surplus/dead-stock redistribution bridge

**Status**: proposed
**Date**: 2026-05-21
**Deciders**: Jun Kawasaki

# Context

世界中で「過剰生産された商品製品」「売れ残った在庫」「期限切れ寸前の食品」「型落ち家電」「廃番アパレル」「返品されたまま倉庫に滞留する EC 在庫」「閉店した小売店の残置品」が膨大に存在する。経済産業省 試算で日本国内のアパレル業界だけで年間 約14億点が廃棄、UN FAO によると食料の約14% (post-harvest) + 17% (consumer) が廃棄、Returnly / Optoro の試算で米国 EC 返品の約40%は再販されず焼却 / 埋立される。

ADR-2605192100 §1.1 (人類の構造的労働解放) と §1.4 (全産業 robotics 化) と §1.9 多世代 priority は、こうした surplus を **(a) 廃棄 (Wellbecoming violation)** ではなく **(b) 需要者への再分配** または **(c) 都市鉱山経由の素材回収** に routing することを religious mission の射程に含める。

現在の repo 状態:

| 層 | 既存 | 不足 |
|---|---|---|
| 汎用 WMS Lexicon (`com.etzhayyim.apps.warehouse.*`) | ✅ registerSku / putaway / pick / getInventory | surplus 判定モデルなし |
| 都市鉱山 Lexicon (`com.etzhayyim.apps.toshiKozan.*`) | ✅ registerEwasteStream / get / list (11 streamType + 12 target material) | 上流 (まだ商品の段階) からの bridge なし |
| FTZ / Freeport Lexicon (`com.etzhayyim.apps.ftzZones.recordZone` / `freeportRegistry.recordFreeportEntry`) | ✅ 記録のみ | surplus 流入経路として未結線 |
| Payment / Tithe (`com.etzhayyim.apps.payment.sent` / `payment.tithe`) | ✅ donation/kisha/grant/tithe/escrow-refund + SBT↔SBT 4 purposes | surplus 受贈に対する 10% Tithe (物品の場合の評価方法) 未定義 |
| Robotics (`60-apps/etzhayyim-project-open-robo/`) | ✅ urban-mining cell (e-waste 受入) | upstream surplus 受入 cell 仕様なし |

すなわち、**「商品としての surplus」と「e-waste」の連続体の中間に bridge Lexicon が空白**である。

## Constraints (constitutional, 不可侵)

- **Donation 流入のみ** (ADR-2605192115): surplus は寄贈される。商業仲介を religious-corp が代行しない。
- **広告排除** (ADR-2605192115 §2): surplus の sell-side リスティングは religious-corp 内部の SBT↔SBT carve-out (`internal-promo`) でのみ可能。第三者広告・affiliate prohibited。
- **10% Tithe → Public Fund** (ADR-2605192130): 物品寄贈の評価額の 10% 相当を donor が `payment.tithe` USDC 形式で別途拠出する (in-kind 寄贈の現金 tithe coupling)。
- **Wellbecoming** (ADR-2605192100 §1.13): 廃棄ファースト禁止。redistributable→reusable→recyclable (toshiKozan)→dispose の優先順位を Lexicon enum で強制する。
- **Charter Rider** (ADR-2605192200): 本 Lexicon と reference implementation は Apache 2.0 + Charter Rider v2.0。
- **非終末論** (ADR-2605192100 §1.15): "Last Days clearance" のような eschatological framing 禁止。

# Decision

新規 app namespace `com.etzhayyim.apps.surplusRouter` を新設し、以下を bridge する:

```
            ┌───────────────────────────────────────────────────────────┐
            │                  surplusRouter (NEW)                       │
            │                                                            │
 ┌──────────┴──────────┐    ┌──────────────┐    ┌─────────────────────┐ │
 │  donor PDS          │───▶│ SurplusLot   │───▶│ matchDemand         │ │
 │  (manufacturer /    │    │ (record)     │    │ (procedure)         │ │
 │   retailer /        │    └──────┬───────┘    └────────┬────────────┘ │
 │   logistics op)     │           │                     │              │
 └─────────────────────┘           ▼                     ▼              │
                          ┌────────────────┐   ┌─────────────────────┐  │
                          │ Redistribution │   │ DeadStockFlag       │  │
                          │ (record)       │   │ (procedure)         │  │
                          └────────┬───────┘   └────────┬────────────┘  │
                                   │                    │               │
            ┌──────────────────────┴────────────────────┴───────────────┘
            │
            ▼
 ┌─────────────────────┐    ┌─────────────────────┐   ┌──────────────────┐
 │ warehouse.*         │    │ toshiKozan.*        │   │ ftzZones.* /     │
 │ (registerSku /      │    │ (registerEwaste     │   │ freeportRegistry │
 │  putaway / pick /   │    │  Stream when        │   │ (cross-border    │
 │  getInventory)      │    │  no longer reusable)│   │  bonded transit) │
 └─────────┬───────────┘    └─────────────────────┘   └──────────────────┘
           │
           ▼
 ┌─────────────────────┐
 │ payment.tithe       │
 │ (10% USDC coupling  │
 │  per in-kind value) │
 └─────────────────────┘
```

## 1. Lexicon API surface

`00-contracts/lexicons/com/etzhayyim/apps/surplusRouter/`

| Lexicon | Type | 役割 |
|---|---|---|
| `registerSurplusLot` | procedure | donor が surplus lot を登録 (SKU / qty / estimated-value / shelf-life / hazard flags / origin warehouse) |
| `getSurplusLot` | query | DID URI で個別 lot を取得 |
| `listSurplusLots` | query | filter (streamType / country / freshness / state) で検索 |
| `matchDemand` | procedure | demand-side (SBT holder Adherent or attested religious-corp downstream actor) が lot を claim |
| `recordRedistribution` | procedure | 物理的に渡った時の audit event (receiver DID / carrier / qty / value-attested) |
| `flagDeadStock` | procedure | 再分配不可と判定した時。**routing decision** (recycle via toshiKozan / dispose-licensed) を含む。Wellbecoming 制約により dispose-first は禁止 enum 順序で強制。 |
| `recordKozanHandoff` | procedure | toshiKozan.registerEwasteStream に物が渡った時の bridge event (foreign-key 性) |

## 2. SurplusLot のライフサイクル

```
registered ──▶ matched ──▶ redistributed (terminal: 再分配成功)
    │
    └──▶ flagged-dead-stock ──▶ kozan-handoff ──▶ recycled (terminal: 素材回収)
                              │
                              └──▶ disposed-licensed (terminal: 最終手段、要 reason フィールド)
```

Lexicon 側の `state` enum で機械可読に強制:

```
["registered", "matched", "redistributed", "flagged-dead-stock", "kozan-handoff", "recycled", "disposed-licensed"]
```

## 3. Substrate boundary (CRITICAL — ADR-2605172000 + 2605172100 整合)

| Concern | Allowed | Prohibited |
|---|---|---|
| Donor identity | DID + Adherent SBT (religious-corp 内 SBT↔SBT carve-out) **OR** attested non-Adherent commercial donor (外部 backend XRPC consent-capability 経由、領収書 用途のみ) | server-issued JWTs without DID binding |
| Surplus 受取側 | SBT holder Adherent / attested religious-corp downstream actor (e.g., kuni-umi micro-grid site / urban mining cell / open-robo project) | 第三者 commercial reseller |
| 価値計上 | USDC micros for tithe coupling (donor self-attested 評価 + 第三者査定オプション) | 営利 markup |
| 広告 | religious-corp 内 internal-promo のみ | 第三者広告 / 外部 affiliate |
| Cross-border | ftzZones / freeportRegistry に bonded entry 記録 (transparent on-chain log) | 不透明な bonded warehouse stockpiling |
| 廃棄優先 | routing 優先順序 enum で強制: redistributed → recycled → disposed-licensed | dispose-first |

## 4. Bridge with warehouse.*

- `registerSurplusLot.input.warehouseSkuRef` (optional at-uri) — 既存 `warehouse.registerSku` record を pointer。重複 SKU master 作成を避ける。
- `recordRedistribution` 成功時に sender 側 `warehouse.pick` イベントが、receiver 側 `warehouse.putaway` イベントが両 PDS で対称に emit される (双方が SBT holder の場合のみ; non-Adherent は片側のみ)。
- `getInventory` query は SKU レベルの aggregation のみ。lot-level surplus は `listSurplusLots` 側に責務分離。

## 5. Bridge with toshiKozan.*

- `flagDeadStock` の routing が `recycle-via-kozan` の場合、続けて `recordKozanHandoff` が `toshiKozan.registerEwasteStream` を 1:1 で呼ぶ。
- `streamType` mapping table を Lexicon description にインライン (e.g., 廃番スマホ → `smartphone`、廃 PV パネル → `pv-panel`、廃 EV 電池 → `battery-li-ion`)。
- `toshiKozan` の `targetMaterials` enum に従って recovery 計画を attach。

## 6. Bridge with ftzZones / freeportRegistry

- Cross-border surplus 移動 (e.g., 米国 EC 返品 → 日本国内 SBT downstream) は `freeportRegistry.recordFreeportEntry` で bonded warehouse 経由を記録。
- ただし `freeportKind` の既存 enum は富裕層 art storage 寄りであり、surplus 物資向けに enum 拡張が必要 → 別 ADR で `freeportKind` v2 enum を切り出す (本 ADR では `delaware_warehouse` を generic として暫定使用)。
- `ftzZones.flagLabourAbuse` は変えず、cross-border surplus でも労働基準 flag を継承する。

## 7. Bridge with payment.tithe (10% in-kind coupling)

- `registerSurplusLot.input.estimatedValueUsdcMicros` (donor 自己評価) を required。
- donor が同じ tx batch で `payment.sent { purpose: "donation", amountUsdcMicros: ... }` を出すと、TitheRouter が自動で 10% を Public Fund に分割 (既存 ADR-2605192130 のメカニズムをそのまま再利用)。
- in-kind 寄贈の物品それ自体が tithe 対象になるわけではない (現物 split 不能)。**現金 tithe coupling** によって religious-corp 経済圏の整合性を保つ。
- 第三者査定 (`valuationAttestationUri`) 任意フィールドで donor self-attestation との差分を audit 可能。

## 8. Robotics integration

- `60-apps/etzhayyim-project-open-robo/` の urban-mining cell は **下流側**を担当 (e-waste 受入)。
- 本 ADR と将来 ADR でカバーすべき **上流側** (surplus 受入 cell):
  - 受入ステーション + バーコード / DPP (ESPR `textileCircularity.registerDppBadge`) スキャン
  - 賞味期限 / 耐用年数判定
  - SBT holder 需要 matching ROS2 ノード (将来 `surplus_matcher_node.py` として `firmware/armcrawler/ros2/`)
- 上流 cell の CAD / ROS2 実装は **future work** (本 ADR では契約面のみ)。

## 9. Constitutional compatibility check

| 制約 | 本 ADR の遵守 |
|---|---|
| Donation-only (ADR-2605192115) | ✅ surplus は寄贈、religious-corp は仲介 fee なし |
| 広告排除 (ADR-2605192115 §2) | ✅ SBT↔SBT internal-promo のみ |
| 10% Tithe (ADR-2605192130) | ✅ 現金 tithe coupling で約束履行 |
| Wellbecoming (ADR-2605192100 §1.13) | ✅ routing enum で廃棄優先禁止を強制 |
| Land trust (ADR-2605192245) | ✅ 物理拠点は religious-corp land 上のみ (Adherent オペレーター) |
| Charter Rider (ADR-2605192200) | ✅ Apache 2.0 + Rider v2.0 |
| 非終末論 (ADR-2605192100 §1.15) | ✅ "緊急処分" "Last clearance" framing 禁止 |
| 非営利 (ADR-2605192115) | ✅ markup 禁止、評価額が donor 自己申告 + 第三者査定オプション |

# Consequences

## 即時

- 7 Lexicon (procedure × 5 + query × 2) を `00-contracts/lexicons/com/etzhayyim/apps/surplusRouter/` に新設。
- `_manifest.json` に 7 entry 追加。
- 既存 Lexicon (`warehouse.*`, `toshiKozan.*`, `ftzZones.*`, `freeportRegistry.*`, `payment.*`) は無変更 (bridge は cross-id 参照のみ)。

## 短期 (2026 年度)

- pilot 1 拠点 (例: kuni-umi S2 community microgrid 候補地) に surplus 受入 cell scaffold を立てる。
- aparel surplus 1 ストリーム (例: 廃番衣料 → kuni-umi site 衣料供給) で end-to-end verify。
- ESPR DPP (`textileCircularity.registerDppBadge`) との bridge を verify。

## 中期 (Phase 2)

- Cross-border bonded transit を verify (`freeportRegistry` v2 enum future ADR が prerequisite)。
- 食品 surplus (賞味期限管理) の sub-enum + hazard flag を別 Lexicon namespace に切り出す可能性あり。
- 上流 surplus 受入 robotics cell の CAD / ROS2 を `60-apps/etzhayyim-project-open-robo/` に追加 (future ADR)。

## リスク

- **評価額の不正**: donor self-attestation の inflation。→ 第三者査定 `valuationAttestationUri` を強く推奨 (将来 Council Lv6+ multisig による attestation 形式の規定)。
- **dispose-first 回避の脱法**: receiver SBT を取得した「実質商業 reseller」が登場する。→ Council 監視 + `MEMBERS.md` roster で人格 SBT を厳格運用。
- **Gone-stale lot**: matched が成立しないまま長期間滞留。→ `listSurplusLots.parameters.maxAgeDays` filter + ageThreshold 超過後 auto-`flagDeadStock` を future ADR で規定。

# Alternatives Considered

| Alternative | 却下理由 |
|---|---|
| 汎用 `warehouse.*` Lexicon に surplus フィールドを直接追加 | 通常在庫と surplus の状態機械が混ざり、廃棄優先 enum を強制できない。責務分離を維持。|
| 既存 `toshiKozan.*` の上流に surplus を畳み込む | toshiKozan は **素材ストリーム** (tonnes/year, target materials) 単位。商品 lot の identity を失う。|
| 別 GitHub repo (e.g., `etzhayyim/surplus-router`) として外出し | religious-corp の Lexicon は本 monorepo 1 箇所が SSoT (CLAUDE.md ADR placement policy)。分散すると drift。 |
| Stripe / 既存マーケットプレイス連携 | substrate boundary 違反 (Stripe 等 fiat processor 禁止)、Charter Rider §2 (営利仲介禁止) 違反。 |
| Solidity contract で on-chain ownership 移転 | 物品の所有権移転は物理イベント。on-chain は USDC tithe coupling と audit event のみで十分。over-engineering 回避。 |
| Lexicon 不要、純粋に robotics 側でやる | 監査性・interoperability・cross-actor 可視性を失う。AT Protocol firehose による religious-corp 経済圏 全体観測ができなくなる。|

# References

- ADR-2605192100 (etzhayyim Mission Charter) — §1.1, §1.4, §1.13, §1.15
- ADR-2605192115 (Non-profit / Donation-only / No-ads) — surplus §55
- ADR-2605192130 (10% Tithe → Public Fund)
- ADR-2605192200 (IP-Free Release Charter Rider v2.0)
- ADR-2605192245 (Global Land Sovereignty / waqf-equivalent inalienability)
- ADR-2605202015 (Robotics First-Industry — Agriculture)
- ADR-2605201600 (kuni-umi S2 community microgrid)
- `00-contracts/lexicons/com/etzhayyim/apps/warehouse/*.json`
- `00-contracts/lexicons/com/etzhayyim/apps/toshiKozan/*.json`
- `00-contracts/lexicons/com/etzhayyim/apps/ftzZones/*.json`
- `00-contracts/lexicons/com/etzhayyim/apps/freeportRegistry/*.json`
- `00-contracts/lexicons/com/etzhayyim/apps/payment/{sent,tithe}.json`
- `60-apps/etzhayyim-project-open-robo/docs/urban-mining-automation-v1.md`
- `60-apps/etzhayyim-project-open-robo/docs/urban-mining-business-model-v1.md`
- UN FAO Food Loss and Waste Database (post-harvest ~14% + consumer ~17%)
- 経産省 アパレル産業廃棄量試算 (年間 約14億点)
- Optoro / Returnly 試算 (米国 EC 返品 約40% 非再販)
