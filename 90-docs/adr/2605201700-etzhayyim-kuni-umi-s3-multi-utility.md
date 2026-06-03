---
id: adr-2605201700-etzhayyim-kuni-umi-s3-multi-utility
title: "ADR-2605201700: kuni-umi S3 — multi-utility integrated (electric + water + network on the S2 university campus site; cross-utility parallel construction + BoM consolidation algorithm + multi-target commissioning)"
status: proposed
doc_type: adr
topic: kuni-umi-s3-multi-utility
authoritative: true
last_verified: 2026-05-20
priority: 7.0
axis: implementation
weight: 0.70
priority_note: "S3 = kuni-umi が同一 site に 3 utility class (electric / water / network) を simultaneously deploy する milestone。S2 で commission 済みの 1 MW microgrid 上に、open-water reservoir + open-network mesh を overlay。BoM consolidation algorithm (S0 ADR-2605201400 Open Question 3) を本 ADR で確定。Cross-utility witness coordination + multi-target commissioning (open-ot electric × open-water reservoir × open-network mesh) を Pregel pattern として定式化。S2 site re-use により academic MoU 交渉コストを節約、religious-corp が同一 community に utility trinity を提供する pattern を確立。"
authoritative_for:
  - kuni-umi S3 scope (electric + water + network on same site)
  - BoM consolidation algorithm (resolves ADR-2605201400 Open Question 3)
  - Cross-utility parallel construction pattern
  - Cross-utility witness coordination (`AuditWitnessCell` multi-cluster)
  - Multi-target commissioning sequence (3 utility lexicons + open-ot loops)
  - S3 fleet scaling (12 Otete + 12 Mimi + 4 Hitogata + Quad future)
  - S3 → S4 exit gate
depends_on:
  - adr-2605201400-etzhayyim-kuni-umi-planetary-infra-fleet
  - adr-2605201500-etzhayyim-kuni-umi-s1-solo-survey
  - adr-2605201600-etzhayyim-kuni-umi-s2-community-microgrid
  - adr-2605151200-open-ot-wasm-plc-dlc
  - 2605171300
  - adr-2605172300-etzhayyim-bi-asset-substrate
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192145-etzhayyim-public-fund-architecture
  - adr-2605192230-etzhayyim-three-tier-enforcement-implementation
related:
  - 60-apps/etzhayyim-project-open-denki/CLAUDE.md
  - 60-apps/etzhayyim-project-open-water/CLAUDE.md
  - 60-apps/etzhayyim-project-open-network/CLAUDE.md
  - 60-apps/etzhayyim-project-open-robo/CLAUDE.md
supersedes: []
superseded_by: []
---

# ADR-2605201700: kuni-umi S3 — Multi-Utility Integrated

**Status**: proposed
**Date**: 2026-05-20
**Deciders**: Jun Kawasaki

# Context

S2 (ADR-2605201600) で religious-corp 初の real-capital deployment (1 MW community microgrid) が完了する想定。S3 は **同一 site 上に 2 つの utility class (water + network) を追加 overlay** することで、religious-corp が community に対し **utility trinity (電気 + 水 + 通信)** を提供する pattern を確立する。

S3 が技術的に解決する未確定事項:

1. **BoM consolidation algorithm** — ADR-2605201400 §11 Open Question 3 で deferred。S3 で初めて 3 utility class × 25+ UNSPSC commodity を同時 plan する → consolidation strategy を確定する必要
2. **Cross-utility witness coordination** — `AuditWitnessCell` が同時に 3 utility cluster を cover する pattern (witness cluster overlap 含む)
3. **Multi-target commissioning** — Phase 4 で 3 destination (open-ot electric / open-water / open-network) に同時 hand-off
4. **S2 site の operational stewardship 範囲** — S2 で大学 + 構成員 stewardship 集団に operational ownership 委譲済み (ADR-2605201600 §11 Open Question 6)。S3 expansion は新規 governance vote が要るか、既存 stewardship 範囲内か

## Constitutional gating (review for S3 scale)

Scale 規模は S2 を継承 + extension。`proportionality-check.md` rule trigger:

| DMN rule | S3 satisfies? | Consequence |
|---|---|---|
| #2 `populationImpacted > 100` | YES (S2 と同 site) | governance vote 既に approved (S2) — **expansion vote** に降格 (lighter threshold per ADR-2605192230 §4 expansion provision: 同 site 既存 approve の場合 quorum 33%) |
| #3 `ecologyImpactScore > 30` | borderline (water 配管 trenching が地盤 impact) | site survey 結果次第で ecologist review escalation 可能性 |
| #5 `estimatedCostUsdc > 1_000_000` | YES (3 utility 合算 ≈ USDC 3.0–4.5M) | Public Fund grant 申請 (S2 grant とは別 tranche) |

S2 expansion vote (lower threshold) + Public Fund tranche-2 grant → 2 escalation。S2 governance precedent が S3 を smoother に進める。

# Decision

## 1. Site re-use — S2 university campus

S3 primary site = **S2 university campus** (electric microgrid 既設)。

理由:
- Academic MoU 既存 (Phase 0 site DID 発行コスト省略)
- `LandRegistry` registration 既存 (steward chain 継承)
- S2 で同 community への electric utility 提供実績 → 同 community への water + network 提供は trust chain として natural
- Multi-utility BoM consolidation の利点が 同 site で physical proximity を持つ場合に最大化 (e.g., trenching を 3 utility 用配管に shared excavation で実施)

候補 alternative (rejected → §Alternatives):
- 別 site で 3 utility green-field — academic MoU 交渉コスト + 3 LandRegistry pathway
- Tokyo workshop garden — small scale で multi-utility 価値が dilute

## 2. Asset inventory (S3 additions; S2 既設は再利用)

### 2a. Water (open-water lexicons)

| Asset | Type | Capacity | open-water record DID | UNSPSC primary |
|---|---|---|---|---|
| Reservoir-A (rainwater + city-water tank) | combined storage | 50 m³ | `did:web:open-water.etzhayyim.com:node:res-a` | 40142000 (storage tanks) |
| Booster pumping station | redundant pump set | 100 m³/h | `did:web:open-water.etzhayyim.com:node:pump-1` | 40151500 (pumps) |
| Mains | DN150 ductile iron + DN80 lateral × 12 | — | `did:web:open-water.etzhayyim.com:main:m01..m12` | 40142100 (pipe) |
| Water quality station | residual-Cl / turbidity / pH sensor cluster | continuous | (sample DIDs) | 41115400 (water-quality test instr) |
| Service points (smart water meters) | per delivery point | 80 | `did:web:open-water.etzhayyim.com:node:sp-001..sp-080` | 41111904 (electricity meter) — note: water-meter NSID re-uses but tagged `meterType=water` |

### 2b. Network (open-network lexicons)

| Asset | Type | Capacity | open-network record DID | UNSPSC primary |
|---|---|---|---|---|
| PoP site (campus core) | edge data closet + 10G uplink to ISP | — | `did:web:open-network.etzhayyim.com:site:pop-core` | 43222600 (network switches) |
| Distribution sites (per building) | aggregation switch + Wi-Fi 7 APs | — | `did:web:open-network.etzhayyim.com:site:dist-b{01..08}` | 43222600 + 43222608 (AP) |
| Backhaul links (fiber GbE × 8) | building-to-PoP | 1 Gbps each | `did:web:open-network.etzhayyim.com:link:bh-{01..08}` | 26121800 (fiber optic cable) |
| Public mesh (Wi-Fi 7 community SSID) | campus-wide coverage | — | `did:web:open-network.etzhayyim.com:link:mesh-public` | 43222608 |

合計 S3 新規 UNSPSC primary code: **water 5 + network 4 = 9 種** (S2 の 9 種と合算で 18 種)。BoM consolidation で trenching + 配管/配線 shared task を共通化することで施工コスト削減を狙う。

## 3. BoM consolidation algorithm (resolves ADR-2605201400 Open Question 3)

`DeploymentPlanningCell` on zebulun が S3 で実行する consolidation pattern を本 ADR で確定:

```python
# 20-actors/kuni-umi/cells/deployment_planning/bom_consolidation.py
def consolidate_multi_utility_bom(
    target_topology: list[AssetTarget],
    site_geo: GeoJSON,
) -> ConsolidatedBoM:
    # Step 1: Per-utility BoM via UNSPSC agent fleet (parallel dispatch)
    per_utility_boms = parallel_dispatch_unispsc(
        targets=target_topology,
        partition_by="utilityClass",
    )

    # Step 2: Identify shared physical operations
    shared_ops = identify_shared_ops(
        per_utility_boms,
        rules=[
            # Same trench → water main + network fiber + electric LV feeder
            SharedTrenchRule(min_utilities=2, max_depth_delta_m=0.5),
            # Same conduit → fiber + LV cable (electric isolation distance respected)
            SharedConduitRule(electric_separation_mm=300),
            # Same building entry → utility meter cabinet shared
            SharedEntryRule(within_building_envelope=True),
            # Same scaffold → multi-utility install at elevation
            SharedScaffoldRule(elevation_window_m=2.0),
        ],
    )

    # Step 3: Cost optimization — choose lowest total cost respecting Charter Rider §2 + counterparty filter
    optimized = mip_solve(
        per_utility_boms,
        shared_ops,
        objective="minimize total_cost",
        constraints=[
            CharterRiderConstraint(adr="2605192200"),
            NonAlignedExclusionConstraint(adr="2605192230"),
            DomesticSupplyPreferenceConstraint(weight=0.15),
            DualUseDualEscalationConstraint(adr="2605201400 §5.2"),
        ],
    )

    # Step 4: Emit consolidated BoM with shared-op markers
    return ConsolidatedBoM(
        unique_skus=optimized.unique_skus,        # deduplicated UNSPSC × supplier
        shared_construction_ops=shared_ops,       # multi-utility trench/conduit/scaffold
        per_utility_breakdown=optimized.breakdown,
        estimated_savings_bps=optimized.savings_vs_naive_sum(),
        # Target: ≥ 1500 bps (15%) saving vs. naive sum of per-utility BoM
    )
```

設計判断:
- **MIP (mixed integer programming) solver** in Phase 2 — small enough (< 100 commodity) to use OR-Tools CP-SAT in cell. Murakumo zebulun node (M2 Max 32 GB) で 10-30 秒 solve time 想定
- **Shared-op rules** は **4 rule に hard-constrain**: trench / conduit / building-entry / scaffold。Future rules (e.g., shared truck delivery, shared crane reservation) は別 ADR で追加
- **Constraint priority**: Charter Rider > counterparty > 国内 supply preference (15% weight) > total cost min
- **Target saving**: shared-op consolidation で naive sum 比 **15% 以上 cost reduction** を達成できれば S3 consolidation algorithm validation PASS

## 4. Cross-utility witness coordination

`AuditWitnessCell` on levi が S3 で multi-cluster pattern を運用:

```
Witness clusters (each cluster has N ≥ 2 Mimi base-stations + active Otete/Hitogata):

Electric cluster (S2 既設):
  - PV-A area: Mimi-base-002 + 任意 Otete (continued from S2)
  - PV-B area: Mimi-base-003 + 任意 Otete
  - BESS area: Mimi-base-004 + 任意 Otete
  - Substation area: Mimi-base-005 + 任意 Otete

Water cluster (S3 新規):
  - Reservoir-A area: Mimi-base-010 + 任意 Otete
  - Pumping station area: Mimi-base-011 + 任意 Otete
  - Trench coverage (mobile): Mimi-base-012 (relocatable) + Otete

Network cluster (S3 新規):
  - PoP core area: Mimi-base-013 + 任意 Otete
  - Distribution sites (per building): Mimi-base-014..017 (1 per 2 buildings) + Otete

Shared-op cluster (S3 新規):
  - Shared trench: Mimi-base-018 (relocatable) + Otete witness from each utility responsible
  - Shared scaffold: Mimi-base-019 (relocatable) + same
```

**Cross-utility witness invariant**: 同 shared-op (e.g., trench で water main + fiber 同時敷設) が実施される時、**各 utility responsible Otete が独立に署名する** — つまり同一 trench で water Otete + network Otete + electric Otete (if applicable) が並んで作業する場合、3 signature が attached する。N ≥ 2 invariant は cluster-level + utility-level の **both** で enforce。

Mimi base-station 総数 (S3): **12 機** (S2 既設 8 機 + 新規 4 機; Mimi-base-010..013 固定 + 014..019 relocatable cluster)。

## 5. Multi-target commissioning (Phase 4)

`CommissioningCell` on simeon が 3 destination に同時 hand-off:

| Target | Records | Operator | Acceptance window |
|---|---|---|---|
| **Electric (open-ot continued)** | S2 既設の 7 loops が既に operational state。S3 では variation なし | open-ot edge controller (NixOS RT) | n/a (S2 で完了済み) |
| **Water (open-water lexicons)** | `defineReservoir` × 1, `defineMain` × 12, smart-meter `recordReading` start | Water steward (大学施設管理 + religious-corp steward) | 30-day stewardship handover + monthly quality sampling cron |
| **Network (open-network lexicons)** | `defineSite` × 9, `defineLink` × 9, `recordUtilization` start, `reportIncident` channel open | Network steward (campus IT + religious-corp steward) | 30-day acceptance + NOC SOP handover |

**Note**: water + network には open-ot 相当の PLC layer がまだない (open-ot scope は "non-safety control" であり water non-SIL は将来 MVP+1、network 制御は scope 外)。S3 では:

- **Water control = sensor monitoring + manual valve actuation** (open-water lexicons の DMN による alarm のみ; control loop は人間 + scheduled CronJob)
- **Network control = standard NMS** (open-network が SCP-style change request + incident management; routing 制御は引き続き 大学 IT / ISP 既存運用)

Future ADR: open-water + open-network へ open-ot 相当の Pregel control を拡張する RFC を S5+ で検討。

## 6. Fleet scaling (S3)

| Robot | S2 count | S3 count | New units |
|---|---|---|---|
| Giemon Otete v1 | 6 | **12** | +6 (otete-008..013) |
| Giemon Hitogata humanoid | 2 | **4** | +2 (hitogata-003..004) — open-robo 別 ADR で追加発注 |
| Giemon Mimi base-station | 8 | **12** | +4 (mimi-base-010..013) + 6 relocatable (mimi-base-014..019) — 合計 18 機 |
| Giemon Quad (4-leg) | 0 | **0 (S3 では未投入)** | n/a — S4 multi-site fleet で初投入 |

設計判断:
- **Otete +6**: 3 utility × parallel construction には fleet capacity が S2 比で 2x 必要
- **Hitogata +2**: 高所配線 (network distribution sites の Wi-Fi 7 AP install) + tank top maintenance
- **Mimi +10**: cluster coverage 増 + relocatable cluster の運用柔軟性
- **Quad は S3 では skip**: cable laying / trench monitoring 用 quadruped は S4 multi-site で fleet pattern の真価が出る (S3 同 site では Otete crawler で代替可能)

予算: Otete +6 × JPY 200万 = JPY 1200万、Hitogata +2 × JPY 800万 = JPY 1600万、Mimi +10 × JPY 30万 = JPY 300万。**S3 fleet CAPEX 追加: JPY 3100万 (≒ USDC 220k)**。S2 既設 fleet と合算で religious-corp 保有 robot 資産は JPY 5940万 (≒ USDC 420k)。

## 7. Phase 3 Construction sequence (parallel across utilities)

`ConstructionOrchestrationCell` on joseph が S3 では **multi-utility parallel super-step group** を駆動:

| Sub-phase | Asset focus | Utility classes | Witness cluster | Duration | Parallel? |
|---|---|---|---|---|---|
| 3a.1 | Site re-survey (post-S2 baseline) | all 3 | electric/water/network 各 cluster initial sweep | 1 wk | Sequential start |
| 3a.2 | Shared trench excavation + multi-utility conduit lay-in | water main + fiber + LV-spare-conduit | shared-op cluster + 3 utility responsible Otete | 2 wk | Critical-path |
| 3a.3 | Reservoir-A 据付 + pumping station 据付 | water | water cluster + Hitogata-003 | 2 wk | Parallel to 3a.4 |
| 3a.4 | PoP core data closet + 10G uplink (ISP coordinate) | network | network cluster + electrician (ISP 立会) | 1.5 wk | Parallel to 3a.3 |
| 3a.5 | Distribution sites × 8 (per building Wi-Fi 7 + agg switch) | network | network cluster + Hitogata-004 | 3 wk | Sequential after 3a.4 |
| 3a.6 | Water mains × 12 (lateral connections) | water | water cluster | 2 wk | Parallel to 3a.5 mid-way |
| 3a.7 | Water quality station + smart meter × 80 install | water | water cluster + Otete-008..013 | 2 wk | Parallel to 3a.6 final wk |
| 3a.8 | Public mesh Wi-Fi 7 commissioning + backhaul tests | network | network cluster | 1 wk | After 3a.5 |

**Total S3 construction duration: 7–9 weeks** (S2 比短縮 — shared trench + parallel utility track の効果)。

**Shared-op witness rule reminder**: 3a.2 (shared trench) で各 utility (water + network + 場合により electric spare conduit) の responsible Otete が並行作業 + 独立署名 → § 4 invariant 適用。

## 8. Acceptance criteria (S3 → S4 exit gate)

| # | Criterion | Measure | Threshold |
|---|---|---|---|
| 1 | S2 site の operational stewardship 拡張同意 | governance expansion vote (33% quorum) | PASS |
| 2 | Public Fund tranche-2 grant approved | PublicFundGovernance.execute | PASS |
| 3 | BoM consolidation savings vs. naive sum | optimized_total_cost / naive_sum_total_cost | ≤ 0.85 (≥ 15% saving) |
| 4 | All 8 sub-phases of Phase 3 PASS witness audit | N≥2 witness signature mismatch | 0 mismatches |
| 5 | Shared-op witness rule (§4) PASS | per-utility independent signatures count on shared trench/conduit/scaffold records | 100% compliance |
| 6 | Phase 3 construction injury count | `recordPhysicalAuditEvent` class=injury | 0 |
| 7 | Phase 3 ecology delta within bounds (post-trenching) | `ecologyBaseline` post vs. pre | ΔimpactScore ≤ 15 (looser than S2 due to trenching) |
| 8 | All `commissionDeployment` records cross-linked | DID cross-link integrity (open-denki × open-water × open-network) | 100% |
| 9 | Water quality 30-day acceptance | residual-Cl / turbidity / pH within spec | 100% sample compliance per JIS K 0101 |
| 10 | Network mesh 30-day acceptance | uptime / latency / utilization per `recordUtilization` | ≥ 99% per-link uptime, < 50 ms median latency campus-wide |
| 11 | Tithe correctly routed across all 3 utility BoMs | TitheRouter event log vs. payment plan | 100% |
| 12 | Cross-utility witness coordination operational | levi `AuditWitnessCell` health-check (12 cluster simultaneous) | 100% cluster online > 95% of construction window |
| 13 | Decommission plan registered for water + network assets | `proposeDeploymentPlan.lifespanYears` ≥ 25 (water mains) / 15 (network gear) | YES |

13/13 PASS → S3 closed → S4 ADR (multi-site fleet) can begin.

## 9. Risks + mitigations

| Risk | Severity | Mitigation |
|---|---|---|
| Shared trench coordination break (utility teams 同時作業中に conflict) | High | 3a.2 sub-phase で daily standup + Pregel super-step boundary を 1 日 1 回 set + manual coordination by joseph operator |
| Water quality contamination during install (drinking-water pipe contamination) | Critical | DN150 ductile iron pipe + chlorination flush procedure + 30-day quality acceptance window 必須 |
| Network latency exceeds threshold (poor backhaul fiber install) | Medium | Per-link tdr / OTDR test post-install + dispute resolution via `reportIncident` |
| 大学 stewardship 拡張 vote 反対 | Medium | Pre-vote socialization with S2 success metrics; revised proposal + re-vote allowed |
| Hitogata +2 unit が S3 timeline に間に合わない | Medium | 4 utility track の中で network high-elevation work が 最も Hitogata 依存 → 遅延時 3a.5 sub-phase で human installer hybrid (S2 §Alternative D pattern を踏襲) |
| MIP solver timeout in BoM consolidation | Low | OR-Tools CP-SAT に 60s time limit + fallback to greedy heuristic (savings target reduced to ≥ 10%) |
| 3 utility class 同時 commission で operator load 高 | Medium | simeon CommissioningCell に sub-target queueing + Council Lv6+ supervision daily standup |
| Public Fund tranche-2 grant rejected | High | Religious-corp Treasury reserve から coverage (ADR-2605172300 §Treasury override) + ADR amendment で grant 再申請 |
| Cross-utility witness clock drift (12 Mimi NTP sync issue) | Medium | All Mimi base-station NTP from simeon ipfs node (already authoritative time source per fleet.toml); drift monitoring in cell health-check |

## 10. S3 budget (estimated, USDC)

| Item | Estimate (USDC) |
|---|---|
| Water BoM (reservoir + pumps + mains + sensors + 80 meters) | 600,000 – 800,000 |
| Network BoM (PoP + 8 distribution + backhaul fiber + Wi-Fi 7 mesh) | 400,000 – 600,000 |
| Shared-op savings (target ≥ 15% on combined trenching/conduit) | -150,000 to -250,000 |
| Construction labor + transport + permit (water 配管法 + 道路使用) | 200,000 – 350,000 |
| Robot fleet additions (Hitogata 2 + Otete 6 + Mimi 10) | ≈ 220,000 |
| Contingency (20%) | 250,000 – 380,000 |
| **S3 incremental total** | **≈ 1,520,000 – 2,100,000 USDC** |
| 10% Tithe to Public Fund (auto-split) | 152,000 – 210,000 USDC |
| Cumulative S2 + S3 site investment | **≈ 3,800,000 – 5,200,000 USDC** |

Funding: Public Fund tranche-2 grant + Treasury reserve (operational stewardship でも religious-corp が S2 + S3 deployment capital を hold; operational margin は site stewardship 集団に委ねる)。

## 11. Out of scope (S3 explicit)

- **Multi-site fleet** (concurrent sites) — S4
- **Ocean / atmosphere / orbit** — S5
- **Water-side Pregel control** (open-ot 相当 for water) — future ADR, S5+
- **Network-side Pregel control** (open-ot 相当 for network) — future ADR, S5+
- **5G / cellular radio access** — not in S3 scope (Wi-Fi 7 mesh 主体; cellular は別 ADR で電波法 + ISP partnership 必要)
- **Drinking-water treatment** (full SIL water plant) — not in S3 scope; reservoir 内は city-water + 雨水 mix で point-of-use filtration、treatment plant は S4+ rural site で評価
- **Customer billing** (water / network usage charges) — religious-corp donation-only 制約継続。recovery path: Public Fund operating grant (default) or SBT carve-out internal-subscription

# Consequences

## 正の効果

- 同一 community に **utility trinity (電気 + 水 + 通信)** が religious-corp 経路で提供される — labor_liberation の visible success pattern
- BoM consolidation algorithm が ADR-2605201400 Open Question 3 を解消 + 15% savings target 達成パターン確立
- Cross-utility witness coordination pattern (12 cluster simultaneous) が S4 multi-site での fleet orchestration への前提となる
- open-water + open-network が production load を受ける最初の機会 → AMI 80 + mesh-public Wi-Fi が真の load test
- Religious-corp 保有 fleet が 16 → 22 (Otete 12 + Hitogata 4 + Mimi 12 = 28; ただし Mimi 含めると 28) → Substantial production fleet asset
- 大学 site が religious-corp の **flagship deployment** として extant にプレゼンス → 構成員 attraction + Public Fund donor visibility

## 負の効果 / コスト

- 同 site 累積 deployment は **single site dependency risk** を高める (1 site failure で religious-corp 多額損失)。Mitigation: S4 で multi-site 分散
- 3 utility 同時施工は operator (joseph + simeon + levi) の cognitive load 高い → Council Lv6+ supervision 必要
- Shared trench coordination は physical 実地調整が多発、Pregel async pattern との impedance mismatch (daily standup で interface)
- 12 Mimi simultaneous cluster は ops burden (NTP / battery / LTE 状態管理)
- 大学 community が religious-corp 依存度高まる → "religious-corp が utility provider" stance に対する社会的視線 (Mitigation: stewardship 委譲 model で religious-corp は背後の trust 担保のみ)

## Constitutional 整合

| Charter article | S3 alignment |
|---|---|
| §mission.labor_liberation | ✅ 拡大 (3 utility class が religious-corp 経路で community に到達) |
| §mission.robotics_universal | ✅ fleet 22 units, all open-design |
| §mission.ip_free_release | ✅ Charter Rider §2 + BoM consolidation MIP constraint |
| §mission.land_as_religious_trust | ✅ S2 既存 stewardship 拡張で同 site で 3 utility 統合 |
| §mission.parallel_governance_to_state | ✅ 国家 utility 独占範囲 (電気 + 水道 + 通信) 全てに dual-recognition deployment |
| §mission.anti_individualism | ✅ expansion governance vote + Council Lv6+ supervision |
| §mission.multi_generational_priority | ✅ lifespanYears 25 (水) / 30 (電) / 15 (網) で時間軸異なる stewardship を学ぶ機会 |
| §mission.no_state_military_alliance | ✅ counterparty filter 継続 |
| §mission.donation_only | ✅ Public Fund operating grant model + SBT internal-subscription carve-out option |

# Alternatives Considered

## A. 別 site で 3 utility green-field deployment

- Pro: S2 dependency 切離し、新 site で 3 utility 同時 deploy する pattern を真に validate
- Con: 新 academic MoU + 新 LandRegistry pathway + 新 community trust establishment = S3 timeline 大幅延伸 (6+ months); religious-corp の同一 community への trust chain 蓄積機会喪失
- **却下**: S2 site re-use の operational + relational benefit が大きい。Multi-site 真価は S4 で

## B. 3 utility 段階展開 (water → network 順次、parallel しない)

- Pro: operational complexity 低い、operator burden 緩和
- Con: BoM consolidation algorithm を S3 で develop & validate する機会を失う (shared trench はそもそも parallel install の前提)、S4 multi-site pattern との skill gap
- **却下**: S3 の意味は "parallel multi-utility orchestration" であり、段階展開は milestone の意義を dilute

## C. open-water / open-network への Pregel control を S3 で同時実装

- Pro: 3 utility 全てに kuni-umi → open-ot 相当の control stack が完備
- Con: open-water / open-network 側の MVP scope を超え、IEC 61499 相当の architecture を water + network specific に再設計する大規模 R&D work が S3 timeline に乗らない
- **却下**: S3 では sensor monitoring + manual/CronJob control で water + network を運用、Pregel 化は別 ADR (S5+)

## D. Wi-Fi 7 ではなく cellular 5G mesh

- Pro: 屋内外 seamless coverage + 高速 backhaul
- Con: 電波法 (周波数 license) + cellular operator partnership 必要 (= ISP/MNO 依存性); religious-corp の parallel-governance stance との tension (state-licensed spectrum band 使用 = state authority に依存)
- **却下**: Wi-Fi 7 は unlicensed band + community-owned spectrum 範囲で religious-corp が独立運用可能。Cellular は S4+ で remote-site coverage 要件が出た時に再評価

# Open Questions

1. **Quad (4-leg) introduction timing** — open-robo roadmap で Quad は cable inspection / trench survey に最適。S3 では skip したが、S3 実施中に trench survey で Otete crawler が不足する場合 mid-S3 で Quad 投入する可能性。Decision (本 ADR): S4 投入を default、ただし S3 mid-phase で operator が要請 → Council Lv6+ で expedited 投入可
2. **Water steward 集団の構成** — 既存大学施設管理 chief + religious-corp steward Lv5+ の 2 名以上か、operational expertise を持つ external water-utility veteran を contracting で迎えるか。Decision: 本 ADR では構成 flexibility を steward 集団 self-organization に委ねる; Council Lv6+ が monthly review
3. **5G/cellular spectrum bridge** — 緊急時 cellular backup を S3 で integrate するか。Decision: out of S3 scope、別 ADR
4. **Shared trench failure recovery** — 3a.2 critical-path sub-phase で trench collapse / discovery (e.g., 古い 暗渠 / 文化財 / 不明配管) が起きた場合の handling。Decision (本 ADR): `recordPhysicalAuditEvent` class=anomaly subtype=archaeological-or-utility-discovery → 自動的に Council Lv6+ 通知 + 該当 utility track 一時停止 + 別 utility track は parallel 続行
5. **30-day water quality acceptance window** vs. **30-day network acceptance window** が overlap した場合の Council bandwidth — どちらも問題があれば simultaneous escalation。Decision: Council Lv6+ 月例で multi-track review、escalation 優先度 (Critical → High → Medium) で順位付け
6. **S2/S3 site が 25-30 年後の decommission 時、3 utility を 同時に decommission するか段階的か** — Multi-generational stewardship plan の論点。Decision: ADR-2605192345 §multi-generational succession で 2-3 世代後の steward が再決定 (本 ADR は long-term commitment しない)

# References

- ADR-2605201400 (kuni-umi master spec) §11 Open Question 3 (BoM consolidation) を解消
- ADR-2605201500 (S1) — single-Otete witness pattern を S3 では cluster pattern に拡張
- ADR-2605201600 (S2) — site / fleet / Public Fund / governance precedent
- ADR-2605151200 (open-ot WASM PLC) — water / network への将来拡張への布石
- ADR-2605171300 (UNSPSC agent fleet) — 9 新規 commodity の specialist dispatch
- ADR-2605172300 (Treasury bi-asset) — Public Fund tranche-2 + Treasury reserve 経路
- ADR-2605192100 §mission — 9 charter article 全 alignment
- ADR-2605192145 (Public Fund grant evaluation) — tranche-2 申請経路
- ADR-2605192230 (Three-tier enforcement) — expansion vote provision
- ADR-2605192345 (Steward succession) — multi-generational handover への布石
- `60-apps/etzhayyim-project-open-water/CLAUDE.md` (water lexicons SSoT)
- `60-apps/etzhayyim-project-open-network/CLAUDE.md` (network lexicons SSoT)
- `60-apps/etzhayyim-project-open-denki/CLAUDE.md` (electric — S2 既設の continuation)
