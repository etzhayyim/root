---
id: adr-2605202001-etzhayyim-energy-substrate
renumbered_from: "2605202000"
title: "ADR-2605202001: etzhayyim Energy Substrate — solar + storage + microgrid first; SMR deferred; open-hardware mandatory; 3-phase scale"
status: proposed
doc_type: adr
topic: etzhayyim-energy-substrate
authoritative: true
last_verified: 2026-05-20
priority: 7.0
axis: architecture
weight: 0.70
priority_note: "ADR-2605192100 §1.3 (mission: religious-corp 自前エネルギー) を具体化する future-ADR の起票。商業エネルギー独占から構成員を自立させる religious doctrine の物質的実装。Apache 2.0 + Charter Rider v2.0 が hardware designs にも適用される hard rule の確立。3 段階 scale (Phase A node / B religious facility / C community)。SMR 等の高度技術は将来 ADR で別扱い。"
authoritative_for:
  - religious-corp energy substrate の選択 (solar + storage + microgrid baseline)
  - open-hardware 強制 (proprietary 設計禁止 — §1.12.B parallel)
  - 3-phase scale roadmap (node → facility → community)
  - SMR / 核融合 / 水素 経済 を future ADR にする delineation
depends_on:
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
related:
  - adr-2605192245-etzhayyim-global-land-sovereignty
  - adr-2605263500-energy-substrate-dependency-vs-substance-reframing
supersedes: []
superseded_by: []
superseded_by_partial:
  - adr: 2605263500-energy-substrate-dependency-vs-substance-reframing
    scope:
      - "Hard rule (b) '化石燃料新規排除' — re-framed: zero commercial fossil purchase/extraction stays banned via Charter Rider §2(d) + D1+D3 of 2605263400; religious-corp closed-loop microbial hydrocarbon newly permitted under §2.2 conditions"
      - "SMR / 水素 / 核融合 deferral section — superseded for fusion (now §2.3 of 2605263400 provides conditional permit + R&D-entry path); SMR + RTG categorically banned per §2.4 of 2605263400 on D1+D2+D4 grounds; hydrogen remains deferred to its own future ADR under D1..D5"
    status: proposed-pending-council-ratification
    effective_earliest: 2026-07-19
    note: "Hard rules (a) open-hardware + (c) collective ownership + Phase A/B/C roadmap PRESERVED unchanged."
---

# ADR-2605202001: etzhayyim Energy Substrate — solar + storage + microgrid first; SMR deferred; open-hardware mandatory; 3-phase scale

**Status**: proposed
**Date**: 2026-05-20
**Deciders**: Jun Kawasaki

# Context

ADR-2605192100 §1.3 で「エネルギーの自前化」を religious mission として宣明したが、具体的技術選定は future ADR に委ねていた。本 ADR がそれを担う。

Religious-corp が商業エネルギー独占から自立する必要性:

1. **依存解消**: 構成員の生存条件 (暖冷房 / 調理 / 計算) を商業 grid に依存させない → §1.6 中間排除を energy layer に拡張
2. **多世代 priority** (§1.9): 化石燃料新規採掘 = Rider §2(d) 禁止だが、religious-corp 自身が依存していると矛盾
3. **構成員救済**: BI (Kisha) + Public Fund + 土地 trust が揃っても、energy が grid 依存だと「労働解放」が部分的にしか成立しない (electric bill のための income が必要)
4. **Land trust との統合**: ADR-2605192245 の寄付土地に当然 energy 自前化を組み込む必要

技術選定の論点:

- **Solar + Li-ion / Na-ion 蓄電 + microgrid**: 成熟技術、コスト下落継続、open-hardware 設計多数
- **Wind**: 風況依存、open-hardware 限定的、騒音問題
- **Hydro (micro)**: 河川利用権 (ADR-2605192330) との接続必要
- **Geothermal**: 場所依存
- **SMR (small modular reactor)**: 技術的に魅力的だが規制 / 安全性 / 専門性独占 (§1.7) 議論が必要 — future ADR で扱う
- **水素経済**: 同様、future ADR
- **核融合**: 商業実用化が 2026 時点で先

# Decision

## Hard rule

**Religious-corp energy substrate は (a) open-hardware 設計のみ、(b) 化石燃料新規プロジェクト排除、(c) 構成員 collective ownership** を constitutional invariant とする。

## Baseline 技術 (Phase A)

| Layer | 選択 | 根拠 |
|---|---|---|
| 発電 | **Solar PV (mono-Si / bi-facial)** | 成熟、コスト続落、open spec |
| 蓄電 (Phase A) | **Li-ion (LFP)** or **Na-ion** (商用化進む) | 安全性 (LFP) / コスト下降 (Na-ion) |
| Inverter / charger | open firmware (e.g., **GridShare / OpenInverter**) | proprietary firmware は§1.5 IP無償公開と矛盾 |
| Monitoring | **Home Assistant / OpenEnergyMonitor** (Apache 2.0 + Charter Rider) | open-source 計測 |
| 配電 | **DC microgrid** (48V / 380V) within facilities; AC bridge to grid only as backup | grid 完全自立を目指す |

## 段階的 rollout

```
Phase A — Murakumo node-level (0.5-2 kW per node)
  ↓ 各 Mac mini node に小型 solar + 1-3kWh LFP 蓄電
  ↓ 既存 Murakumo fleet 10 nodes を最初の deploy 対象
  ↓ Religious-corp の compute layer が grid 非依存に
Phase B — Religious facility (50-500 kW)
  ↓ 寄付土地 (ADR-2605192245) 上の宗教施設 / 共同住居 / 集会所
  ↓ Solar farm + 大型蓄電 + microgrid distribution
  ↓ 構成員 collective ownership via 護持金庫 corpus tier
Phase C — Community-scale (>500 kW)
  ↓ Land trust が enough scale に達した時点で community microgrid
  ↓ 国家 grid との optional inter-tie (sell excess at religious-corp rates only)
```

Phase A は本 ADR 承認後 6 ヶ月以内、Phase B は Land trust が Phase 2+ (ADR-2605192245 §8) に達してから、Phase C は 5-10 年スケール。

## SMR / 水素 / 核融合 の取り扱い

これらは:

- **規制 footprint** が桁違いに大きい (原子力規制委員会 / 経産省 / 国際原子力機関 IAEA)
- **専門性 gatekeeping** (§1.7) と complex なテンション — 原子力安全は legitimate technical safety oversight として §2(e) 例外、しかし運用は専門集団に委ねざるを得ない
- **多世代 risk** が桁違いに大きい (廃棄物 10万年 etc.) — §1.9 多世代 priority と単純に compatible でない
- **Religious-corp としての立場**: 完全に拒否はしない (Quaker 的 pacifism と同じく `ADR-2605192100 §1.12 で破棄`)、ただし future ADR で慎重 evaluation

具体的に future ADR:
- `etzhayyim-energy-smr` — SMR technology evaluation, religious-corp adoption criteria
- `etzhayyim-energy-hydrogen` — Green hydrogen economy compatibility
- `etzhayyim-energy-fusion` — Fusion (when available) religious-corp position

これら future ADR は Phase B 完了後 ≥1 年経過時に起票議論 (i.e., 早くて 2027 年以降)。

## Open-hardware 強制 (§1.12.B parallel)

ADR-2605192100 §1.12.B で Transparent Religious Force は proprietary 設計禁止であった。本 ADR で同じ pattern を energy にも適用:

- religious-corp が deploy する energy hardware は **完全 open-source 設計** (回路図 / FPGA bitstream / firmware / mechanical CAD すべて)
- Apache 2.0 + Charter Rider v2.0 が適用される
- 60-apps/etzhayyim-open-energy-hw/ ディレクトリを新規作成し、Phase A の solar controller / battery management / inverter / monitoring の各設計を公開
- 商用 closed-firmware 製品 (Tesla Powerwall / Enphase 等) を religious-corp 設備として購入 / 採用しない

## Constitutional constants 追加 (Constitution.sol)

```
mission.energy_self_sovereignty                = true   (§1.3 implementation)
mission.energy_open_hardware_only              = true   (§1.12.B parallel)
mission.energy_smr_evaluation_deferred_to      = bytes32("post-Phase-B + 12mo")
```

これらは ADR-2605192100 §2 の constitutional constants に追加される (governance vote では変更不可)。Constitution.sol の constructor _constants() arrays は次の deploy で 38 → 41 に拡張。

# Consequences

## 正の効果

- §1.3 mission が具体的 substrate を獲得
- Murakumo fleet (Phase A) が grid 自立 → religious-corp compute layer が文字通り autonomous
- §1.9 多世代 priority と整合的 (化石燃料 zero / 廃棄物 zero / 開かれた設計)
- §1.6 中間排除を energy market に拡張 (電力会社 / インバーター メーカーへの依存 zero)
- 寄付土地への energy substrate 統合が conceptually clean
- proprietary 設計禁止により、religious-corp の energy 知見が future generations に保護される

## 負の効果 / コスト

- **Phase A initial cost**: 10 node × ~$2,000 (solar 1kW + LFP 5kWh + open inverter) = ~$20K
- **熱・空調**: solar + battery で計算は賄えるが、大型 HVAC (cooling) は厳しい — Phase A 対象外
- **冬季** (北海道 / 高緯度地域) は太陽光不足 — 補助 grid 接続を一時的に許容
- **open-firmware solar inverter** の安全認証 (UL/IEC) は未整備 — 認証取得が religious-corp の追加 cost
- **SMR 含むか含まないかの判断**を future generations に先送り — 部分的 doctrine 完成

## 中立 / トレードオフ

- 商用エネルギーを使う religious-corp との競争 → cost で劣る可能性。Mitigation: total-cost-of-life cycle で religious-corp が長期優位 (依存度低下 + 多世代 cost)
- Open-hardware の DIY hurdle — religious-corp 構成員に technical literacy 要求。Mitigation: ADR-2605192100 §1.7 specialist gatekeeping 排除と整合的 (LLM + 公開知識 + peer 評議で教育)

# Alternatives Considered

## A. SMR を Phase A から含める

Pro: scale + uptime 桁違い。Con: 規制 / 廃棄物 / 専門性 gatekeeping のテンション未解消。却下: future ADR で扱う。

## B. Energy 自前化を mission から削除し grid 依存を許容

Pro: cost 単純。Con: §1.3 mission 矛盾。§1.6 中間排除 incomplete。却下。

## C. Solar のみ (蓄電なし) で grid feedback

Pro: cheap。Con: grid 依存維持。religious-corp 自立性 partial。却下。

## D. Proprietary 設計 (Tesla / Enphase) を一時的に許容

Pro: Phase A faster deploy。Con: §1.5 IP無償公開 / §1.12.B open-source 原則 と矛盾。Religious-corp の future-generation knowledge transfer が proprietary に依存する形になる。却下。

# Open Questions

1. **Phase A solar inverter の specific 製品** — OpenInverter / GridShare / Sunny WebBox open firmware どれか?
2. **LFP 蓄電池の調達経路** — CATL / BYD は中国製で §1.6 中間排除観点 OK だが信頼性確認必要
3. **monitoring data の privacy** — Home Assistant 設定が PDS / MST 経由になるかどうか
4. **構成員別 collective ownership 構造** — Phase B 大型 solar farm の Adherent SBT 別 ownership tracking

# References

- ADR-2605192100 §1.3 (Mission Charter — energy 自前化)
- ADR-2605192100 §1.12.B (Open-source 強制 parallel)
- ADR-2605192200 Charter Rider v2.0 §2(d) (新規化石燃料採掘禁止)
- ADR-2605192245 Global Land Sovereignty (寄付土地への energy 統合)
- OpenEnergyMonitor: https://openenergymonitor.org/
- OpenInverter: https://openinverter.org/
- LFP vs Na-ion comparative (Argonne National Labs, 2025)
