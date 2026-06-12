---
id: adr-2605200101-defense-mission-orchestration-lattice
renumbered_from: "2605200100"
title: "Defense Mission Orchestration — Lattice 相当 C2 レイヤー"
status: active
doc_type: adr
topic: defense-mission-orchestration
authoritative: true
last_verified: 2026-05-20
authoritative_for:
  - defense C2 / multi-domain mission orchestration
  - defMission lexicon NSID namespace
  - mission state machine (planning → completed | aborted)
  - vertex_defense_mission / edge_defense_mission_platform schema
priority: 8.5
axis: architecture
weight: 0.85
depends_on:
  - adr-2605190100-defense-cluster-topology
  - adr-2605080000-distributed-cognitive-actor-system
  - adr-2605091400-mcp-as-cell-membrane-lexicon-xrpc-demotion
related:
  - adr-2605200200-defense-platform-control-autonomous
  - adr-2605200300-defense-isr-sensor-fusion
  - adr-2605200400-defense-ew-counteruas-judgment
supersedes: []
superseded_by: []
---

# Defense Mission Orchestration — Lattice 相当 C2 レイヤー

## Context

defense actor v8 は調達・サプライヤー・CAD に限定される。
Anduril Lattice OS 相当の C2 (Command & Control) / マルチドメインミッション編成機能が存在しない。
air / undersea / ground / cyber の横断ミッションを LangGraph Pregel fan-out で管理する必要がある。

## Decision

### Lexicon (defMission)

`00-contracts/lexicons/com/etzhayyim/apps/defMission/` に以下を追加:

| Method | NSID | 機能 |
|---|---|---|
| createMission | `com.etzhayyim.apps.defMission.createMission` | ミッション作成 (classification ≥ 2 必須) |
| updateMissionStatus | `com.etzhayyim.apps.defMission.updateMissionStatus` | 状態遷移 |
| listMissions | `com.etzhayyim.apps.defMission.listMissions` | ミッション一覧 (clearance-gated) |

### ミッション状態機械

```
planning → approved → executing → completed
                    ↘             aborted
```

遷移ルール: `approved` → `executing` は人間承認トークン必須 (autonomyMode: supervised)。

### LangGraph グラフ

`60-apps/etzhayyim-terminal-agent/graphs/defense/mission_orchestration.py`:
- エントリ: `classify_mission_domain` ノード (air | undersea | ground | cyber)
- Pregel Send fan-out: 各ドメインエージェントへ並列ディスパッチ
- 合流: `mission_sync` ノードで状態集約

### Kotoba/Datomic スキーマ

```
vertex_defense_mission       — ミッションノード (classificationLevel, domain[], state)
edge_defense_mission_platform — ミッション ↔ プラットフォーム割当
```

classification ≥ 2 のミッションは EVM 監査チェーンへ自動送信 (audit_chain.py)。

## Consequences

- マルチドメインミッションスケジューリングが可能になる
- classificationLevel ≥ 3 のミッションは T1-sovereign または T2-airgap でのみ実行可
- lexicon JSON が MCP inputSchema と内部 XRPC validation の両方を駆動 (ADR-2605091400 準拠)
- record-log semantics: INSERT only、ON CONFLICT 禁止
