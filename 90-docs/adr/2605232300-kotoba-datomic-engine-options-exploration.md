---
id: adr-2605232300-kotoba-datomic-engine-options-exploration
title: "ADR-2605232300: kotoba-datomic — engine architecture options exploration (Hummock fork / RW fork / GraphAr+MV no-fork) (SUPERSEDED by 2605262130)"
status: superseded
doc_type: adr
topic: kotoba-datomic-engine
authoritative: false
last_verified: 2026-05-23
priority: 7.5
axis: substrate-engine
weight: 0.7
priority_note: "Exploratory only. No option adopted. Sets up a future authoritative ADR once Council/timeline trade-offs are resolved."
authoritative_for: []
depends_on:
  - adr-2605172000-etzhayyim-rw-free-substrate
  - adr-2605231400-kotoba-datomic-holochain-iso-substrate
  - adr-2605231500-kotoba-datomic-projection
  - adr-2605181100-mst-encrypted-records-signal-keywrap
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
  - adr-2605192415-etzhayyim-religious-corp-daemon-architecture
related:
  - adr-2604241342-kotoba-out-of-band-migration-pattern
  - 2605171300
supersedes: []
superseded_by:
  - adr-2605262130-kotoba-storage-substrate-unification
---

# ADR-2605232300: kotoba-datomic — engine architecture options exploration

**Status**: proposed — **EXPLORATORY ONLY, NOT ADOPTED**
**Date**: 2026-05-23
**Deciders**: Jun Kawasaki

> **重要**: 本 ADR は engine 選定の決定文書ではない。複数 option の数値比較と
> trade-off の record。authoritative engine 選定は将来別 ADR で行う。本 ADR は
> その時の input として保存される。

## Context

[ADR-2605231400](/90-docs/adr/2605231400-kotoba-datomic-holochain-iso-substrate.md) は
`kotoba-datomic` を Holochain-isomorphic な substrate composition の名称として定義し、
[ADR-2605231500](/90-docs/adr/2605231500-kotoba-datomic-projection.md) は hot-path projection
layer (RW / Lance / Iroh / index) の使用条件を規定した。

しかし **projection layer の具体的な engine 実装** は両 ADR ともオープン。一方で
religious-corp は:

- **18,345 unispsc LangGraph agents** (`20-actors/magatama/py/.../unispsc_agents/`) を
  動かす Pregel 基盤を必要とする (ADR-2605171300)
- **SQL + Graph + GraphQL** 三面のクエリ surface を必要とする (commercial-evidence / member roster / SBT graph / land registry)
- **暗号化 + RLS** を DID 主体で強制する (ADR-2605181100)
- **Object storage + IPFS をデータ実体** として保持する (ADR-2605172000)
- **Mac mini fleet** (Apple Silicon、unified memory + Metal GPU) で運用する
  (`50-infra/murakumo/fleet.toml`、ADR-2605192415)
- **Council bootstrap 2026-06-19 + mainnet ~2027** の timeline 制約 (CLAUDE.md Status #18-20)

この複合要件に対し、projection engine をどう構成するかを **4 option** に整理し
数値比較した結果を本 ADR に保存する。

## Problem statement

kotoba-datomic projection layer に求められる機能を 9 つに分解:

1. Object storage / IPFS native (write home は MST、projection は S3/R2/IPFS)
2. Streaming MV / projector (MST CDC → materialized view)
3. SQL surface (PgWire 互換が望ましい)
4. Graph surface (openCypher subset + property graph)
5. **GraphQL surface** (API クエリ言語、Hasura-iso、subscription 含む)
6. UDF protocol (Arrow Flight、pymagatama 18,345 agents を直接呼べる)
7. Encryption integration (`com.etzhayyim.encrypted.*` envelope を貫通)
8. RLS (DID-bound UCAN capability、三層 defense in depth)
9. **Pregel epoch semantics** (LangGraph super-step ↔ engine barrier の整合)

これらを **どの engine で**、**どこまで fork して**、**どこまで upstream に依存**するかが
本 ADR の central question.

## Hard constraints (consitutional invariants)

- **Primary write home は MST のみ** (ADR-2605172000)
- **Projection は MST root から決定論的に再構築可能** であること (ADR-2605231500)
- **License は Apache 2.0 + Charter Compliance Rider v2.0** (ADR-2605192200)
- **暗号化は `com.etzhayyim.encrypted.*` 形式** (ADR-2605181100)
- **直接 import 禁止**: アプリは `@etzhayyim/sdk` 経由のみ
- **Religious-corp parallel-substrate 原則** を毀損しない (ADR-2605192100 §1.12)

## Options considered

### Option A — Hummock fork (yata-slate 名で religious-corp 内製化)

Kotoba/Datomic の Hummock state store layer のみ fork し、religious-corp 専用 engine
(`yata-slate`) として最適化。SQL planner は DataFusion 流用、streaming engine は
自前実装。Hummock の Pregel epoch semantics は保持。

### Option B — Kotoba/Datomic 全体 fork (yata-wave)

Kotoba/Datomic 全体を religious-corp 用に fork (`yata-wave`)、Charter Rider 適用、
graph 対応を追加。Hummock + RW Compute + RW Meta + connector を継承し、religious-corp
固有要件を上に追加する。

### Option C — SlateDB fork

object-storage-native な独立 LSM である SlateDB (Apache 2.0、Slate Computing) を
fork。Kotoba/Datomic の代わりに自前 stream/SQL layer を構築。

**早期に却下**:

- SlateDB は pure KV LSM、**Pregel epoch / barrier semantics を持たない** ため
  LangGraph super-step との内部 isomorphism が成立しない
- UDF protocol を自前で実装する必要があり、pymagatama 18,345 agents の統合コストが
  Option B より高い
- Apple Silicon unified memory の利点を活かす Arrow Flight UDF zero-copy が
  自前構築になる

### Option D — RW upstream + Apache GraphAr + MV/projector (NO FORK, "yatabase" 構成)

RW を **fork せず upstream そのまま使用**、graph storage は Apache GraphAr (Parquet-based,
Apache 2.0, Apache Incubator) を採用。religious-corp 固有 layer (MST CDC source /
GraphAr sink / GraphQL surface / RLS proxy / encryption hook) のみを extension として
作る。**Hummock = hot tier、GraphAr = warm/cold tier** の 2-tier 設計。

### Option E — RW + Lance (旧提案、本 ADR の範囲外)

Lance を vector / columnar projection に併用する旧設計。本 ADR ではユーザ判断で
**Lance 不採用** が確定済み (vector workload の優先度低)。記録のみ。

### Considered and rejected — bulk graph framework としての追加候補

| Framework | License | 評価 | 却下理由 |
|---|---|---|---|
| Apache Giraph | Apache 2.0 | ✗ | 休眠 (~2021 以降 inactive)、Hadoop ecosystem 引き込み、religious-corp 規模で overkill |
| Spark GraphX | Apache 2.0 | ✗ | Databricks 自身が開発停止、deprecated by GraphFrames |
| Spark GraphFrames | Apache 2.0 | △ | maintained だが Spark JVM 重装、religious-corp 規模で overkill |
| Apache HAMA | Apache 2.0 | ✗ | Apache Attic 引退済 |
| NVIDIA cuGraph (RAPIDS) | Apache 2.0 | ✗ | CUDA only、Mac Silicon Metal で動かない |
| GraphScope (Alibaba) | Apache 2.0 | △ (future) | active、openCypher native、Stage 2 で外部接続候補として保持 |
| timely-dataflow / differential-dataflow | MIT | △ (research) | Pregel++ 最先端、長期 R&D 候補 |
| Materialize | **BSL** | ✗ | BSL は Apache 2.0 + Charter Rider と非可換 |

将来 bulk graph analytics が必要になった場合は **GraphScope を GraphAr 経由で外部
接続** する形を推奨 (Option D との相性が良い)。

## Numerical comparison

### Code volume

| 項目 | A (Hummock fork) | B (RW fork) | D (no fork + GraphAr) |
|---|---|---|---|
| 継承 LOC | ~110K | ~550K | 0 (依存のみ) |
| 新規実装 LOC | 150-230K | 57-99K | **30-50K** |
| 完成時所有 codebase | 260-340K | 610-650K | **30-50K** |
| Charter Rider 適用範囲 | 全 | 全 | **新規 30-50K のみ** |
| fork 維持コスト (年) | 6-10 weeks | 8-16 weeks | **0** |

### Engineering effort (3-person Rust team、religious-corp 想定)

| Phase | A | B | D |
|---|---|---|---|
| P0 ADR / scoping | 1 | 1 | 1 |
| P1 MST source + sink connector | 6-9 | 2 | 2-3 |
| P2 MV engine 自前 / Encrypted block | 9-15 | 1-2 | 0 |
| P3 GraphAr lakehouse (chunking / metadata / witness) | n/a | n/a | 2-3 |
| P4 PgWire + RLS proxy | 6-9 | 1 | 1-2 |
| P5 GraphQL | 4-6 | 4-6 | 4-6 |
| P5b Cypher subset | 3-4 | 3-4 | 3-4 |
| P6 UDF / pymagatama 統合 | 4-6 | 1-2 | 1-2 |
| P7 RLS / encryption end-to-end | 4-6 | 2-3 | 2-3 |
| P8 Witness / L2 anchor | 2-3 | 2-3 | 2-3 |
| P9 Mac Silicon GPU runtime | 2-3 | 2-3 | 2-3 |
| **合計 person-months** | **44-67** | **20-29** | **20-32** |
| **3 人並列 暦月** | 15-22 ヶ月 | 7-10 ヶ月 | **7-11 ヶ月** |

### Performance prediction (religious-corp 5y target: 10M members, 100M edges, 18K agents)

| 指標 | A | B | D |
|---|---|---|---|
| Hot ingest (events/sec/node) | 50-500K (自前 tuning 次第) | 500K-1M | 500K-1M |
| Hot MV latency (barrier) | 1-5s → 500ms | 100ms-1s | 100ms-1s |
| Cold scan (10M vertex) | 自前 | 5-15s | **2-5s** (Parquet columnar) |
| Cold PageRank (100M edge) | 自前 | 10-30 min | **1-5 min** (GraphScope on GraphAr) |
| GraphQL p99 | 50-200ms | 50-100ms | 50-100ms |
| Bulk graph analytics 接続 | △ | △ | **★★★** (GraphAr 標準で外部 engine 直接) |

### Risk

| Risk | A | B | D |
|---|---|---|---|
| 5 年以内 mainnet 完成確率 | 50% | 85% | **90-95%** |
| MV engine bug | high (自前) | low | low |
| 上流 RW BSL 化リスク | n/a | medium (fork 凍結可) | medium (最終 Apache commit pin 可能) |
| GraphAr 標準衰退リスク | n/a | n/a | low (Apache project) |
| Bus factor | high | medium | **low** |
| Religious-corp constitutional 整合 | ★★★ | ★ | **★★** |

### 7-axis weighted scoring

| 軸 | weight | A | B | D |
|---|---|---|---|---|
| Time-to-MVP | 0.20 | 3 | 9 | 9 |
| Engineering effort | 0.15 | 3 | 9 | 8 |
| Performance (initial) | 0.10 | 5 | 9 | 9 |
| Performance (5y matured) | 0.10 | 8 | 8 | 9 |
| Completion risk | 0.15 | 4 | 9 | 10 |
| Strategic independence | 0.15 | 10 | 4 | 6 |
| Long-term maintenance | 0.10 | 8 | 5 | 9 |
| GraphQL fit | 0.05 | 7 | 8 | 8 |
| **Total (max 10)** | 1.0 | **5.6** | **7.7** | **8.4** |

## Findings (analytical, non-decisional)

### Finding 1: Hummock の epoch model は LangGraph Pregel と内部 isomorphic

Kotoba/Datomic streaming barrier の epoch = Pregel super-step boundary。LangGraph
`BaseCheckpointSaver` の super-step もこれと 1:1 対応する。Hummock の per-key
epoch versioning は per-vertex super-step history と構造一致 → **LangGraph
checkpointer 実装は Hummock 上で薄い PgWire client** で済む。

SlateDB は pure KV のため epoch coordinator を自前で乗せる必要があり、本要件には
不適。これは Option C 却下の決定的理由。

### Finding 2: Mac Silicon は CPU/GPU 二択ではなく物理的に co-located

Apple Silicon unified memory (M4 Pro 273 GB/s) は CPU/GPU 間ゼロコピーを成立させる。
"GPU-first vs MV-first" の二択は誤った問題設定。正解は **per-node hybrid** で:

- CPU cores: RW Compute + Hummock state + MV evaluation + encryption
- GPU cores: Ollama (llama.cpp Metal) + MLX inference + 将来 GNN
- Unified memory: 両方が同一 RAM プールを共有 (Arrow Flight UDF zero-copy)

10-node Mac mini fleet (M4 Pro 64GB) = aggregate 640GB memory, ~92 TFLOPS FP32 →
H100 1台相当 + 8x memory。religious-corp の inference 中心 workload に適合。

### Finding 3: Data sovereignty は fork なしで GraphAr で達成できる

religious-corp parallel-substrate 原則 (ADR-2605192100 §1.12) が要求する
"data + governance を religious-corp が所有" は、**engine fork とは独立に成立する**。

- データ実体: MST (atproto repo) + IPFS (CIDv1) + GraphAr (Parquet on S3) →
  すべて religious-corp 所有 bucket
- 計算 engine (Kotoba/Datomic) は **transient な計算層** で、いつでも他 engine に
  乗り換え可能 (GraphAr / Parquet 標準 format なので DuckDB / GraphScope / Flink
  などへ移送なしで切替可)
- Charter Rider は extension layer (~30-50K LOC) のみに適用、upstream RW 本体
  には適用不要

→ **Option D は strategic independence を毀損せずに fork コストを回避する設計**。

### Finding 4: GraphAr は kotoba-datomic の MST 不変性と format 設計が整合

GraphAr の chunk は **append-only Parquet ファイル** で immutable。これは MST の
content-addressed commit と semantics 一致。Hummock epoch flush → GraphAr chunk
write の cadence は religious-corp の barrier interval (100ms-1s) と整合する。

vertex/edge の label partition は religious-corp の graph structure (Member / Agent /
Land / SBT relation) に 1:1 mapping 可。

### Finding 5: 4 option は evolutionary に重ね合わせ可能

```
2026 ┃ D (no fork + GraphAr)           ← Phase 1 ship, mainnet ready
2027 ┃ D + extension plugin 整理        ← Phase 2 Charter Rider surface 最小化
2028 ┃ D + B-partial (Hummock fork のみ) ← Phase 3 性能/制御限界に到達したら
2029+┃ A (full Hummock-fork yata-slate) ← Phase 4 religious-corp 完全 own
```

各 phase は前 phase の **データを GraphAr で持ち越せる** ため、engine 移行コストが
最小化される。これは Option D を出発点に選ぶことの **構造的利点**。

## Tentative direction (NOT ADOPTED)

数値分析からは **Option D を Phase 1 として選ぶのが numerically dominant**。
しかし本 ADR は **decision ではない**。Council 議論および religious-corp の
constitutional principles に基づく最終判断は別途行う。

決定保留の主な理由:

1. **Constitutional 重み付け未確定**: 7-axis scoring の "strategic independence"
   weight を 0.15 → 0.30 に上げると D と B が拮抗し、0.40 にすると A が首位に
   なる。religious-corp Council が parallel-substrate 原則をどの強度で要求するか
   による。

2. **GraphAr の Apache Incubator status**: Apache Incubator project が graduation
   する確率は経験的に ~50%。失敗時に format spec が孤立する可能性がある。
   Phase 1 で D を採用する場合、GraphAr graduation 監視を mandatory にする必要が
   ある。

3. **Council bootstrap timeline との関係**: 2026-06-19 まで Council 5 seats が
   未確定。engine 選定は Council 5-of-7 multisig 必要 (ADR-2605192115)。本 ADR は
   Council 入力資料として保存される位置づけ。

4. **religious-corp owned engine の constitutional 価値**: ADR-2605192100 §1.12
   は "parallel substrate" を求めるが、それが engine ownership まで及ぶかは
   明文化されていない。GraphAr による format ownership で十分とするか、engine
   ownership まで求めるかが open question。

5. **upstream RW labs governance**: Kotoba/Datomic Labs の license 政策変化リスクは
   2025-2026 時点では低い (core は Apache 2.0 維持) が、Materialize の BSL 転換例
   もあり 5 年スパンでは zero とは言えない。リスクヘッジを fork で取るか pin で
   取るかの判断保留。

## Open questions

1. **GraphAr の religious-corp 拡張**: vertex/edge メタに DID-bound capability /
   encryption envelope を埋め込めるか? Apache GraphAr に upstream 提案するか、
   religious-corp 固有 extension にするか?

2. **Witness quorum と GraphAr chunk hash**: Hummock SSTable epoch hash と
   GraphAr chunk CID をどう統合して L2 anchor に書くか? (ADR-2605231500 §
   "rebuild" との整合)

3. **Arrow Flight UDF Server の religious-corp 化**: pymagatama 18,345 agents を
   一つの UDF Server にまとめるか、agent 毎に分離するか? Resource isolation と
   coldstart の trade-off。

4. **GraphQL Subscription と barrier alignment**: RW MV → WebSocket の
   live query が religious-corp の epoch barrier とどう同期するか? GraphQL
   client が見る "現在" は どの epoch か?

5. **Mac Silicon GPU 上の MLX runtime stability**: religious-corp scale (24/7
   inference) で MLX が production stable か? llama.cpp Metal vs MLX vs Ollama
   の選定根拠を benchmark で固める必要。

6. **Lance を本当に外したか**: vector similarity が religious-corp で需要が出る
   場合 (例えば信者の baien profile matching、agent skill search) どう対応するか?
   GraphAr に vector column 追加で対応するか、pgvector projection 別途立てるか?

7. **Solidity contracts との接続**: religious-corp Constitution.sol / TitheRouter
   / LandRegistry / PublicFund / ForceAuthorization が emit する Base L2 event
   をどう kotoba-datomic MV に取り込むか? RW Postgres CDC source の Base L2 版が
   必要。

## Decision

**No decision adopted in this ADR.**

This ADR captures the analytical record. A future ADR (provisionally
`ADR-26MMDDHHHHMM-kotoba-datomic-engine-selection`) will reference this document
and adopt one of Option A / B / D (or a Phase 1 D → Phase 4 A evolutionary
path) once:

- Council 5-of-7 multisig approval is available (post-2026-06-19)
- GraphAr Apache Incubator graduation outlook is clarified
- Mac Silicon MLX production benchmarks are available
- religious-corp constitutional weight on engine ownership (vs format
  ownership) is settled

## Consequences (of leaving decision open)

### Positive

- **Records the analytical work** so future ADRs can reference it without
  redoing the comparison.
- **No premature commitment** to a path that may not survive Council review or
  upstream license changes.
- **Preserves optionality** — Phase 1 D, Phase 4 A are still both reachable
  starting from the current scaffold (`20-actors/etzhayyim-sdk/`,
  `50-infra/murakumo/`).

### Negative

- **Engineering cannot start substrate-engine work** until decision ADR lands.
  Mitigation: `20-actors/etzhayyim-sdk/src/checkpointer.ts` work and
  `50-infra/etzhayyim-{did-web,mst-projector,ipfs-pinner,...}` scaffold can
  proceed substrate-engine-agnostic.
- **GraphAr ecosystem might evolve** between this ADR and the decision ADR
  (Apache Incubator graduation, breaking format changes). Track in
  `90-docs/_registry/external-dependencies.json` (pending tooling).

### Neutral

- **Does not amend** ADR-2605172000 / 2605231400 / 2605231500. Their semantics
  remain intact regardless of engine choice.
- **Does not constrain** the LangGraph checkpointer interface in
  `20-actors/etzhayyim-sdk/src/checkpointer.ts` — it stays
  engine-agnostic via dependency injection.

## Alternatives considered

See **Options considered** section above. Five options surveyed (A, B, C, D, E),
plus seven bulk-graph framework alternatives rejected or deferred.

## Implementation plan (decision-pending)

No implementation in this ADR. The following follow-up tasks are decision-pending:

| # | Step | Trigger | Owner |
|---|---|---|---|
| 1 | This exploratory ADR | this session 2026-05-23 | shipped |
| 2 | Update `10-protocol/kotoba-datomic/SPEC.md` to reference this ADR as engine-options input | follow-up | doc maintainer |
| 3 | GraphAr graduation watch entry in `90-docs/_registry/external-dependencies.json` | tooling exists | follow-up |
| 4 | MLX production benchmark on `mac-mini-01` (`50-infra/murakumo/fleet.toml`) | hardware available | infra |
| 5 | Council 5-of-7 deliberation packet referencing this ADR | post 2026-06-19 | Jun Kawasaki |
| 6 | Decision ADR (`ADR-26MMDDHHHHMM-kotoba-datomic-engine-selection`) | Council vote complete | TBD |

## Future Work

- **Decision ADR**: as above.
- **GraphAr religious-corp extension proposal**: if Option D advances, draft an
  Apache GraphAr community proposal for DID-bound capability + encryption
  envelope metadata.
- **yata-slate fork governance ADR**: if Option A advances, define release
  cadence, upstream sync policy, Charter Rider applicator integration.
- **Pregel multi-scale ADR**: formalize L1 (LangGraph) / L2 (RW barriers) / L3
  (GraphScope future) / L4 (MST commit) as a nested Pregel system. This may
  itself be a substrate-design ADR independent of engine choice.

## References

- ADR-2605172000 (etzhayyim RW-free substrate boundary)
- ADR-2605172100 (etzhayyim payment substrate hard rules)
- ADR-2605181100 (encrypted records on MST)
- ADR-2605192100 (etzhayyim mission charter — constitutional invariants)
- ADR-2605192115 (Council 5-of-7 multisig + Public Fund)
- ADR-2605192200 (Apache 2.0 + Charter Compliance Rider v2.0)
- ADR-2605192415 (religious-corp daemon architecture — Murakumo cells)
- ADR-2605231400 (kotoba-datomic Holochain-iso substrate)
- ADR-2605231500 (kotoba-datomic-projection — derived read paths)
- ADR-2605171300 (magatama unispsc LangGraph agents — 18,345 cells)
- ADR-2604241342 (Kotoba/Datomic out-of-band migration pattern — historical RW usage record)

External:

- Kotoba/Datomic (Apache 2.0): https://github.com/kotobalabs/kotoba
- Apache GraphAr (Apache 2.0, Incubator): https://github.com/apache/incubator-graphar
- SlateDB (Apache 2.0): https://github.com/slatedb/slatedb
- GraphScope (Apache 2.0): https://github.com/alibaba/GraphScope
- LangGraph Pregel: https://langchain-ai.github.io/langgraph/concepts/low_level/
- MLX (Apple, Apache 2.0): https://github.com/ml-explore/mlx
- Ollama / llama.cpp: https://github.com/ollama/ollama
