---
id: adr-2605200200-defense-platform-control-autonomous
title: "Defense Autonomous Platform Control — UAV / UUV / Ground State Machine"
status: active
doc_type: adr
topic: defense-platform-control
authoritative: true
last_verified: 2026-05-20
authoritative_for:
  - defense autonomous platform registry (UAV / UUV / ground / cyber)
  - defPlatform lexicon NSID namespace
  - platform domain state machines
  - fixed-point telemetry schema (no float)
  - vertex_defense_platform schema
priority: 8.5
axis: architecture
weight: 0.85
depends_on:
  - adr-2605190100-defense-cluster-topology
  - adr-2605200100-defense-mission-orchestration-lattice
  - adr-2605091400-mcp-as-cell-membrane-lexicon-xrpc-demotion
related:
  - adr-2605200300-defense-isr-sensor-fusion
  - adr-2605200400-defense-ew-counteruas-judgment
supersedes: []
superseded_by: []
---

# Defense Autonomous Platform Control — UAV / UUV / Ground State Machine

## Context

defense actor v8 にプラットフォーム状態機械が存在しない。
Anduril Ghost / Roadrunner / Dive-LD 相当のプラットフォームレジストリ・状態機械・テレメトリ管理が必要。

## Decision

### Lexicon (defPlatform)

| Method | NSID | 機能 |
|---|---|---|
| registerPlatform | `com.etzhayyim.apps.defPlatform.registerPlatform` | プラットフォーム登録 (classification ≥ 2 必須) |
| updatePlatformState | `com.etzhayyim.apps.defPlatform.updatePlatformState` | 状態遷移 + テレメトリ更新 |
| listPlatforms | `com.etzhayyim.apps.defPlatform.listPlatforms` | フリート一覧 (clearance-gated) |

### ドメイン別状態機械

```
UAV:    standby → preflight → airborne → on_station → returning → landed
UUV:    docked → transiting → on_station → egressing → docked
Ground: standby → moving → on_station → returning → standby
Cyber:  idle → tasked → executing → complete
```

### テレメトリスキーマ (固定小数点、float 禁止)

AT Protocol Lexicon は float 未対応のため整数化:

| フィールド | 型 | 単位 |
|---|---|---|
| latMicrodegrees | integer | 度 × 10⁶ |
| lonMicrodegrees | integer | 度 × 10⁶ |
| altitudeMm | integer | mm |
| bearingMdeg | integer | 度 × 10 |
| velocityMmps | integer | mm/s |

### LangGraph グラフ

`60-apps/etzhayyim-terminal-agent/graphs/defense/platform_control.py`:
- `route_platform_domain` ノードで UAV / UUV / Ground / Cyber に分岐
- 各ドメインノードが状態遷移バリデーションを実行
- テレメトリは `vertex_defense_platform` に INSERT (record-log)

### Kotoba/Datomic スキーマ

```
vertex_defense_platform      — プラットフォームノード (domain, state, 固定点テレメトリ)
edge_defense_mission_platform — ミッション ↔ プラットフォーム割当 (ADR-2605200100 共有)
```

## Consequences

- フリートリアルタイム追跡が可能になる
- テレメトリ更新頻度は Kotoba/Datomic DML rate limit による制約を受ける (`SET dml_rate_limit` 必須)
- classification ≥ 2 必須; T2 airgap 配備前は T0 SaaS で模擬テレメトリのみ
- 全テレメトリフィールドは整数型のみ (AT Protocol float 禁止規則準拠)
