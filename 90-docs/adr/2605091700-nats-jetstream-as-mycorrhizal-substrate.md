---
id: adr-2605091700-nats-jetstream-as-mycorrhizal-substrate
title: "ADR-2605091700: NATS JetStream as Mycorrhizal Connective Substrate"
status: active
doc_type: adr
topic: nats-jetstream-mycelium
authoritative: true
last_verified: 2026-05-13
priority: 8.7
axis: architecture
weight: 0.87
priority_note: "CRITICAL — biological architecture コミットメントに沿った唯一の messaging broker、kabi actor の hyphal network 物理層"
authoritative_for:
  - inter-cell chemical signaling substrate (NATS JetStream)
  - subject hierarchy convention (mitama.{actor}.{kind}.>, bonsai.water.>, gradient.flow.>, etc.)
  - retention model (memory-bounded short-term, file-bounded long-term)
  - RW NATS source integration pattern (CREATE TABLE FROM nats)
  - rejection of Kafka/Redpanda for inter-cell signaling
related:
  - adr-2605091400-mcp-as-cell-membrane-lexicon-xrpc-demotion
  - adr-2605091500-mycorrhizal-watering-consent-gated-mutation
  - adr-2605091600-plasmid-graft-horizontal-tool-acquisition
  - adr-2605092200-continuous-metabolic-training
  - adr-2605092500-reasoning-as-sap-flow-walk
  - adr-2605071200-myco-yeast-artificial-organism-jp-naming
  - adr-2605072000
  - adr-2605080000-distributed-cognitive-actor-system
  - adr-2605091300-bonsai-cultivar-layer-above-myco-yeast
supersedes: []
superseded_by: []
---

# ADR-2605091700: NATS JetStream as Mycorrhizal Connective Substrate

**Status**: accepted
**Date**: 2026-05-09
**Deciders**: Jun Kawasaki (etzhayyim authority via etzhayyim agent)

## Context

Platform 全体で Kotoba/Datomic への INSERT を直接打つ writer (PDS Worker / Mitama
actor / SpiffWorkflow worker / LangGraph node / OSM bulk ingester) が多数
存在し、以下の構造的問題を抱える:

1. **RW recovery cascade で writer が死ぬ** — 2026-05-08/09 の世界 OSM
   ingest で 7+ 回観測。"database 1 reset" cascade で in-flight pod が一掃。
2. **Layer 違いの retention 要件混在** — T1 (PDS, <500ms) / T2 (Mitama,
   <30s) / T3 (OSM bulk, minutes) を 1 RW に直接ぶつけて互いに圧迫。
3. **Bio-architectural mismatch** — 既存 ADR (cell-membrane MCP /
   mycorrhizal-watering / sap-flow / continuous-metabolic-training /
   saikin horizontal-transfer / kabi anastomosis) は明示的に
   "decentralized chemical signaling + continuous gradient" の生命科学
   モデルに platform をコミットしている。Kafka/Redpanda の
   topic-partition + leader-follower は "engineered nervous system" で
   生命組織の phenotype に合わない。

## Decision

> **NATS JetStream を platform の inter-cell chemical signaling
> substrate (= mycorrhizal connective tissue) として採用する。**
> kabi (カビ/Fungi) actor が論理的に運用する hyphal network の物理層。

### Why NATS over Kafka/Redpanda (10-axis bio fit score)

| Axis | NATS | Kafka/Redpanda |
|---|---|---|
| 受容体性 (subject wildcard pattern matching) | 9 | 6 |
| 分散性 (leaderless gossip mesh) | 10 | 5 |
| 連続勾配 (streaming continuous values) | 6 | 4 |
| 多態 fan-out (pleiotropic 1-to-many) | 10 | 5 |
| 化学走性 (content-addressed routing) | 9 | 4 |
| 自己組織化 (no central coordinator) | 9 | 3 |
| 階層 subject (hierarchical naming `a.b.c.*`) | 10 | 4 |
| 異 anastomosis (network merge / topology evolution) | 8 | 3 |
| overhead (lightweight footprint) | 9 (17MB Go binary) | 5 (JVM 1GB+) |
| platform 哲学 fit | 9 | 4 |
| **合計** | **89/100** | **43/100** |

NATS は `bash` 1 binary、cluster は gossip mesh (leaderless)、subject
wildcard `mitama.kabi.hyphal.signal.>` が **chemoreceptor selectivity**
そのもの。Kafka の topic-partition モデルは axon/synapse の neural
engineering metaphor で、生命組織の網状 / 分散 / 多態的な signaling
には合わない。

## Biological Mapping

| 生命層 | NATS feature | 既存 ADR 整合 |
|---|---|---|
| 細胞間 chemical signaling | subject hierarchy | ADR-2605091400 (MCP-as-cell-membrane) |
| 菌糸 anastomosis (網融合) | cluster gossip mesh | ADR-2605071200 (kabi anastomosis) |
| Pheromone broadcast | subject wildcard `*` / `>` | ADR-2605091400 |
| Morphogen gradient persistence | JetStream durable stream | ADR-2605092200 (continuous-metabolic-training) |
| Chemotactic 受容体特異性 | subject hierarchy 階層マッチング | ADR-2605091500 (mycorrhizal-watering) |
| Spore dispersal | subject `spore.dispersal.>` | ADR-2605092100 (lora-per-cell-moe) |
| Quorum sensing | NATS queue group | ADR-2605072000 (saikin-bacteria) |
| Plasmid horizontal transfer | NATS KV bucket | ADR-2605091600 (plasmid-graft) |
| 細胞膜 (lightweight protocol) | 17MB Go binary | ADR-2605091400 |
| Sap-flow / gradient propagation | stream interest + consumer pull | ADR-2605092500 (reasoning-as-sap-flow) |

## Subject Hierarchy Convention (authoritative)

| Subject pattern | Stream | Bio meaning | Tier |
|---|---|---|---|
| `mitama.{actor}.{kind}.>` | MITAMA | Per-actor cell-cell signaling | T2 |
| `bonsai.water.>` | BONSAI_WATER | Mycorrhizal watering signal (consent-gated) | T2 |
| `gradient.flow.>` | GRADIENT_FLOW | Continuous metabolic gradient (training signal) | T2 |
| `pds.repo.>` | PDS_REPO | T1 hot path PDS commits/records | T1 |
| `ingest.osm.>` | INGEST_OSM | T3 cold path OSM bulk ingest | T3 |
| `spore.dispersal.>` | SPORE | Houshi propagation / AT firehose 拡散 | T2 |
| `anastomosis.>` | ANASTOMOSIS | Hyphal fusion events (kabi network merge) | T2 |
| `com.etzhayyim.apps.>` | LG_DISPATCH | LangGraph graph invocation dispatch (pull consumer per graph, WorkQueue, memory store) | L7 |

Future additions follow the same convention: `{domain}.{kind}.{further...}`.

## Topology (current 2026-05-09)

```
Production cluster: 1 replica (Vultr block storage account quota)
  - StatefulSet: nats-0 (Running, 2/2)
  - PVC: nats-js-nats-0 10Gi vultr-block-storage (bound)
  - File store: 10 GiB (durable streams future)
  - Memory store: 512Mi (current production stream backend)

  Resources:
    requests: 50m CPU / 128Mi memory
    limits:   1000m CPU / 1Gi memory

  Service:
    nats.nats.svc.cluster.local:4222   (client + cluster + JetStream)
    monitor.nats.nats.svc.cluster.local:8222  (health/metrics)
```

HA (3-node cluster) は Vultr block storage quota が増えた時点で復活。
1-replica 状態は本格 production 前の **soak phase** とみなす。

## Kotoba/Datomic Integration (verified 2026-05-09)

RW v2.8.x has **native NATS JetStream source** (`src/connector/src/source/nats/`).
End-to-end pattern (CREATE TABLE form, verified working):

```sql
CREATE TABLE tbl_gradient_flow (
  signal VARCHAR,
  weight DOUBLE PRECISION,
  src VARCHAR,
  dst VARCHAR
) WITH (
  connector = 'nats',
  server_url = 'nats.nats.svc.cluster.local:4222',
  subject = 'gradient.flow.>',
  stream = 'GRADIENT_FLOW',
  connect_mode = 'plain',
  "consumer.durable_name" = 'rw_gradient_flow'
) FORMAT PLAIN ENCODE JSON;
```

注意点 (本検証で発見):
- `type = 'append-only'` は `CREATE SOURCE` 専用、`CREATE TABLE` ではエラー
- `consumer.durable_name` (dotted property) は double-quote 必須
- `CREATE SOURCE` は `consumer.durable_name` が必須 (見つからないと
  "missing field" でエラー)、`CREATE TABLE` は同フィールドの quoting で
  動く

End-to-end pub/sub verified:
```
nats pub gradient.flow.test '{"signal":"fruit-accept","weight":1.0,"src":"...","dst":"..."}'
                              ↓
SELECT * FROM tbl_gradient_flow;  -- row visible <8s
```

## Migration Strategy

| Phase | What | Status |
|---|---|---|
| 0 | NATS deploy (1 replica, 7 streams) | ✓ done 2026-05-09 |
| 1 | RW NATS source 1 stream PoC (gradient.flow) | ✓ done 2026-05-09 |
| 2 | Mitama 1 actor pilot — shinshi audit subject e2e verified (5/5 events, <12s) | ✓ done 2026-05-09 |
| 3 | All Mitama actors → NATS publish via bpmn-dispatcher fan-out (subject `mitama.{nsid}`) | ✓ done 2026-05-09 (code landed, image rebuild required) |
| 4 | T3 OSM ingest → NATS publish (RW table `tbl_ingest_osm_element` ← `ingest.osm.element.>` verified) | ✓ infra + RW source done 2026-05-09; v0.5.0 ingester rewrite TODO |
| 5 | T1 PDS commits → NATS publish (firehose-to-NATS bridge scaffold + RW source verified) | ✓ infra+RW done 2026-05-09; bridge image build TODO |
| 6 | LangGraph pull consumer pattern — lg-animeka `NatsConsumerManager` (stream `LG_DISPATCH`, subjects `com.etzhayyim.animeka.{autopilot\|cutRunner\|autoTraceCut\|breakdownScene}`, WorkQueue retention, memory store, max_age=1h). CronJob replaced by `nats pub` (nats-box). APScheduler disabled. 0.1.9 deployed 2026-05-13. | ✓ done 2026-05-13 |
| 7 | HA expand: 3-node cluster (Vultr quota lift required) | TODO |

Rejected alternatives (see comparison table in §Decision):
- Kafka / Redpanda: bio-architectural mismatch (43/100 score)
- Pulsar: overkill (4/10 platform fit)
- MQTT: volume insufficient for OSM bulk
- Pure RW direct INSERT: current state, fails under cascade
- Debezium PG CDC + Kafka: extra layer, less bio-fit

## Consequences

**Pro**:
- Writer crash isolation (RW down → buffered in NATS, replay on recover)
- Bio-architectural commitment fully expressed at infra layer
- $0 marginal cost (replaces would-be Redpanda $80/mo)
- Lightweight (17MB binary, ~50m CPU production observed)
- Native subject hierarchy = chemoreceptor pattern
- RW native source = no bridge layer

**Neg**:
- 1-replica HA gap until Vultr block quota lift (~1 broker fail = full outage during transition)
- File store quota 10Gi tight; current production uses memory store (loses on pod restart)
- Migration is **opt-in per writer** — both PG-direct and NATS-mediated
  paths coexist during Phase 2-5
- Operators need to learn NATS CLI (`nats stream`, `nats consumer`)

**Reversibility**: high. NATS streams are independent of RW state;
deleting them does not affect existing tables. Writers can revert to
direct INSERT by changing target.

## References

- ADR-2605091400 — MCP as cell membrane (external receptor)
- ADR-2605091500 — Mycorrhizal watering consent-gated mutation
- ADR-2605091600 — Plasmid graft horizontal tool acquisition
- ADR-2605092200 — Continuous metabolic training (gradient_flow)
- ADR-2605092500 — Reasoning as sap-flow walk
- ADR-2605071200 — Myco-yeast organism (kabi anastomosis)
- ADR-2605072000 — Saikin bacteria horizontal transfer
- ADR-2605080000 — Distributed cognitive actor system
- RW source: `src/connector/src/source/nats/mod.rs` (verified 2026-05-09)
- NATS Helm chart: `nats/nats v2.12.6` (Apache 2.0)
- Live values: `50-infra/vultr/nats/values.yaml`

## Verification queries

```sql
-- list NATS-fed RW tables/sources
SELECT name FROM rw_catalog.rw_sources WHERE name LIKE 'src_%';
SELECT relname FROM pg_class WHERE relname LIKE 'tbl_%';

-- NATS streams
-- kubectl -n nats exec deploy/nats-box -- nats stream ls --server=nats://nats:4222
```
