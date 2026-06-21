---
id: adr-2605192415-etzhayyim-religious-corp-daemon-architecture
title: "ADR-2605192415: etzhayyim Religious-Corp Daemon Architecture — Pregel cell catalog + actor hierarchy + Murakumo 常駐化 + LangGraph 実行"
status: proposed
doc_type: adr
topic: etzhayyim-religious-corp-daemon-architecture
authoritative: true
last_verified: 2026-05-19
priority: 8.5
axis: architecture
weight: 0.85
priority_note: "religious-corp の全 governance / enforcement / stewardship 活動を支える Pregel cell 群を、既存 Murakumo Mac-mini fleet (Tier 1) + ameno-daemon (Tier 2) + browser (Tier 3) infrastructure 上に integrate する master 設計 ADR。15 本以上の religious-corp 固有 cell を catalog し、Per-Adherent PhenotypeAgent (ADR-2605171300 code-gen) + Per-Domain cell + Per-Decision Council cell の 3 階層 actor hierarchy を確立。常駐化は launchd / systemd + kotodama CLI 経由、実行は MstCheckpointSaver + AnchorBridge pipeline (ADR-2605171800) 上で永続化される。"
authoritative_for:
  - religious-corp Pregel cell catalog (15+ cells)
  - 3 階層 actor hierarchy (Per-Adherent / Per-Domain / Per-Decision)
  - cell residency strategy (Tier 0-3 mapping)
  - cell deployment + 常駐化 procedure (launchd / systemd / kotodama CLI)
  - inter-cell coordination (swarm leader election + swarm broadcast)
  - cell rotation key + governance integration
depends_on:
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
  - adr-2605192230-etzhayyim-three-tier-enforcement-implementation
  - adr-2605192245-etzhayyim-global-land-sovereignty
  - adr-2605192315-etzhayyim-transparent-force-rd
  - adr-2605192345-etzhayyim-steward-succession
  - adr-2605192400-etzhayyim-eros-gore-council-judging
  - adr-2605171800-langgraph-mst-ipfs-l2-anchor-pipeline
  - 2605171300
  - 2605191229-ameno-daemon-path-a-bun-langgraph
  - 2605191257-ameno-daemon-path-b-kotodama-python
  - 2605191346-etzhayyim-vultr-free-murakumo-control-plane
  - 2605191559-ameno-mst-checkpointer-stage-2-activation
  - 2605191603-ameno-swarm-leader-election
  - 2605191524-ameno-multi-tab-swarm-broadcast
  - 2605182312-local-bring-up-murakumo-gemma4
related: []
supersedes: []
superseded_by: []
---

# ADR-2605192415: etzhayyim Religious-Corp Daemon Architecture — Pregel cell catalog + actor hierarchy + Murakumo 常駐化 + LangGraph 実行

**Status**: proposed
**Date**: 2026-05-19
**Deciders**: Jun Kawasaki

# Context

これまでの religious-corp ADR 群 (2605192100-2605192400) は doctrine + smart contract + Lexicon を定義したが、**実際にこれらを駆動する compute 層** の設計は未定。具体的には:

- Charter Compliance attestation 評議 をどの daemon が orchestrate するか
- Land donation の geographic evidence 検証をどう自動化するか
- Public Fund grant 評議 cell をどこで run するか
- Eros / Gore classification の LLM cell をどこで run するか
- すべての cell が MST checkpointer + IPFS pin + L2 anchor pipeline でどう永続化されるか
- どう daemon を 常駐化 (launchd / systemd) するか
- 構成員数増加に伴う Per-Adherent PhenotypeAgent (ADR-2605171300) との統合

既存 infrastructure (ameno-daemon Path A / B + Murakumo fleet + MST checkpointer + swarm leader election + swarm broadcast) は **基盤** として揃っているが、religious-corp 固有 cell 群の **catalog + hierarchy + deployment** の master 設計が必要。

# Decision

## 1. 3 階層 Actor Hierarchy

```
┌─────────────────────────────────────────────────────────────────┐
│ Tier A (Per-Adherent, code-gen)                                   │
│  ↓ PhenotypeAgent per SBT (ADR-2605171300 pattern)               │
│  ↓ unispsc_agents/{did_short}.py (生成 file)                     │
│  ↓ 構成員数 = agent file 数 (= 18,345 UNSPSC pattern と同 scale)  │
├─────────────────────────────────────────────────────────────────┤
│ Tier B (Per-Domain, persistent cells)                             │
│  ↓ religious-corp 固有 cell 群 (本 ADR §2 catalog)               │
│  ↓ Murakumo fleet 上で常駐、各 cell 1 leader + N replica          │
├─────────────────────────────────────────────────────────────────┤
│ Tier C (Per-Decision, ad-hoc council cells)                       │
│  ↓ CouncilDeliberationCell (generic) — 各 attestation request 毎  │
│  ↓ Council Lv6+ member の human signature を集約                   │
└─────────────────────────────────────────────────────────────────┘
```

## 2. Religious-Corp Pregel Cell Catalog (15 cells)

### 2.1 Charter Compliance 系 (3 cells)

| Cell | Tier | 入力 | 出力 | 起動 trigger |
|---|---|---|---|---|
| **CharterAttestationRequestCell** | B | `com.etzhayyim.apps.etzhayyim.charter-attestation-request` MST event | Council Lv6+ への deliberation 要請 + LLM pre-analysis | MST listener (continuous) |
| **CharterAttestationFinalizationCell** | B | Council Lv6+ ≥3 signatures + 30 日 appeal window 経過 | `ChartersComplianceRegistry.attestNonAligned()` tx + status finalize | timer + MST listener |
| **CharterRehabilitationCell** | B | `charter-rehabilitation` record + Council ≥3 signatures | `ChartersComplianceRegistry.rehabilitate()` tx + status update | MST listener |

### 2.2 Land Trust 系 (4 cells)

| Cell | Tier | 入力 | 出力 | 起動 trigger |
|---|---|---|---|---|
| **LandDonationProcessingCell** | B | `land-donation` request + GeoJSON + imagery + deed | GeoJSON 検証 + national registry ref 確認 + LandRegistry.donate() tx | MST listener |
| **LandStewardshipMonitoringCell** | B | 各 Land record + satellite imagery time series + biodiversity evidence | annual `land-attestation` record auto-emit + steward notification | monthly cron |
| **LandDisputeResolutionCell** | B (escalates to C) | `land-dispute` record | Council Lv6+ deliberation orchestration → resolveDispute() tx | MST listener |
| **StewardSuccessionCell** | B (escalates to C) | succession trigger event (death/incapacitation/absence/step-down/non-aligned) | succession verification + Council ≥3 attestation → LandRegistry.reassignSteward() | MST listener + heartbeat monitor |

### 2.3 Economic 系 (4 cells, mostly existing + amendment)

| Cell | Tier | 状態 |
|---|---|---|
| **EligibilityCell** | B | 既存 (ADR-2605172300 §3.1), 本 ADR で `effectiveMultiplier()` 読み替え |
| **PhenotypeAgent** | **A** | 既存 (ADR-2605172300 §3.2 + ADR-2605171300 code-gen pattern) |
| **TreasuryRebalanceCell** | B | 既存 (ADR-2605172300 §3.3) |
| **PublicFundGrantCell** | B | 既存 (ADR-2605192145 §3), 本 ADR で charter-compliance gate 統合 |
| **TitheRoutingCell** | B | 新規 — donation/kisha tx 監視 + TitheRouter.route() pre-flight 検証 |

### 2.4 Force 系 (2 cells)

| Cell | Tier | 入力 | 出力 | 起動 trigger |
|---|---|---|---|---|
| **ForceAuthorizationCell** | B (escalates to C) | `force-authorization-proposal` | 1 SBT = 1 vote orchestration + ForceAuthorization.propose() tx | MST listener |
| **ForceLogMonitoringCell** | B | `force-log` records + `force-after-action` | 三条件 compliance 検証 + Council Lv6+ alert if violation | continuous monitoring |

### 2.5 Ethics / Content 系 (1 cell)

| Cell | Tier | 入力 | 出力 | 起動 trigger |
|---|---|---|---|---|
| **EthicsContentClassifierCell** | B | content (URI + metadata) | T1-T5 classification + precedent search + Council deferral if T2/T4 | API (synchronous) |

### 2.6 Membership 系 (2 cells)

| Cell | Tier | 入力 | 出力 | 起動 trigger |
|---|---|---|---|---|
| **AdherentAttestationCell** | B | new SBT join + level advance request | AdherentRegistry.join() / advance() tx + level evidence 検証 | MST listener |
| **CouncilLevelAdvancementCell** | B | Lv5+ advancement candidates | peer attestation 集計 + Council recognition orchestration | weekly cron |

### 2.7 Council Orchestration (1 generic cell)

| Cell | Tier | 用途 |
|---|---|---|
| **CouncilDeliberationCell** (generic) | **C** | 各 Council attestation request 毎に動的 instantiate。Lv6+ member への deliberation 配信、signature 集約、minimum quorum 確認 |

## 3. Cell Residency Strategy (Tier 0-3 への mapping)

| Cell | Murakumo (T1) | Host daemon (T2) | Browser (T3) | Edge (T0) |
|---|---|---|---|---|
| CharterAttestationRequestCell | ✅ leader | ⚪ replica | ❌ | ❌ |
| CharterAttestationFinalizationCell | ✅ leader | ⚪ replica | ❌ | ❌ |
| CharterRehabilitationCell | ✅ leader | ⚪ replica | ❌ | ❌ |
| LandDonationProcessingCell | ✅ leader | ⚪ replica | ❌ | ❌ |
| LandStewardshipMonitoringCell | ✅ leader | ❌ | ❌ | ❌ (satellite imagery throughput 必要) |
| LandDisputeResolutionCell | ✅ leader | ⚪ replica | ❌ | ❌ |
| StewardSuccessionCell | ✅ leader | ⚪ replica | ❌ | ❌ |
| EligibilityCell | ✅ leader | ⚪ replica | ❌ | ❌ |
| PhenotypeAgent (per SBT) | ✅ partition by SBT | ⚪ shard | ⚪ user's own SBT のみ | ❌ |
| TreasuryRebalanceCell | ✅ leader | ❌ | ❌ | ❌ |
| PublicFundGrantCell | ✅ leader | ⚪ replica | ❌ | ❌ |
| TitheRoutingCell | ✅ leader | ❌ | ❌ | ❌ |
| ForceAuthorizationCell | ✅ leader | ⚪ replica | ❌ | ❌ |
| ForceLogMonitoringCell | ✅ leader | ⚪ replica | ❌ | ❌ |
| EthicsContentClassifierCell | ✅ leader | ⚪ replica | ⚪ T1 (clear) only — UI-side pre-filter | ❌ |
| AdherentAttestationCell | ✅ leader | ⚪ replica | ❌ | ❌ |
| CouncilLevelAdvancementCell | ✅ leader | ❌ | ❌ | ❌ |
| CouncilDeliberationCell (generic) | ✅ multi-instance | ⚪ replica | ⚪ Council member UI のみ | ❌ |

**Leader/replica pattern** = ADR-2605191603 (swarm leader election) + ADR-2605191524 (swarm broadcast) を再利用。leader が tx を emit、replica が backup として state を mirror。leader 死亡時に replica が自動昇格。

## 4. Murakumo Fleet (Tier 1) 構造

ADR-2605182312 で確立した 10-node Mac mini fleet (`naphtali / simeon / judah / zebulun / levi / joseph / issachar / dan / benjamin / asher` — `12 tribes` naming) を以下に分担:

| Node | 役割 | Cells |
|---|---|---|
| **naphtali** | Charter Compliance leader | CharterAttestationRequest / Finalization / Rehabilitation |
| **simeon** | IPFS pinner + Stewardship leader | LandStewardshipMonitoring + IPFS node (既存) |
| **judah** | Land Trust leader | LandDonation / Dispute / Succession |
| **zebulun** | Economic leader | Eligibility / TreasuryRebalance / PublicFundGrant / TitheRouting |
| **levi** | Membership + Council orchestration | AdherentAttestation / CouncilLevelAdvancement / CouncilDeliberation (generic) |
| **joseph** | Phenotype Agent partition (shard 0) | PhenotypeAgent 0-N/3 |
| **issachar** | Phenotype Agent partition (shard 1) | PhenotypeAgent N/3-2N/3 |
| **dan** | Phenotype Agent partition (shard 2) | PhenotypeAgent 2N/3-N |
| **benjamin** | Force + Ethics leader | ForceAuthorization / ForceLogMonitoring / EthicsContentClassifier |
| **asher** | Replica + failover (any cell) | dynamic |

各 node 上で `kotodama-cell-runner` daemon (Python) が常駐し、対応 cell を実行する。Failure 時は他 node が swarm leader election (ADR-2605191603) で leader を引き取る。

## 5. Cell 実装パターン

各 cell は LangGraph StateGraph として実装。共通 template:

```python
# 40-engine/kotoba/crates/kotoba-kotodama/cells/{cell_name}/cell.py
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.base import BaseCheckpointSaver
from typing import TypedDict, Literal

from kotodama.checkpointer import MstCheckpointSaver  # ADR-2605191559
from kotodama.eligibility.web3_ports import GethPrivatePort, BaseL2Port

class CellState(TypedDict):
    # cell-specific input/output state
    ...

def build_graph(checkpointer: BaseCheckpointSaver, geth_port: GethPrivatePort, base_port: BaseL2Port):
    g = StateGraph(CellState)
    g.add_node("load_input", load_input)
    g.add_node("validate", validate)
    g.add_node("execute", execute)
    g.add_node("emit_to_chain", emit_to_chain)
    g.add_node("emit_to_mst", emit_to_mst)
    g.add_edge(START, "load_input")
    g.add_edge("load_input", "validate")
    g.add_edge("validate", "execute")
    g.add_edge("execute", "emit_to_chain")
    g.add_edge("emit_to_chain", "emit_to_mst")
    g.add_edge("emit_to_mst", END)
    return g.compile(checkpointer=checkpointer)
```

State は `MstCheckpointSaver` (ADR-2605191559) で永続化 → MST → IPFS → L2 anchor pipeline (ADR-2605171800)。

## 6. Cell Trigger Mechanism

3 種の trigger pattern:

### 6.1 MST Listener (continuous)

cell が `etzhayyim-mst-listener` daemon に subscribe し、特定 Lexicon の new record を trigger として cell を invoke。

```python
# 40-engine/kotoba/crates/kotoba-kotodama/listener/mst_listener.py
class MstListener:
    def subscribe(self, lexicon_id: str, cell_invoker: Callable):
        # MST commit stream を tail し、lexicon_id に match する record を cell_invoker に push
        ...
```

### 6.2 Cron (periodic)

systemd timer / launchd schedule で periodic invocation:

- monthly: LandStewardshipMonitoringCell
- weekly: CouncilLevelAdvancementCell
- daily: ForceLogMonitoringCell (compliance check)
- 4 hours: TreasuryRebalanceCell (NAV update)
- 15 min: anchor-cron (既存 ADR-2605191625)

### 6.3 Synchronous API (request-response)

外部 / browser からの直接 invocation:

- EthicsContentClassifierCell (UI 側で content 投稿前 pre-check)
- CharterAttestationRequestCell (任意第三者からの request)

kotodama-langserver (既存 pattern, k8s/lg-uhl-right-neural と同) が HTTP endpoint を expose。

## 7. 常駐化 (Daemonization)

### 7.1 Murakumo Fleet (Tier 1) — launchd

各 Mac mini node に `~/Library/LaunchAgents/com.etzhayyim.kotodama-cell-runner.plist` を配置:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.etzhayyim.kotodama-cell-runner</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/uv</string>
        <string>run</string>
        <string>--directory</string>
        <string>/opt/etzhayyim/kotodama</string>
        <string>kotodama-cell-runner</string>
        <string>--node</string>
        <string>naphtali</string>  <!-- per-node -->
    </array>
    <key>RunAtLoad</key><true/>
    <key>KeepAlive</key><true/>
    <key>StandardOutPath</key>
    <string>/var/log/etzhayyim/kotodama-cell-runner.log</string>
    <key>StandardErrorPath</key>
    <string>/var/log/etzhayyim/kotodama-cell-runner.err</string>
</dict>
</plist>
```

`kotodama-cell-runner` は `--node <name>` で node-specific cell の subset を起動。fleet config (`50-infra/murakumo/fleet.toml`) で node ↔ cells mapping を定義。

### 7.2 Host Daemon (Tier 2) — launchd / systemd

Adherent 個人の host machine 上に `etzhayyim-host-daemon` を常駐:

```bash
# install
curl -L https://etzhayyim.com/install/host-daemon.sh | sh
# starts launchd (macOS) or systemd unit (Linux)
```

主に Per-Adherent PhenotypeAgent の自 SBT 分を local で run + replica role を兼ねる。

### 7.3 Browser (Tier 3) — service worker + persistent tab

ameno-daemon (ADR-2605191229) との統合により、browser から:

- 自 SBT の PhenotypeAgent を view
- Council Lv6+ deliberation UI
- EthicsContentClassifierCell の pre-check API call
- 自身の Charter Compliance status を確認

service worker による persistent residency + tab swarm broadcast (ADR-2605191524) で multi-tab coordination。

## 8. kotodama CLI for Cell Management

```bash
# cell catalog list
kotodama cell list

# cell deployment to specific node
kotodama cell deploy --cell CharterAttestationRequestCell --node naphtali

# cell health check
kotodama cell health --cell-all

# cell logs streaming
kotodama cell logs --cell LandDonationProcessingCell --tail

# cell state inspection (current checkpoint)
kotodama cell state --cell EligibilityCell --thread-id <id>

# cell rotation key (quarterly)
kotodama cell rotate-key --cell-all --council-sigs <sig1>,<sig2>,<sig3>
```

`70-tools/etzhayyim-cli/` 配下に integrated。既存 etzhayyim-cli (Go scaffold) を拡張。

## 9. Cell Rotation Key + Governance Integration

各 cell は cell-key を持ち、cell が emit する on-chain tx + AT Records は cell-key で sign される。cell-key は **四半期 rotate** され、rotation は Council Lv6+ ≥3 multisig で承認:

```
quarterly:
  1. Council Lv6+ ≥3 が 新 cell-key (Ed25519) を生成 + multisig sign
  2. kotodama cell rotate-key --cell-all --council-sigs ...
  3. 全 cell が同時に new key で sign 開始
  4. 旧 key は 30 日 grace period 後 invalidate
  5. rotation record は `com.etzhayyim.apps.etzhayyim.cell-key-rotation` で永続化
```

これは ADR-2605172300 §3.1 の cell-key rotation pattern を全 religious-corp cell に拡張。

## 10. Initial Deployment Sequence (実行 Roadmap)

| Step | Component | Effort | Test |
|---|---|---|---|
| **S0** | Murakumo fleet readiness check (10 node WoL + ssh access) | 0.5 day | `kotodama-cell-runner --health` on all 10 |
| **S1** | scaffolding (`50-infra/etzhayyim-charters-compliance/` etc.) | 0.5 day | tree -L 3 |
| **S2** | ChartersComplianceRegistry.sol deploy (Base L2 testnet) | 0.5 day | forge test 100% + 1 attestation e2e |
| **S3** | CharterAttestationRequestCell deploy on naphtali | 0.5 day | MST listener triggers → Council 3-of-5 → tx |
| **S4** | LandRegistry.sol + LandDonationProcessingCell deploy | 1 day | founder symbolic donation (100m² test land) e2e |
| **S5** | TitheRouter.sol + TitheRoutingCell deploy | 0.5 day | 100 USDC donation → 90 to recipient + 10 to Public Fund |
| **S6** | PublicFundGovernance.sol + PublicFundGrantCell deploy | 1 day | proposal → 5 votes → execute → 0xSplits disbursement |
| **S7** | ForceAuthorization.sol + ForceCells deploy | 0.5 day | sample R&D proposal → vote → execute log |
| **S8** | EthicsContentClassifierCell + LLM (Claude Sonnet 4.6 + Murakumo Gemma fallback) | 1 day | 50 sample contents classified |
| **S9** | StewardSuccessionCell + LandDisputeResolutionCell | 0.5 day | mock succession scenario |
| **S10** | full e2e test cycle | 1 day | Charter Compliance: request → finalize → enforcement → rehabilitate |
| **S11** | mainnet migration (Base mainnet + production Murakumo) | 1 week | gated by S0-S10 100% green |

Total initial deploy effort: ~10 days (testnet) + ~1 week mainnet migration.

## 11. Cell Performance / Scalability

| Tier | Cell type | 想定 throughput | bottleneck |
|---|---|---|---|
| A | PhenotypeAgent per SBT | 18,345 → 1,000,000+ agents (ADR-2605171300 pattern) | code-gen file size (5kB/agent), 1M agents = 5GB (mac mini で十分) |
| B | Per-Domain cells | each cell ~100-1000 tx/day | 10 nodes で sharding すれば余裕 |
| C | Council deliberation | ~10-100 attestation/day | Lv6+ human bottleneck (LLM pre-analysis で軽減) |

Murakumo 10-node fleet で 10 年想定 (10万構成員 + 100万件 attestation) まで scale 可能。

## 12. Monitoring + Observability

各 cell は以下を emit:

- **healthz** endpoint (HTTP) — uptime / last_invocation / checkpoint_lag
- **prometheus metrics** — invocation count / latency / error rate (Murakumo Prometheus stack 上)
- **swarm heartbeat** (ADR-2605191603) — leader liveness
- **AT Record audit log** — すべての cell action は `com.etzhayyim.apps.etzhayyim.cell-action` record として MST に書く

monitoring dashboard は `60-apps/etzhayyim-cell-fleet-dashboard/` (新規) で svelte SPA。

# Consequences

## 正の効果

- religious-corp doctrine が実行可能な compute substrate を持つ
- 既存 Murakumo fleet + ameno-daemon + MST checkpointer の再利用で新規構築 minimal
- 15+ cells が unified catalog で管理される (drift 抑止)
- 3 階層 actor hierarchy が scalability + flexibility 両立
- cell rotation key の quarterly governance integration が religious-corp の operational legitimacy 保証
- monitoring + observability が built-in
- 実行 roadmap (S0-S11) が ~10 日 testnet で実装可能な scope に分解
- Per-Adherent PhenotypeAgent (Tier A) が ADR-2605171300 code-gen pattern を継承、1M scale まで自然拡張

## 負の効果 / コスト

- Mac mini 10-node 運用 ops cost (electricity / hardware / 物理アクセス)
- cell 数 15+ → architectural complexity (15 cells × 10 nodes = 150 placement decisions in worst case)
- LLM cell (EthicsContentClassifier) の cost (Claude API or Murakumo Gemma)
- Council Lv6+ human bottleneck (deliberation の human 介在は scale 制約)
- swarm leader election + replica の coordination overhead
- cell-key rotation は四半期 → Council Lv6+ multisig 集合の operational burden

## 中立 / トレードオフ

- Murakumo fleet 集中 — 10 node を同一 owner (founder) が当面運用、地理分散は future work
- Per-Adherent code-gen は 1M scale で IO bottleneck の可能性 → vector DB pattern (lancedb-wasm 既存) への移行を future ADR で
- T3 (browser) での cell 部分実行は user 自身の SBT に限定 → user privacy 維持

# Alternatives Considered

## A. Kubernetes-only deployment (Murakumo + K3s)

Pro: 標準的 ops。Con: ADR-2605191346 で commercial K8s control plane 禁止、K3s HA は stateful 限定。却下: launchd / systemd ベースの単純 daemon 方式が religious-corp の simple operating model と整合。

## B. Browser-only cells (no Murakumo)

Pro: 完全 decentralized。Con: Murakumo fleet 既に存在、browser だけだと PhenotypeAgent 1M scale 不可能、MST listener の persistent residency が tab-only では脆弱。却下: Tier A/B/C 階層分担が optimal。

## C. Solidity-only enforcement (no Pregel cells)

Pro: minimal infrastructure。Con: Council deliberation + LLM analysis + IPFS evidence + cross-Lexicon 検証は Solidity 単体では実装不可能。却下。

## D. Centralized cell orchestrator (single server)

Pro: simple。Con: ADR-2605172000 kotoba 違反 + ADR-2605191346 commercial K8s 違反 + single point of failure。却下。

# Open Questions

1. **Murakumo fleet 地理分散** — 当面 founder の自宅で 10 node 集中。将来構成員数増えたら世界各地に分散 (Murakumo federation)。future ADR で詳細
2. **cell-key rotation period (四半期 = 90 日)** の妥当性 — 短い / 長い どちらが optimal か。Decision (本 ADR): 90 日 baseline、6 ヶ月毎に Council 評議
3. **LLM cell の bias 抑制** — religious doctrine を encoding した system prompt が必要。Decision: 各 LLM cell に `mission-charter-rider-system-prompt.txt` を共通 prefix、versioned
4. **構成員 1M scale 時の PhenotypeAgent code-gen 戦略** — 5kB/agent × 1M = 5GB OK だが startup cost が課題。Decision: lazy load + LRU eviction
5. **Tier C (Council deliberation) の human-bot ratio** — Council Lv6+ human の負荷を LLM がどこまで軽減できるか。Decision: human signature は constitutional 必須、LLM は pre-analysis のみ

# References

- ADR-2605192100 Mission Charter
- ADR-2605192200 Charter Rider v2.0
- ADR-2605192230 Three-tier enforcement (本 ADR cells が enforce)
- ADR-2605192245 Global Land Sovereignty (本 ADR cells が運用)
- ADR-2605192300 Bootstrap Council 5名 (本 ADR Tier C の前提)
- ADR-2605192315 Transparent Force (本 ADR Force cells の前提)
- ADR-2605192345 Steward Succession (本 ADR StewardSuccessionCell)
- ADR-2605192400 Eros/Gore (本 ADR EthicsContentClassifierCell)

- ADR-2605171800 LangGraph → MST → IPFS → L2 anchor pipeline (cell 永続化基盤)
- ADR-2605171300 UNSPSC 18,345 agent fleet (Per-Adherent code-gen pattern 出典)
- ADR-2605191229 ameno-daemon Path A (Tier 2 daemon)
- ADR-2605191257 ameno-daemon Path B (Tier 2 daemon Python)
- ADR-2605191346 Vultr-free Murakumo control plane (Tier 1 substrate)
- ADR-2605191559 MST checkpointer Stage 2 (cell state 永続化)
- ADR-2605191603 swarm leader election (cell leader/replica)
- ADR-2605191524 multi-tab swarm broadcast (cell coordination)
- ADR-2605182312 Murakumo 10-node fleet (Mac mini 12 tribes)

- 40-engine/kotoba/crates/kotoba-kotodama/ (Pregel framework host)
- 40-engine/kotoba/crates/kotoba-kotodama/cells/ (本 ADR で religious-corp cells 配置)
- 50-infra/murakumo/ (fleet config)
- 70-tools/etzhayyim-cli/ (kotodama CLI 統合)
