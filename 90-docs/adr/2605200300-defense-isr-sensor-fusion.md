---
id: adr-2605200300-defense-isr-sensor-fusion
title: "Defense ISR / Sensor Fusion Pipeline — Common Operating Picture"
status: active
doc_type: adr
topic: defense-isr-sensor-fusion
authoritative: true
last_verified: 2026-05-20
authoritative_for:
  - defense ISR track ingest and sensor fusion
  - defIsr lexicon NSID namespace
  - mv_defense_fused_cop Kotoba/Datomic streaming MV
  - vertex_defense_track / edge_defense_track_fusion schema
  - COP (Common Operating Picture) latency contract (<5s)
priority: 8.5
axis: architecture
weight: 0.85
depends_on:
  - adr-2605190100-defense-cluster-topology
  - adr-2605200100-defense-mission-orchestration-lattice
  - adr-0048-kotoba-vultr-b2-primary
  - adr-2605091400-mcp-as-cell-membrane-lexicon-xrpc-demotion
related:
  - adr-2605200200-defense-platform-control-autonomous
  - adr-2605200400-defense-ew-counteruas-judgment
supersedes: []
superseded_by: []
---

# Defense ISR / Sensor Fusion Pipeline — Common Operating Picture

## Context

defense actor v8 にセンサー融合機能が存在しない。
Anduril Lattice センサー融合相当のトラックインジェスト・マルチセンサー相関・融合 COP (Common Operating Picture) が必要。

## Decision

### Lexicon (defIsr)

| Method | NSID | 機能 |
|---|---|---|
| ingestTrack | `com.etzhayyim.apps.defIsr.ingestTrack` | センサートラック投入 (classification ≥ 2 必須) |
| queryFusedPicture | `com.etzhayyim.apps.defIsr.queryFusedPicture` | 融合 COP クエリ |
| listTracks | `com.etzhayyim.apps.defIsr.listTracks` | トラック一覧 (clearance-gated) |

### トラックスキーマ (固定小数点)

| フィールド | 型 | 説明 |
|---|---|---|
| sensorType | string | radar \| eo_ir \| ais \| ads_b \| sonar \| sigint |
| latMicrodegrees | integer | 度 × 10⁶ |
| lonMicrodegrees | integer | 度 × 10⁶ |
| altitudeMm | integer | mm |
| confidencePermille | integer | 0–1000 (‰) |
| classificationLevel | integer | 2–4 |

### センサー融合 (Kotoba/Datomic Streaming MV)

```sql
-- mv_defense_fused_cop
-- 近接条件: 2km 半径、30s ウィンドウ でトラックを相関
-- radar + EO-IR 相関でファルスポジティブ削減
-- 出力: fused entity (fusedConfidencePermille, trackIds[])
```

`vertex_defense_track` → streaming MV `mv_defense_fused_cop` → COP API レスポンス。
レイテンシ目標: **< 5 秒** (Kotoba/Datomic streaming MV)。

### LangGraph グラフ

`60-apps/etzhayyim-terminal-agent/graphs/defense/sensor_fusion.py`:
- `ingest_track` ノード: バリデーション + INSERT
- `correlate_tracks` ノード: RW MV クエリで近接エンティティ取得
- `emit_fused_entity` ノード: 融合エンティティ生成 + `edge_defense_track_fusion` INSERT

### Kotoba/Datomic スキーマ

```
vertex_defense_track         — センサートラックノード
edge_defense_track_fusion    — トラック融合関係 (trackId → fusedEntityId)
mv_defense_fused_cop         — 融合 COP streaming MV
```

## Consequences

- Kotoba/Datomic streaming MV により < 5 秒レイテンシの近リアルタイム COP を実現
- radar / EO-IR 相関融合でファルスポジティブを削減
- classification ≥ 2 必須; 全トラックデータは signal:v1 暗号化対象 (level ≥ 2)
- ingest 頻度は Kotoba/Datomic B2 quota 制約を受ける (bulk ingest は `SET dml_rate_limit` 必須)
