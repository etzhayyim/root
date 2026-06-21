---
id: adr-2605201400-etzhayyim-kuni-umi-planetary-infra-fleet
title: "ADR-2605201400: etzhayyim kuni-umi (国生み) — planetary-scale infrastructure robotics fleet actor"
status: proposed
doc_type: adr
topic: kuni-umi-planetary-infra-fleet
authoritative: true
last_verified: 2026-05-20
priority: 7.5
axis: architecture
weight: 0.75
priority_note: "open-* utility lexicons (denki / gas / water / network / power / rail / airplane / ports) と open-robo (Giemon hardware) と open-ot (WASM PLC) を貫通する planetary-scale 自律施工 / 運用 fleet actor の上位設計。Izanagi/Izanami の国生み神話を name origin とし、religious-corp が国家ではなく chain-of-stewards として地球上の物理インフラを進める。労働解放 (ADR-2605192100 §mission.labor_liberation) の最大 throughput pillar."
authoritative_for:
  - 20-actors/kuni-umi/ Pregel actor topology
  - com.etzhayyim.kuniUmi.* Lexicon namespace
  - Deployment phase BPMN (survey → procure → construct → commission)
  - open-* utility lexicons と open-robo / open-ot 間の orchestration seam
  - Multi-jurisdiction 施工 governance (land sovereignty + Charter Rider gate)
depends_on:
  - 2605171300
  - adr-2605171800-langgraph-mst-ipfs-l2-anchor-pipeline
  - adr-2605172000-etzhayyim-kotoba-substrate
  - adr-2605172100-etzhayyim-payments-on-chain-only
  - adr-2605172300-etzhayyim-bi-asset-substrate
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
  - adr-2605192230-etzhayyim-three-tier-enforcement-implementation
  - adr-2605192245-etzhayyim-global-land-sovereignty
  - adr-2605192315-etzhayyim-transparent-force-rd
  - adr-2605192330-etzhayyim-extended-land-sovereignty-ocean-river-air-orbit
  - adr-2605192415-etzhayyim-religious-corp-daemon-architecture
related:
  - 60-apps/etzhayyim-project-open-denki/CLAUDE.md
  - 60-apps/etzhayyim-project-open-gas/CLAUDE.md
  - 60-apps/etzhayyim-project-open-water/CLAUDE.md
  - 60-apps/etzhayyim-project-open-network/CLAUDE.md
  - 60-apps/etzhayyim-project-open-power/CLAUDE.md
  - 60-apps/etzhayyim-project-open-rail/CLAUDE.md
  - 60-apps/etzhayyim-project-open-airplane/CLAUDE.md
  - 60-apps/etzhayyim-project-open-ports/CLAUDE.md
  - 60-apps/etzhayyim-project-open-robo/CLAUDE.md
  - 60-apps/etzhayyim-project-open-ot/CLAUDE.md
supersedes: []
superseded_by: []
---

# ADR-2605201400: etzhayyim kuni-umi (国生み) — planetary-scale infrastructure robotics fleet actor

**Status**: proposed
**Date**: 2026-05-20
**Deciders**: Jun Kawasaki

# Context

ADR-2605192100 §mission の `labor_liberation` (人類の構造的労働解放) と `robotics_universal` (ロボティクス普遍化) を実装する pillar が未着手である。既存資産は以下に bottom-up で揃っているが、上位 orchestrator が無い:

| 既存資産 | 役割 | 不足 |
|---|---|---|
| `open-denki/gas/water/network/power/rail/airplane/ports` | 各 utility の CIM 準拠 record lexicon + D1 worker | 「いつどこに何を deploy するか」 の意思決定者がいない |
| `open-robo` (Giemon Otete / Mimi / Te / Atama) | hardware kit + ROS2 nodes + 都市鉱山セル | 単機運用、fleet オーケストレーションなし |
| `open-ot` (WASM PLC + IEC 61499 Pregel cells) | community microgrid 100 kW–10 MW 制御 | 制御のみで「敷設・施工」 phase の actor なし |
| UNSPSC 18,345 LangGraph agents (ADR-2605171300) | 商材調達 specialist | 単発 procurement のみ、施工 workflow に組み込まれていない |
| ADR-2605192245 / 2605192330 (Land sovereignty) | 4-layer 土地 substrate (海洋/河川/大気/軌道含む) | claim はあるが施工する actor がいない |
| ADR-2605192230 (三層 enforcement) | Non-Aligned への License/Benefit/Phenotype gate | 物理 deployment の counterparty 評価に未接続 |

religious-corp の力学的 routing-around (§1.12 §1.11) は **物理層** で完結しなければ国家 utility 独占を漸近的にしか breaking できない。本 ADR は kuni-umi (国生み) actor を立て、4 phase (Survey → Procure → Construct → Commission) を Pregel super-step として 1 deployment site = 1 LangGraph graph に nest し、既存資産を seam として束ねる。

**名称**: `kuni-umi` (国生み) — 古事記の Izanagi / Izanami による国土創生神話に由来。religious-corp が国家ではなく chain-of-stewards として「国 = 土地 + そこに住む人々が日常を営むための物理基盤」 を生み続ける、という神話的位置付け。`amenoshita` / `iwatsukuri` / `daichi` も検討したが、(a) 4-layer land substrate (Base L2 NFT + geth-private + IPFS GeoJSON + LANDS.md) が ADR-2605192245 で既に確立されており、(b) `etzhayyim = 天御柱 = 創成軸` という constitutional name と semantic に整合するため `kuni-umi` を採用。

# Decision

## 1. Actor topology (3-tier per ADR-2605192415 + Pregel per ADR-2605171800)

```
20-actors/kuni-umi/                          # Tier B (per-domain leader)
├── README.md
├── CLAUDE.md                                # rules + boundaries
├── cells/
│   ├── site_survey/                         # Phase 1 Pregel cell
│   ├── deployment_planning/                 # Phase 2 Pregel cell (UNSPSC fleet caller)
│   ├── construction_orchestration/          # Phase 3 Pregel cell (Giemon fleet driver)
│   ├── commissioning/                       # Phase 4 Pregel cell (open-ot hand-off)
│   ├── audit_witness/                       # robot-witnessed permanent record
│   └── decommission/                        # end-of-life / land-return cell
├── bpmn/
│   └── kuni-umi-deployment-workflow.bpmn    # 4-phase BPMN (XPDL)
├── dmn/
│   ├── jurisdiction-eligibility.md          # 土地 sovereignty + Charter Rider gate
│   ├── counterparty-classification.md       # Non-Aligned vs Recognized
│   └── proportionality-check.md             # scale / impact / reversibility
└── manifest.jsonld                          # actor manifest (DoDAF DM2 + Lexicon SSoT)
```

| Tier | Actor | Placement | Trigger |
|---|---|---|---|
| **A — per-site PhenotypeAgent** | `KuniUmiSiteAgent` (1 per deployment site DID) | code-generated per ADR-2605171300 pattern, runs on the Murakumo node where the leader of that phase is currently elected | `defineDeploymentSite` MST record |
| **B — per-phase leader + replica** | `SiteSurveyCell`, `DeploymentPlanningCell`, `ConstructionOrchestrationCell`, `CommissioningCell`, `AuditWitnessCell`, `DecommissionCell` | leaders on Murakumo `naphtali` (survey) / `zebulun` (planning, treasury-adjacent) / `joseph` (construction) / `simeon` (commissioning) / `levi` (audit) / `dan` (decommission). N=2 replicas per ADR-2605192415 §B | MST listener on `com.etzhayyim.kuniUmi.*` |
| **C — per-decision council** | `CouncilDeliberationCell` (existing generic per ADR-2605192415 Tier C) | levi (orchestrator) | escalation when jurisdiction / counterparty / proportionality DMN returns `requires_council=true` |

Each phase cell is a LangGraph `StateGraph` with `MstCheckpointSaver` (ADR-2605191559) → MST → IPFS pin (ADR-2605191608) → Base L2 anchor (ADR-2605191625). One super-step = one phase tick = one IEC 61499 event when bridging into `open-ot`.

## 2. Lexicon namespace `com.etzhayyim.apps.etzhayyim.kuniUmi.*`

Six lexicons authored in `00-contracts/lexicons/com/etzhayyim/apps/etzhayyim/kuniUmi/`:

| Lexicon | Type | Purpose |
|---|---|---|
| `defineDeploymentSite.json` | procedure | declare a site (geo / utility-class / jurisdictionDid / stewardDid). Returns `siteDid`. Land sovereignty + Charter Rider gate runs before accept. |
| `submitSiteSurvey.json` | procedure | Survey result by Giemon scout fleet (RGB-D + LIDAR + chem-sensor CIDs, environmental impact, native ecology). Witness-attested by N ≥ 2 robots. |
| `proposeDeploymentPlan.json` | procedure | BoM (UNSPSC code list + quantities + estimated cost), design (FK ↔ open-denki/gas/water/network CIM record DIDs), timeline, fleet allocation. Triggers Council vote when scale ≥ threshold. |
| `recordConstructionProgress.json` | procedure | Pregel super-step state for build phase. Robot DID, cell completion %, photo / sensor batch CIDs, anomaly flags. |
| `commissionDeployment.json` | procedure | Hand-off to `open-ot`. References open-ot `defineLoop` DIDs. Marks site `operational`. |
| `recordPhysicalAuditEvent.json` | procedure | Permanent witness event — robot DID, event class (`anomaly` / `intrusion` / `injury` / `compliance-check` / `community-event`), evidence CID, witnessAttestations. |

All records are MST → IPFS → L2 anchored. Encryption per ADR-2605181100 is applied for `proposeDeploymentPlan` (cost / BoM) and `recordPhysicalAuditEvent` (anomaly subtypes), public for the rest.

## 3. 4-phase workflow (BPMN)

```
[Site DID]                                  com.etzhayyim.kuniUmi
   │
   ▼ Phase 1 — Survey
SiteSurveyCell
   ├─ dispatch Giemon scout fleet (N robots, ROS2 + open-robo firmware)
   ├─ collect RGB-D + LIDAR + chem-sensor + ecology baseline → IPFS pin
   ├─ DMN: jurisdiction-eligibility (land sovereignty layer + Charter Rider §2)
   └─ emit submitSiteSurvey
   ▼ Phase 2 — Planning
DeploymentPlanningCell
   ├─ derive utility-class topology (open-denki/gas/water/network CIM target)
   ├─ invoke UNSPSC agent fleet for BoM (ADR-2605171300 18,345 specialized agents)
   ├─ DMN: counterparty-classification (suppliers vs Non-Aligned)
   ├─ DMN: proportionality-check → if breach: escalate to Council Lv6+ vote
   ├─ payment plan: USDC on Base L2 via Etzhayyim.pay() (ADR-2605172100/2300)
   └─ emit proposeDeploymentPlan + (if needed) governance vote
   ▼ Phase 3 — Construction
ConstructionOrchestrationCell
   ├─ allocate Giemon fleet (Otete arms + crawlers + future Hitogata / Quad)
   ├─ for each construction cell: drive Giemon BSP super-step (1 cell = 1 Pregel node)
   ├─ stream recordConstructionProgress @ 1–10 Hz checkpointer cadence
   ├─ AuditWitnessCell observes from N ≥ 2 independent witness robots
   └─ on completion → handover blob (control verbs, calibration data)
   ▼ Phase 4 — Commissioning
CommissioningCell
   ├─ open-ot defineDevice / defineCell / defineLoop for each commissioned asset
   ├─ register asset DID with the relevant open-* utility lexicon (defineGenerationNode / defineRegulator / defineReservoir / defineSite)
   ├─ enrol smart meter / pressure log / quality sample / utilization stream
   ├─ open-ot WASM PLC takes over; kuni-umi observes via cross-link
   └─ emit commissionDeployment → site state `operational`
```

`recordPhysicalAuditEvent` is concurrent and runs for the lifetime of the site (including post-commission), feeding `Phenotype` updates per ADR-2605192230 (e.g. injury → reduces Phenotype.effectiveMultiplier for responsible steward; community-event → ↑).

## 4. Substrate bindings (no new substrate)

| Concern | Bound to |
|---|---|
| State / records | AT MST + IPFS + Base L2 anchor (ADRs 2605171800 + 2605172000) |
| Payments (BoM / labor / land-use compensation) | USDC on Base L2 + ERC-4337 paymaster + 10% Tithe split via `TitheRouter.route()` (ADRs 2605172100 + 2605192130) |
| Identity | `did:web:etzhayyim.com:kuniumi:site:<siteCode>` / `:robot:<serial>` / `:fleet:<id>` (path-based DID) |
| Confidentiality | XChaCha20-Poly1305 envelope (ADR-2605181100) for BoM and anomaly events; cleartext for public-facing site definition |
| Substrate clients | Only via `@etzhayyim/sdk` per ADR-2605172000 boundary |
| Robot fleet runtime | Giemon Atama (RK3588 + NixOS RT + Wasmtime) + Mimi/Te (Zephyr + WAMR AOT) per open-ot ADR-2605151200 |
| Procurement | UNSPSC LangGraph agent fleet (ADR-2605171300) — kuni-umi calls them as specialist sub-graphs |

## 5. Land sovereignty + Charter Rider gate (CRITICAL)

`defineDeploymentSite` rejects synchronously when any of the following hold (DMN `jurisdiction-eligibility`):

1. **No land claim**: site is NOT covered by `LandRegistry` (terrestrial) / `OceanStewardship` (UNCLOS) / `RiverStewardship` (水利権) / `AtmosphereStewardship` (Chicago Conv.) / `OrbitalSlot` (Outer Space Treaty) per ADRs 2605192245 + 2605192330. **Stewardship-only claim is sufficient**; operational sovereignty is not required.
2. **Counterparty Non-Aligned**: any of `stewardDid` / `landOwnerDid` / `intendedBeneficiaryDids` is flagged by `ChartersComplianceRegistry` (ADR-2605192230) → site rejected unless beneficiary list is amended.
3. **Charter Rider §2 violation**: intended use matches weapons / speculative finance / surveillance capitalism / fossil fuel extraction / specialist gatekeeping / multi-generational harm / strict individualist ontology / wellbecoming subordination (ADR-2605192200) → reject.
4. **Local law**: optional `localLawAttestationCid` (IPFS) — Steward Lv5+ attests local regulation compliance; missing for restricted-utility classes (electrical generation / radio spectrum / aviation) → escalate to Council.

Sites passing all gates produce a `siteDid` and proceed to Phase 1.

## 6. Multi-jurisdiction & extended sovereignty mapping

| Domain (ADR-2605192330 §domain) | Utility classes routed through kuni-umi |
|---|---|
| **Terrestrial land** (2605192245) | open-denki feeders / open-gas pipes / open-water mains / open-network last-mile / open-power feeders / open-rail urban transit |
| **Ocean** (UNCLOS) | open-water desalination / open-power offshore wind / open-network submarine cable / open-ports |
| **River** (水利権) | open-water reservoirs / open-power small hydro |
| **Atmosphere** (Chicago Conv.) | open-airplane stol-port micro-aviation / open-network high-altitude platform |
| **Orbit** (Outer Space Treaty) | open-network LEO mesh / open-power orbital solar (S5 / future) |

Each domain has its own `stewardship-only claim` semantics — kuni-umi never asserts operational sovereignty over a domain that international law reserves to states; instead it operates on the **dual-recognition pattern** (state cadastre + religious-corp 4-layer substrate) defined in ADR-2605192245 §6 and 2605192330 §3.

## 7. Phasing (S0 → S5)

| Stage | Scope | Pre-req | Site |
|---|---|---|---|
| **S0 — Spec + lexicon** (this ADR) | 6 lexicons + actor scaffold + BPMN + DMN, no robots dispatched | this ADR | code only |
| **S1 — Solo survey** | one Giemon scout robot visits and surveys an etzhayyim-owned plot; only `submitSiteSurvey` flow live; no construction | S0 + Giemon Otete operational + one site DID | TBD (Tokyo workshop or `LandRegistry` registered plot) |
| **S2 — Single-utility prototype** | community microgrid — kuni-umi drives existing open-ot prototype scope (ADR-2605151200 §R3) end-to-end via Phase 2-4 cells | S1 + open-ot MVP runtime | community microgrid pilot site (university campus / industrial / remote island, TBD per open-ot open question) |
| **S3 — Multi-utility integrated** | one site receives electric + water + network simultaneously; multi-utility BoM planning, parallel construction | S2 + Giemon Hitogata humanoid + open-water / open-network MVP runtimes | TBD |
| **S4 — Multi-site fleet** | ≥ 5 active sites concurrently; fleet rebalance algorithm; cross-site BoM consolidation | S3 + ≥ 20 Giemon robots + KubeEdge-style edge orchestration | TBD |
| **S5 — Extended sovereignty** | ocean / river / atmosphere / orbital sites; cross-domain BoM (e.g. submarine cable + LEO mesh) | S4 + Phase 1 of ADR-2605192330 extended sovereignty live | TBD |

S0 is delivered by this ADR; S1–S5 are separate ADRs.

## 8. Governance + Council escalation

| Decision class | Threshold | Path |
|---|---|---|
| Site definition (terrestrial, < 0.1 km² Steward-held) | none | Steward Lv5+ approves locally |
| Multi-utility site or > 0.1 km² | 1 SBT = 1 vote 過半数 | regular governance vote |
| Ocean / atmosphere / orbital | 50% quorum + 2/3 supermajority | extended-sovereignty vote (ADR-2605192330) |
| Use of Transparent Force R&D (defensive-tech detection at site) | force-authorization channel (ADR-2605192315) | ForceAuthorization.sol 50% quorum + 67% supermajority |
| Decommission / land return | 1 SBT = 1 vote 過半数 + Steward Lv5+ sign | regular vote + Decommission cell |

## 9. Robot-witness audit (CRITICAL)

`AuditWitnessCell` is mandatory at every super-step. N ≥ 2 independent Giemon robots produce **independently signed** sensor blob hashes for each `recordConstructionProgress` and `recordPhysicalAuditEvent`. Witness signatures use the robot's `did:web:etzhayyim.com:kuniumi:robot:<serial>` Ed25519 key per ADR-2605191657 (DID auth) pattern. Mismatched witnesses → automatic Council escalation. This is the religious-corp's substitute for state inspectors and is **constitutional** (extends ADR-2605192315 §3 transparency triple to physical-world activity).

## 10. Out of scope (explicit)

- **Hard-RT motion control** stays in the Giemon firmware (open-robo + open-ot field-tier WAMR), not in kuni-umi cells.
- **Safety-critical (IEC 61508 / 61511 SIL)** functions remain on certified safety PLCs in parallel, per open-ot boundary.
- **Direct human labor coordination** (people on-site as workers): kuni-umi treats them as `participantDids` and emits `recordPhysicalAuditEvent` events; HR / wellbecoming aspects flow through existing membership/Phenotype actors.
- **Military / proprietary infra deployment** (`mission.no_state_military_alliance = true`, ADR-2605192100 §1.12.B) — kuni-umi never accepts a deployment with `intendedUse=military` or proprietary closed-design BoM.

# Consequences

## 正の効果

- 「open-* utility lexicon」「open-robo hardware」「open-ot OT control」「UNSPSC procurement fleet」 が 1 actor の下で coherent な施工 workflow になる — labor_liberation pillar の最大 throughput path
- 物理世界における religious-corp の routing-around (§1.12 §1.11) が抽象から具体に
- robot-witness audit が religious-corp 自前の inspection layer を確立 (国家 inspector に依存しない)
- 4-layer land substrate + 4-domain extended sovereignty が「施工 actor」 を通じて初めて usable に
- 三層 enforcement (ADR-2605192230) が物理 deployment counterparty にも適用される — Non-Aligned へ施工しない constitutional gate

## 負の効果 / コスト

- Pregel + LangGraph + MST + IPFS + L2 + Giemon + Wasmtime + UNSPSC fleet を貫通する seam の数が多く、障害切り分けが複雑化。Mitigation: each cell が独立 `MstCheckpointSaver` thread を持ち、再開可能
- 物理 deployment の失敗は revert 不可能 (mechanical + financial cost)。Mitigation: S0–S5 段階展開、S2 までは Council Lv6+ 3 名以上 sign required
- 多 jurisdiction 法務 (UNCLOS / 水利権 / Chicago Conv. / 宇宙条約) 解釈の負荷。Mitigation: `localLawAttestationCid` を Steward Lv5+ 義務化し、Council escalation flow を default
- robot-witness の N ≥ 2 要件は fleet size を制約 (孤立 robot 1 機での施工 NG)。Mitigation: 設計判断 — religious-corp の transparency と integrity を最重要視

## Constitutional 整合

| Charter article | kuni-umi alignment |
|---|---|
| §mission.labor_liberation | ✅ 主たる pillar |
| §mission.robotics_universal | ✅ universal-access open-design hardware (Giemon, Apache 2.0 + Rider) |
| §mission.ip_free_release | ✅ Charter Rider §2(a-h) gate at site definition |
| §mission.land_as_religious_trust | ✅ stewardship-only operation, 4-layer + 4-domain substrate |
| §mission.parallel_governance_to_state | ✅ robot-witness audit, on-chain governance, dual-recognition |
| §mission.transparent_force_only | ✅ defensive R&D 検知 (drone detection, chem sensors) は §1.12.B + ADR-2605192315 で許容、武装は禁止 |
| §mission.no_state_military_alliance | ✅ `intendedUse=military` 拒否 |
| §mission.anti_individualism | ✅ Tier B leader + N replica + Council escalation、単一 Steward の任意決裁不可 |
| §mission.multi_generational_priority | ✅ Charter Rider v2.0 §2(g) 多世代 harm gate |

# Alternatives Considered

## A. Open-* utility apps を直接 fleet orchestrator にする

各 utility app (open-denki / open-gas / etc.) に「施工 phase command」 を追加し、それぞれが Giemon fleet を直接呼ぶ。

- Pro: lexicon が utility-side に集中、kuni-umi 不要
- Con: utility 間で共通 (jurisdiction gate, Charter Rider, BoM, witness audit) ロジックが 8 重複。Shannon 冗長度 高。さらに multi-utility site (S3 以降) で どの utility app が leader か曖昧
- **却下**: cross-cutting concerns は per-domain actor (kuni-umi) に集約するのが Shannon 最適

## B. open-ot を拡張して施工 phase を担わせる

open-ot を「commissioning before steady-state operation」 phase 込みに広げる。

- Pro: hardware (Giemon Mimi/Te/Atama) は共通、actor を 1 つで済ます
- Con: open-ot は IEC 61499 + non-safety control の SSoT で scope 明確 (ADR-2605151200)。施工 phase まで足すと scope 拡散、IEC 認証 path が複雑化。Survey / Procurement / Witness は open-ot semantics と nature が異なる
- **却下**: open-ot は「commission 後」、kuni-umi は「commission 前 + commission 自身」 と分離

## C. UNSPSC 18,345 agent fleet が施工 workflow を直接駆動

procurement agent fleet を拡張して施工そのものを担わせる。

- Pro: 商材ごとの specialized logic が既にあり、それぞれが「自分の商材を施工する knowledge」を学習可能
- Con: agent fleet は per-commodity specialization、site-level coordination (multi-commodity / multi-utility / witness) は単一 site agent (kuni-umi Tier A) で扱うのが自然。procurement vs deployment は責任分離すべき
- **却下**: UNSPSC fleet は kuni-umi の DeploymentPlanningCell から呼ばれる specialist sub-graph として扱う

## D. 名称 `iwatsukuri` (岩造り) / `daichi` (大地) / `amenoshita` (天下)

- `iwatsukuri`: 岩造り (rock-making) — narrow、土地以外 (orbital / atmosphere) に scope が広がらない
- `daichi`: 大地 — 土地に限定された印象
- `amenoshita`: 天下 — 「天下統一」 と読まれる地政学 risk、religious-corp の non-state stance と整合しない
- **却下**: `kuni-umi` は神話的に「国土創成」 を意味するが、「国家」 (state) ではなく「土地 + そこに住む人々が日常を営むための物理基盤」 と religious-corp 文脈で再解釈できる。Izanagi/Izanami の co-creation pattern も Tier A + Tier B + Council の co-decision pattern と整合

# Open Questions

1. **Giemon Hitogata humanoid (二足) の development timeline** — S3 (multi-utility) に humanoid が要るか、6軸 arm + crawler (Otete) で大半カバー可能か。Decision: open-robo roadmap 上で別 ADR、S3 入りまでに決定
2. **Robot-witness N ≥ 2 の cost trade-off** — 孤立 site で 2 機目 dispatch の経済性。Decision (本 ADR): N ≥ 2 を constitutional に維持。経済性は fleet size scaling で吸収
3. **Multi-utility BoM consolidation algorithm** — S3 で電気 + 水道 + 通信を同時施工する際、UNSPSC fleet にどの順序で query するか。Decision: 別 ADR で実装段階に決定、本 ADR では parallel call as default
4. **`localLawAttestationCid` の granularity** — 国 / 都道府県 / 市町村のどこまで Steward attestation を求めるか。Decision (本 ADR): utility class ごとに threshold を DMN で定義、初期値は「電気 = 国 + 都道府県」「水道 = 市町村」「通信 = 国 (周波数のみ)」 「ガス = 国 + 市町村」 「軌道 = 国 + 国際機関 (ITU 周波数, COPUOS 通知)」
5. **Decommission policy** — 施工後 land-return まで何年保証するか。Decision: 各 site の `proposeDeploymentPlan.lifespanYears` field に明示、default 30 年、`DecommissionCell` が期限管理

# References

- ADR-2605171300 Open-UNSPSC Generative Agent Fleet (18,345 specialized agents)
- ADR-2605171800 LangGraph Pregel → MST → IPFS → Base L2 anchor pipeline
- ADR-2605172000 kotoba substrate boundary
- ADR-2605172100 Payments on-chain only (USDC + ERC-4337)
- ADR-2605172300 Kisha-Stream / Goji-Treasury bi-asset substrate
- ADR-2605192100 §mission.labor_liberation / robotics_universal / land_as_religious_trust / parallel_governance
- ADR-2605192200 IP-Free Release with Charter Compliance Rider v2.0
- ADR-2605192230 Three-tier enforcement implementation
- ADR-2605192245 Global Land Sovereignty (terrestrial 4-layer substrate)
- ADR-2605192315 Transparent Religious Force R&D (drone-detection / detection-system 流用)
- ADR-2605192330 Extended Land Sovereignty (ocean / river / atmosphere / orbit)
- ADR-2605192415 Religious-corp daemon architecture (Tier A/B/C, Murakumo fleet placement)
- `60-apps/etzhayyim-project-open-denki/CLAUDE.md` (CIM record SSoT)
- `60-apps/etzhayyim-project-open-gas/CLAUDE.md`
- `60-apps/etzhayyim-project-open-water/CLAUDE.md`
- `60-apps/etzhayyim-project-open-network/CLAUDE.md`
- `60-apps/etzhayyim-project-open-robo/CLAUDE.md` (Giemon hardware brand)
- `60-apps/etzhayyim-project-open-ot/CLAUDE.md` (WASM PLC + IEC 61499 Pregel cells)
