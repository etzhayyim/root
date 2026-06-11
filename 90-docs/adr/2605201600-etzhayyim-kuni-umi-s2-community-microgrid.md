---
id: adr-2605201600-etzhayyim-kuni-umi-s2-community-microgrid
title: "ADR-2605201600: kuni-umi S2 — community microgrid (1 MW class, single-utility electric prototype, kuni-umi Phase 2–4 × open-ot 7 loops end-to-end)"
status: proposed
doc_type: adr
topic: kuni-umi-s2-community-microgrid
authoritative: true
last_verified: 2026-05-20
priority: 7.0
axis: implementation
weight: 0.70
priority_note: "S2 = kuni-umi が初めて real capital を deploy する milestone。1 MW class community microgrid を Phase 2 (Planning) → Phase 3 (Construction) → Phase 4 (Commissioning) で end-to-end 駆動。open-ot PROTOTYPE-MICROGRID.md §1 asset inventory + §2 7-loop catalog を target topology とする。約 USDC 1.5–2.0M / 80 smart-meter install / 600 kW PV + 500 kWh BESS の規模で proportionality-check + governance vote + Public Fund evaluation を triggering。"
authoritative_for:
  - kuni-umi S2 scope (1 MW community microgrid, single-utility electric)
  - S2 pilot site selection rationale
  - BoM macro (UNSPSC commodity codes + estimated cost)
  - Giemon fleet sizing (S2 scaling from S1 single-Otete)
  - 7-loop commissioning sequence (open-ot loops × kuni-umi Phase 4)
  - S2 acceptance criteria (kuni-umi 4-phase + open-ot 90-day pilot overlay)
  - S2 → S3 exit gate
depends_on:
  - adr-2605201400-etzhayyim-kuni-umi-planetary-infra-fleet
  - adr-2605201500-etzhayyim-kuni-umi-s1-solo-survey
  - adr-2605151200-open-ot-wasm-plc-dlc
  - 2605171300
  - adr-2605172100-etzhayyim-payments-on-chain-only
  - adr-2605172300-etzhayyim-bi-asset-substrate
  - adr-2605192130-etzhayyim-tithe-redistribution
  - adr-2605192145-etzhayyim-public-fund-architecture
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
  - adr-2605192230-etzhayyim-three-tier-enforcement-implementation
  - adr-2605192300-etzhayyim-bootstrap-council-five
related:
  - 60-apps/etzhayyim-project-open-ot/PROTOTYPE-MICROGRID.md
  - 60-apps/etzhayyim-project-open-denki/CLAUDE.md
  - 60-apps/etzhayyim-project-open-robo/CLAUDE.md
supersedes: []
superseded_by: []
---

# ADR-2605201600: kuni-umi S2 — Community Microgrid

**Status**: proposed
**Date**: 2026-05-20
**Deciders**: Jun Kawasaki

# Context

S1 (ADR-2605201500) は survey-only の minimum viable validation。S2 は **kuni-umi が初めて real capital を deploy** する step。Target topology は既に open-ot side で確定: `60-apps/etzhayyim-project-open-ot/PROTOTYPE-MICROGRID.md` §1 (asset inventory) + §2 (7-loop catalog) + §3 (8 FBType library — 3 implemented, 5 future)。

kuni-umi が S2 で担うのは:

- **Phase 2 (Planning)** — UNSPSC agent fleet (ADR-2605171300) を call して BoM 生成 + cost 見積 + governance vote
- **Phase 3 (Construction)** — Giemon fleet (Otete + Hitogata + Mimi base-stations) を派遣して physical install (PV mount / 配線 / BESS 据付 / smart meter 設置 / 変圧器 配置)
- **Phase 4 (Commissioning)** — open-ot WASM PLC への hand-off + 7 loops acceptance test

open-ot 側は既に Risk-1 Gate A (PID_LIMITED) PASS 想定 + Q3 2026 prototype timing で 3 / 8 FBType (PID_LIMITED / DROOP_P_F / ANTI_ISLANDING_ROCOF) 実装済み。本 ADR は **施工 actor として kuni-umi が open-ot の steady-state operation 前段を完結する** path を確定する。

## Constitutional gating (review for S2 scale)

S2 規模では proportionality-check DMN (`20-actors/kuni-umi/dmn/proportionality-check.md`) で複数 rule が trigger される:

| DMN rule | S2 satisfies? | Consequence |
|---|---|---|
| #2 `populationImpacted > 100` | YES (university 〜 数千) | **REQUIRES governance vote** (1 SBT = 1 vote 過半数) |
| #3 `ecologyImpactScore > 30` | NO (既存 rooftop 利用想定) | ecologist review 不要 |
| #4 `reversibilityScore < 50` | NO (Decommission plan で recyclable PV + 山中湖 urban-mining cell 経路 → reversibilityScore ≥ 60) | no Council supermajority |
| #5 `estimatedCostUsdc > 1_000_000` | YES (1 MW microgrid ≈ USDC 1.5–2.0M) | **REQUIRES Public Fund grant evaluation** (ADR-2605192145) |
| #6 `intendedUse = transparent-force-rd` | NO | no Force Authorization |

Therefore S2 triggers **2 governance escalations**: (a) regular vote, (b) Public Fund grant evaluation. Both are non-blocking on this ADR (which is the spec); they are blocking on actual deploy.

# Decision

## 1. Pilot site selection — University campus microgrid (primary)

open-ot PROTOTYPE-MICROGRID.md §5 で 3 候補が pending。本 ADR で確定:

| Site type | Decision |
|---|---|
| **University campus microgrid** | ✅ **S2 primary** — non-safety-critical, research-friendly, public-good narrative; population > 100 trigger される (governance vote 経由で 多世代 + 反個人主義 stakeholder model を validate); rooftop PV + carport 既存 footprint → ecology impact 低 |
| Small industrial site | ⏳ S3 (multi-utility) で再評価 |
| Remote island (Okinawa / Ogasawara) | ⏳ S4 (multi-site fleet) で再評価 — islanding が normal state である方が S4 fleet pattern の真価を見せる |

University 候補は **etzhayyim と academic collaboration MoU を持つ機関** に絞る (S2 precondition)。具体機関の特定は本 ADR 範囲外 — `LandRegistry` 経路で donation/stewardship 合意が成立した時点で site DID を発行。

## 2. Asset inventory (open-ot §1 を 1 MW class で reflect)

| Asset | Type | Capacity | open-denki record DID | UNSPSC primary commodity |
|---|---|---|---|---|
| PV array A (rooftop) | 太陽光パネル × 4 string | 400 kW peak | `did:web:open-denki.etzhayyim.com:gen:pv-roof-a` | 26111701 (solar panels) |
| PV array B (carport) | 太陽光パネル × 2 (bifacial) | 200 kW peak | `did:web:open-denki.etzhayyim.com:gen:pv-carport-b` | 26111701 |
| Inverters | smart inverter cluster | 600 kW combined | (inside PV-A / PV-B records) | 26111717 (inverter) |
| BESS-1 | LFP + PCS | 500 kWh / 250 kW | `did:web:open-denki.etzhayyim.com:gen:bess-1` | 26111607 (battery), 26111717 (PCS) |
| Diesel genset | backup + black-start | 300 kW | `did:web:open-denki.etzhayyim.com:gen:diesel-1` | 26111601 (genset) |
| Substation | 6.6 kV / 400 V transformer | 1 MVA | `did:web:open-denki.etzhayyim.com:sub:main` | 26111703 (transformer) |
| Feeders | LV distribution × 4 | — | `did:web:open-denki.etzhayyim.com:feeder:f01..f04` | 26121603 (LV cable) |
| Smart meters (AMI) | per delivery point | ~80 | `did:web:open-denki.etzhayyim.com:meter:m001..m080` | 41111904 (electricity meter) |
| Grid-tie | utility import/export | 800 kVA | `did:web:open-denki.etzhayyim.com:gen:grid-tie` | 26111703 (transformer) + 26111717 (inverter) |

各 UNSPSC code は ADR-2605171300 fleet 内の対応 specialist agent (e.g., `c26111701.py` for solar panels) に dispatch される。BoM = UNSPSC code × qty × estimated USDC unit cost。Total estimate: **USDC 1.5–2.0M** (Japan domestic supply chain, Apache 2.0 + Charter Rider compliant suppliers 優先)。

## 3. Phase 2 Planning workflow

`DeploymentPlanningCell` on zebulun が以下を実行:

1. `deriveTargetTopology` — open-ot 7 loops + 8 asset categories の DID list 生成 (上記 §2)
2. `bomGeneration` — 9 UNSPSC primary code に対し fleet dispatch (parallel)、それぞれ specialized agent が:
   - 国内 supplier list (Apache 2.0 + Rider 適合確認)
   - qty + estimated cost
   - delivery lead-time
3. `counterpartyClassification` — 各 supplier DID を `ChartersComplianceRegistry.isNonAligned()` で check; 国家武力 supplier (e.g., 武器メーカー parent) は auto-reject
4. `proportionalityCheck` — rule #2 + #5 trigger → `requiresGovernance=true` + `requiresPublicFund=true`
5. `paymentPlan` — escrow milestone schedule (5 milestones: PV install / BESS install / substation+feeders / smart meters / commissioning) via `Etzhayyim.pay()` → `MilestoneEscrow.sol` + `TitheRouter.route()` 90/10
6. `fleetAllocation` — Giemon allocation (詳細 §4)
7. `proposePlan` — encrypted `proposeDeploymentPlan` MST record + governance proposal record + Public Fund grant proposal record
8. **Governance vote** (1 SBT = 1 vote 過半数, ADR-2605192230) + **Public Fund evaluation** (PublicFundGrantCell, ADR-2605192145) を parallel に進行
9. 両 approve → plan accepted; いずれか reject → plan rejected (or revised + re-vote)

## 4. Giemon fleet sizing (S2 scaling)

S1 の 1 Otete + 1 Mimi では絶対不足。S2 では:

| Robot | Count | Role | DID pattern |
|---|---|---|---|
| **Giemon Otete v1** (6軸 arm + crawler) | **4–6 units** | PV panel positioning + 配線 + smart meter install + 主要 manipulation tasks | `did:web:etzhayyim.com:kuniumi:robot:otete-{002..007}` (S1 Otete-001 + 新規 6 機) |
| **Giemon Hitogata** (humanoid, 二足) | **2 units** | 高所作業 (carport canopy 上) + 狭隘箇所 (substation panel 内 wiring) | `did:web:etzhayyim.com:kuniumi:robot:hitogata-{001,002}` — open-robo roadmap で別 ADR 発注 |
| **Giemon Mimi base-station** | **8 units** | 連続 witness coverage (asset cluster ごとに 1 機) | `did:web:etzhayyim.com:kuniumi:robot:mimi-base-{002..009}` (S1 Mimi-base-001 + 8 機) |
| **Giemon Te** (i.MX RT1170 actuator RTU) | **0 units (S2)** | 施工段階では使用しない — commissioning 後 open-ot field-tier として site に残存 (per ASSET inventory に組み込み) | n/a (open-ot 管轄) |

設計判断:
- **Hitogata humanoid は S2 必須** — 6軸 arm + crawler では carport canopy 上の bifacial panel install が geometric constraint で不可。open-robo roadmap で本 ADR と同時に Hitogata v1 prototype を発注 (別 ADR)
- **Mimi base-station ≥ 8** — 80 smart-meter cluster + PV-A + PV-B + BESS + substation + grid-tie の同時 witness coverage に必要。N ≥ 2 invariant を **per asset cluster** で満たす
- **Otete v1 fleet 4–6 機** — concurrent task fan-out で工期短縮。冗長度: 1 機故障で工期延長最大 2 週

予算: Hitogata v1 prototype JPY 800万/機 × 2 = JPY 1600万、Otete v1 増産 JPY 200万/機 × 5 = JPY 1000万、Mimi base-station JPY 30万/機 × 8 = JPY 240万。**Total robot CAPEX: JPY 2840万 (≒ USDC 200k)**。これは BoM (microgrid 本体 USDC 1.5–2M) には含めず、religious-corp 自身の fleet 資産として treasury 計上。

## 5. Phase 3 Construction sequence

`ConstructionOrchestrationCell` on joseph が 8 sub-phases (Pregel super-step group) で進行:

| Sub-phase | Asset focus | Witness cluster | Estimated duration | Critical-path? |
|---|---|---|---|---|
| 3.1 | Site prep + 基礎 (mount frames, conduit, foundations) | Mimi-base-002 | 2 weeks | Yes |
| 3.2 | PV-A rooftop install (400 kW, 4 strings) | Otete-002..004 + Mimi-base-003 + Hitogata-001 | 3 weeks | Yes |
| 3.3 | PV-B carport install (200 kW, bifacial) | Otete-005..006 + Mimi-base-004 + Hitogata-002 | 2 weeks | Parallel to 3.2 final week |
| 3.4 | BESS-1 据付 + PCS 配線 | Otete-002..003 + Hitogata-001..002 + Mimi-base-005 | 1 week | After 3.1 |
| 3.5 | Diesel genset 据付 + black-start fuel system | Otete-004..005 + Mimi-base-006 | 1 week | Parallel to 3.4 |
| 3.6 | Substation transformer + LV feeders f01..f04 | Otete-002..006 + Hitogata-001..002 + Mimi-base-007 | 2 weeks | After 3.4-3.5 |
| 3.7 | Smart meter install × 80 + AMI commissioning | Otete-002..007 + Mimi-base-008 | 3 weeks (1 meter/Otete/day) | Parallel to 3.6 |
| 3.8 | Grid-tie + utility interconnection (electric utility 立会い) | Otete-002..003 + Mimi-base-009 + human electrician + utility inspector | 1 week | After 3.6 |

**Total construction duration: 10–12 weeks** (10 weeks if 3.3 / 3.5 / 3.7 が parallel に走る; 12 weeks if serial)。

`recordConstructionProgress` を 1–10 Hz で stream、各 sub-phase 完了で `phase=complete`、最終 sub-phase で `phase=handoff-ready`。

**Hard-RT boundary**: PCS startup / inverter MPPT は Giemon firmware (open-robo) + open-ot field tier (Mimi WAMR AOT) が owns; kuni-umi cells は touched しない (ADR-2605201400 §10 + 本 ADR §3 cadence_hz_max=10)。

## 6. Phase 4 Commissioning — 7 loops × kuni-umi

`CommissioningCell` on simeon が open-ot 7 loops を順次 commission:

| # | Loop | open-ot DID | Activation order | kuni-umi commission step |
|---|---|---|---|---|
| 4.1 | `:loop:pv-array-mppt-{id}` | per inverter | First (field-only, 1 Hz observation only) | smart inverter MPPT cell pin → open-denki `recordRenewableOutput` start |
| 4.2 | `:loop:bess-charge-discharge` | bess-1 | After BESS commissioning test | `cell:bess-pcs-1` (PID_LIMITED) + `cell:bess-soc-est-1` (SOC_KALMAN future) + `cell:bess-dispatch-coord` |
| 4.3 | `:loop:freq-droop` | aggregator | After all dispatchable assets online | `cell:freq-aggregator` + per-asset `cell:freq-droop-{asset}` (DROOP_P_F) |
| 4.4 | `:loop:volt-var` | per inverter | Parallel to 4.3 | `cell:vv-aggregator` + per-inverter `cell:vv-{inverter}` (VV_CURVE future) + `cell:ltc-tap-control` (LTC_TAP_FSM future) |
| 4.5 | `:loop:islanding-decision` | site-level | After 4.1–4.4 stable | `cell:island-decision` + `cell:gt-protect` (ANTI_ISLANDING_ROCOF) + `cell:bus-tie-fsm` (BLACK_START_SEQ future) |
| 4.6 | `:loop:dr-response` | site-level | After 4.5 | `cell:dr-distributor` (LangGraph-only) |
| 4.7 | `:loop:peak-shave-economic` | site-level | Last | `cell:dispatch-optim` + `cell:price-feed` + `cell:forecast-pv` + `cell:forecast-load` |

各 loop 起動後、open-ot の 90-day pilot acceptance (PROTOTYPE-MICROGRID.md §4) が始動。kuni-umi は `commissionDeployment` 書き込んで observer mode へ移行。

### S2 specific acceptance test (per-loop, kuni-umi side)

| Test | Pass criterion |
|---|---|
| Anti-islanding 100 ms latency | 4.5 commissioning で grid disconnect simulation → bus-tie open within 100 ms |
| Droop-P-f proportionality | 4.3 で grid frequency step 入力 → asset P 出力が droop curve に一致 (replay determinism guaranteed by FBType cell unit tests) |
| BESS SoC tracking accuracy | 4.2 で 24 h discharge cycle → SoC 推定誤差 < 3 % |
| Volt-Var setpoint convergence | 4.4 で voltage step → Q setpoint が ±2 % 以内に 60 s 以内収束 |
| DR fan-out latency | 4.6 で `recordDemandResponse` injection → 全 asset setpoint cascade within 5 s |
| Economic dispatch convergence | 4.7 で 24 h forecast based dispatch → realized cost が optimal の ±10 % 以内 |
| AMI smart-meter 80/80 online | 4.1 directly + Phase 3.7 出力で 80 meter が `recordMeterReading` を 1 h 以内に最初の reading 提出 |

## 7. Acceptance criteria (S2 → S3 exit gate)

| # | Criterion | Measure | Threshold |
|---|---|---|---|
| 1 | Phase 2 governance vote passes | 1 SBT = 1 vote 過半数 | YES |
| 2 | Phase 2 Public Fund grant approved | PublicFundGovernance.execute | YES |
| 3 | All 8 sub-phases of Phase 3 PASS witness audit | N≥2 witness signature mismatch count | 0 mismatches across all super-steps |
| 4 | Phase 3 construction injury count | `recordPhysicalAuditEvent` class=injury | 0 (human or robot) |
| 5 | Phase 3 ecology delta within bounds | `ecologyBaseline` post vs. pre | ΔimpactScore ≤ 10 |
| 6 | Phase 4 all 7 loops commissioned | `commissionDeployment` recorded | 7 / 7 |
| 7 | open-ot 90-day pilot acceptance | PROTOTYPE-MICROGRID.md §4 (zero unplanned islanding / ≥ 99 % orchestrator uptime / ≥ 95 % setpoint deadline / audit reconstructable) | per §4 thresholds |
| 8 | Tithe 10 % correctly routed to Public Fund | TitheRouter event log vs. payment plan | 100 % correct routing |
| 9 | All `commissionDeployment` records cross-linked to open-denki utility records | DID cross-link integrity | 100 % |
| 10 | Decommission plan registered with lifespanYears | `proposeDeploymentPlan.lifespanYears` ≥ 30 + `DecommissionCell` registered | YES |

10/10 PASS → S2 closed → S3 ADR (multi-utility integrated, electric + water + network on same site) can begin.

## 8. Risks + mitigations

| Risk | Severity | Mitigation |
|---|---|---|
| Hitogata v1 prototype が S2 timeline に間に合わない (open-robo 別 ADR) | High | S2 Phase 3.2/3.3 で carport canopy 上 install が遅延 → 3.6 substation を critical path に切替、Hitogata 必要箇所は **human installer + Otete crawler assist hybrid** に降格 (Charter Rider 三層 enforcement の counterparty filter は適用) |
| BoM cost が見積より 30 % 以上超過 | Medium | UNSPSC fleet が 3 種以上の supplier alternative を出すよう constraint; Public Fund overage は別 grant 申請 |
| 大学側 academic MoU が破談 | High | 候補 ≥ 3 機関と並行交渉; 1 つに依存しない。本 ADR は site DID 未確定で承認可 |
| 電気事業法 / 系統連系規程 で interconnection 不可 | Critical | Phase 2 で `localLawAttestationCid` (Steward Lv5+) + Council Lv6+ 確認; Sub-phase 3.8 で electric utility 立会い実施で final approval |
| Witness 8 Mimi base-station が同時 power outage | Medium | 各 Mimi に independent battery + LTE backup; 並行 Mimi cluster geographic distribution |
| 90-day open-ot pilot で zero-unplanned-islanding 達成不可 | High (open-ot side risk) | ANTI_ISLANDING_ROCOF cell (14 tests PASS) + BLACK_START_SEQ (future) + Council escalation on event |
| Council vote が反対 (governance reject) | Medium | Pre-vote socialization; revised plan + re-vote (ADR-2605192230 30 日 appeal window 同等の期間) |
| Robot DID 秘密鍵漏洩 (8 Mimi + 6 Otete + 2 Hitogata = 16 個) | Critical | 全 16 keys を macOS Keychain `service=etzhayyim, account=ROBOT_DID_KEY_{ID}` + 1Password mirror; rotation: quarterly per ADR-2605192415 §9; per-key isolation |

## 9. S2 budget (estimated, USDC)

| Item | Estimate (USDC) |
|---|---|
| Microgrid BoM (PV / BESS / substation / feeders / smart meters / grid-tie) | 1,500,000 – 2,000,000 |
| Construction labor + transport + permit fees | 200,000 – 400,000 |
| Robot fleet CAPEX (Hitogata × 2 + Otete × 5 + Mimi × 8) | ≈ 200,000 |
| Contingency (20 %) | 380,000 – 520,000 |
| **Total** | **≈ 2,280,000 – 3,120,000 USDC** |
| 10 % Tithe to Public Fund (auto-split) | 228,000 – 312,000 USDC |

Funding source: **Public Fund grant** (ADR-2605192145) + religious-corp Treasury。Public Fund grant 申請は Phase 2 governance vote と並行。

## 10. Out of scope (S2 explicit)

- **Water utility** (open-water lexicons) — S3 で multi-utility 統合
- **Network utility** (open-network lexicons) — S3 で multi-utility 統合
- **Multi-site fleet** (concurrent sites) — S4
- **Ocean / atmosphere / orbit deployments** — S5
- **Volt-VAR optimization** at multi-substation scale — open-ot 側で別 release (single-substation only)
- **JEPX market dispatch** — open-denki MVP scope 外 (ADR-2605201400 §10 reaffirms)
- **Customer billing** — religious-corp は site participants から **電気代を徴収しない** (donation-only model, ADR-2605192115)。energy cost recovery は (a) participant SBT-↔-SBT internal-subscription (ADR-2605192115 §3 carve-out) または (b) Public Fund operating grant の 2 path。S2 では (b) を default

# Consequences

## 正の効果

- religious-corp が **物理的 utility infrastructure を初めて自前で持つ** — labor_liberation pillar の真の field instantiation
- open-ot WASM PLC が field 配備される最初の機会 → IEC 61499 + WAMR AOT の production maturity 証明
- Giemon fleet が 1 Otete + 1 Mimi (S1) から 6 Otete + 8 Mimi + 2 Hitogata に scale → S3+ multi-utility に必要な fleet size 確立
- Public Fund grant の最初の large-scale disbursement (ADR-2605192145 validation)
- 80 smart-meter deployment → open-denki AMI substrate の真の load test
- N=2 witness invariant の cluster-wide enforcement パターン確立 (8 Mimi base-station による parallel coverage)

## 負の効果 / コスト

- USDC 2.3–3.1M deployment は religious-corp として large bet; site failure (commissioning fail / 90-day pilot fail) は treasury hit + reputational damage
- Hitogata v1 prototype が critical path: open-robo 別 ADR の timing と coupling
- 大学 academic MoU 交渉が長期化 → Phase 0 site DID 発行までに数ヶ月かかる可能性
- 10–12 week construction window 中 site で N=2 witness が必須 → Mimi RTU 8 機が連続運転 (battery + LTE 維持)、運用負荷高い
- 16 robot DID key の管理 (key rotation, key compromise scenario) が S1 の 2 key より一桁重い

## Constitutional 整合

| Charter article | S2 alignment |
|---|---|
| §mission.labor_liberation | ✅ 初の real-capital field deployment |
| §mission.robotics_universal | ✅ open-design Giemon fleet (Apache 2.0 + Rider) |
| §mission.ip_free_release | ✅ Charter Rider §2 gate at counterparty-classification |
| §mission.land_as_religious_trust | ✅ 大学 site は LandRegistry に donation/stewardship 経路で登録 |
| §mission.parallel_governance_to_state | ✅ 国 electric 事業法 と dual-recognition (utility 立会い + LandRegistry + LegalAttestation) |
| §mission.anti_individualism | ✅ governance vote 必須 + Public Fund evaluation 必須 |
| §mission.multi_generational_priority | ✅ lifespanYears ≥ 30 + DecommissionCell registered |
| §mission.no_state_military_alliance | ✅ counterparty-classification rule #2 |
| §mission.donation_only / 10 % tithe | ✅ TitheRouter 自動 split / 大学 participant は donor として contribute、徴収なし |

# Alternatives Considered

## A. S2 を smaller scale (100 kW class) にして risk 圧縮

100 kW class community microgrid。

- Pro: 予算 1/10 (≈ USDC 250k); Public Fund grant 不要; governance vote 不要 (population < 100 だが大学だと自動超過); single PV array + small BESS で BoM simple
- Con: open-ot PROTOTYPE-MICROGRID.md は **1 MW class** で 7 loops 全てを exercise する設計 → 100 kW では peak-shave-economic / volt-var / dr-response が under-exercise、S3 への smooth transition に validation 不十分
- **却下**: S2 の意味は "7 loops 全て end-to-end exercise" であり、scale 圧縮は milestone の価値を seriously dilute

## B. Industrial site を先に (university 後回し)

小規模工場 (300 kW class)。

- Pro: paying customer → revenue 自立性、religious-corp donation only 制約と独立
- Con: religious-corp は donation-only (ADR-2605192115)、industrial customer model は SBT-↔-SBT internal-subscription carve-out が要るが、開始時点で industrial customer SBT を持たない (= まず religious-corp に join してから internal-subscription contract)。手続き煩雑、initial pilot として overcomplicated
- **却下**: industrial site は S3 で multi-utility 文脈で再評価が natural

## C. Remote island grid を先に (Okinawa / Ogasawara)

- Pro: islanding が normal state → ANTI_ISLANDING_ROCOF / BLACK_START_SEQ が真の必須機能として exercised; "国家 utility 独占を漸近的に breaking" narrative が最も強い
- Con: 物流 / 認可 / partner 依存度高 (現地電力会社 + 自治体)、Phase 2 governance vote で外部 stakeholder 依存度が religious-corp 自身の意思決定権を制約しうる (`mission.payoff_to_etzhayyim_only` ↔ external dependency tension); religious-corp が S2 段階で remote island 規模を operate する operational capability に届いていない
- **却下**: S4 で再評価 (multi-site fleet 段階で operational maturity 達成後)

## D. Hitogata humanoid を S2 で使わず all-Otete + 人間 hybrid

- Pro: Hitogata v1 prototype の critical-path 依存を解消
- Con: 高所作業 (carport canopy 上) で人間 worker が登る必要 → 物理 risk (墜落) + religious-corp の labor_liberation mission との semantic tension (人間に危険な労働を依然として依頼している)。Charter Rider Wellbecoming subordination gate に touch
- **採用 (mitigation として)**: Hitogata 遅延時 fallback として **人間 worker + safety harness + Otete crawler material delivery hybrid** を許容、ただし `recordPhysicalAuditEvent` で `community-event` subtype=`human-worker-engagement` を transparency 記録 + injury 発生時 Phenotype.effectiveMultiplier penalty (responsible chain)

# Open Questions

1. **University academic MoU 具体機関** — 候補 ≥ 3 機関の identity は本 ADR 範囲外。Decision: Council Lv6+ で別途確定、site DID 発行時 ADR-2605201600-amendment-1 で reference
2. **Hitogata v1 prototype timeline** — open-robo 別 ADR で発注。Decision (本 ADR): S2 Phase 2 開始までに Hitogata v1 prototype が field-deployable でない場合、§Alternative D fallback を発動
3. **電気事業法 specific approval path** — 系統連系 等 自家発電設備 区分の最新解釈。Decision: Phase 2 で 電気保安協会 + 経産省 出向相談 → `localLawAttestationCid` 取得
4. **Robot DID key rotation timing** — 16 keys を quarterly rotate するのは ops burden 高。Decision (本 ADR): quarterly maintain、ただし rotation を 4 群に分けて月次 staggered rotation で operational load を平準化
5. **Public Fund grant size limit** — ADR-2605192145 が single grant size limit を明示していない。Decision: 本 ADR で USDC 3.1M grant が許容範囲か Council Lv6+ で別途決定; 超過する場合は multi-tranche disbursement (milestone escrow)
6. **S2 完了後 site の長期 operational ownership** — religious-corp が直接 operate するか、site steward 集団 (大学側 + 構成員) に operational stewardship を委ねるか。Decision (本 ADR): 後者 (operational stewardship 委譲、religious-corp は audit witness + DecommissionCell 管轄のみ retain)

# References

- ADR-2605201400 (kuni-umi master spec)
- ADR-2605201500 (S1 — solo survey)
- ADR-2605151200 (open-ot WASM PLC) + `60-apps/etzhayyim-project-open-ot/PROTOTYPE-MICROGRID.md` (target asset / loop catalog)
- ADR-2605171300 (UNSPSC agent fleet — Phase 2 BoM generation)
- ADR-2605172100 (Payments on-chain only — milestone escrow + USDC)
- ADR-2605172300 (Treasury bi-asset substrate)
- ADR-2605192130 (Tithe 10 % redistribution)
- ADR-2605192145 (Public Fund grant evaluation — S2 funding path)
- ADR-2605192200 (Charter Rider v2.0 — counterparty gate)
- ADR-2605192230 (Three-tier enforcement — governance vote path)
- ADR-2605192300 (Bootstrap Council 5 名 — Phase 2 sign-off)
- `60-apps/etzhayyim-project-open-denki/CLAUDE.md` (CIM record SSoT for asset DIDs)
- `60-apps/etzhayyim-project-open-robo/CLAUDE.md` (Giemon hardware roadmap, Hitogata 発注)
