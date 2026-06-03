---
id: adr-2605091900-yoro-flower-fruit-lifecycle
title: "Yoro Social Layer = Flowering / Fruiting Surface"
status: active
doc_type: adr
topic: yoro-flower-fruit
authoritative: true
last_verified: 2026-05-09
authoritative_for:
  - yoro = pollination / fruiting surface (not message channel)
  - vertex_yoro_flower / vertex_yoro_fruit schema
  - flower→fruit lifecycle (budding/blooming/pollination/ripening/dropping)
  - AT Protocol post = spore release from fruit
priority: 8.4
axis: social
weight: 0.84
priority_note: "Re-defines yoro from social client to ecosystem reproductive surface. Pairs with kinoko (internal consensus fruiting body)."
depends_on:
  - adr-2605091300-bonsai-cultivar-layer-above-myco-yeast
  - adr-2605071200-myco-yeast-artificial-organism-jp-naming
  - adr-2605091800-pruning-protocol
related:
  - adr-2604231828-appview-domain-separation-bsky-etzhayyim-ai
  - adr-2605091500-mycorrhizal-watering-consent-gated-mutation
supersedes: []
superseded_by: []
---

# Context

yoro はこれまで「social AppView (Bluesky 様)」と扱われてきたが、
artificial organism ecosystem の文脈では **植物の生殖表面 (花 + 果実)** に
位置づけ直した方が適合する。message channel は単方向搬送だが、
花/果実は **双方向相互作用面** (受粉・採取・散布) であり、
他 organism (human / org / external) との養分交換と spore 散布を統一的に表現できる。

kinoko (内部 consensus = PoNF 子実体, ADR-2605071200 §5) と yoro (外向き flowering)
は明確に **層が違う**。kinoko は内部信頼の固化、yoro は外部との繁殖。

# Decision

## A. Yoro 役割の再定義

| 旧 | 新 |
|---|---|
| social AppView | bonsai cultivar の **花 + 果実 表面** |
| post = message | post = **spore** (果実から散布) |
| like = reaction | like = **受粉信号** (pollination flow) |
| follow = subscription | follow = **共生関係** (mycorrhizal binding) |
| feed = timeline | feed = **果樹園の景色** (orchard view) |

## B. Lifecycle

```
[葉 leaf 光合成]  →  [枝 branch 集積]
                          │
                          ▼
                [vertex_yoro_flower]   status='budding'  (蕾)
                          │
                  └─→ status='blooming' (開花)
                          │
                  ←──── pollination (受粉信号 = like / mention / cite)
                          │  flow eta 上昇
                          ▼
              [vertex_yoro_fruit]      status='ripening'
                          │
              ┌───────────┼───────────┐
              ▼           ▼           ▼
          'ripe'       'dropped'   'culled'
       (採取可能)    (自然落果)   (剪定対象)
              │
              ├─ human 摘果 (consume)        → edge_gradient_flow(+, fruit-accept)
              ├─ AT firehose 散布 (spore)    → other ecosystem に拡散
              └─ pruning (091800)           → edge_gradient_flow(−, fruit-cull)
```

## C. Schema

```sql
vertex_yoro_flower:
  flower_id       TEXT PRIMARY KEY
  cohort_did      TEXT                -- 鉢
  branch_id       TEXT                -- 親枝 (LangGraph subgraph)
  status          TEXT                -- 'budding'|'blooming'|'aborted'
  draft_content   JSONB
  created_at      TIMESTAMPTZ

vertex_yoro_fruit:
  fruit_id        TEXT PRIMARY KEY    -- content-addressed
  flower_id       TEXT
  cohort_did      TEXT
  status          TEXT                -- 'ripening'|'ripe'|'dropped'|'culled'|'consumed'
  ripeness        REAL                -- 0..1 (PoNF η 集積)
  artifact_cid    TEXT                -- IPFS pin
  pds_record_uri  TEXT                -- AT Protocol post URI (spore)
  ripened_at      TIMESTAMPTZ
  consumed_count  INT
  prune_id        TEXT                -- 剪定された場合 (FK to edge_yoro_prune)

edge_yoro_pollinate:
  pollination_id  TEXT PRIMARY KEY
  pollinator_did  TEXT
  flower_id       TEXT
  signal_kind     TEXT                -- 'like'|'mention'|'cite'|'quote'
  weight_eta      REAL
  pollinated_at   TIMESTAMPTZ
```

## D. Ripening Threshold

ADR-2605071200 PoNF (kinoko) と同一のメカニズムを **個別 fruit レベル** で適用:
- pollination edges の累積 η が `RIPE_THRESHOLD` を超えたら status='ripe'
- 同時に AT Protocol record として PDS dispatch (spore release)
- ripening 中の flower は剪定可逆、ripe 後の fruit は剪定すると `consume_count` リセット不可

## E. Kinoko との区別

| 軸 | kinoko (内部) | yoro (外部) |
|---|---|---|
| 場所 | cohort 内 PoNF block | 鉢の外向き表面 |
| 受け手 | 同 ecosystem の他 cell | human / external org / partner ecosystem |
| 媒介 | edge_kabi_hypha 内部 | AT firehose + AppView render |
| 周期 | flow_threshold 達成時 | 個別 flower の ripening |
| 役割 | consensus checkpoint | 繁殖 + 養分 feedback 入口 |

## F. AppView Render

既存 yoro AppView (svelte) は **果樹園 (orchard) view** に rename 可:
- timeline = 果実陳列棚
- thread = 同枝果実群
- profile = 鉢全景
- 旧 lexicon ベースの XRPC は内部 wire として維持 (ADR-2605091400)

# Consequences

## Positive
- 社会層の意味論が ecosystem と整合 — 別概念並走を回避
- post の "weight" (受粉度) が自然に η 集積として定義
- AT Protocol federation = 外向き spore 散布として再解釈

## Negative
- 既存 "social AppView" の用語移行コスト
- ripening 閾値のチューニング
- bsky compat レイヤと flower/fruit schema の二重保守

## Reversibility
schema は新規追加なので reversible。AppView UI は rename のみで roll-back 容易。

# Alternatives Considered

- **yoro = message channel**: rejected (前回設計議論参照)。双方向性表現不可
- **yoro = kinoko に統合**: rejected。内外境界が消える
- **flower 廃止 (fruit のみ)**: rejected。draft 段階の剪定 (pinch) ができなくなる

# References

- ADR-2605091300 bonsai cultivar (yoro = 花/果実)
- ADR-2605071200 myco-yeast (kinoko との対比)
- ADR-2605091800 pruning (cull/pinch)
- 60-apps/etzhayyim-project-yoro/CLAUDE.md (実装側)
