# otakiage.etzhayyim.com

**Reuse & Ritual Platform** — 物の reuse (ローカル譲渡) と ritual (お焚き上げ) を 1 actor 内の単一 state machine で扱う。

ADR: `90-docs/adr/2605081700-otakiage-reuse-ritual-platform.md`

## Tier

T2 actor (ADR-0036 + ADR-0056 + ADR-2604282300)
- Domain write = Hyperdrive 直接 (`createKyselyDb` / `psycopg3 sync_cursor`)
- Business logic = kotodama + LangServer BPMN-contract (no CF Worker for logic)
- CF Worker (Phase 2 で追加) = Svelte CSR + XRPC facade のみ

## Path-based DIDs (ADR-0019)

| DID | 役割 |
|---|---|
| `did:web:otakiage.etzhayyim.com` | controller (primary) |
| `did:web:otakiage.etzhayyim.com:reuse` | 近接マッチ broker (handover author) |
| `did:web:otakiage.etzhayyim.com:ritual` | 司式 actor (certificate issuer) |
| `did:web:otakiage.etzhayyim.com:matsuri` | 季節祭 organizer |

## Item Lifecycle (state machine)

```
submitted → reuse_open (TTL 30d, auto)
              ├→ handed_over (terminal, T1 social derive)
              └→ reuse_expired
                    └→ ritual_pending (mode=reuse_then_ritual のみ)
                         └→ ritualized (terminal, certificate URI 発行)
```

Mode は category から auto-derive:

| Category | Mode |
|---|---|
| ehon / jidousho / nuigurumi / ningyo / omocha | `reuse_then_ritual` |
| kagu / kaden | `reuse_only` (ritual に流れない) |

## Schema (Hyperdrive 直、ADR-0036)

| Table | 役割 |
|---|---|
| `vertex_otakiage_item` | 物品 (category, story, photo[], h3_cell, mode, state) |
| `vertex_otakiage_reuse_request` | 引取希望 |
| `vertex_otakiage_handover` | 譲渡完了 (terminal) |
| `vertex_otakiage_ritual` | 供養記録 |
| `vertex_otakiage_matsuri` | 季節祭 (calendar 駆動) |
| `vertex_otakiage_certificate` | 永続証跡 (Phase 1 = AT Record JSON) |
| `edge_otakiage_item_owner` / `_handover` / `_ritual` / `_ritual_certificate` | グラフ |
| `mv_otakiage_*` (4) | reuse match / matsuri upcoming / items_by_state / donor lifetime |

Migrations:
- `30-graph/graph-schema/migrations/20260508120000_vertex_otakiage_schema.ts`
- `30-graph/graph-schema/migrations/20260508120100_seed_otakiage_bpmn_actors.ts`
- `30-graph/graph-schema/migrations/20260508120200_seed_otakiage_matsuri_calendar.ts`

## BPMN-as-actor (ADR-0056)

| process_id | trigger | task chain |
|---|---|---|
| `otakiage_reuse_match` | R/PT1H | `otakiage.reuse.findCandidates` → audit |
| `otakiage_reuse_expire` | R/PT24H | `otakiage.reuse.expireOpen` (TTL 30d, category-aware) → audit |
| `otakiage_matsuri_schedule` | cron 月初 | `otakiage.matsuri.seedNextMonth` → audit |
| `otakiage_social_announce` | XRPC fan-in | `otakiage.social.composeAnnounce` → `generic.pds.dispatch` → audit |

BPMN files: `etzhayyim-root/00-contracts/bpmn/com/etzhayyim/otakiage/`

## Lexicons (11, NSID `com.etzhayyim.otakiage.*`)

| NSID | type | scope |
|---|---|---|
| `submitItem` | procedure | T2 + T1 derive |
| `requestReuse` | procedure | T2 |
| `confirmHandover` | procedure | T2 + T1 derive (handover) |
| `requestRitual` | procedure | T2 (state machine transition) |
| `scheduleMatsuri` | procedure | T2 (authority gated) |
| `issueCertificate` | procedure | T2 + T1 derive (ritual completed) + auto-queue anchor (Phase 2b1) |
| `agentChat` | procedure | T2 (LangGraph multi-turn agent, Phase 2a) |
| `anchorCertificate` | procedure | T2 (ERC725 anchor token, Phase 2b1) |
| `listItems` | query | filter by state/category/h3_cell |
| `getItem` | query | single item with related URIs |
| `coverage` | query | mv_otakiage_items_by_state |

Lexicon files: `00-contracts/lexicons/com/etzhayyim/apps/otakiage/`

## Phase 2 — Conversational LangGraph Agent (2026-05-08)

`com.etzhayyim.otakiage.agentChat` — kotodama persona、3 LLM call の StateGraph。

**Graph** `otakiage.agent.chat.v1` (`kotodama/agents/otakiage_agent.py`):

```
START → load_history → parse_intent (LLM #1)
                          ├─ submit  → extract_details (LLM #2)
                          ├─ search  → search_candidates (DB)
                          ├─ ritual  → resolve_matsuri (DB)
                          ├─ inquire → fetch_info (DB)
                          └─ chat    → (no extra)
                              ↓
                         compose_reply (LLM #3) → persist_turn → END
```

**Conversation persistence**:
- `vertex_otakiage_conversation` (1 thread = N turns)
- `vertex_otakiage_conversation_turn` (append-only、user_message + agent_reply + intent + actions_json + llm_calls)
- `mv_otakiage_conversation_recent` (24h active threads)

**Intents**:

| Intent | LLM count | DB ops | 用途 |
|---|---|---|---|
| `submit` | 3 (parse + extract + reply) | 0 (draft only、submit は別 XRPC) | 物品登録の対話 (category/title/story 抽出) |
| `search` | 2 (parse + reply) | 1 (reuse_open by H3) | 近隣 reuse 候補提示 |
| `ritual` | 2 | 1 (matsuri upcoming) | 供養依頼の matsuri 提案 |
| `inquire` | 2 | 1 (coverage stats) | 季節祭/証跡の質問対応 |
| `chat` | 2 | 0 | 一般会話 |

**ADR-2605072000 適合**: submit パスが ≥3 LLM (条件達成)。他 intent は 2 LLM だが ADR は per-graph 条件として読み取り、submit が代表。

**Phase 3 拡張余地**:
- LangGraph BaseCheckpointSaver (RW 実装、ADR-2605080600) で 中断/再開対応
- search に 3 つ目の LLM (候補ランクづけ) で全 path 3-LLM 化
- intent `complain` (苦情) を追加して人間 escalate

## Phase 2b1 — ERC725 Certificate Anchor (2026-05-08)

供養証跡 (certificate) を ERC725 anchor token として on-chain に固定する経路。**Phase 2b1 = state tracking のみ** (queue / sweep stub finalize)、Phase 2b2 で ethers/viem 経由の実 on-chain submission を実装。etzhayyim の blockchain 登記の延長として、各供養に対して改ざん耐性のある永続証跡を持たせる。

### State machine (`anchor_status`)

```
issueCertificate → (auto-queue, non-fatal)
        ↓
     queued ──[sweep R/PT1H]──→ submitted (token_id assigned from sha256(certificate_json)[:16])
                                    ↓
                                 anchored (Phase 2b1: stub tx_hash; Phase 2b2: real receipt)

  failed ←─[content_hash 欠落 / chain RPC error 等]
  (force=true で再 queue 可能)
```

### Schema (ALTER `vertex_otakiage_certificate`、migration 20260508140000)

| 列 | 型 | 用途 |
|---|---|---|
| `anchor_chain` | varchar | `base` / `base-sepolia` / `polygon` / `polygon-amoy` |
| `anchor_contract` | varchar | ERC725 anchor contract address (env `ANCHOR_CONTRACT_BASE` 等で injection) |
| `anchor_token_id` | varchar | (Phase 1 で既存) sha256[:16] from content_hash |
| `anchor_status` | varchar | `pending` / `queued` / `submitted` / `anchored` / `failed` |
| `anchor_tx_hash` | varchar | Phase 2b1 = `stub:{token_id_prefix}`、Phase 2b2 = 実 tx hash |
| `anchor_block_number` | bigint | Phase 2b2 で receipt から記録 |
| `anchored_at` | varchar | terminal 到達時刻 |
| `content_hash` | varchar | sha256(certificate_json) — token URI base、token_id 派生元 |
| `failure_reason` | varchar | failed 時の reason |

### Streaming MV

- `mv_otakiage_anchor_status` — anchor_status × anchor_chain 別件数 (soak monitor)

### BPMN

| process_id | trigger | task chain |
|---|---|---|
| `otakiage_anchor_certificate` | XRPC `com.etzhayyim.otakiage.anchorCertificate` | `otakiage.certificate.anchor` (queue) → audit |
| `otakiage_certificate_anchor_sweep` | R/PT1H | `otakiage.certificate.anchorSweep` (queued→submitted→anchored) → audit |

### Primitives

| task_type | timeout | 役割 |
|---|---|---|
| `otakiage.certificate.anchor` | 60s | XRPC handler: validate cert + compute content_hash + UPDATE status='queued' |
| `otakiage.certificate.anchorSweep` | 600s | R/PT1H sweep: queued→submitted (deterministic token_id from content_hash) → anchored (stub tx_hash) |

### issueCertificate auto-queue

`task_otakiage_ritual_issue_certificate` が ritual 完了直後に `task_otakiage_certificate_anchor` を非同期呼出 (失敗は ritual 完了を block しない)。default chain = `OTAKIAGE_DEFAULT_ANCHOR_CHAIN` env (= "base")。

### Phase 2b2 ロードマップ (未着手)

- `pyproject.toml` に `web3>=6.x` or `eth-account` 追加
- `task_otakiage_certificate_anchor_sweep` 内の queued→submitted ループで RPC 経由 `ANCHOR_RPC_URL` (env) に向けて `anchor.mint(token_id, content_hash, donor_dids)` tx 送信、tx_hash 記録
- submitted→anchored で `web3.eth.get_transaction_receipt(tx_hash)` を polling、確認 ≥3 で anchored 確定
- gas 上限ガード: per-fire 20 cert × ~50K gas = ~1M gas、$5/fire (Base L2 想定)
- 障害復旧: `failed` 状態は `anchorCertificate force=true` で再 queue

## kotodama primitives

`40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/primitives/otakiage.py`:

| task_type | handler |
|---|---|
| `otakiage.item.submit` | `task_otakiage_item_submit` |
| `otakiage.reuse.requestSubmit` | `task_otakiage_reuse_request_submit` |
| `otakiage.reuse.findCandidates` | `task_otakiage_reuse_find_candidates` (R/PT1H) |
| `otakiage.reuse.expireOpen` | `task_otakiage_reuse_expire_open` (R/PT24H) |
| `otakiage.handover.confirm` | `task_otakiage_handover_confirm` |
| `otakiage.ritual.request` | `task_otakiage_ritual_request` |
| `otakiage.ritual.issueCertificate` | `task_otakiage_ritual_issue_certificate` |
| `otakiage.matsuri.scheduleSubmit` | `task_otakiage_matsuri_schedule_submit` |
| `otakiage.matsuri.seedNextMonth` | `task_otakiage_matsuri_seed_next_month` (cron 月初) |
| `otakiage.social.composeAnnounce` | `task_otakiage_social_compose_announce` |

Worker registration: `40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/zeebe_worker_main.py` `worker_profile in {"otakiage", ...}` branch.

## Helm Pool

`50-infra/vultr/mitama-otakiage-pool/`:
- `Chart.yaml` / `values.yaml` / `templates/otakiage-worker.yaml`
- Dedicated Deployment `otakiage-langserver-worker` (`LANGSERVER_HANDLER_PROFILE=otakiage`)
- Namespace = `mitama-udf` (shared Secrets)

## 3-Tier Write 規約

| Tier | データ | 書き込み API |
|---|---|---|
| **T1 Social** | handover/ritual 完了 post (PII 除去、H3 res-3 まで丸める) | `generic.pds.dispatch` (`app.bsky.feed.post`、author = path-DID :reuse / :ritual / :matsuri) |
| **T2 Domain** | 全 item / reuse_request / handover / ritual / matsuri / certificate | `psycopg3 sync_cursor` で INSERT/UPDATE → RisingWave |
| **T3 State** | donor / recipient PII (氏名 / 住所 / 連絡先) | `Preferences()` (server-side、AT Record に書かない) |

## Certificate (Phase 1 = AT Record JSON)

ritualized 時に発行:

```json
{
  "$type": "com.etzhayyim.otakiage.certificate",
  "ritualUri": "at://did:web:otakiage.etzhayyim.com:ritual/.../...",
  "itemUris": ["at://...", ...],
  "donorDids": ["did:web:alice.etzhayyim.com", ...],
  "issuedAt": "2026-04-15T10:00:00Z",
  "issuer": {
    "name": "etzhayyim",
    "kind": "religious-corporation",
    "did": "did:web:otakiage.etzhayyim.com:ritual"
  },
  "displayText": "ぬいぐるみ 3 体 / 絵本 12 冊 を 春の人形供養祭 にて謹んでお焚き上げいたしました",
  "categoryBreakdown": {"nuigurumi": 3, "ehon": 12},
  "matsuriUri": "at://...",
  "version": "1.0"
}
```

URI が永続 ID。Phase 2 で `anchorTokenId` に ERC725 anchor token を入れる。

## Phase 2 / Phase 3 ロードマップ

- **Phase 2**: ERC725 anchor token (Coinbase Smart Wallet 連携)、配送 actor 連携 (ヤマト集荷 API)、季節祭の Wan 2.2 動画生成 (供養祭 livestream highlight)、Svelte UI (登録/一覧/詳細)
- **Phase 3**: 神社仏閣 actor 連携 (合同供養祭の実物理イベント連携)、寄付 actor `donate.etzhayyim.com` との 2-way bridge、Well-Becoming Spirit objective 上のメトリクス組込

## Cross-deps

- `maps.etzhayyim.com` — H3 res-5 cell ID 借用 (近接マッチ)
- `fleamarket.etzhayyim.com` — 有償譲渡は別 actor (price=0 制約で otakiage は無償のみ)
- `donate.etzhayyim.com` (Phase 3) — 寄付領収書 (税控除) は別 actor
- 神社仏閣 actor (Phase 3) — 実物理ritual連携

## Operator manual run

```bash
# Migration 適用 (out-of-band 推奨, ADR-2604241342)
cd 30-graph/graph-schema && pnpm db:migrate latest
# or 1 本ずつ:
./scripts/apply-pending.sh 20260508120000_vertex_otakiage_schema
./scripts/apply-pending.sh 20260508120100_seed_otakiage_bpmn_actors
./scripts/apply-pending.sh 20260508120200_seed_otakiage_matsuri_calendar

# Helm install
helm install mitama-otakiage-pool 50-infra/vultr/mitama-otakiage-pool/ \
  --namespace mitama-udf

# Manual 1-shot (worker pod 内)
kubectl exec -n mitama-udf deploy/otakiage-langserver-worker -- python -c "
import asyncio
from kotodama.primitives.otakiage import task_otakiage_reuse_find_candidates as f
print(asyncio.run(f(maxItems=10)))
"
```
