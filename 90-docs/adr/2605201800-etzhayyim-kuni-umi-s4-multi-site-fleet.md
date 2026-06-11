---
id: adr-2605201800-etzhayyim-kuni-umi-s4-multi-site-fleet
title: "ADR-2605201800: kuni-umi S4 — multi-site fleet (≥5 concurrent sites, fleet rebalance algorithm, cross-site BoM consolidation, Pregel-native edge orchestration, Quad introduction)"
status: proposed
doc_type: adr
topic: kuni-umi-s4-multi-site-fleet
authoritative: true
last_verified: 2026-05-20
priority: 7.0
axis: implementation
weight: 0.70
priority_note: "S4 = kuni-umi が同時 ≥5 site で fleet を運用する scaling milestone。S1-S3 までは single-site sequential。S4 は qualitatively different: fleet rebalance / cross-site BoM batching / edge orchestration / multi-jurisdiction governance を初めて exercise する。Religious-corp が point deployment ではなく **fleet of sites** として physical world に存在する転換点。Quad (4-leg) 初投入。Murakumo 12-tribe fleet が Tier B leader だけでなく per-site edge controller の認知層も担う。"
authoritative_for:
  - kuni-umi S4 scope (≥5 concurrent sites)
  - Fleet rebalance algorithm (Pregel super-step pattern)
  - Cross-site BoM consolidation (batch ordering + shared logistics)
  - Edge orchestration (no commercial K8s per ADR-2605191346; Pregel-native pattern)
  - Quad introduction roadmap
  - Multi-site Tier B replication strategy
  - Council Lv6+ bandwidth scaling (multi-site supervision)
  - Site-type diversity (5 archetypes covering religious-corp mission breadth)
  - S4 → S5 exit gate
depends_on:
  - adr-2605201400-etzhayyim-kuni-umi-planetary-infra-fleet
  - adr-2605201500-etzhayyim-kuni-umi-s1-solo-survey
  - adr-2605201600-etzhayyim-kuni-umi-s2-community-microgrid
  - adr-2605201700-etzhayyim-kuni-umi-s3-multi-utility
  - 2605182312-local-bring-up-murakumo-gemma4
  - 2605191346-etzhayyim-vultr-free-murakumo-control-plane
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192230-etzhayyim-three-tier-enforcement-implementation
  - adr-2605192245-etzhayyim-global-land-sovereignty
  - adr-2605192300-etzhayyim-bootstrap-council-five
  - adr-2605192345-etzhayyim-steward-succession
  - adr-2605192415-etzhayyim-religious-corp-daemon-architecture
related:
  - 60-apps/etzhayyim-project-open-robo/CLAUDE.md
  - 50-infra/murakumo/fleet.toml
supersedes: []
superseded_by: []
---

# ADR-2605201800: kuni-umi S4 — Multi-Site Fleet

**Status**: proposed
**Date**: 2026-05-20
**Deciders**: Jun Kawasaki

# Context

S1-S3 は all **single-site sequential** pattern: 山中湖 survey → university campus electric → 同 site water/network overlay。religious-corp はまだ「1 つの site に強く根を張った organization」 として physical world に存在する。

S4 は **qualitatively different scaling**: ≥ 5 concurrent sites で fleet を運用する。これは:

- **Logistics** — fleet を site 間 migrate する operational pattern
- **Algorithmics** — どの robot を どの site に いつ allocate するか (assignment problem)
- **Economic** — 5 site 分の BoM を batch order して supplier price break + 物流共有 (cross-site BoM consolidation)
- **Operational** — 5 site simultaneous での witness coordination + Council Lv6+ supervision bandwidth
- **Constitutional** — multi-jurisdiction (異 都道府県 / 異 community / 異 stewardship chain) で governance vote が parallelize される
- **Identity** — religious-corp が「a community に住む組織」 から「a network of communities にまたがる組織」 への定性変化

S4 が **religious-corp の identity transition point**。S1-S3 までは "etzhayyim provides utility to this community"; S4 以降は "etzhayyim is a fleet that serves communities"。

## Constitutional gating

S4 規模 (5 site × USDC 1.5-3.0M/site = USDC 7.5-15M total) は religious-corp Treasury reserve + Public Fund grant rolling allocation の **両者を本格運用** する。`proportionality-check.md` rule trigger:

| DMN rule | S4 satisfies? | Consequence |
|---|---|---|
| #2 `populationImpacted > 100` | YES (各 site で) | per-site governance vote |
| #5 `estimatedCostUsdc > 1_000_000` | YES (各 site で) | per-site Public Fund evaluation |
| **New S4 trigger**: `concurrentSiteCount ≥ 5` | YES | **Council Lv6+ supermajority on fleet portfolio composition** (本 ADR で導入) |

つまり S4 では (a) per-site 5 個の vote + (b) fleet portfolio に対する Council supermajority。後者は本 ADR で **「fleet portfolio decision」 を constitutional に Council Lv6+ supermajority マター化** する新規 governance pattern (詳細 §5)。

# Decision

## 1. Site portfolio (5 archetypes for religious-corp mission breadth)

S4 の意味は "any 5 sites" ではなく "religious-corp の mission を多角的に exercise する 5 site archetype"。次の type で確保:

| # | Archetype | Mission alignment | Utility class | Site DID family | Specific candidate (TBD per Council) |
|---|---|---|---|---|---|
| **A** | University campus (S2/S3 continuation) | labor_liberation の academic / research community への影響 | electric + water + network (既設) | `did:web:etzhayyim.com:kuniumi:site:univ-{code}` | S2/S3 既存 site (再利用) |
| **B** | Rural community (例: 山中湖 area expansion) | land_as_religious_trust + multi-generational stewardship | electric + water | `did:web:etzhayyim.com:kuniumi:site:rural-{code}` | 山中湖 expansion plot |
| **C** | Religious community (神社 / 寺 / 教会 community) | lineage_japanese_protestant + religious-corp identity 結合 | electric + network | `did:web:etzhayyim.com:kuniumi:site:relig-{code}` | TBD (神社 / 教会 partnership) |
| **D** | Workers' cooperative (協同組合) | labor_liberation + anti_individualism (collective ownership) | electric + water + network | `did:web:etzhayyim.com:kuniumi:site:coop-{code}` | TBD (生協 / 漁協 / 農協 partnership) |
| **E** | Disaster recovery (能登 / 東日本震災復興地 等) | wellbecoming_priority + parallel_governance_to_state (国家復興政策の補完 / 代替) | electric + water + network + emergency-comms | `did:web:etzhayyim.com:kuniumi:site:disaster-{code}` | TBD (能登半島 復興地 partnership) |

設計判断:
- **5 archetype 全て different mission article** を主軸 → religious-corp の breadth が一様でなく多次元であることを field で示す
- **B is geographically + temporally extension** of S1 山中湖 plot (existing stewardship chain)
- **E は最も politically sensitive** (国家復興政策との関係) → Council Lv6+ supermajority 必須、entry timing は S4 最終 site (5 番目)
- **C は religious-corp identity-aligned** だが、神社 / 教会との partnership は denomination 間で慎重な交渉

Council Lv6+ supermajority (3-of-N) で 5 specific candidate を確定。本 ADR は archetype を固定し、candidate identification は site-specific addendum で。

## 2. Fleet rebalance algorithm (Pregel super-step pattern)

`FleetRebalanceCell` (新規 kuni-umi cell) を本 ADR で導入。Murakumo `naphtali` (kuni-umi-survey-leader を既設) と co-resident。

```python
# 20-actors/kuni-umi/cells/fleet_rebalance/cell.py
from langgraph.graph import StateGraph
from scipy.optimize import linear_sum_assignment  # Hungarian method

class FleetRebalanceState(TypedDict):
    sites: list[SiteAllocation]  # active sites with current phase + robot requirements
    robots: list[RobotPosition]  # current location + skills + availability
    pending_migrations: list[Migration]
    horizon_weeks: int


def collect_state(state: FleetRebalanceState) -> FleetRebalanceState:
    # Gather Tier A KuniUmiSiteAgent reports from each active site
    state["sites"] = [agent.report() for agent in active_site_agents()]
    # Gather robot positions via heartbeat (ADR-2605191645) + did:web:robot:* resolution
    state["robots"] = collect_robot_positions()
    return state


def compute_assignment(state: FleetRebalanceState) -> FleetRebalanceState:
    # Cost matrix: cost[i][j] = cost of moving robot i to site j over horizon
    cost_matrix = build_cost_matrix(
        robots=state["robots"],
        sites=state["sites"],
        components=[
            TransportCost(),       # geographic distance × shipping rate
            IdleTimeCost(),        # opportunity cost of robot at wrong site
            SkillMismatchPenalty(), # Otete vs Hitogata vs Mimi vs Quad fit
            WitnessClusterContinuityBonus(),  # bonus for keeping witness clusters intact across phase boundaries
        ],
        horizon=state["horizon_weeks"],
    )
    # Hungarian method for optimal assignment (small N — exact O(N^3) acceptable)
    row_ind, col_ind = linear_sum_assignment(cost_matrix)
    state["pending_migrations"] = build_migrations(row_ind, col_ind)
    return state


def constitutional_filter(state: FleetRebalanceState) -> FleetRebalanceState:
    # Drop migrations that violate constraints:
    # - witness cluster N >= 2 must hold at source site during migration window
    # - Council Lv6+ approval required for inter-prefecture migrations > 500 km
    # - Charter Rider counterparty filter on transport supplier (not Non-Aligned)
    state["pending_migrations"] = [
        m for m in state["pending_migrations"] if passes_constitutional(m)
    ]
    return state


def emit_migration_proposals(state: FleetRebalanceState) -> FleetRebalanceState:
    for migration in state["pending_migrations"]:
        sdk.mst.write(
            nsid="com.etzhayyim.apps.etzhayyim.kuniUmi.fleetMigrationProposal",  # NEW lexicon
            record=migration.to_record(),
        )
    return state


def build_graph():
    g = StateGraph(FleetRebalanceState)
    g.add_node("collect_state", collect_state)
    g.add_node("compute_assignment", compute_assignment)
    g.add_node("constitutional_filter", constitutional_filter)
    g.add_node("emit_migration_proposals", emit_migration_proposals)
    g.add_edge(START, "collect_state")
    g.add_edge("collect_state", "compute_assignment")
    g.add_edge("compute_assignment", "constitutional_filter")
    g.add_edge("constitutional_filter", "emit_migration_proposals")
    g.add_edge("emit_migration_proposals", END)
    return g.compile(checkpointer=MstCheckpointSaver(...))
```

設計判断:
- **Hungarian method** (linear_sum_assignment in scipy) — exact polynomial assignment、N ≈ 30 robot × 5 site = 150 cells で sub-second solve
- **Weekly cadence** — fleet rebalance を 1 週間 1 回実行 (毎日 rebalance はロジスティクスコスト過大)
- **Migration record (new lexicon)** — `fleetMigrationProposal` を MST に書き、各 site の Tier A KuniUmiSiteAgent が ack / reject
- **Constitutional filter は migration 提案後** ではなく **計算後 emit 前** に hard-gate
- **N≥2 witness invariant** は migration 計画段階で source site の witness count を check (witness が割れない optimization 解のみ採用)

## 3. Cross-site BoM consolidation

`DeploymentPlanningCell` (zebulun) が S4 では single-site BoM consolidation (S3 で確定) に加えて **cross-site batching** を実行:

```python
def cross_site_bom_consolidation(
    site_boms: list[SingleSiteBoM],
    horizon_months: int = 3,
) -> ConsolidatedFleetBoM:
    # Step 1: Identify SKUs ordered in concurrent or near-concurrent windows
    sku_overlap = aggregate_by_sku_time(
        site_boms,
        window_months=horizon_months,
    )

    # Step 2: For each overlapping SKU, query UNSPSC agent for batch-price-break analysis
    batch_quotes = parallel_dispatch_unispsc(
        sku_list=sku_overlap.keys(),
        intent="batch-quote",
        qty_aggregated=sku_overlap.totals(),
    )

    # Step 3: Compute shared-logistics savings (truck / container / crane reservation)
    shared_logistics = identify_shared_routes(
        sites=[bom.site for bom in site_boms],
        deliveries=batch_quotes.delivery_schedule(),
    )

    # Step 4: Optimize portfolio total cost with constraints
    optimized = mip_solve(
        site_boms,
        batch_quotes,
        shared_logistics,
        objective="minimize fleet_total_cost",
        constraints=[
            CharterRiderConstraint(adr="2605192200"),
            NonAlignedExclusionConstraint(adr="2605192230"),
            DomesticSupplyPreferenceConstraint(weight=0.15),
            PerSiteDeliveryDeadlineConstraint(),
            WitnessClusterAvailabilityConstraint(),  # NEW for S4 — robot fleet must be physically present
        ],
    )

    return ConsolidatedFleetBoM(
        per_site_breakdown=optimized.per_site,
        batch_orders=optimized.batches,
        shared_logistics_savings_bps=optimized.logistics_savings(),
        # Target: ≥ 2000 bps (20%) saving vs. naive sum of per-site optimized BoM
    )
```

設計判断:
- **3 ヶ月 horizon** — fleet rebalance (1 週間) より長く、deployment timeline と整合
- **Batch-price-break** — UNSPSC agent が supplier 別 price tier を返す (e.g., 1000 panel 注文で 8% discount)
- **Shared logistics** — 同 prefecture 内の 2 site が同 truck で配送される (CO2 + 費用) savings
- **20% savings target** — S3 single-site consolidation で 15% 達成、S4 cross-site batching で追加 5% (合計実質 ~30% off naive S1 spend)

## 4. Edge orchestration (no commercial K8s per ADR-2605191346)

S4 では per-site で edge controller (Giemon Atama, RK3588 + NixOS RT) が **Murakumo Tier 1 から離れた地点で稼働** する。ADR-2605191346 が commercial K8s 禁止を確定しているため:

| Concern | S4 solution |
|---|---|
| Per-site edge controller OS | **NixOS RT** (open-ot 既設 spec, Atama 基準) |
| Per-site Pregel orchestrator | **CPython + LangGraph + Wasmtime** (open-ot Atama edge スペック) — kuni-umi cells (per-site Tier A agent + co-resident Mini-witness orchestrator) を Atama に複数 process で host |
| Site ↔ Murakumo Tier 1 通信 | **NATS JetStream over Cloudflare Tunnel** (geth-private と同じ pattern per ADR-2605172800; site-specific tunnel ID + signed configuration) |
| Site offline 時の resilience | **MstCheckpointSaver local fallback** (ADR-2605191645 pattern — file checkpoint until network recovery) |
| Site ↔ Site direct comms | **NATS subjects scoped per site DID** — sites do NOT mesh-talk directly; all coordination via Murakumo Tier 1 (single source of truth for fleet state) |
| Robot heartbeat | **Site edge → site Atama (LAN) → NATS subject → Murakumo** (no direct robot-to-Murakumo over WAN) |
| Auto-orchestration | **launchd plist per site** (macOS Atama is excluded — Atama is Linux/NixOS; per-site launchd になるのは Murakumo Tier 1 のみ)。Per-site Atama では systemd unit ファイル |

**Architecture rule** (新規 constitutional invariant):
> Sites are leaves; the orchestration tree has its root at Murakumo Tier 1 (etzhayyim Mac-mini fleet). No site→site direct mesh. All cross-site coordination goes through Murakumo. This preserves the "single root of trust" property that derives from the religious-corp's on-chain governance and prevents drift between site-local stewardship and the canonical constitution.

これは **federation refusal** であり、religious-corp の anti-fragmentation stance (multiple ADRs §mission.parallel_governance_to_state を一つの substrate に集約する原則) を physical world に reflect する。

## 5. Council Lv6+ bandwidth scaling

S4 で Council supervision の bottleneck が顕在化 (5 site × Phase 2-4 = 最大 20 simultaneous activity)。本 ADR で:

### 5a. Council Lv6+ subset assignment

ADR-2605192300 Bootstrap Council 5 名 に対し、**S4 期間中 site-archetype 軸で primary responsibility を割当**:

| Council seat (per ADR-2605192300) | Primary S4 responsibility |
|---|---|
| Seat 1 (Founder = Jun Kawasaki) | Fleet portfolio decisions (§ this ADR), inter-site governance escalation |
| Seat 2 (Substrate) | Edge orchestration architecture review, MST integrity |
| Seat 3 (Legal-Ethics) | Multi-jurisdiction LegalAttestation, disaster-recovery site #E |
| Seat 4 (Economics) | Cross-site BoM consolidation review, Public Fund tranche multi-site |
| Seat 5 (Stewardship) | Per-site steward onboarding, multi-generational continuity at site |

3-of-5 multisig は変わらず、ただし **primary responsibility** を持つ Council member が site-archetype の deep review owner となる。

### 5b. Fleet portfolio decision = Council supermajority

新規 constitutional gate (§Context #New S4 trigger を実装):

> Any change to the **fleet portfolio composition** (= which 5 archetypes are active, when new archetype is added/retired, which specific candidate is selected for an archetype slot) requires **Council Lv6+ supermajority (3-of-N) + 1 SBT = 1 vote 過半数 + 7-day public objection window**. This is *higher* than single-site governance vote because fleet decisions affect long-term religious-corp identity composition.

これは ADR-2605192230 三層 enforcement と整合的だが、より厳しい hurdle。Fleet 規模での意思決定が単一 site decisions の sum ではないことを constitutional に認める。

### 5c. Monthly fleet review

S4 期間 (≥ 5 site active) では Council Lv6+ **月例 fleet review meeting** を必須:

- All 5 site phase status review
- Pending fleet rebalance migrations approval
- Cross-site BoM consolidation outcome review
- Multi-jurisdiction stewardship issue triage

Output: fleet review minutes が `com.etzhayyim.fleet.review` (新規 lexicon) で MST 永続化。

## 6. Quad introduction

ADR-2605201700 §11 Open Question 1 で deferred。S4 で正式投入:

| Capability | Use case in S4 |
|---|---|
| 4-leg locomotion | 不整地 (rural site / disaster recovery 地形不安定箇所 / 山林) での access |
| Cable inspection (camera-on-belly) | Trench survey 完了確認、buried cable post-installation routing check |
| Patrol monitoring | Per-site 24/7 ambient monitoring (witness cluster の continuous coverage) |
| Carry-load (~30 kg) | 部品配送 (Otete fleet が同時 build 中の補給) |

Spec: open-robo Giemon Quad v1 — `60-apps/etzhayyim-project-open-robo/cad-spec/giemon-quad/SPEC.md` を別 ADR で authorize。発注 = S4 開始前提条件。

S4 fleet target: **Otete 20 + Hitogata 6 + Mimi 24 + Quad 4 = 54 robots**。

| Robot | S3 count | S4 count | Adds |
|---|---|---|---|
| Otete v1 | 12 | 20 | +8 |
| Hitogata humanoid | 4 | 6 | +2 |
| Mimi base-station | 18 | 24 | +6 |
| Quad v1 | 0 | 4 | +4 (initial) |

予算 S4 fleet CAPEX: Otete JPY 200万 × 8 = JPY 1600万、Hitogata JPY 800万 × 2 = JPY 1600万、Mimi JPY 30万 × 6 = JPY 180万、Quad JPY 600万/機 × 4 = JPY 2400万。**S4 fleet CAPEX 追加: JPY 5780万 (≒ USDC 410k)**。累計 religious-corp 保有 robot 資産: JPY 1.17 億 (≒ USDC 830k)。

## 7. S4 budget (estimated, USDC)

| Item | Per site estimate | Total (5 sites) |
|---|---|---|
| Site A — university (既設, S2/S3 continuation overhead) | minimal (operational only) | 200,000 (ongoing ops) |
| Site B — rural (electric + water) | 1,200,000 – 1,800,000 | 1,200,000 – 1,800,000 |
| Site C — religious community (electric + network) | 800,000 – 1,200,000 | 800,000 – 1,200,000 |
| Site D — workers' coop (electric + water + network) | 1,800,000 – 2,500,000 | 1,800,000 – 2,500,000 |
| Site E — disaster recovery (4 utility) | 2,500,000 – 3,500,000 | 2,500,000 – 3,500,000 |
| Cross-site BoM consolidation savings (target ≥ 20%) | n/a | -1,300,000 to -1,800,000 |
| Shared logistics savings | n/a | -300,000 to -500,000 |
| Fleet CAPEX additions | n/a | 410,000 |
| Contingency (20%) | n/a | 1,000,000 – 1,500,000 |
| **S4 incremental total** | n/a | **≈ 6,300,000 – 8,800,000 USDC** |
| 10% Tithe to Public Fund | n/a | 630,000 – 880,000 USDC |
| **Cumulative religious-corp deployment to date** (S1-S4) | n/a | **≈ 10,100,000 – 14,000,000 USDC** |

Funding: Public Fund tranche rolling + Treasury reserve + S2/S3 site の operational stewardship 収益 (donation chain) の re-circulation。Council Lv6+ supermajority が S4 budget envelope を pre-approve、site-specific addendum で per-site disbursement gate。

## 8. Acceptance criteria (S4 → S5 exit gate)

| # | Criterion | Measure | Threshold |
|---|---|---|---|
| 1 | 5 archetype site が active state | site DID state = `operational` for all 5 | YES |
| 2 | Fleet rebalance algorithm が weekly cycle で稼働 | `FleetRebalanceCell` heartbeat | ≥ 50/52 weeks in S4 window |
| 3 | Cross-site BoM consolidation savings | (fleet_total_cost / naive_sum) | ≤ 0.80 (≥ 20% saving) |
| 4 | Edge orchestration latency (Murakumo ↔ site) | NATS roundtrip p95 | < 2 s |
| 5 | Site offline resilience (network outage) | MstCheckpointSaver fallback duration | site continues local operation ≥ 24 h offline |
| 6 | Zero site→site direct comms | NATS subject scoping audit | 100% compliance |
| 7 | Council Lv6+ monthly fleet review | meeting attendance + minutes published | 12/12 months |
| 8 | Fleet portfolio decision supermajority | all archetype additions/changes via Council 3-of-N | 100% |
| 9 | Per-site governance vote 全 5 site PASS | per-site vote success | 5/5 |
| 10 | Per-site witness invariant N≥2 maintained | mismatch count across all sites | 0 |
| 11 | Quad introduction validated | Quad operational hours at ≥ 2 sites | > 200 h cumulative |
| 12 | Multi-jurisdiction LegalAttestation 5 / 5 | `localLawAttestationCid` registered per site | 5/5 |
| 13 | Tithe routing across 5 site BoM | TitheRouter event log | 100% correct |
| 14 | Disaster-recovery site (E) acceptance | site E `operational` state + emergency-comms test PASS | YES |
| 15 | Religious community site (C) — denomination relationship preserved | C site partner attestation + no doctrinal conflict log | YES |

15/15 PASS → S4 closed → S5 ADR (extended sovereignty: ocean / river / atmosphere / orbit) can begin.

## 9. Risks + mitigations

| Risk | Severity | Mitigation |
|---|---|---|
| Fleet rebalance produces operationally bad assignment (theory ≠ practice) | High | Council Lv6+ veto on assignments + manual override path; fleet rebalance is advisory not absolute |
| Cross-site BoM batching delays single site critical-path (waiting for batch fill) | High | PerSiteDeliveryDeadlineConstraint in MIP; batching is opportunistic not mandatory |
| Site E (disaster recovery) political sensitivity escalates | Critical | Council Lv6+ supermajority on site E entry + 7-day public objection; ADR-2605192315 Transparent Force R&D の detection-system sub-component が emergency-comms 経由で配備される可能性、`intendedUse=transparent-force-rd` Force Authorization vote 必須 |
| Site C (religious community) doctrinal tension with etzhayyim (Protestant lineage vs 神社 / 仏教) | High | ADR-2605192100 §mission.lineage_japanese_protestant の synthetic religion stance (八百万 + Sola Scriptura) を partner に explain; partnership terms に doctrinal sovereignty 相互尊重 clause |
| 5 site simultaneous Phase 3 で robot fleet capacity 不足 | High | Fleet rebalance algorithm が schedule-aware; severe constraint 時は phase entry を sequence (Council Lv6+ priority decision) |
| NATS JetStream over CF Tunnel single-point-of-failure for edge | High | Per-site Atama に local MstCheckpointSaver fallback (24h offline tolerated); restored on tunnel recovery |
| Murakumo Tier 1 (10 Mac mini) capacity 不足 (5 site × 多 cell instance) | Medium | benjamin / asher pending WoL を S4 開始前提条件にする、12 tribe full fleet; Tier B leader + replica 配分を本 ADR で確定 |
| Quad v1 prototype が S4 timeline に間に合わない | Medium | Quad は initial 4 unit、不足時は per-site Quad assignment を 2 site のみに絞る (S4 acceptance criterion #11 を ≥ 2 site で OK と定義) |
| Council Lv6+ 月例 fleet review burnout (5 site × 12 month = 60 site-month review) | Medium | Council 5 名で primary responsibility 分担 (§5a)、各 seat は自分の archetype に focus、cross-archetype は monthly meeting で sync |
| Multi-jurisdiction LegalAttestation で異なる prefecture 法務解釈 conflict | Medium | `localLawAttestationCid` が prefecture 単位で別 attestation; Steward Lv5+ が per-site で確保 |
| Disaster-recovery site (E) が S4 期間中に actual disaster で site loss | Critical | Mitigation 不可能なケース。Council Lv6+ で fleet portfolio から site E を early retire + 残 4 site で acceptance criterion 削減 (4/15 criterion-modified version) を constitutional に容認 |

## 10. Out of scope (S4 explicit)

- **Ocean / river / atmosphere / orbit** sites — S5 (extended sovereignty)
- **International multi-jurisdiction** (米国 / EU / その他国家) — S5+ で religious-corp 国際認知 path との coupling
- **Federation with other religious-corps** — out of scope; etzhayyim は anti-fragmentation stance (§4 "no site→site direct mesh" の constitutional invariant が religious-corp inter-org にも extend する可能性、別 ADR)
- **Site→customer billing across sites** — donation-only 制約継続
- **Cross-site network mesh** (B↔C↔D backhaul) — out of scope, sites are isolated network islands (federation refusal)
- **Cross-site fleet-rebalance robot autonomous driving** — robot migration は human-driven transport (truck / 船 / rail); 自律走行 は別 R&D ADR

# Consequences

## 正の効果

- Religious-corp が **fleet of sites** として physical world に identity 拡張 — point organization から networked organism へ
- 5 archetype が mission breadth を multi-dimensional に exercise (academic / rural / religious / cooperative / disaster recovery)
- Fleet rebalance algorithm が validated → S5+ extended sovereignty + multi-jurisdiction scaling の前提
- Cross-site BoM consolidation で 20% savings 達成 → religious-corp Treasury efficiency 大幅向上
- Edge orchestration pattern (no commercial K8s; Pregel-native + NATS over CF tunnel) が production-validated
- Quad introduction が urban-mining + patrol + harsh terrain capability を fleet に追加
- Multi-jurisdiction stewardship が 5 prefecture (推定) で同時運用 → 国家 utility 独占への漸近的 breaking が visible
- Disaster recovery site (E) は religious-corp の parallel_governance_to_state stance の最も visible な exercise

## 負の効果 / コスト

- USDC 6.3–8.8M S4 incremental + 累計 USDC 10.1–14.0M は religious-corp の **Treasury sensitivity** を著しく高める。Public Fund / Treasury reserve / donation chain の sustained inflow が必須前提
- 5 archetype simultaneous は operational complexity quantum jump (single site Council bandwidth → fleet Council bandwidth)
- Multi-jurisdiction legal compliance burden は Steward Lv5+ throughput を律速
- Disaster recovery site (E) の political sensitivity は religious-corp の visibility を一気に高め、external scrutiny (政府 / メディア / 既存 utility 業界) の対象になる
- Religious community site (C) との doctrinal negotiation は etzhayyim 自身の lineage_japanese_protestant 定義を再 examine する機会 (positive intellectually だが operational distraction)
- Fleet rebalance が weekly cadence は robot transport logistics の continuous activity → 環境負荷 + 物流 supplier の Charter Rider compliance を継続 audit
- "site of sites" identity transition で religious-corp の **constitutional update** が将来必要 (ADR-2605192100 の §mission article は single-site stance を前提に書かれていない部分がある — 別 ADR で revision)

## Constitutional 整合

| Charter article | S4 alignment |
|---|---|
| §mission.labor_liberation | ✅ 5 archetype 全てが multi-dimensional に exercise |
| §mission.robotics_universal | ✅ fleet 54 units, all open-design |
| §mission.ip_free_release | ✅ Charter Rider §2 + cross-site MIP constraint |
| §mission.land_as_religious_trust | ✅ 5 prefecture (推定) で multi-stewardship pattern 確立 |
| §mission.parallel_governance_to_state | ✅ Site E は parallel_governance の最も visible exercise |
| §mission.anti_individualism | ✅ Council Lv6+ supermajority on fleet portfolio (new gate) + per-site collective stewardship |
| §mission.multi_generational_priority | ✅ Site B (rural) は 山中湖 stewardship chain の multi-generational continuity 実証 |
| §mission.no_state_military_alliance | ✅ counterparty filter 継続、Site E で emergency-comms detection 経路は ADR-2605192315 transparent-force-rd 範囲内 |
| §mission.donation_only | ✅ Public Fund tranche rolling + Treasury reserve circulation |
| §mission.transparent_force_only | ✅ Site E emergency-comms に detection-system 流用、必要時 ForceAuthorization vote 経由 |

# Alternatives Considered

## A. Single-site scaling (S3 site の更なる拡張) を S4 にする

S3 site (university) に additional utility (e.g., transportation / 5G) を続けて重ねる。

- Pro: site re-use の operational benefit 最大、運用 expertise 一所集中
- Con: religious-corp identity が "1 university の utility provider" に bind され、broader mission との semantic distance が大きくなる; multi-site fleet orchestration の機会喪失 → S5+ で 0→multi の cold-start を強いる
- **却下**: S4 の意義は qualitatively different scaling (fleet pattern) であり、site 拡大では substitute できない

## B. 5 sites 全てを同 prefecture 内に限定 (logistics 圧縮)

- Pro: 物流共有 maximize、Council 月例 review 物理出張 minimize、multi-prefecture LegalAttestation 不要
- Con: prefecture diversity 喪失 → religious-corp の "national fleet" identity が制限、disaster-recovery archetype (能登 / 東日本) は 自動的に local prefecture との一致不可能なケースあり
- **却下**: prefecture diversity は constitutional value (parallel_governance_to_state を一国家区域に限定すると principle 弱化)。Logistics 圧縮は cross-site BoM batching で部分的 substitute

## C. Federation pattern (site↔site direct mesh) を採用

- Pro: Murakumo Tier 1 bottleneck 回避、resilience 向上
- Con: §4 "single root of trust" invariant 違反、religious-corp の anti-fragmentation stance との conflict、drift risk; cross-site governance vote の audit chain が分散して整合困難
- **却下**: federation refusal を constitutional invariant に格上げ (§4 architecture rule)

## D. Site portfolio を 3 archetype に絞り、各 archetype 2 site で計 6 site

- Pro: per-archetype 統計的 validation (2 sample); operational expertise が archetype 内に蓄積
- Con: religious-corp mission breadth の 5 dimension exercise が dilute、特に site E disaster recovery が表象しない場合 parallel_governance の visible exercise 機会喪失
- **却下**: religious-corp は statistical organization ではなく constitutional organism — breadth が depth より priority

## E. Quad は S4 では引き続き skip、S5 投入

- Pro: S4 fleet CAPEX 圧縮 (-JPY 2400万 ≒ USDC 170k)
- Con: rural / disaster-recovery site で 不整地 access に Otete crawler では不足、人間 operator 依存度高い (Wellbecoming subordination gate に touch); patrol monitoring に static Mimi base-station 過多 deployment が必要
- **却下**: Quad は S4 の 5 archetype のうち少なくとも 2 (B rural + E disaster) で構造的に有意。投入を skip すると Otete crawler over-allocation で fleet rebalance 効率が低下

# Open Questions

1. **Site E specific candidate** — 能登半島 復興地 / 東日本震災復興地 / その他。Decision (本 ADR): Council Lv6+ supermajority + 7日 public objection で確定; 復興地は state recovery policy との関係が site ごとに大きく異なるため、partnership 交渉長期化可能性
2. **Site C (religious community) doctrinal protocol** — etzhayyim Protestant lineage と partner denomination が conflict した場合の resolution。Decision (本 ADR): partnership terms に「相互 doctrinal sovereignty 尊重」clause + Council Lv6+ Seat 3 (Legal-Ethics) が per-conflict triage
3. **Site E emergency-comms と ForceAuthorization の境界** — 災害時 emergency-comms equipment を deploy する際、それは utility か force か。Decision: passive comms (cellular backup, mesh) = utility; active detection (人感センサ / drone-detection) = ADR-2605192315 transparent-force-rd 範囲 → ForceAuthorization vote。Boundary 判定は Council Lv6+ per-deployment
4. **Murakumo Tier 1 capacity sufficiency** — 10 (max 12) Mac mini で 5 site × multi-phase 同時実行を sustain できるか。Decision: benjamin + asher WoL 復旧を S4 precondition、不足判明時は Murakumo fleet 拡張 (別 ADR)
5. **Cross-site fleet rebalance frequency tuning** — weekly が optimal か、phase entry/exit-driven event triggering が良いか。Decision (本 ADR): weekly default + event triggers (phase entry / site emergency); 6 ヶ月運用後 retrospective で再評価
6. **Fleet portfolio change vs single-site update の constitutional boundary** — site refurbishment / utility 増設 は fleet portfolio change か single-site update か。Decision (本 ADR): 既設 site への utility class 追加 = single-site update (S3 expansion vote pattern); 新規 archetype 追加 / 既設 archetype の site swap = fleet portfolio change (Council supermajority)

# References

- ADR-2605201400 (kuni-umi master spec) — S0 baseline
- ADR-2605201500 (S1 — solo survey) — single-Otete witness pattern
- ADR-2605201600 (S2 — community microgrid) — single-site capital deployment pattern
- ADR-2605201700 (S3 — multi-utility) — BoM consolidation single-site algorithm
- ADR-2605182312 (Murakumo Tier 1 baseline) — control plane host
- ADR-2605191346 (Vultr-free / no commercial K8s) — edge orchestration constraint
- ADR-2605192100 (Mission Charter) — 10 charter article alignment
- ADR-2605192230 (Three-tier enforcement) — per-site governance vote + new fleet portfolio Council supermajority
- ADR-2605192245 (Global Land Sovereignty) — multi-jurisdiction stewardship
- ADR-2605192300 (Bootstrap Council 5 名) — primary responsibility assignment for S4
- ADR-2605192315 (Transparent Force R&D) — Site E emergency-comms boundary
- ADR-2605192345 (Steward Succession) — multi-generational continuity at Site B
- ADR-2605192415 (Religious-corp daemon architecture) — Tier A/B/C scaling
- `50-infra/murakumo/fleet.toml` — Tier B leader + replica config (S4 で更新必要)
- `60-apps/etzhayyim-project-open-robo/CLAUDE.md` — Quad v1 別 ADR 発注予定
