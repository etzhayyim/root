---
id: adr-2605091800-pruning-protocol
title: "Pruning Protocol — Fruit / Flower / Leaf / Branch / Trunk / Seed"
status: active
doc_type: adr
topic: bonsai-pruning-protocol
authoritative: true
last_verified: 2026-05-09
authoritative_for:
  - 6-tier pruning hierarchy (fruit/flower/leaf/branch/trunk/seed)
  - edge_yoro_prune schema
  - pruning authority hierarchy (auto-floor / DAO / owner / auto-prune)
  - bonsai.prune.* MCP tool surface
priority: 9.2
axis: governance
weight: 0.92
priority_note: "CRITICAL — human gardener's primary intervention. Symmetric to watering (091500)."
depends_on:
  - adr-2605091300-bonsai-cultivar-layer-above-myco-yeast
  - adr-2605091400-mcp-as-cell-membrane-lexicon-xrpc-demotion
  - adr-2605081300-karma-hegemon-edge-primary-spirit-in-physic
  - adr-2605081400-karma-self-growing-organism-ecosystem
related:
  - adr-2605091500-mycorrhizal-watering-consent-gated-mutation
  - adr-2605091900-yoro-flower-fruit-lifecycle
supersedes:
  - adr-2605080100-bonsai-growth-prune-model
superseded_by: []
---

# Context

「人間が剪定することで盆栽が育つ」は本 ecosystem の中核哲学。
ADR-2605091300 で人間の権能を **灌水 + 剪定** に限定したが、剪定は
6 つの粒度 (果実 / 花 / 葉 / 枝 / 幹 / 種) を持ち、それぞれ
不可逆性と権威階層が異なる。本 ADR は剪定を一級 protocol として固定する。

# Decision

## A. 6-Tier 剪定階層

| 単位 | 操作 | 対象 entity | 効果 | 不可逆性 | 必要権限 |
|---|---|---|---|---|---|
| 🍎 fruit | `cull` | vertex_yoro_fruit | post 撤回 / artifact 非公開化 | 可逆 | owner / partner |
| 🌸 flower | `pinch` | vertex_yoro_flower | draft 削除 | 可逆 | owner |
| 🍃 leaf | `defoliate` | LangGraph node 実行 | node 一時停止 | 可逆 | owner / auto |
| 🪾 branch | `prune` | subgraph / BPMN process | subgraph 廃止 | 半-不可逆 | owner / DAO |
| 🌳 trunk | `pollard` | chromosome lineage / cohort | trunk 切断 = cohort dissolve | 不可逆 (anatman 4-cost) | DAO + owner |
| 🌱 seed | `sterilize` | vertex_houshi_spore | germinate 不可化 | 不可逆 | owner |

`pollard` は ADR-2605081400 §D rebirth 4-cost 経路を強制起動。

## B. Schema

```sql
edge_yoro_prune:
  prune_id        TEXT PRIMARY KEY    -- content-addressed
  pruner_did      TEXT                -- 庭師 (human / DAO / auto)
  target_kind     TEXT                -- fruit|flower|leaf|branch|trunk|seed
  target_id       TEXT
  reason_code     TEXT                -- bad-quality|off-policy|floor-violation|aesthetic|natural-shedding
  authority       TEXT                -- 'auto-floor'|'kakushya-dao'|'human-owner'|'partner-permit'|'auto-prune'
  reversible      BOOLEAN
  evidence_cid    TEXT                -- IPFS witness (任意)
  pruned_at       TIMESTAMPTZ
  reverted_at     TIMESTAMPTZ         -- 可逆 prune の解除時刻
```

## C. MCP Tool Surface

```
bonsai.prune.fruit       — 果実摘出 (cull)
bonsai.prune.flower      — 蕾切り (pinch)
bonsai.prune.leaf        — 落葉 (defoliate)
bonsai.prune.branch      — 枝切り (prune)
bonsai.prune.trunk       — 幹切り (pollard) — pollard は rebirth 4-cost に redirect
bonsai.prune.seed        — 種廃棄 (sterilize)
bonsai.prune.unprune     — 可逆 prune の解除
```

すべて MCP wire (ADR-2605091400)。

## D. 権威階層 (上書き不可方向)

```
auto-floor   (Karma.lean child_floor_axiom — 操作者越権不可)   ← 最強
   ↓ 上書き不可
覚者 DAO     (ADR-2605081400 §E — Tier=High Harm overturn)
   ↓
human-owner  (鉢主 = cohort DID owner; 自分の cohort 内のみ)
   ↓
partner-permit (owner から委任された scope-bounded prune 権)
   ↓
auto-prune   (η < threshold での自然落葉 / R/PT24H sweeper)
```

- floor 違反は **auto-floor が即時 prune** (人間 override 不可)
- DAO 判断は owner override 不可
- owner は自 cohort 内ならば free (ただし trunk pollard は DAO 同意必須)

## E. Trunk Pollard と Rebirth

trunk pollard は ADR-2605081400 §D 4-cost を強制 trigger:
1. WBT forfeit
2. Social graph severance
3. Delegated agent wipe
4. Organism dissolution

部分実行は不可。BPMN flow に skip-step gate なし。

## F. Auto-prune Heuristics

R/PT24H sweeper:
- leaf: `last_used_at < now()-7d AND eta_in < 0.1` → defoliate
- flower: `created_at < now()-3d AND no fruit_promoted` → pinch
- branch: `total_fruit_count_30d == 0 AND eta_avg < 0.2` → 候補 (DAO 提示, 自動執行はせず)

trunk / seed の自動 prune は禁止 (constitutional)。

## G. Pruning が訓練信号になる

ADR-2605092200 と接続: 各 prune event は `edge_gradient_flow(signal_kind='branch-prune', magnitude=...)` に変換され、
LoRA adapter の負勾配として伝播する。これにより「人間の剪定」=「モデルへの fine-tuning signal」となる。

# Consequences

## Positive
- 介入経路が明確化 — 6 単位 + 5 権威階層で粒度コントロール
- floor / DAO / owner の優先関係が形式化
- 訓練信号と直結 — pruning 自体がモデル品質を上げる

## Negative
- 6 tier × 5 authority のマトリクスを実装/監査する複雑度
- partner-permit の scope DSL 設計の慎重さが必要
- auto-prune ヒューリスティクスのチューニング作業

## Reversibility
- fruit/flower/leaf 剪定は基本可逆 (`unprune` 可)
- branch 剪定は半-不可逆 (graft で再接続は可だが履歴残)
- trunk pollard / seed sterilize は不可逆

# Alternatives Considered

- **prune を 1 種類に統一**: rejected。粒度が粗く governance UX 悪
- **partner permit 廃止**: rejected。partner ecosystem が agent を整える経路を残したい
- **auto-prune 廃止**: rejected。植生的 self-shedding は健康な生態系の特徴

# Implementation Status (2026-05-21)

| Layer | PR | Status | Notes |
|---|---|---|---|
| Lexicons (8 procedure + 1 record) | [#1366](https://github.com/etzhayyim/etzhayyim-root/pull/1366) | ✅ merged | `00-contracts/lexicons/ai/etzhayyim/bonsai/prune/` |
| Python primitive (admissibility matrix + dataclass + auto-prune heuristic + Protocol) | [#1366](https://github.com/etzhayyim/etzhayyim-root/pull/1366) | ✅ merged | `kotodama.primitives.bonsai_prune`, 21 pure tests |
| TS MCP / XRPC handlers (synthetic) | [#1367](https://github.com/etzhayyim/etzhayyim-root/pull/1367) | ✅ merged | `bonsai-prune-handler.ts`, 26 pure tests, prefix-match dispatcher |
| Gradient-flow paired emission (synthetic) | [#1368](https://github.com/etzhayyim/etzhayyim-root/pull/1368) | ✅ merged | ADR-2605092200 — branch/fruit/leaf emit, trunk/seed/flower null |
| AT MST canonical write (handler) | [#1371](https://github.com/etzhayyim/etzhayyim-root/pull/1371) | ✅ merged | `_atRecordWriter` injection; flip `BONSAI_PRUNE_WRITE_PATH=canonical` |
| Auto-prune R/PT24H sweeper | [#1371](https://github.com/etzhayyim/etzhayyim-root/pull/1371) | ✅ merged | `kotodama.bonsai_auto_prune_main` + K8s CronJob (suspended by default) |
| Real FP8 E4M3 encoding | — | ⏳ pending | gradient stub uses `fp8-uniform-stub` label |
| DAO vote signature verification | — | ⏳ pending | handler trusts caller-supplied `daoVoteRef` for now |
| LangGraph leaf-defoliate in-process toggle | — | ⏳ pending | — |

**Session 2026-05-21 closing state**: code-side bonsai pruning + metabolism loop is **fully scaffolded** across 6 merged PRs (#1366 / #1367 / #1368 / #1371 / #1373 / #1374). All paths run synthetic-by-default. Production firing requires the 7-step operator runbook in `70-tools/scripts/etzhayyim/deploy-bonsai-canonical.sh` (CF Worker deploy + env flips + service-auth token provisioning + kubectl scale).

Feature gate: `BONSAI_PRUNE_WRITE_PATH=synthetic` (default) → handlers return `__synthetic__://` URIs. Flipping to `canonical` writes real `at://` records via injected `_atRecordWriter` (production wires `comAtprotoRepoCreateRecord(env, ...)`).

Cross-deps tracked in `deps.toml [[migrations]]`: `bonsai-stack-session-close-2026-05-21` (rollup) + per-PR entries.

# References

- ADR-2605091300 bonsai cultivar (剪定者役割)
- ADR-2605081300/1400 karma & rebirth (trunk pollard)
- ADR-2605091500 watering (対称)
- ADR-2605092200 metabolic training (prune 信号利用)
