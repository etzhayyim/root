---
id: adr-2605081700-otakiage-reuse-ritual-platform
title: "ADR-2605081700: Otakiage Reuse & Ritual Platform — 物の再生と供養を 1 つのライフサイクルで扱う"
status: active
doc_type: adr
topic: otakiage-reuse-ritual-platform
authoritative: true
last_verified: 2026-05-08
priority: 7.0
axis: product
weight: 0.70
priority_note: "新規 actor 設計。物の reuse → 供養までを 1 つの state machine で扱う differentiation"
authoritative_for:
  - otakiage actor topology and DID composition
  - item lifecycle state machine (submitted → reuse_open → handed_over | ritualized)
  - reuse matching by H3 res-5 cell adjacency
  - ritual ceremony scheduling (季節祭 calendar)
  - certificate issuance (Phase 1 = AT Record JSON / Phase 2 = ERC725 anchor)
  - 3-Tier Write boundaries for item / handover / ritual records
  - category-specific lifecycle rules (絵本 / ぬいぐるみ / 家具)
depends_on:
  - adr-0036-worker-direct-hyperdrive-persistence
  - adr-0056-bpmn-as-actor
  - adr-0019-atproto-native-identifier-topology
  - adr-2604282300
  - adr-2604291800-well-becoming-spirit-objective-function
related:
  - adr-2605080100-bonsai-growth-prune-model
  - adr-0018-pii-tier3-cohort-first
  - adr-0095-simplified-3layer-identity-rw-vault
supersedes: []
superseded_by: []
---

# ADR-2605081700: Otakiage Reuse & Ritual Platform

**Status**: accepted
**Date**: 2026-05-08
**Deciders**: Jun Kawasaki
**Supersedes**: —

## Context

絵本・家具・ぬいぐるみなどの「思い出のある物」の不要化局面で、現状 platform は受け皿を持たない。
既存 `fleamarket.etzhayyim.com` は個人間売買に特化 (有償取引、Clerk 認証、決済前提)、
`toshi-kozan.etzhayyim.com` は工業 e-waste / urban mining 向けで一般家庭向けではない。

ユーザは 4 つの C2C / 譲渡モデルから platform 適合度を比較した:

| モデル | 決済 rail | KYC/PII | 終端状態 | etzhayyim 親和 | 適合度 |
|---|---|---|---|---|---|
| メルカリ型 (escrow + 配送) | 必須 | T3 重 | sold | ❌ 商業 | △ — 決済 actor / 配送 actor 未着手、ADR-0036 の 1-RTT 設計と DO state heavy が衝突 |
| Craigslist (掲示板) | ❌ | 軽 | TTL expire | △ 中立 | ○ — yoro feed で代替可、差別化弱い |
| jmty (ジモティー、ローカル譲渡) | ❌ | 軽 | handover | ○ ローカル | ◎ — H3 res-5 マッチ + 多モード (gift/lend/swap/wanted) |
| 寄付 (NPO) | ❌ → 領収書 | T3 中 | acknowledged | ◎ 宗教法人 | ○ narrow |
| **お焚き上げ (otakiage)** | ❌ → お志 | 軽 | ritualized (永続記録) | **◎◎** | **◎◎ unique** |

「お焚き上げ」は platform-native な差別化要素を持つ:

1. **etzhayyim = 宗教法人・任意団体・blockchain 登記** が他に類を見ない operator 属性 → 司式の正当性が platform 側に内在
2. **Bonsai Growth & Prune Model (ADR-2605080100)** と同型 — 物品 lifecycle の「prune = sporulation (dormant → ritual → 永続記録)」に相似
3. **ERC725 + blockchain 登記 (ADR-0074)** で「お焚き上げ証明」の永続証跡 anchor 可能 (Phase 2)
4. **Well-Becoming Spirit 目的関数 (ADR-2604291800)** の Spirit healing axis と整合 — 物への愛着の終端ケア
5. **AT Protocol 公開記録** = ritual transparency が federate しても問題ない (PII を含まない設計)
6. メルカリは liquidity プールが prerequisite で後発不利、otakiage は競合ほぼゼロ

ただし otakiage 単体だと scope が狭い (供養前に reuse の選択肢を持たないと「捨てる前に救う」流れが切れる)。
**otakiage を主軸に reuse layer を内包する 2 layer 構成**で物のライフサイクル全体を扱う。

## Goal

物の「不要になった」局面から「再生 (reuse) → 供養 (ritual)」までを単一の state machine と
graph schema で扱い、各遷移を AT Protocol 公開記録 + Kotoba/Datomic Hyperdrive 直接書込
(ADR-0036) で永続化する。

## Scope

### In scope (Phase 1)

- 物品登録 (写真 + 思い出 + カテゴリ + 立地 H3 cell)
- reuse 近接マッチング (H3 res-5 同一 + 隣接 6 cells)
- 譲渡完了記録 (handover)
- お焚き上げ依頼 (ritual)
- 季節祭スケジュール (人形供養祭 / 絵本供養祭 / 家具解体祭)
- 永続証跡発行 (Phase 1: AT Record JSON、URI = `at://otakiage.etzhayyim.com/com.etzhayyim.otakiage.certificate/{rkey}`)
- T1 social derive (handover / ritual 完了時に PII を含まない post)

### Out of scope (Phase 2+)

- ERC725 NFT anchor (blockchain 登記による改ざん耐性証跡)
- 配送 actor 連携 (家具の引取 / 集荷)
- 神社仏閣 actor 連携 (実物理的な合同供養祭)
- 寄付領収書 (T3 PII 必要、別 actor `donate.etzhayyim.com` で扱う)
- 売買 (escrow / 決済) — `fleamarket.etzhayyim.com` の責務

### Non-goals

- メルカリ型の決済 escrow を otakiage 内で実装しない
- ヤマト/佐川の配送 API を直接叩かない
- 個人の住所 / 電話番号を AT Record に書かない (Tier 3 Preferences のみ)

## Executive Summary

`otakiage.etzhayyim.com` を T2 actor (CF Worker = Svelte CSR + XRPC facade、業務ロジック = pyzeebe + BPMN-as-actor)
として立ち上げ、以下の不変条件を持つ:

1. **State machine 1 本**: `submitted → reuse_open → {handed_over | ritualized}`、家具のみ `reuse_only` モードで ritual に流れない
2. **3-Tier Write 厳守 (ADR-0036)**:
   - T1 Social: handover / ritual 完了時の謝辞 post (PII なし、位置 H3 res-3 まで丸める)
   - T2 Domain: 全 item / reuse_request / handover / ritual / matsuri / certificate を Hyperdrive 直接
   - T3 State: 受領者 / 寄贈者 PII (氏名 / 住所 / 連絡先) は Preferences
3. **Path-based DID (ADR-0019)**: `did:web:otakiage.etzhayyim.com:{root,reuse,ritual,matsuri}` の 4 sub-DID で責務分離
4. **BPMN-as-actor (ADR-0056)**: 4 process_def (reuse_match R/PT1H, reuse_expire R/PT24H, matsuri_schedule cron 月1, social_announce XRPC)
5. **永続証跡 = AT Record (Phase 1)**: ritualized 時に `com.etzhayyim.otakiage.certificate` を発行、URI が永続 ID
6. **季節祭 calendar 内蔵**: 人形供養祭 (3月/11月)、絵本供養祭 (4月)、家具解体祭 (随時、reuse_expired バッチ)

## Decision

### 1. Topology

```
Layer        | Component
-------------|-------------------------------------------------------------
L1 Edge      | Cloudflare DNS / Pages / TLS
L2 Routing   | atproto.etzhayyim.com (PDS gateway, social federation 経路)
L3 Dispatcher| otakiage.etzhayyim.com CF Worker (Svelte CSR + XRPC facade のみ)
L4 Registry  | Kotoba/Datomic: vertex_otakiage_*, vertex_bpmn_process_def
L5 Storage   | B2 (写真 blob, content-addressed) + Kotoba/Datomic Hummock
L6 Compute   | RW SQL UDF (h3_neighbors_at_res, category_match_score)
L7 Orchestr. | Zeebe + pyzeebe (mitama-otakiage-pool 専用 worker)
L8 Tools     | (Phase 1 不要 — pure SQL + LLM only)
```

CF Worker `otakiage.etzhayyim.com` の責務 = Svelte UI 配信 + XRPC 受付 + bpmn-dispatcher への internal forward のみ
(ADR-2604282300 §Addendum 2026-04-30 の K8s-internal routing 経路)。
業務ロジックは pyzeebe primitive が担う。

### 2. Path-based DIDs (ADR-0019)

| DID | nanoid | 役割 |
|---|---|---|
| `did:web:otakiage.etzhayyim.com` | `0t4k1ag3` | controller (primary)、profile / coverage |
| `did:web:otakiage.etzhayyim.com:reuse` | — | reuse broker (近接マッチ + 通知) |
| `did:web:otakiage.etzhayyim.com:ritual` | — | 司式 actor (供養記録 + 証跡発行) |
| `did:web:otakiage.etzhayyim.com:matsuri` | — | 季節祭 organizer (calendar 駆動) |

各 sub-DID で post する社 social (`app.bsky.feed.post`) は path-DID author の T1 (PDS dispatch)。

### 3. Item Lifecycle (state machine)

```
                                 ┌─ category=furniture? ──→ reuse_only
                                 │
[submit]                         │
   │                             ▼
   ▼                       ┌──────────────┐
submitted ──[auto]──→ reuse_open (TTL 30d)
                             │
              ┌──────────────┼──────────────┐
              │              │              │
       [requestReuse]   [TTL expired]  [skipReuse + requestRitual]
              ▼              ▼              ▼
        reuse_matched   reuse_expired       │
              │              │              │
       [confirmHandover]     │ (家具なら止まる)
              ▼              ▼              ▼
         handed_over    ritual_pending ◀────┘
         (terminal)         │
                            ▼
                     [matsuri 開催 + issueCertificate]
                            │
                            ▼
                       ritualized
                       (terminal, certificate URI 発行)
```

不変条件:
- `submitted` → `reuse_open` は自動遷移 (登録 = 即 reuse 開放)
- `reuse_open` の TTL = 30 日 (BPMN `reuse_expire` R/PT24H が `reuse_expired` へ昇格)
- `reuse_expired` から `ritual_pending` への遷移は category 別:
  - `nuigurumi / ningyo / omocha / ehon / jidousho` → 自動で `ritual_pending`
  - `kagu / kaden` → 留まる (`reuse_only` mode、解体パートナー edge 推奨)
- `ritualized` は terminal、AT Record `com.etzhayyim.otakiage.certificate` を発行して URI を `vertex_otakiage_item.certificate_uri` に書く

### 4. Schema (Hyperdrive 直、ADR-0036)

#### Vertices

| table | PK | tier | 主要列 |
|---|---|---|---|
| `vertex_otakiage_item` | content-addressed `at://...` | T2 | category, title, story_text, photo_blob_keys[], h3_cell, h3_res, mode (reuse_only \| reuse_then_ritual), state, weight_kg_class, owner_did, actor_did, org_did, at_did, created_at |
| `vertex_otakiage_reuse_request` | content-addressed | T2 | item_uri, requester_did, message, h3_cell, distance_km, state, created_at |
| `vertex_otakiage_handover` | content-addressed | T2 | item_uri, donor_did, recipient_did, handover_at, photo_blob_key, gratitude_text |
| `vertex_otakiage_ritual` | content-addressed | T2 | matsuri_id, item_uris[], ceremony_date, photo_blob_key, certificate_uri |
| `vertex_otakiage_matsuri` | content-addressed | T2 | name (人形供養祭 等), category_scope[], scheduled_date, capacity, registered_count, location_h3, state |
| `vertex_otakiage_certificate` | content-addressed | T2 | ritual_uri, item_uris[], donor_dids[], issued_at, certificate_json (JSON-LD), display_text |

#### Edges

- `edge_otakiage_item_owner` (item → owner DID)
- `edge_otakiage_item_handover` (item → handover、reuse 経路)
- `edge_otakiage_item_ritual` (item → ritual、供養経路)
- `edge_otakiage_ritual_certificate` (ritual → certificate)

#### Streaming MVs

- `mv_otakiage_reuse_match_by_h3` — `vertex_otakiage_item WHERE state='reuse_open'` を H3 res-5 cell + 隣接 6 cells で grouping、距離順 ranking
- `mv_otakiage_matsuri_upcoming` — `scheduled_date > now()` AND `< now() + interval '90 days'`
- `mv_otakiage_items_by_state` — state 別件数 (coverage 表示用)
- `mv_otakiage_donor_lifetime_count` — 寄贈者 DID 別累積件数 (gamification の余地、Phase 2)

#### RW SQL UDF (ADR-0044)

- `h3_neighbors_at_res(cell varchar, res int) returns varchar[]` — H3 res-5 隣接 cell 配列
- `otakiage_category_to_lifecycle(category varchar) returns varchar` — `'furniture'` → `'reuse_only'`、他 → `'reuse_then_ritual'`

### 5. Lexicon (NSID `com.etzhayyim.otakiage.*`)

Phase 1 = 9 lexicon:

| NSID | type | scope |
|---|---|---|
| `submitItem` | procedure | 物品登録 (T1: derive で簡易 post, T2: vertex_otakiage_item INSERT) |
| `requestReuse` | procedure | 引取希望 (T2: vertex_otakiage_reuse_request INSERT) |
| `confirmHandover` | procedure | 譲渡完了 (T2: handover INSERT, item.state → handed_over, T1 derive 謝辞 post) |
| `requestRitual` | procedure | お焚き上げ依頼 (T2: item.state → ritual_pending) |
| `scheduleMatsuri` | procedure | 季節祭追加 (T2: vertex_otakiage_matsuri INSERT、authority gated) |
| `issueCertificate` | procedure | 証跡発行 (T2: vertex_otakiage_certificate INSERT、ritual 完了時に内部呼出) |
| `listItems` | query | state / category / h3_cell でフィルタ |
| `getItem` | query | item URI 単発取得 |
| `coverage` | query | mv_otakiage_items_by_state を返す |

### 6. BPMN actors (ADR-0056)

| process_id | trigger | task chain |
|---|---|---|
| `otakiage_reuse_match` | timer R/PT1H | `otakiage.reuse.findCandidates` (H3 + category match) → `generic.audit.emit` |
| `otakiage_reuse_expire` | timer R/PT24H | `otakiage.reuse.expireOpen` (TTL 30d → reuse_expired or ritual_pending) → `generic.audit.emit` |
| `otakiage_matsuri_schedule` | cron `0 0 0 1 * ?` (月初) | `otakiage.matsuri.seedNextMonth` → `generic.audit.emit` |
| `otakiage_social_announce` | XRPC binding (handover/ritual 完了で内部呼出) | `otakiage.social.announceHandover` or `announceRitual` → `generic.pds.dispatch` |

XRPC binding は `submitItem / requestReuse / confirmHandover / requestRitual / scheduleMatsuri / issueCertificate` の 6 つのみ (query 系は `generic.db.select` 経由)。

### 7. Certificate (Phase 1 = AT Record JSON)

ritualized 時に `vertex_otakiage_certificate` + AT Record `com.etzhayyim.otakiage.certificate/{rkey}` を発行:

```json
{
  "$type": "com.etzhayyim.otakiage.certificate",
  "ritualUri": "at://did:web:otakiage.etzhayyim.com:ritual/.../...",
  "itemUris": ["at://...", "at://..."],
  "donorDids": ["did:web:alice.etzhayyim.com", "did:web:bob.etzhayyim.com"],
  "issuedAt": "2026-05-15T10:00:00Z",
  "issuer": {
    "name": "etzhayyim",
    "kind": "religious-corporation",
    "did": "did:web:otakiage.etzhayyim.com:ritual"
  },
  "displayText": "ぬいぐるみ 3 体 / 絵本 12 冊 を 2026-05-15 春の供養祭にて謹んでお焚き上げいたしました",
  "categories": {"nuigurumi": 3, "ehon": 12},
  "matsuriId": "at://...",
  "photoBlobKey": "blobs/.../...",
  "version": "1.0"
}
```

URI が永続 ID。Phase 2 で ERC725 anchor token を `anchorTokenId` field 追加で参照可能。

### 8. T1 Social Derive 規約

`magatama.jsonld` の `derive` rule で host-sdk derive executor が自動発火。
handler は **explicit `postFeed()` を書かない** (ADR-0004 / ADR-0036 不変条件)。

| Domain write | T1 Social derive | author DID | PII 除去 |
|---|---|---|---|
| `vertex_otakiage_handover` INSERT | `app.bsky.feed.post` 「♻️ {category} が新しいお家へ。ありがとうの気持ちが循環しました」 | `did:web:otakiage.etzhayyim.com:reuse` | donor / recipient DID は post 本文に含めない、handle は記載しない、H3 res-3 (~50km) まで丸める |
| `vertex_otakiage_ritual` INSERT | `app.bsky.feed.post` 「✨ {category 集計} を {matsuri.name} にてお焚き上げいたしました」 | `did:web:otakiage.etzhayyim.com:ritual` | donor DIDs は集計のみ、個別 mention なし |
| `vertex_otakiage_matsuri` INSERT | `app.bsky.feed.post` 「📅 {matsuri.name} を {date} に開催します。受付中です」 | `did:web:otakiage.etzhayyim.com:matsuri` | — |

### 9. Helm Pool

`50-infra/vultr/mitama-otakiage-pool/` を `mitama-shinshi-pool` / `mitama-shosha-pool` と同形パターンで作成:
- `otakiage-zeebe-worker` Deployment (`ZEEBE_WORKER_PROFILE=otakiage`)
- 専用 pool 理由: `otakiage.matsuri.seedNextMonth` が将来 LLM call (供養祭の説明文生成) を含む可能性、共有 worker で他 actor を starve させない隔離

### 10. Phase 1 → Phase 2 → Phase 3 ロードマップ

| Phase | Scope | 期限目安 | 状態 |
|---|---|---|---|
| **Phase 1** | Schema + Lexicon + BPMN + pymagatama primitives + Helm pool。Certificate = AT Record JSON。社内テスト | 1-2 週間 | ✅ 2026-05-08 完了 (ファイル) / migration apply pending |
| **Phase 2a** | Conversational LangGraph agent (kotodama persona、`com.etzhayyim.otakiage.agentChat`) | 1 週間 | ✅ 2026-05-08 完了 (ファイル) |
| **Phase 2b1** | ERC725 anchor — state tracking + queue + sweep stub (`anchorCertificate` + `certificateAnchorSweep`) | 1 週間 | ✅ 2026-05-08 完了 (ファイル) |
| **Phase 2b2** | ERC725 anchor — 実 on-chain submission (ethers/viem、Base L2) | 2-3 週間 | 未着手 |
| **Phase 2c** | 配送 actor 連携 (ヤマト集荷 API)、季節祭の Wan 2.2 動画生成 | 1-2 ヶ月 | 未着手 |
| **Phase 3** | 神社仏閣 actor 連携 (合同供養祭の実物理イベント連携)、寄付 actor `donate.etzhayyim.com` との 2-way bridge、Well-Becoming Spirit objective 上のメトリクス組込 (ADR-2604291800 の Spirit healing axis として)、LangGraph BaseCheckpointSaver で会話 中断/再開 | 3-6 ヶ月 | 未着手 |

### 11. Phase 2a — Conversational LangGraph Agent (2026-05-08)

ADR-2605072000 (LangGraph Agent Loop Pattern) と ADR-2605080200 (Pydantic L6) に従い、対話 entry-point を追加。

**Graph design** (`pymagatama.agents.otakiage_agent`、graph_id = `otakiage.agent.chat.v1`):

```
START → load_history (DB) → parse_intent (LLM #1)
                              ├─ submit  → extract_details (LLM #2)
                              ├─ search  → search_candidates (DB)
                              ├─ ritual  → resolve_matsuri (DB)
                              ├─ inquire → fetch_info (DB)
                              └─ chat    → (no extra)
                                  ↓
                             compose_reply (LLM #3)
                                  ↓
                             persist_turn (DB) → END
```

**ADR-2605072000 ≥3 LLM branches 条件**: submit パスが parse + extract + reply の 3 LLM、principal path として条件達成。他 intent (search/ritual/inquire/chat) は 2 LLM で、Phase 3 で search に 3 つ目の LLM (候補ランクづけ) を入れて全 path 3-LLM 化する余地。

**Persona**: `kotodama` — etzhayyim (宗教法人) 主催 otakiage の対話 assistant。敬語、200 字以内、emoji 控えめ (✨🙏♻️)、決済/配送話題は Phase 1 制約として丁重に拒否。

**Conversation persistence schema** (migration `20260508130000_vertex_otakiage_conversation`):
- `vertex_otakiage_conversation` — thread (caller_did, turn_count, last_intent, state)
- `vertex_otakiage_conversation_turn` — append-only per-turn (user_message, agent_reply, intent, actions_json, llm_calls, latency_ms)
- `mv_otakiage_conversation_recent` — 24h active threads (soak monitor)

**Lexicon**: `com.etzhayyim.otakiage.agentChat` (procedure)。Output に `draftItem` (submit 時の抽出結果)、`candidates` (search 時の reuse_open URI 配列)、`actions[]` (turn 内の副次操作)、`llmCalls` (≥2 or ≥3)、`intent` を含む。

**BPMN**: `otakiage_agent_chat` (XRPC binding、resultTimeoutMs=90000 — 3-LLM cold-start 余裕)。

**Primitive**: `task_otakiage_agent_chat` in `primitives/otakiage.py` — `otakiage_chat_graph.ainvoke()` を await して output を XRPC envelope に整形。eager import を `register()` で実行し graph_id 登録を保証。

**未対応 (Phase 3 で対応)**:
- LangGraph BaseCheckpointSaver (RW 実装、ADR-2605080600) — 現在は会話 turn を DB に append-only で保存しているが LangGraph 内部の checkpoint は in-memory のみ
- complain intent (苦情エスカレーション)
- Pydantic v2 入出力 (ADR-2605080200) — 現在 TypedDict、Phase 3 で BaseModel 化

### 12. Phase 2b1 — ERC725 Certificate Anchor (state tracking, 2026-05-08)

ADR-0074 (ERC725 root identity) と etzhayyim の blockchain 登記性質を活用し、各 ritual certificate を on-chain anchor token に固定する経路を導入。**Phase 2b1 = state machine + sweep stub**、Phase 2b2 = 実 on-chain submission (ethers/viem)。

**State machine** (`vertex_otakiage_certificate.anchor_status`):

```
issueCertificate → (auto-queue, non-fatal)
        ↓
     queued ──[sweep R/PT1H]──→ submitted (token_id = sha256(certificate_json)[:16])
                                    ↓
                                 anchored (Phase 2b1: stub tx_hash; Phase 2b2: real receipt + ≥3 conf)

  failed ←─[content_hash 欠落 / chain RPC error 等]
  (force=true で再 queue 可能)
```

**Schema (ALTER `vertex_otakiage_certificate`、migration `20260508140000_alter_otakiage_certificate_anchor`)**:

8 列追加 — `anchor_chain` / `anchor_contract` / `anchor_status` / `anchor_tx_hash` / `anchor_block_number` / `anchored_at` / `content_hash` / `failure_reason`。

`anchor_token_id` は Phase 1 で既に存在。`content_hash` から `0x` + sha256 先頭 16 hex を deterministic に派生 → 同一 certificate を 2 度 mint できない。

**Streaming MV**: `mv_otakiage_anchor_status` (status × chain × count 別 soak metric)。

**Lexicon**: `com.etzhayyim.otakiage.anchorCertificate` (procedure)。`chain` enum = `base|base-sepolia|polygon|polygon-amoy` (default `base`、Coinbase L2 で gas $0.01〜$0.10/anchor)。`force=true` で failed → queued 再試行。

**BPMN**:
- `otakiage_anchor_certificate` — XRPC binding (60s timeout)、queue 1 件
- `otakiage_certificate_anchor_sweep` — R/PT1H、20 件/fire 上限 (Phase 2b2 gas 予算 ~$2/fire 想定)

**Primitive (`primitives/otakiage.py`)**:
- `task_otakiage_certificate_anchor` — XRPC handler。cert 存在検証 → content_hash 計算 → status='queued' UPDATE。submitted/anchored は force=false で no-op。
- `task_otakiage_certificate_anchor_sweep` — R/PT1H sweep。queued → submitted (token_id 派生) → anchored (Phase 2b1: stub `stub:{token_id_prefix}` tx_hash)。Phase 2b2 で web3 RPC 呼出に置換。

**issueCertificate auto-queue**: `task_otakiage_ritual_issue_certificate` が ritual 完了後に `task_otakiage_certificate_anchor` を非同期呼出 (try/except でラップ、失敗は ritual 完了を block しない)。

**Phase 2b2 への移行 (未着手)**:
- `pyproject.toml` に `web3>=6` 追加
- `ANCHOR_RPC_URL` / `ANCHOR_PRIVATE_KEY` / `ANCHOR_CONTRACT_BASE` 等 K8s Secret 化
- sweep の queued→submitted ループで `Web3.eth.send_raw_transaction(...)` 経由で `anchor.mint(uint256 tokenId, bytes32 contentHash, address[] donors)` 呼出
- submitted→anchored で `eth.get_transaction_receipt(tx_hash)` を polling、`block_number` 記録 + ≥3 confirmations 確認
- 障害時 `anchor_status='failed'` + `failure_reason=str(e)`、`anchorCertificate force=true` で復旧

## Rationale

### なぜ otakiage が Mercari より platform fit か

| 軸 | Mercari | Otakiage |
|---|---|---|
| 競合 | レッドオーシャン (Mercari, Yahoo オク, eBay, jmty) | ほぼゼロ (kuyo.com 等少数、デジタル証跡持つ事例なし) |
| 必要 infra | 決済 escrow / KYC / 配送 / 紛争処理 | T2 Hyperdrive + AT Record + B2 blob のみ |
| operator 親和 | 商業 entity 想定 (etzhayyim と miss-match) | 宗教法人・任意団体・blockchain 登記 (etzhayyim 直球) |
| 永続価値 | 取引 1 回で完結 (再訪問動機弱) | 証跡が永続、家族内伝承 (祖父母 → 親 → 子) で再訪 |
| AT Protocol federate | escrow ID / PII で federate 不可 | ritual ceremony record は federate 可 (transparency 価値) |
| Shannon η | 決済情報冗長 (PCI / KYC) で η 低 | 公開記録 + 集計のみで η 高 |

### なぜ Phase 1 で ERC725 を見送るか

- ERC725 anchor は Coinbase Smart Wallet + gas (L2 でも cents) コスト発生
- AT Record URI は immutable identity を提供 (改ざんは検出可能、再 publish 不可)
- 「永続証跡」の semantic は AT Protocol で十分。ERC725 はその上の defense-in-depth として Phase 2 で追加
- Phase 1 で UX を確認 → 価値が証明されてから ERC725 anchor 投資判断

### なぜ家具を ritual から除外するか

- 大型家具 / 大型家電は物理的に焼却不可、廃棄物処理法上もフロー違反
- 「お焚き上げ」の semantic は「思い出と共に」が本質、家具は対象外で defaults を守る
- 解体パートナー edge (Phase 2) で「物としての終わり」は記録できる
- reuse_only モードを設けることで「家具は徹底的に reuse」の社会的価値を提示

### なぜ 1 actor 内に reuse + ritual を統合するか

- ライフサイクルが連続している (reuse 失敗 → ritual は自然な遷移)
- DB join 不要 (同一 graph schema 内、`item.state` で trace)
- ユーザ動線が単純 (登録 → 自動的に reuse 候補に出る → 不成立なら供養に流れる)
- 別 actor だと state 同期コスト発生、ADR-0036 の 1-RTT 設計と衝突

## Comparison

### Item lifecycle 設計の選択肢

| 設計 | Pros | Cons | 採否 |
|---|---|---|---|
| **A. 単一 state machine (採用)** | 1 graph で完結、user 動線単純、derive rule で社 social 自動 | category 別ロジックが state machine に内在 | ✅ |
| B. reuse / ritual 別 actor | scope 分離、責務明確 | 2 actor 跨り state 同期、ADR-0036 違反 | ❌ |
| C. fleamarket に reuse mode 追加 | 既存 actor 流用 | fleamarket は決済 escrow 前提、auth model 衝突 | ❌ |

### Certificate 形式の選択肢

| 形式 | Pros | Cons | 採否 |
|---|---|---|---|
| **A. AT Record JSON (Phase 1 採用)** | 既存 infra のみ、URI が permanent ID、federate 可 | 改ざん耐性は AT Repo の正常性に依存 | ✅ Phase 1 |
| B. ERC725 NFT anchor | blockchain 永続、改ざん検出強 | gas コスト、wallet 連携 UX | Phase 2 |
| C. PDF + QR | 物理印刷可能、贈答に使える | digital primary の意義が薄れる、QR は AT Record リンクで代替可 | 補助 (Phase 2 PDF generator) |

### マッチング距離の選択肢

| 設計 | 範囲 | Pros | Cons | 採否 |
|---|---|---|---|---|
| H3 res-5 cell only | ~9 km² | 厳密に近接 | マッチ難民、家具など重い物には適切 | 補助 |
| **H3 res-5 + 隣接 6 cells (採用)** | ~63 km² | バランス、~5km 圏 | 都市部はやや広い | ✅ |
| H3 res-4 cell | ~280 km² | 都市内全域 | 「ローカル譲渡」semantics 失う | ❌ |

## Exceptions

- **donate (寄付) は別 actor**: 寄付領収書 (税控除) は T3 PII heavy で otakiage に混ぜない。`donate.etzhayyim.com` を別 ADR で立ち上げる
- **fleamarket との関係**: 「有償譲渡したい」ユーザは fleamarket、「無償譲渡 / 供養したい」は otakiage。submitItem 時に price=0 制約 (有償化したければ fleamarket へリダイレクト)
- **物品の写真がない場合**: photo_blob_keys[] = [] を許容 (story_text 必須)、ただし reuse マッチ率は下がる
- **現実のお焚き上げ実施**: Phase 1 は digital ritual のみ (記録 + 証跡)。実物理的な火を使う供養は Phase 3 の神社仏閣 actor 連携時に解禁

## References

- ADR-0036 (Worker-direct Hyperdrive Persistence) — 全 domain write が Hyperdrive 直
- ADR-0056 (BPMN-as-actor) — 4 BPMN process_def + lexicon binding
- ADR-0019 (atproto-native Identifier Topology) — path-based DID
- ADR-2604282300 (CF Worker Edge Layer) — CF Worker = Svelte CSR + XRPC facade のみ
- ADR-2604291800 (Well-Becoming Spirit) — Spirit healing axis 整合
- ADR-2605080100 (Bonsai Growth & Prune) — sporulation / dormancy 概念の物への適用
- ADR-0018 (PII Tier 3 + Cohort-First) — donor / recipient PII の T3 Preferences 配置
- ADR-0095 (3-Layer Identity + Kotoba/Datomic Canonical Columns) — `actor_did / org_did / at_did / created_at` 4 列規約
- root CLAUDE.md §Operating entity boundary — etzhayyim = sole principal
- `60-apps/etzhayyim-project-fleamarket/` — 個人間売買 (有償) の責務分離先
