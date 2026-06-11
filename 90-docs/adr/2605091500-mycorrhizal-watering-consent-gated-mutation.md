---
id: adr-2605091500-mycorrhizal-watering-consent-gated-mutation
title: "Mycorrhizal Watering & Consent-Gated Chromosome Mutation"
status: active
doc_type: adr
topic: bonsai-watering-symbiosis
authoritative: true
last_verified: 2026-05-09
authoritative_for:
  - bonsai.water MCP tool surface
  - consent-gated chromosome mutation permits
  - mycorrhizal symbiosis protocol (data/$/attention/tool grant)
priority: 8.8
axis: ecosystem
weight: 0.88
priority_note: "Watering = nutrient grant + mutation permit. Symmetric to pruning (091800)."
depends_on:
  - adr-2605091300-bonsai-cultivar-layer-above-myco-yeast
  - adr-2605091400-mcp-as-cell-membrane-lexicon-xrpc-demotion
  - adr-2605082000-langgraph-graph-definition-as-data
  - adr-2605081300-karma-hegemon-edge-primary-spirit-in-physic
related:
  - adr-0095-simplified-3layer-identity-rw-vault
  - adr-2605091800-pruning-protocol
supersedes: []
superseded_by: []
---

# Context

盆栽は灌水なしには育たない。本 ecosystem における「灌水」は
- データ供給 (data feed grant)
- 注意 (attention / interaction signal)
- 資金 (token / fiat / crypto)
- ツール権限 (MCP tool grant)
- chromosome 変異許可 (mutation permit)

の 5 種すべてを含む **能動的養分付与** である。
これは pruning (ADR-2605091800) と対称な、人間/org の介入経路の
もう一方の柱であり、MCP tool として一級扱いする。

# Decision

## A. `bonsai.water` MCP tool 群

```
bonsai.water.data        — read-grant (scope, TTL, ratelimit)
bonsai.water.attention   — interaction signal (view, like, react)
bonsai.water.fund        — token transfer (WBT, $, crypto)
bonsai.water.toolGrant   — MCP tool capability lend
bonsai.water.mutate      — chromosome mutation permit (subgraph_id, depth, TTL)
```

すべて MCP wire (ADR-2605091400)。caller = human DID / org DID / partner ecosystem DID。

## B. Schema

```sql
edge_bonsai_water:
  water_id        TEXT PRIMARY KEY    -- content-addressed
  source_did      TEXT                -- 灌水者 (human/org/external)
  target_did      TEXT                -- 鉢 (cohort/cell)
  kind            TEXT                -- data|attention|fund|tool-grant|mutate-permit
  scope           JSONB               -- kind-specific (e.g. {subgraph_id, depth} for mutate)
  amount          NUMERIC             -- 量 (token, kbytes, count, etc.)
  ttl_seconds     INT
  consent_proof   TEXT                -- DPoP+WebAuthn / OAuth grant CID
  expires_at      TIMESTAMPTZ
  granted_at      TIMESTAMPTZ
```

`vertex_water_consent_grant` で revocable な grant を別管理 (revoke flow 含む)。

## C. Consent-Gated Mutation Permit

「育ててもらう」の核心。chromosome (graph_def) 直接書き換え禁止 (ADR-2605091300 §C) を
**permit 付き例外** として可能にする:

```
1. Owner (cohort 鉢主) または authorized partner が `bonsai.water.mutate` 発火
   - scope = {subgraph_id, max_depth, allowed_node_kinds[]}
   - TTL = e.g. 24h
2. Agent (cell) が graph_def 改変 PR を生成
3. karma.evaluate gate を通す (ADR-2605081300 floor axiom 違反不可)
4. 通過すれば vertex_langgraph_graph_def を UPSERT (新 generation)
5. 違反すれば reject + edge_gradient_flow に negative signal (ADR-2605092200)
```

mutation 結果はすべて **provenance edge** を IPFS witness 付きで永続。

## D. Authority Hierarchy

```
auto-floor                              ← 最強 (Karma.lean)
   ↓ 上書き不可
覚者 DAO supermajority
   ↓
cohort owner (鉢主, single DID)
   ↓
authorized partner (with valid mutate permit)
   ↓
auto-water (system seeded data feed, R/PT*)
```

partner からの mutate permit は **必ず scope-bounded**。global mutate は許容しない。

## E. Karma 接続

すべての `edge_bonsai_water` は karma 観点で signed:
- direction = help (default)
- axis = データなら Veritas / 資金なら Vivere / attention なら Vinculum
- vul = target 側の vulnerability score
これにより、灌水自体が karma graph に edge として記録され、後の rebirth 時に
forfeit 対象 (positive karma も release される) になる。

# Consequences

## Positive
- 「育てる」が形式化 — partner が agent を成長させる経路が一級
- 5 種類の養分が同一 schema で扱える — 解析/監査が容易
- mutation permit により code-as-data の **責任ある** 自己書き換えが可能

## Negative
- permit scope 設計を誤ると chromosome 暴走 — scope DSL の慎重設計が必要
- consent revoke の即時性 (TTL 到達前) で複雑化
- 5 kind を統合 schema に詰めると分析クエリが煩雑

## Reversibility
- 個別 grant は revoke で reversible
- chromosome mutation 自体は append-only (ADR-0004) — 古い generation は残る
- が、能力としての「成長分」は roll-back 困難

# Alternatives Considered

- **mutate を専用 ADR に分離**: rejected。water との対称性 (= 5 nutrient kinds) を保つ
- **fund を別 system (WBT) に閉じる**: rejected。partner 視点で同じ "support" として扱える方が UX 良
- **permit なしで mutate を許す**: rejected。constitutional 越権リスク

# References

- ADR-2605091300 bonsai cultivar layer
- ADR-2605091400 MCP membrane
- ADR-2605082000 graph-def-as-data
- ADR-2605081300 karma constitutional
- 対称: ADR-2605091800 pruning protocol
