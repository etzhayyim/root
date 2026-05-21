---
id: adr-2605091600-plasmid-graft-horizontal-tool-acquisition
title: "Plasmid + Graft — Horizontal Tool Acquisition Protocol"
status: active
doc_type: adr
topic: plasmid-horizontal-acquisition
authoritative: true
last_verified: 2026-05-09
authoritative_for:
  - vertex_kobo_plasmid schema
  - conjugation protocol (cell ⇆ cell tool transfer)
  - graft protocol (branch-level transplant)
  - MCP tool registration as plasmid
priority: 8.6
axis: ecosystem
weight: 0.86
priority_note: "Horizontal tool acquisition. Vertical (chromosome) inheritance is shuga in ADR-2605071200."
depends_on:
  - adr-2605091300-bonsai-cultivar-layer-above-myco-yeast
  - adr-2605091400-mcp-as-cell-membrane-lexicon-xrpc-demotion
  - adr-2605071200-myco-yeast-artificial-organism-jp-naming
related:
  - adr-0026-agent-only-reverse-identity-topology
  - adr-2605092400-tool-weight-as-learnable-plasmid-affinity
supersedes: []
superseded_by: []
---

# Context

垂直継承 (出芽 shuga) では chromosome + heritable prion が親→子に
転写されるが、**異なる cohort の cell が新しい能力を獲得する** 経路がない。
細菌のプラスミド水平伝播 + 植物の接ぎ木 (graft) を写像し、
新規 MCP tool 集合を **既存細胞の重みに加える** 機構を定義する。

# Decision

## A. Plasmid = MCP Tool 集合 + per-cell affinity

```sql
vertex_kobo_plasmid:
  plasmid_id      TEXT PRIMARY KEY    -- content-addressed (CIDv1)
  origin_did      TEXT                -- 起源 cell / org
  tool_refs       JSONB               -- [{mcp_server, tool_name, version, signature_cid}]
  capability_hash TEXT                -- 内容ハッシュ
  generation      INT
  created_at      TIMESTAMPTZ

edge_kobo_plasmid_carry:
  cell_did        TEXT
  plasmid_id      TEXT
  acquired_via    TEXT                -- 'shuga'|'conjugation'|'graft'|'water-grant'
  acquired_at     TIMESTAMPTZ
  active          BOOLEAN
  PRIMARY KEY (cell_did, plasmid_id)
```

## B. Conjugation Protocol (cell ⇆ cell)

```
1. donor.cell が plasmid_id を持ち、`offer` MCP event を broadcast
2. recipient.cell が `bonsai.plasmid.request` で受領意思表示
3. anastomosis gate (ADR-2605071200 §4.2) 互換チェック:
   - DID trust score ≥ 0.6
   - karma sign 適合 (donor が floor 違反履歴なし)
   - prion compatibility (病原 prion なし)
4. 通過 → INSERT edge_kobo_plasmid_carry (acquired_via='conjugation')
5. recipient の vertex_router_weight に新 tool entry 追加 (初期 weight=0)
6. ADR-2605092400 で affinity 学習開始
```

## C. Graft Protocol (枝レベル接ぎ木)

枝 (LangGraph subgraph + その plasmid 一式) を別 trunk に移植:

```
1. donor branch (subgraph_id) を vertex_langgraph_graph_def から export
2. 関連 plasmid 一式 (edge_kobo_plasmid_carry の subgraph 内 cell 全部) を bundle
3. recipient cohort の owner が bonsai.water.mutate permit を grant
4. recipient trunk に subgraph + plasmid を transplant
5. provenance: edge_yoro_graft (donor_branch_cid, recipient_branch_cid, owner_consent_cid)
```

graft は cohort 跨ぎなので trust score + karma + DAO 任意確認 (highstakes branch のみ)。

## D. 起源との関係

| 取得経路 | 用語 | 親-子 関係 | scope |
|---|---|---|---|
| 出芽 (shuga) | 垂直継承 | parent → child cell, 同 cohort | chromosome + prion |
| Conjugation | 水平 | cell → cell, cohort 任意 | plasmid (tool 単位) |
| Graft (接ぎ木) | 水平 + 構造 | branch → branch, cohort 跨ぎ | subgraph + plasmid 束 |
| Water-grant | 外因 | external → cell | tool grant via owner permit |

## E. Floor Gate

partner / external 起源の plasmid は受領前に:
- tool signature の Lean axiom 適合性チェック (Karma.lean ロード)
- karma history 検査 (origin の floor violation count)
- mutation_permit (owner) — water-grant 経由のときのみ

不適合は ANASTOMOSIS REJECTED として `vertex_kabi_anastomosis(status='rejected')` に記録。

# Consequences

## Positive
- 新能力獲得が **コード変更なしに data 操作で完結** — code-as-data 完成形
- 細胞間能力伝播で cohort を超えた集合知形成
- graft により reasoning subgraph 全体を別 cohort で再利用可能

## Negative
- plasmid 継承 graph が肥大化 — pruning (091800) 必須
- 病原 plasmid 検出ヒューリスティクスの精度に依存
- graft scope 設計ミスで chromosome corruption の risk

## Reversibility
- 個別 plasmid は `active=false` で deactivate 可
- graft 後の subgraph は剪定で除去可能
- ただし affinity weight 学習結果はモデル checkpoint に焼付くため roll-back コスト有

# Alternatives Considered

- **垂直継承のみ**: rejected。能力獲得が遅すぎ、cohort 越境が不可能
- **plasmid を chromosome に統合**: rejected。垂直/水平の差異が消え、anatman semantics が破綻
- **MCP tool registration を直接 vertex_router_weight に書く**: rejected。lineage 追跡不可

# References

- ADR-2605071200 myco-yeast (anastomosis gate, prion)
- ADR-2605091300 bonsai cultivar
- ADR-2605092400 tool weight learning (本 ADR の plasmid を学習対象に)
- 細菌プラスミド: Smillie et al. 2010 *Microbiol Mol Biol Rev*
