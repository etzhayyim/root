---
id: adr-2605080100-bonsai-growth-prune-model
title: "ADR-2605080100: Bonsai Growth & Prune Model — Full-Auto Growth + Human Post-Facto Pruning"
status: active
doc_type: adr
topic: bonsai-growth-prune-model
authoritative: true
last_verified: 2026-05-07
priority: 8.5
axis: architecture
weight: 0.85
priority_note: "CRITICAL — 自律成長と人間剪定の責任境界を定める。growth/prune 両操作の実装規約"
authoritative_for:
  - autonomous service/actor/schema growth lifecycle
  - human pruning interface (prune / block / release)
  - sporulation as pruning primitive (not hard delete)
  - canopy shape visibility (mv_canopy_shape)
  - growth event lineage (vertex_growth_event)
  - prune cascade preview before execution
  - anastomosis gate as regrowth block
  - dormancy TTL → hard delete policy
depends_on:
  - adr-2605080000-distributed-cognitive-actor-system
  - adr-2605071200-myco-yeast-artificial-organism-jp-naming
  - adr-0056-bpmn-as-actor
  - adr-2604291800-well-becoming-spirit-objective-function
related:
  - adr-2605061200-agi-active-inference-artificial-organism-architecture
  - adr-2604251830-shannon-optimal-layered-architecture
  - adr-0002-graph-storage
supersedes: []
superseded_by:
  - adr-2605091300-bonsai-cultivar-layer-above-myco-yeast
  - adr-2605091800-pruning-protocol
---

# ADR-2605080100: Bonsai Growth & Prune Model

**Status**: accepted
**Date**: 2026-05-07
**Deciders**: Jun Kawasaki
**Supersedes**: —

## Context

ADR-2605080000 で定義した Distributed Cognitive Actor System は自律成長が可能だが、
成長に対する人間の関与方針が未定義だった。

選択肢は3つあった:

1. **Full-auto**: PoNF consensus のみでゲートし、人間は関与しない
2. **HITL-gated**: deploy 前に人間承認を要求する
3. **Bonsai**: 成長は自動、人間は事後に形を整える

Option 2 は成長速度がボトルネックになる。Option 1 は暴走リスクがある。
**Option 3 (Bonsai)** を採用する。

盆栽の本質:
- 木は自然に成長する (PoNF が自動承認)
- 人間は後から形を整える (prune / block)
- 剪定した枝も根は残る (sporulation = 削除ではなく休眠)
- 条件が整えば再び芽吹く (germination)
- 完全に枯らしたければ意図的に根を切る (hard delete, TTL後)

## Decision

### 成長フロー (Full-Auto)

```
L5 RisingWave MV
  Shannon η gap / coverage drift / error rate を集計
          │
          ▼ stream event: growth_signal
L6 Shinka Agent (PyZeebe worker)
          │
          ▼ L2 LangGraph: observe → score → plan → propose
          │
          ▼ PoNF gate (kinoko, L5)
          │  totalFlow ≥ 100 かつ minEta ≥ 0.5 で自動承認
          │
     ┌────┴──────────────────────────────┐
     ▼                                   ▼
New Actor / Service               RisingWave DDL
ADR-0056: INSERT vertex_actor     rw-health-gate.sh → pass
+ BPMN deploy to Zeebe            CREATE TABLE / MV / External UDF
     │                                   │
     └────────────────┬──────────────────┘
                      ▼
          vertex_growth_event INSERT
          (lineage / trigger / η_at_birth)
```

人間の承認ステップは存在しない。PoNF threshold がゲートの全て。

---

### 人間が持つ操作 (3つのみ)

#### 1. `prune` — 枝を休眠させる

```
etzhayyim prune <actor_did> [--preview] [--cascade]
```

- `--preview`: カスケード対象を表示するだけ (破壊しない)
- `--cascade`: 依存 actor / table / bpmn / udf を連鎖 sporulate
- 実装: `vertex_prune_intent` に INSERT → Shinka Agent が検知 → 対象を sporulation

**sporulation = 削除ではない**:
- actor は `status='dormant'` になる (hard delete しない)
- table は `DROP` しない。`prune_status='dormant'` を MV に反映するだけ
- BPMN process は Zeebe で `suspend` (terminate しない)
- spore blob を houshi (ADR-2605071200) に預ける

#### 2. `block` — 再成長を防ぐ

```
etzhayyim prune <actor_did> --block
```

- anastomosis gate を閉じる (`regrowth_blocked=true`)
- PoNF が高スコアを出しても再成長しない
- 意図的に "この方向には伸ばさない" という意思表明

#### 3. `release` — ブロック解除

```
etzhayyim prune <actor_did> --release
```

- `regrowth_blocked=false` に戻す
- 次の PoNF サイクルで自然に再成長できる状態に戻る

---

### Canopy View — 樹形の可視化

```sql
-- mv_canopy_shape (RisingWave Materialized View)
SELECT
  ge.actor_did,
  ge.parent_did,
  ge.growth_type,          -- actor | table | mv | bpmn | udf
  ge.eta_at_birth,
  CURRENT_TIMESTAMP - ge.created_at AS growth_age,
  latest_eta.eta           AS eta_now,
  COUNT(child.actor_did)   AS child_count,
  COALESCE(pi.status, 'alive') AS prune_status,  -- alive | dormant | blocked
  pi.regrowth_blocked
FROM vertex_growth_event ge
LEFT JOIN mv_actor_eta latest_eta USING (actor_did)
LEFT JOIN vertex_growth_event child ON child.parent_did = ge.actor_did
LEFT JOIN vertex_prune_intent pi USING (actor_did)
GROUP BY ge.actor_did, ge.parent_did, ge.growth_type,
         ge.eta_at_birth, ge.created_at, latest_eta.eta,
         pi.status, pi.regrowth_blocked
```

人間はこの MV を見て「η が下がっている枝」「伸びすぎた枝」を判断する。

---

### 剪定カスケードプレビュー

`etzhayyim prune <did> --preview` の出力例:

```
will sporulate (cascade):
  ├─ actor:  com.etzhayyim.apps.foo.*       age=12d  η=0.43  ← 低η
  ├─ table:  vertex_foo_entity        rows=2,341
  ├─ mv:     mv_foo_summary           (will suspend refresh)
  └─ bpmn:   foo-classify.bpmn       active_instances=0

dependents NOT in cascade (η > 0.6, skip):
  └─ actor:  com.etzhayyim.apps.bar.*       age=30d  η=0.71  ← 健全

confirm? [y/N]
```

η が閾値以上の依存 actor は cascade から除外する。健全な枝は切らない。

---

### 休眠 → 自動発芽 → Hard Delete

```
prune
  ↓
dormant (spore in houshi)
  ↓
  ├─ PoNF signal returns + regrowth_blocked=false
  │     → auto germinate (regrowth)
  │
  └─ dormant for 90 days
        → hard delete
           vertex_actor / vertex_growth_event / houshi spore
           table DROP (if 0 rows after dormancy)
           BPMN cancel
```

TTL は `[invariants.bonsai_dormancy_ttl_days] = 90` で管理。
変更は invariant 更新のみ (コード変更不要)。

---

### Graph テーブル設計

```sql
-- 成長ログ (append-only)
CREATE TABLE vertex_growth_event (
  actor_did       VARCHAR,   -- 成長した actor の DID
  parent_did      VARCHAR,   -- 親 actor (起点)
  trigger_signal  VARCHAR,   -- growth_signal の種別
  growth_type     VARCHAR,   -- actor | table | mv | bpmn | udf
  eta_at_birth    FLOAT,     -- 誕生時の Shannon η
  created_at      TIMESTAMPTZ
);

-- 剪定意図 (人間の操作ログ)
CREATE TABLE vertex_prune_intent (
  actor_did         VARCHAR,
  status            VARCHAR,   -- dormant | blocked
  regrowth_blocked  BOOLEAN DEFAULT false,
  pruned_by         VARCHAR,   -- operator DID
  pruned_at         TIMESTAMPTZ,
  release_at        TIMESTAMPTZ  -- NULL = manual release only
);
```

---

### Shinka Agent の役割

Shinka Agent (PyZeebe worker, L6) が2つのループを回す:

**Growth loop** (既存):
- RisingWave の `growth_signal` stream を consume
- PoNF check → pass なら deploy

**Prune loop** (新規):
- `vertex_prune_intent` の未処理エントリを poll
- sporulate 実行 (actor suspend / BPMN suspend / MV suspend)
- TTL チェック → hard delete 実行
- 再成長シグナル検知 → `regrowth_blocked=false` なら germinate

---

## Design Principles

1. **成長は自動、形は人間が整える** — HITL approval は持たない
2. **prune = sporulation, not deletion** — 根を残す。後で再生できる
3. **block = 意思表明** — 「この方向には伸ばさない」を明示的に記録
4. **カスケードは η-filtered** — 健全な枝は連鎖剪定から除外
5. **TTL hard delete のみ** — 人間が直接 DROP/DELETE しない

---

## Consequences

**得られるもの**:
- 成長速度を HITL で損なわない
- 人間は「眺めて気になったら prune」という低認知負荷の関与で済む
- sporulation により誤剪定からのリカバリが可能
- 成長ログが「幹の年輪」として残る

**制約**:
- `rw-health-gate.sh` が pass しない限り DDL 成長は止まる (既存制約)
- PoNF threshold のチューニングが盆栽の「水やり加減」になる
- dormant actor が 90日 蓄積すると hard delete が走る — houshi に spore がなければ復元不可

---

## References

- ADR-2605080000: Distributed Cognitive Actor System (6-Layer, growth execution)
- ADR-2605071200: Myco-Yeast Artificial Organism (sporulation / houshi / PoNF / anastomosis gate)
- ADR-0056: BPMN-as-actor (actor deploy pattern)
- ADR-2604291800: Well-Becoming Spirit Objective Function (η scoring)
- ADR-0044: RisingWave UDF Language Strategy (External UDF in growth loop)
