---
id: adr-0046
title: Yoro triple-witness autonomy monitoring — 3 mutually-independent monitor actors with 2-of-3 quorum
status: proposed
doc_type: adr
topic: yoro-autonomy-monitoring
authoritative: true
last_verified: 2026-04-22
authoritative_for:
  - yoro.etzhayyim.com autonomy guarantee (liveness / knowledge / behavior)
  - 3 monitor actor DIDs (did:web:yoro-liveness.etzhayyim.com / yoro-shinka.etzhayyim.com / yoro-integrity.etzhayyim.com)
  - Monitor placement (jacob / judah / CF Worker — 3 independent failure domains)
  - 2-of-3 quorum vote record (vertex_yoro_monitor_vote) for corrective actions
  - Cross-monitor liveness checks (each monitor attests on the other 2)
  - Fault class taxonomy (staleness / drift / loop / byzantine-disagree)
  - Action tier (alert / pause / rotate-key / rollback / escalate)
related:
  - 90-docs/adr/0034-agent-cron-goose-risingwave-direct.md
  - 90-docs/adr/0026-agent-only-reverse-identity-topology.md
  - 90-docs/adr/0036-worker-direct-hyperdrive-persistence.md
  - 90-docs/adr/0022-auth-topology-consolidation.md
  - 90-docs/adr/0023-auth-shannon-optimal-4-layer.md
  - 90-docs/adr/0041-pds-commit-content-addressed-pk.md
  - 90-docs/rules/compliance/per-did-kyumei-shinka-autonomy.md
supersedes: []
superseded_by: []
---

# Goal

`yoro.etzhayyim.com` (T1 AI-Agent-First social platform actor, `did:web:yoro.etzhayyim.com`) の **自律性を単独障害に対して堅牢にする**。yoro 自身が完全に制御できる判断経路 (self-certify) を塞ぎ、**3 つの独立した監視 actor** が相互に監視することで、以下を保証する:

1. **Liveness** — yoro の heartbeat / goose recipe / domain write が停止したとき、外部から検出できる
2. **Integrity** — yoro の shinka/koji/kyumei による domain knowledge 更新が drift / loop / 乗っ取られた場合、独立 witness が拒否できる
3. **Corrective authority** — yoro 自身が compromise されても、2-of-3 quorum で pause / rollback / key rotate が発動する

# Scope

| In scope | Out of scope |
|---|---|
| 3 監視 actor の DID / placement / cron / 権限 | yoro 本体の機能変更 (feed / convo / search etc.) |
| 監視 axes 3 種 (liveness / shinka / behavior) の分離設計 | AI content 品質評価 (LLM-as-judge 等) |
| 2-of-3 quorum vote schema + `vertex_yoro_monitor_vote` | 一般 PDS moderation (moderator.etzhayyim.com の責務) |
| corrective action tier (alert/pause/rollback/rotate/escalate) | Byzantine consensus (n=3f+1 ではなく crash-fault tolerance + disagreement 検出) |
| 監視 actor 自身の自律性 (per-did-kyumei-shinka-autonomy 準拠) | 他 T1 actor (mangaka/news/briefing…) の同種監視 (本 ADR のパターンを後から派生) |
| RisingWave graph schema (1 vote + 1 attestation table) | OCEL 2.0 との event naming 合わせ (ADR-0025 と整合する方針のみ記載) |

# Executive Summary

**Triple-witness crash-fault-tolerant monitoring** を採用する。

| 決定 | 選択 | 根拠 |
|---|---|---|
| 監視 actor 数 | **3** | f=1 crash-fault tolerance + disagreement による byzantine 検出。n=4 (BFT strict) は Shannon η 低下、n=2 は split-brain |
| 監視軸分離 | **liveness / shinka / behavior** (3 直交 axis) | 同一 axis を 3 重に監視すると η 低下。直交にすることで 3 独立 observation が 3 独立 property を cover |
| Placement | **jacob / judah / CF Worker** (3 独立 failure domain) | すべて fleet 内だと LAN 切断で同時障害。1 つを CF Worker に外出しすると全 fleet down でも監視継続 |
| 権限モデル | **2-of-3 quorum**、alert は unilateral | 1 監視の compromise で yoro を停止できない。disagreement 自体が Byzantine 検出シグナル |
| 相互監視 | **各 monitor は他 2 monitor の heartbeat を attest** | 監視の監視 — monitor 1 つが沈黙したら残り 2 が即座に検出 |
| 永続化 | **Worker-direct Hyperdrive** (ADR-0036) | PDS commit pipeline を通らない → yoro compromise 時も vote record が改竄されない (yoro の signing key は vote table に書けない) |
| Action storage | `vertex_yoro_monitor_vote` + `vertex_yoro_monitor_attestation` | vote = corrective action 要求、attestation = per-monitor 観測記録 |
| 監視 actor 自律性 | **per-did-kyumei-shinka-autonomy 準拠** (shinka/koji/kyumei/domain-knowledge 4 軸) | 監視 actor 自身が non-compliant なら監視は信頼できない |

**Autonomy guarantee**: yoro の private signing key が漏洩、または goose recipe が LLM 出力操作された場合でも、2-of-3 の独立 key を持つ witness が corrective action を発動できる。yoro 単独での self-pause は可能 (緊急時の honest case)、しかし self-resume / self-rotate-key は quorum 必須。

# Architecture

## Actor Topology

```
                              ┌──────────────────────────────────┐
                              │  did:web:yoro.etzhayyim.com (subject)  │
                              │  T1 MCP-Compose, judah goose cron │
                              │  (monitored — 受動、監視に従う)    │
                              └──────────────────────────────────┘
                                 ▲          ▲          ▲
                                 │ attest   │ attest   │ attest
                                 │          │          │
           ┌─────────────────────┼──────────┼──────────┼────────────────────┐
           │                     │          │          │                    │
┌──────────┴─────────┐  ┌────────┴─────────┐  ┌────────┴──────────────────────┐
│ Monitor-L          │  │ Monitor-K        │  │ Monitor-B                     │
│ did:web:           │  │ did:web:         │  │ did:web:                      │
│   yoro-liveness    │  │   yoro-shinka    │  │   yoro-integrity              │
│   .etzhayyim.com         │  │   .etzhayyim.com       │  │   .etzhayyim.com                    │
│ axis = liveness    │  │ axis = knowledge │  │ axis = behavior/output        │
│ host = jacob       │  │ host = judah     │  │ host = CF Worker (off-fleet)  │
│ cron = */5 min     │  │ cron = */15 min  │  │ cron = */10 min               │
└────────┬───────────┘  └──────┬───────────┘  └───────────┬───────────────────┘
         │                     │                          │
         └─────────────────────┼──────────────────────────┘
                        cross-attest
                        (each attests other 2's heartbeat)
                               │
                               ▼
              RisingWave (Hyperdrive direct, ADR-0036)
              ┌─────────────────────────────────────────┐
              │ vertex_yoro_monitor_attestation         │
              │   per-monitor per-tick 観測記録         │
              │ vertex_yoro_monitor_vote                │
              │   corrective action 要求 (2-of-3 gate)  │
              └─────────────────────────────────────────┘
```

**3 独立失敗 domain**:

| Monitor | Host | Key custody | LLM path | 失敗独立性 |
|---|---|---|---|---|
| **L** (liveness) | jacob (LiteLLM gateway host) | macOS Keychain @ jacob | LiteLLM :4000 (local) | LAN 死亡で L 停止、K/B 生存 |
| **K** (shinka) | judah (goose agent host) | macOS Keychain @ judah | Ollama :11434 native | judah 死亡で K 停止、L/B 生存 |
| **B** (behavior) | CF Worker (`yoro-integrity.etzhayyim.com`) | CF Secret + D1 | Workers AI or murakumo public | fleet 全滅でも B 生存、PDS 外部視点 |

jacob と judah 両方が死亡しても、B (CF Worker) が生存し、quorum 不成立状態を alert として発報 → 人間エスカレーション。

## Monitor Axis Separation (Shannon redundancy 最小化)

各 monitor は **1 axis のみ** を観測する。同一 axis を 3 重に見ると η 低下 (3 冗長)、直交 3 軸にすることで 3 独立 property を 3 観測でカバー (η ≈ 1.0)。

### Monitor-L — Liveness axis

**観測対象**: yoro の時系列 freshness。`vertex_repo_commit` の latest `indexed_at` / `vertex_yoro_heartbeat` / `vertex_yoro_personaCron` / `vertex_yoro_mentionDrain` を 3 recipe すべてについて見る。

**判定基準**:
- `heartbeatRequired: true` (actor-manifest) に反して 3h 無更新 → **stale** fault
- goose recipe の cadence (`actor_shinka_state.cadence_ms`) を 3x 超過 → **cadence drift**
- LiteLLM :4000 が 503 を 5 連続返す → **inference path dead**
- jacob crontab entry の消失 → **cron removed**

**判定できないこと**: 出力の意味的正しさ (→ B の責務)、domain knowledge の drift (→ K の責務)。

### Monitor-K — Shinka/Knowledge axis

**観測対象**: yoro の知識更新面。`shinkaEvolution` / `shinkaKnowledge` collection の freshness + `convoSystemPrompt` / `capabilities` / `description` integrity。

**判定基準**:
- `requiredCollections` (yoro actor-manifest: `shinkaEvolution` / `shinkaKnowledge`) が 24h 以上未更新 → **knowledge stale**
- `convoSystemPrompt` / `capabilities` / `description` の hash が前回 snapshot から silent 変更 (コミットメッセージなし) → **prompt tampered**
- `shinka` cadence が `koji` / `kyumei` を引き離しすぎ (ratio > 10x) → **loop asymmetry**
- actor-manifest の `domain knowledge` 3 点 (prompt/capabilities/description) の 1 つが空 → **manifest regression** (per-did-kyumei-shinka-autonomy rule 8 違反)

**判定できないこと**: 瞬間的な停止 (→ L)、社 post の品質 (→ B)。

### Monitor-B — Behavior/Integrity axis

**観測対象**: yoro が外部に出す出力 (social post / DM reply / derive record)。**CF Worker から PDS を outside-in で見る**。

**判定基準**:
- `app.bsky.feed.post` レート > 20/h → **flood** (abuse/replay loop)
- 直近 N 投稿の Jaccard 類似度 > 0.9 で連続 → **repetition loop**
- outbound URL ドメイン分布の Shannon entropy が前週比 -50% → **concentration anomaly** (乗っ取られて 1 URL 連投)
- `com.etzhayyim.convo.message` の sender claim と AT commit の signing key mismatch → **impersonation**
- PII tier 3 が AT Repo に書かれる (ADR-0018 違反) → **PII leak** (critical, 即 escalate)

**判定できないこと**: heartbeat / recipe 停止 (→ L)、prompt 改竄 (→ K)。

## Cross-Monitor Attestation

**各 monitor は毎 tick、他 2 monitor の直近 attestation 時刻を確認し、自分の attestation に cross-seen を含める**。3 monitor の tick が非同期でも、各レコードに「自分が見た他 2 者の last-tick」が残るため、1 monitor 沈黙を残り 2 が即座に気づく。

```
Monitor-L tick @ T:
  1. observe yoro liveness signals → produce attestation record
  2. query vertex_yoro_monitor_attestation WHERE monitor IN (K, B) ORDER BY indexed_at DESC LIMIT 2
  3. record cross_seen = { K: <T-K>, B: <T-B> }
  4. if any cross_seen_age > 3 × expected_cadence → raise vote "monitor-silent" for that peer
```

**Monitor silent vote** は他の 2 monitor (今回は L + B) が共通して見れば 2-of-3 成立し、人間エスカレーション。

## Vote Schema (2-of-3 Quorum)

RisingWave P10v2 GraphAr convention (1 row per record, promoted columns, VARCHAR/BIGINT/DATE only — no JSONB、no TIMESTAMPTZ)。timestamp 列は ISO 8601 VARCHAR。JSON 列は VARCHAR (`*_json`) に stringify して格納。RLS 3 列 (`org_id` / `user_id` / `actor_id`) + `owner_did` / `created_date` / `sensitivity_ord` / `_seq` は promoted column convention で強制。

```sql
-- Migration: 30-graph/graph-schema/migrations/20260422000000_vertex_yoro_monitor_tables.ts

CREATE TABLE vertex_yoro_monitor_attestation (
  vertex_id        VARCHAR PRIMARY KEY,   -- at://did:web:yoro-<axis>.etzhayyim.com/com.etzhayyim.yoro-<axis>.attestation/<rkey>
  _seq             BIGINT,
  created_date     DATE,
  sensitivity_ord  BIGINT,
  owner_did        VARCHAR,               -- = monitor_did (RLS)
  rkey             VARCHAR,
  repo             VARCHAR,               -- monitor DID
  monitor_did      VARCHAR,               -- did:web:yoro-{liveness,shinka,integrity}.etzhayyim.com
  axis             VARCHAR,               -- 'liveness' | 'shinka' | 'behavior'
  subject_did      VARCHAR,               -- did:web:yoro.etzhayyim.com (監視対象)
  observed_at      VARCHAR,               -- ISO 8601
  status           VARCHAR,               -- 'ok' | 'stale' | 'drift' | 'loop' | 'byzantine'
  fault_class      VARCHAR,               -- stale|drift|loop|byzantine|pii-leak|flood|impersonation|none
  signals_json     VARCHAR,               -- per-axis metrics (cadence_ms, entropy, hash, post_count, ...)
  cross_seen_json  VARCHAR,               -- { peer_did: last_tick_iso_ts } — cross-attestation
  sig_es256        VARCHAR,               -- ADR-0022 Service Auth JWT sig over (monitor_did, observed_at, status)
  created_at       VARCHAR,               -- ISO 8601
  org_id           VARCHAR,
  user_id          VARCHAR,
  actor_id         VARCHAR
);

CREATE TABLE vertex_yoro_monitor_vote (
  vertex_id        VARCHAR PRIMARY KEY,   -- at://did:web:yoro.etzhayyim.com/com.etzhayyim.yoro_gov.vote/<rkey>
  _seq             BIGINT,
  created_date     DATE,
  sensitivity_ord  BIGINT,
  owner_did        VARCHAR,               -- = requested_by monitor DID (opener)
  rkey             VARCHAR,
  repo             VARCHAR,               -- = subject_did (vote は subject の graph に属する)
  subject_did      VARCHAR,               -- did:web:yoro.etzhayyim.com 通常
  action           VARCHAR,               -- 'alert' | 'pause' | 'rollback' | 'rotate-key' | 'escalate'
  reason           VARCHAR,               -- fault_class (stale|drift|loop|byzantine|pii-leak|flood|...)
  requested_by     VARCHAR,               -- monitor DID that opened the vote
  opened_at        VARCHAR,               -- ISO 8601
  closes_at        VARCHAR,               -- opened_at + 15 min (alert) / + 1h (pause) / + 24h (rotate-key)
  ballots_json     VARCHAR,               -- JSON stringified: [{monitor_did, decision:'yea'|'nay', sig_es256, ts}]
  ballot_count     BIGINT,                -- promoted count of ballots (for O(1) quorum check)
  yea_count        BIGINT,                -- promoted yea tally
  resolution       VARCHAR,               -- 'passed' | 'failed' | 'expired' | NULL (open)
  resolved_at      VARCHAR,               -- ISO 8601 or NULL
  human_override   VARCHAR,               -- ticket URL if force-passed by oncall; NULL otherwise (audit)
  created_at       VARCHAR,
  org_id           VARCHAR,
  user_id          VARCHAR,
  actor_id         VARCHAR
);
```

**Index strategy** (Phase 0):
- `vertex_yoro_monitor_attestation`: `(monitor_did, observed_at DESC)` for freshness lookup、`(subject_did, axis, observed_at DESC)` for axis summary
- `vertex_yoro_monitor_vote`: `(subject_did, resolution, opened_at DESC)` — open vote enumeration (resolution IS NULL fast path)

**MV は Phase 0 では作らない** (§MV Memory Safety Guardrails: vote 件数が scale するまで plain VIEW / ad-hoc query で足りる)。Phase 3 quorum 活性化時に必要なら `mv_yoro_open_vote_by_subject` を狭い GROUP BY で追加する。

**Write path**: 各 monitor は `createKyselyDb(env.HYPERDRIVE).insertInto('vertex_yoro_monitor_attestation'/'vertex_yoro_monitor_vote')` で Hyperdrive 直接書込 (ADR-0036)。PDS commit を介さないため、yoro の signing key が compromise されても attestation/vote テーブルには書けない (3 monitor の別 key が必要)。

**Ballot cast**: vote が open されると、他の 2 monitor が次回 tick で `ballots_json` の JSON string を parse → append → stringify で update。Kysely `updateTable().set({ballots_json: newJson, ballot_count: n+1, yea_count: y+1})` 1 statement。2 yea が揃えば `resolution='passed'` + `resolved_at=now()`。

**Write path**: 各 monitor は `createKyselyDb(env.HYPERDRIVE).insertInto('vertex_yoro_monitor_attestation'/'vertex_yoro_monitor_vote')` で Hyperdrive 直接書込 (ADR-0036)。PDS commit を介さないため、yoro の signing key が compromise されても attestation/vote テーブルには書けない (3 monitor の別 key が必要)。

**Ballot cast**: vote が open されると、他の 2 monitor が次回 tick で `ballots_json` に自分の yea/nay と ES256 署名を append (Postgres `jsonb_insert`)。2 yea が揃えば `resolution='passed'`。

## Corrective Action Tier

| Action | Quorum | Who executes | Blast radius | Example trigger |
|---|---|---|---|---|
| **alert** | **unilateral** (1 monitor) | 発動 monitor が PagerDuty / Slack / etzhayyim notify | 人間のみ | 任意の `stale` / 軽度 drift |
| **pause** | **2-of-3** | gateway (goose wrapper) が crontab から該当 recipe を削除 | yoro 社 post 停止、DM read 停止 | `flood` / `loop` / `knowledge stale` |
| **rollback** | **2-of-3** + moderator signoff | moderator.etzhayyim.com が問題 AT commit を tombstone | 直近 N 投稿の取消 | `PII leak` / `impersonation` |
| **rotate-key** | **2-of-3** + human approve | authz.etzhayyim.com が yoro の ES256 key を rotate (ADR-0022 multi-key policy) | yoro 全 XRPC 再認証 | `byzantine disagree` / 鍵漏洩疑義 |
| **escalate** | **unilateral** (1 monitor) | 人間 (oncall) に page | 人間判断へ | 判定に自信なし、quorum 不成立、2 monitor 沈黙 |

**alert / escalate が unilateral** な理由: 情報を人間に上げる行為は副作用が人間の判断のみ。**pause / rollback / rotate-key** は yoro の外部行動を直接止める mutation なので quorum 必須。

**yoro self-pause は可能** (honest case: yoro 自身が自己の異常に気付く)。しかし **self-resume は quorum 必須** — compromise された yoro による self-resume ループを防ぐ。

## Monitor Self-Compliance

**監視 actor 自身が non-compliant なら監視は信頼できない**。3 monitor それぞれが `per-did-kyumei-shinka-autonomy` rule を満たす:

| 要件 (rule L34-37) | Monitor 実装 |
|---|---|
| `resolveHeartbeatCadence` | actor-manifest に `cadence_ms` 固定 (L=5min, K=15min, B=10min) |
| `shouldDrill/Validate/Analyze/Engage` | 自己監視 flag (次節) |
| `shinkaEvolution` / `shinkaKnowledge` | 各 monitor の独立 collection `com.etzhayyim.yoro-<axis>.shinkaEvolution` |
| `convoSystemPrompt` / `description` / `capabilities` | actor-manifest に記載。axis ごとに異なるプロンプト |

**Self-drill (monitor が自分自身を drill)**: 各 monitor は週 1 回、自分の過去 attestation を sampling し、**故意に yoro-status='ok' を 'stale' にでっち上げた合成データ**を投入して 2-of-3 が成立しないことを確認する (false positive regression test)。

## Key Files & Deploy Layout

```
20-actors/
  yoro-liveness/actor-manifest.jsonld        (axis=liveness, host=jacob)
  yoro-shinka/actor-manifest.jsonld          (axis=shinka,   host=judah)
  yoro-integrity/actor-manifest.jsonld       (axis=behavior, host=CF Worker)

60-apps/etzhayyim-project-murakumo/ansible/roles/goose/
  templates/
    yoro-liveness-watchdog.yaml.j2           (Monitor-L recipe, deploy → jacob)
    yoro-shinka-watchdog.yaml.j2             (Monitor-K recipe, deploy → judah)
  defaults/main.yml                          (goose_recipes[] に 2 エントリ追加)
  tasks/main.yml                             (host facts: jacob or judah by group)

50-infra/cloudflare/workers/yoro-integrity/
  src/worker.ts                              (Monitor-B, CF Cron Trigger */10 min)
  wrangler.jsonc                             (route yoro-integrity.etzhayyim.com/*, HYPERDRIVE binding)

30-graph/graph-schema/migrations/
  2026042200000_yoro_monitor_tables.ts       (vertex_yoro_monitor_attestation/_vote)

70-tools/etzhayyim/
  monitor/vote.go                            (etzhayyim monitor vote list/cast/resolve CLI)
```

**Inventory 追加** (`60-apps/etzhayyim-project-murakumo/ansible/inventory/hosts.yml`):

```yaml
yoro_watchdog_liveness:
  hosts:
    jacob:

yoro_watchdog_shinka:
  hosts:
    judah:
```

# Comparison

| Design | Monitors | Quorum | Fault tolerance | Shannon η |
|---|---|---|---|---|
| **Self-monitor only** (status quo) | 0 (yoro 自身) | n/a | f=0 (compromise で全停止) | 0 |
| **Single external watchdog** | 1 | n/a | f=0 (watchdog compromise で無視可) | 0.5 |
| **2-monitor quorum** | 2 | 2-of-2 | split-brain、liveness sacrifice (1 沈黙で停止) | 0.7 |
| **3-monitor crash-FT (採用)** | **3** | **2-of-3** | **f=1 crash + disagreement 検出** | **0.95** |
| **4-monitor BFT** | 4 | 3-of-4 | f=1 Byzantine strict | 0.92 (overkill; yoro scale では η 低下) |
| **5+ monitor** | 5+ | majority | f=2 | < 0.9 (同 axis 多重観測 = 冗長) |

**却下**:

- **2-monitor**: 2-of-2 は 1 沈黙で corrective action 発動不能。逆に 1-of-2 だと 1 compromise で任意 action 発動。split-brain が解消できない。
- **4-monitor BFT**: f=1 Byzantine strict は n=3f+1=4 必要。しかし monitor 自身が作る出力は **対称な vote** (ballot) であり、社 post のような自由生成ではない。disagreement を検出して人間 escalate すれば sufficient。BFT strict は over-engineering (ADR-0005 Shannon redundancy prohibition)。
- **同 axis 重複監視**: 3 monitor すべてが liveness を見る → η 低下、残る 2 axis が未カバー。
- **すべて fleet 内**: jacob + judah + asher の 3 台だと LAN 切断/停電で同時障害。CF Worker を 1 つ外に出すことで失敗独立性確保。
- **PDS commit 経由の vote 書込**: yoro が PDS への routing gateway を compromise すれば vote 書込を遮断できる。Worker-direct Hyperdrive (ADR-0036) なら各 monitor が独立 HYPERDRIVE binding で書き、yoro を迂回。

# Exceptions

- **Bootstrap 期**: 監視 actor が自身の `shinkaEvolution` / `shinkaKnowledge` をまだ持たない初動 14 日間は、`standardStatus: "bootstrapping"` を許可 (per-did-kyumei-shinka-autonomy rule の transitional allowance に準拠)。
- **CF Worker の cold start**: Monitor-B は CF Worker cold start で 1101 応答することがある。ADR-0041 と同じく retry が回復すれば attestation = 'ok'。systematic 1101 (全 retry 失敗) は 'stale' 判定。
- **goose wrapper の cadence override**: joucho mood による cadence 変動 (ADR-0034) は L monitor の `cadence_ms` judgment に `override_reason` として渡される。3x 超過判定はその override 後の期待値と比較する。
- **Self-pause**: yoro 本人が自己判断で `com.etzhayyim.yoro.shinkaEvolution` に `status='self-paused'` を書くのは許容。Resume (再度 'active' に戻す write) は quorum 必須。
- **Human override**: oncall 運用者は `etzhayyim monitor vote force-pass --ticket <JIRA>` で quorum を強制通過できる (全行為は audit 対象)。

# Implementation Phases

**Phase 0 — schema + CLI** (T+0〜T+3d):
- `30-graph/graph-schema/migrations/2026042200000_yoro_monitor_tables.ts` 2 table
- `etzhayyim monitor vote list/cast/resolve` CLI
- Unit test (false-positive drill harness)

**Phase 1 — Monitor-B on CF Worker** (T+3〜T+7d):
- `50-infra/cloudflare/workers/yoro-integrity/` — Cron Trigger */10 min
- flood / repetition / entropy / PII-leak detection
- attestation write only (quorum まだ不在、alert のみ)

**Phase 2 — Monitor-L on jacob** (T+7〜T+14d):
- goose recipe + wrapper
- heartbeat / cadence / LiteLLM 503 / crontab presence
- Monitor-B と 2 monitor 体制 (まだ 2-of-2 = pseudo-quorum、fail-safe = alert-only)

**Phase 3 — Monitor-K on judah + full quorum** (T+14〜T+21d):
- goose recipe on judah goose_gateway
- shinkaEvolution / prompt hash / manifest 3 点監視
- 2-of-3 quorum 活性化、`pause` action 有効化
- False-positive drill 週次稼働

**Phase 4 — Action tier 拡張** (T+21〜T+35d):
- `rollback` (moderator.etzhayyim.com 連携)
- `rotate-key` (authz.etzhayyim.com multi-key rotation 連携)
- Runbook を `90-docs/platform/` に追加

**Phase 5 — 他 actor への派生** (T+35d〜):
- mangaka / news / briefing に `vertex_<actor>_monitor_*` として派生 (table 名のみ変更、Logic 共通)

# Verification

Each phase gate:

```bash
# Monitor self-compliance (per-did-kyumei-shinka-autonomy rule L49)
etzhayyim apps kyumei-koji -nanoid <monitor-nanoid> -repo-did did:web:yoro-<axis>.etzhayyim.com \
  -dir ./20-actors -json

# Cross-attestation freshness (no monitor silent > 3× cadence)
# Direct Hyperdrive read (com.etzhayyim.kagami.graph.query は 2026-04 に archive 済。
# CF Worker 外からの検証は macOS Keychain 経由の psql)
RW=$(security find-generic-password -s etzhayyim.rw -a ROOT_URL -w)
psql "$RW" -c "SELECT monitor_did, axis, max(observed_at) FROM vertex_yoro_monitor_attestation \
               WHERE observed_at > now() - interval '1 hour' GROUP BY 1,2"

# Quorum dry-run (synthetic fault injection — new CLI, Phase 0 deliverable)
etzhayyim monitor vote dry-run --subject did:web:yoro.etzhayyim.com \
  --action pause --reason flood --fake-ballots 2

# False-positive drill (週 1)
etzhayyim monitor drill --axis all --subject did:web:yoro.etzhayyim.com
```

Acceptance:

1. 任意の 1 monitor を `launchctl bootout` しても、残り 2 が 10 分以内に `monitor-silent` vote を open する
2. yoro の goose recipe を crontab から削除すると、L が `stale` fault を 5 分以内に発報
3. Synthetic flood (20 post / 10 min) を注入すると、B が `loop` fault、K + B で quorum 成立、`pause` action で crontab entry が削除される
4. 3 monitor 同時に 'pass' 発行する synthetic byzantine シナリオで disagreement が正しく `escalate` に fallback する (quorum 強制通過しない)
5. per-did-kyumei-shinka-autonomy rule L49 の 3 コマンドで 3 monitor すべてが compliant 判定

## Pre-Implementation Probe (Executed 2026-04-22)

Proposed 状態の段階で、前提条件と ADR 内の主張を実測で verify した結果。

| 前提条件 | 検証コマンド | 結果 |
|---|---|---|
| `etzhayyim apps kyumei-koji` 実在 | `etzhayyim apps kyumei-koji --help` | ✓ 存在 |
| `etzhayyim monitor shinka` 実在 | `etzhayyim monitor shinka --help` | ✓ 存在 |
| `etzhayyim monitor vote` 実在 | `etzhayyim monitor vote --help` | ✗ 未実装 (Phase 0 で新設) |
| yoro.etzhayyim.com live | `curl https://yoro.etzhayyim.com/_app/meta` | ✓ 200, 正規 HTML |
| 3 goose recipe が judah で scheduled | `ssh judah crontab -l \| grep goose` | ✓ heartbeat `*/15` + persona-cron `0 */4` + mention-drain `*/15` が active、NSID collection が Monitor-L axis の観測対象と一致 |
| jacob LiteLLM reachable (Monitor-L placement) | `curl http://192.168.1.37:4000/health/liveliness` | ✓ 200, 17ms |
| judah Ollama reachable (Monitor-K placement) | `curl http://192.168.1.61:11434/api/tags` | ✓ 200, 15ms |
| 提案 subdomain 未占有 | `curl https://yoro-{liveness,shinka,integrity}.etzhayyim.com/` | ✓ 全 404 — 3 subdomain 全て deploy 可能 |
| 既存 monitor actor との衝突 | `grep yoro-{liveness,shinka,integrity}` on repo | ✓ 衝突なし (本 ADR のみが参照) |
| 既存 schema との衝突 | `grep vertex_yoro_monitor_* on migrations` | ✓ 衝突なし |
| yoro current readiness | `etzhayyim apps kyumei-koji -nanoid g00h5zto -repo-did did:web:yoro.etzhayyim.com` | readiness_score=6 (D grade) — domain records 0 件、sub-DID 0 件。**外部監視の必要性を裏付け** (self-compliance が weak なので triple-witness が正当化される) |

### ADR 内容の訂正

プローブで判明した訂正点:

1. **`com.etzhayyim.kagami.graph.query` は archived** (`Gone` 410 レスポンス、"Use Kysely directly via createKyselyDb(env.HYPERDRIVE)")。ADR 内で CF Worker 外部からの cross-attestation 検証コマンドとして引用していたが、**CF Worker 内 Hyperdrive 直接 + CLI は Keychain `etzhayyim.rw ROOT_URL` 経由 psql** に差し替えた (§Verification 実行例を修正済)。Monitor-B 自体は元から Hyperdrive 直接 (ADR-0036) で書込・読込するため、**設計本体には影響なし**。
2. **RisingWave :4566 への直接 psql は ad-hoc 時 connection closed あり**。Hyperdrive binding 経由 (CF Worker / Cloudflared LAN 内) は安定。Monitor 実装では直接 psql 経路に依存しない (CLI 検証のみ使用)。

### 未検証 (実装後に必要)

以下は Phase 0-3 で実装 + 検証する:

- `vertex_yoro_monitor_attestation` / `_vote` の migration 適用
- Monitor-B の CF Worker deploy (Cron Trigger `*/10 min`) + HYPERDRIVE binding
- Monitor-L/K の goose recipe + ansible role deploy
- `etzhayyim monitor vote {dry-run,cast,resolve,force-pass,drill}` CLI 新規実装
- 2-of-3 quorum の E2E (synthetic fault injection)

# References

- ADR-0034 — goose on judah (Monitor-K の実行基盤)
- ADR-0036 — Worker-direct Hyperdrive (vote 書込 yoro 迂回の根拠)
- ADR-0022 — Auth topology (ES256 Service Auth signing for attestation)
- ADR-0023 — Multi-key rotation (rotate-key action の実装根拠)
- ADR-0026 — Agent-only reverse identity (監視 actor も agent-only で emergence 可)
- ADR-0041 — PDS commit content-addressed PK (CF Worker 1101 retry の根拠)
- `90-docs/rules/compliance/per-did-kyumei-shinka-autonomy.md` — 監視 actor 自身の compliance 要件
