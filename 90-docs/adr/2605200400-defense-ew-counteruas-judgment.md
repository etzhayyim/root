---
id: adr-2605200400-defense-ew-counteruas-judgment
title: "Defense EW / Counter-UAS Judgment Engine"
status: active
doc_type: adr
topic: defense-ew-counteruas
authoritative: true
last_verified: 2026-05-20
authoritative_for:
  - defense EW / counter-UAS threat classification and escalation
  - defEw lexicon NSID namespace
  - OPA Rego extension etzhayyim.defense.ew.escalation
  - human-in-loop authorization for kinetic / HPM interventions
  - vertex_defense_ew_event / edge_defense_track_ew schema
priority: 9.0
axis: architecture
weight: 0.90
depends_on:
  - adr-2605190100-defense-cluster-topology
  - adr-2605200300-defense-isr-sensor-fusion
  - adr-2604261100-rego-dmn-policy-decision-layers
  - adr-2605091400-mcp-as-cell-membrane-lexicon-xrpc-demotion
related:
  - adr-2605200100-defense-mission-orchestration-lattice
  - adr-2605200500-defense-t2-airgap-overlay-complete
supersedes: []
superseded_by: []
---

# Defense EW / Counter-UAS Judgment Engine

## Context

defense actor v8 に EW (Electronic Warfare) / Counter-UAS 機能が存在しない。
Anduril Leonidas / Pulsar 相当のソフトウェアレイヤーが必要:
脅威分類・エスカレーションチェーン・介入認可。

## Decision

### Lexicon (defEw)

| Method | NSID | 機能 |
|---|---|---|
| declareTarget | `com.etzhayyim.apps.defEw.declareTarget` | 脅威ターゲット宣言 (classification ≥ 3 必須) |
| requestIntervention | `com.etzhayyim.apps.defEw.requestIntervention` | 介入要求 (人間承認トークン必須) |
| listInterventions | `com.etzhayyim.apps.defEw.listInterventions` | 介入履歴一覧 |

### 介入タイプ

```
electronic_jamming — 電子妨害 (T1 以上)
hpm               — High-Power Microwave (T2 必須 + 人間承認)
kinetic           — 動力学的手段 (T2 必須 + 人間承認 + clearance ≥ 3)
cyber             — サイバー手段 (T1 以上)
```

### OPA Rego エスカレーション

`00-contracts/policies/defense/ew_escalation.rego` — `etzhayyim.defense.ew.escalation` パッケージ:
- `allow_intervention` ルール: autonomyMode + interventionType + clearanceLevel の 3 軸チェック
- `supervised` モード: 全介入タイプで人間承認トークン (humanAuthToken) を必須とする
- `autonomous` モード: T0/T1 では禁止 (T2 air-gap のみ許可、かつ electronic_jamming のみ)

### 自律性モード

| autonomyMode | 許可環境 | 人間承認 |
|---|---|---|
| supervised | T0 / T1 / T2 | 全介入タイプで必須 |
| autonomous | T2 のみ | electronic_jamming のみ (HPM/kinetic/cyber は supervised 強制) |

### 監査チェーン

EW イベントは常に audit_chain.py へ同期送信 (classification level ≥ 2 以上の全イベント)。
`asyncio.ensure_future` 非同期ではなく **同期 await** — EW イベントの監査省略は禁止。

### LangGraph グラフ

`60-apps/etzhayyim-terminal-agent/graphs/defense/ew_counteruas.py`:
- `classify_threat` ノード: ISR トラックから脅威スコア算出
- `rego_escalation_check` ノード: OPA ポリシー評価
- `await_human_auth` ノード: supervised モード時の承認待機 (タイムアウト 60s)
- `execute_intervention` ノード: 介入実行 + 監査レシート

### RisingWave スキーマ

```
vertex_defense_ew_event   — EW イベントノード (interventionType, autonomyMode, humanAuthToken)
edge_defense_track_ew     — ISR トラック ↔ EW イベント関連
```

## Consequences

- kinetic / HPM 介入は clearance ≥ 3 + 人間承認トークンなしには実行不可 (OPA ポリシー強制)
- supervised モードは T0 / T1 環境で強制適用される
- EW イベントの監査証跡は省略不可 (同期 audit_chain.submit_audit_receipt)
- classification ≥ 3 (secret) 必須のため T2 air-gap 環境でのみフル機能が利用可能
