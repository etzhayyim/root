---
id: 260322-w-protocol-record-encryption-lexicon-design
title: "W Protocol Record Encryption & Lexicon Design — API 使い分けガイド"
status: active
doc_type: reference
topic: w-protocol-encryption-lexicon
authoritative: true
last_verified: 2026-03-22
authoritative_for:
  - W Protocol record encryption model
  - Lexicon namespace encryption classification
  - ATPost vs WRecord vs WSend API selection
related:
  - 260317-w-protocol-design
  - 260318-w-protocol-sender-trust-design
  - 260321-consent-gated-data-sharing-design
supersedes: []
superseded_by: []
---

# W Protocol Record Encryption & Lexicon Design

## Goal

App 開発者が **どの API で何を書くか** を迷わず選択できるようにする。暗号化はチャネル単位で自動適用され、record 単位の明示的暗号化は不要。

## Executive Summary

W Protocol は **3 層の書き込み API** を提供する。各 API は異なる AT Protocol Lexicon namespace にマッピングされ、暗号化ポリシーが異なる。

| API | 用途 | AT Lexicon | 暗号化 | 可視性 |
|---|---|---|---|---|
| **`ATPost`** | Social (投稿/Like/Follow) | `app.bsky.*` | **Plaintext** | **Public** (Bluesky federation) |
| **`WRecord`** | Domain data write | `ai.gftd.apps.*` | **Plaintext** | **App-scoped** (org_id RLS) |
| **`WSend`** | Channel messaging | `ai.gftd.messaging.*/ai.gftd.signal.*/ai.gftd.matrix.*` | **Channel 依存** | **Channel members** |

**禁止**: `WSend` を social post に使用。`WRecord` を private messaging に使用。

## Namespace Architecture (10 namespaces)

権威ソース: `10-protocol/wproto/core/src/record.rs` (`kind_to_collection`)

### Bluesky 互換 (Public)

| Collection | Kind | 暗号化 | 公開 | SDK |
|---|---|---|---|---|
| `app.bsky.feed.post` | `"follow"` auto-map | Plaintext | Public (firehose) | `ATPost(text, opts)` |
| `app.bsky.feed.like` | `"like"` | Plaintext | Public | `ATLike(uri, cid)` |
| `app.bsky.feed.repost` | `"repost"` | Plaintext | Public | `ATRepost(uri, cid)` |
| `app.bsky.graph.follow` | `"follow"` | Plaintext | Public | `Follow(nanoid)` |
| `app.bsky.graph.block` | `"block"` | Plaintext | Public | `ATBlock(did)` |
| `app.bsky.actor.profile` | `"profile"` | Plaintext | Public | Auto (`App.Serve()`) |

**設計意図**: Bluesky エコシステムと 100% 互換。全ての social graph action は公開情報として AT Protocol firehose で配信される。

### W Protocol Structured (Internal)

| Namespace | Kind prefix | 暗号化 | 可視性 | 用途 |
|---|---|---|---|---|
| `ai.gftd.messaging.*/ai.gftd.signal.*/ai.gftd.matrix.*` | `message`, `channel`, `member`, ... | **Channel 依存** | Channel members | Messaging, Signal session |
| `wproto.convo.*` | `conversation-message` | **Signal E2E** | Agent pair | Agent 間通信 |
| `ai.gftd.governance.*` | `governance-*` | Plaintext | Org-internal | RACI, risk, data classification |
| `ai.gftd.contract.*` | `contract-*` | Plaintext | Org-internal | 法的根拠, agreements |
| `ai.gftd.consent.*` | `consent-*` | Plaintext (VC/VP metadata) | Identity-scoped | Cross-app data sharing |
| `ai.gftd.rbac.*` | `rbac-*` | Plaintext | Org-internal | RBAC roles/assignments |
| `ai.gftd.audit.*` | `audit-*` | Plaintext | Auditor | Compliance log, OCEL |
| `ai.gftd.dm2.*` | `dm2-*` | Plaintext | Org-internal | DoDAF DM2 topology |
| `ai.gftd.identity.*` | `identity-*` | Plaintext | Public (federation) | ActorCard, capabilities |
| `ai.gftd.apps.*` | `{domain}.{record}` | **Plaintext** | App-scoped (RLS) | App domain data |

### Legacy (後方互換)

| Namespace | 状態 | 移行先 |
|---|---|---|
| `ai.gftd.w.*` | **Legacy reads only** | Social → `app.bsky.*`、Data → `ai.gftd.apps.*`、Messaging → `ai.gftd.messaging.*/ai.gftd.signal.*/ai.gftd.matrix.*` |

## Encryption Model

権威ソース: `10-protocol/wproto/core/src/crypto.rs` (`AutoCrypto`)

### 原則

1. **Host は暗号参加者ではない** — 暗号文リレーのみ
2. **暗号化は channel 単位** — record 単位ではない
3. **Guest WASM が暗号化** — Signal Protocol は guest component (yata-signal-wasm) 内で実行
4. **AutoCrypto が判定** — channel の `encryption_mode` + payload の `content_type` で自動判定

### Channel Kind → Encryption

| Channel Kind | Encryption Mode | Content-Type (wire) | 暗号化主体 |
|---|---|---|---|
| `Public` / `Space` | **Plaintext** | any | なし |
| `Private` | **Plaintext** | any | なし |
| `Direct` (1:1 DM) | **Signal 1:1** (X3DH + Double Ratchet) | `application/x-signal-envelope` | Guest WASM (human: client、bot: composed WASM) |
| `GroupDm` (N-party) | **Signal group** (Sender Keys) | `application/x-signal-envelope` | Guest WASM |
| `Bot` (Agent channel) | **Signal 1:1** (host-assisted) | `application/x-signal-envelope` | Guest WASM |
| `A2a` (Agent-to-Agent) | **Signal E2E** | `application/x-signal-envelope` | Guest WASM (both agents) |

### AutoCrypto Decision Matrix

| Channel encryption_mode | Payload content_type | Host action | 結果 |
|---|---|---|---|
| Plaintext | any | **Passthrough** | 平文で保存・配信 |
| Signal1to1 / SignalGroup | `application/x-signal-envelope` | **E2EEncrypted** (passthrough) | 暗号文をそのまま保存・リレー |
| Signal1to1 / SignalGroup | その他 (平文) | **ERROR** | Sender が暗号化していない → reject |
| ClientEncrypted | any | **E2EEncrypted** (passthrough) | 不透明な暗号文としてリレー |

### Data Flow

```
[ATPost] ──→ app.bsky.feed.post ──→ PDS ──→ AT Record (plaintext) ──→ Firehose (public)

[WRecord] ──→ ai.gftd.apps.{domain}.{kind} ──→ PDS ──→ yata Cypher direct (SHA-256 content CID)

[WSend to public channel] ──→ ai.gftd.platform.message ──→ Plaintext ──→ Channel members

[WSend to DM channel] ──→ ai.gftd.platform.message ──→ Signal E2E ──→ Ciphertext only ──→ Endpoints only

[WCreateDM] ──→ Signal session auto-create ──→ all messages E2E encrypted
```

## API Selection Guide

### Question: 「何を使うべき?」

```
公開したい情報?
  ├─ はい → 人に見せる social 投稿?
  │   ├─ はい → ATPost (app.bsky.feed.post)
  │   └─ いいえ → WRecord (ai.gftd.apps.{domain}.{kind})
  │
  └─ いいえ → 特定の相手に送る?
      ├─ 1:1 DM → WCreateDM (Signal E2E 自動)
      ├─ Agent 間 → Invoke (GovernanceGate + Signal E2E 自動)
      └─ Channel members → WSend (channel encryption_mode に従う)
```

### Concrete Examples

| シナリオ | API | Collection | 暗号化 |
|---|---|---|---|
| Victory Royale 通知 | `ATPost("Winner: Alice!")` | `app.bsky.feed.post` | Plaintext (public) |
| マッチ結果データ | `WRecord("kami.matchResult", data)` | `ai.gftd.apps.kami.matchResult` | Plaintext (app-scoped) |
| ランク昇格通知 | `ATPost("Promoted to Diamond!")` | `app.bsky.feed.post` | Plaintext (public) |
| Ranked profile 更新 | `WRecord("kami.rankedProfile", data)` | `ai.gftd.apps.kami.rankedProfile` | Plaintext (app-scoped) |
| Agent 間タスク依頼 | `Invoke("", tool, args)` | `wproto.convo.message` | **Signal E2E** |
| ユーザーへの DM | `WCreateDM(did, kind, payload, ct)` | `ai.gftd.platform.message` | **Signal E2E** |
| 監査ログ | `WRecord("audit-entry", data)` | `ai.gftd.audit.entry` | Plaintext (auditor) |
| 契約参照 | `WRecord("contract-ref", data)` | `ai.gftd.contract.ref` | Plaintext (org) |
| 個人プロフィール | Auto (`App.Serve()`) | `app.bsky.actor.profile` | Plaintext (public) |
| Follow 関係 | `Follow(nanoid)` | `app.bsky.graph.follow` | Plaintext (public) |

## Information Classification

| Level | 例 | 暗号化 | Access Control |
|---|---|---|---|
| **Public** | Social post, profile, follow | Plaintext | なし |
| **Internal** | Governance, DM2, RBAC | Plaintext | `org_id` RLS |
| **Confidential** | Contract, audit | Plaintext | `org_id` RLS + clearance |
| **Restricted** | DM, cross-actor, Signal session | **Signal E2E** | Members only + Signal keys |

## App Implementation Rules

### DO (推奨)

```go
// Social notification (public, Bluesky Lexicon)
magatama.ATPost("New article published: "+title, &magatama.ATPostOpts{
    Embed: &magatama.ATEmbed{
        Type: "app.bsky.embed.external",
        URI:  "https://app.gftd.ai/articles/" + id,
        Title: title,
    },
})

// Domain data write (app-scoped, plaintext)
magatama.WRecord("myapp.article", map[string]any{
    "id": id, "title": title, "content": body,
    "org_id": ctx.OrgID, "user_id": ctx.UserID,
})

// Domain data read
resultJSON, err := magatama.G("Article").
    Match(magatama.Eq{"org_id": ctx.OrgID}).
    Return("id", "title", "content").
    Query()
```

### DON'T (禁止)

```go
// NG: WSend で social post
magatama.WSend("feed", "post", data, "text/plain", nil, nil) // ← Bluesky に載らない

// NG: WRecord で private message (暗号化されない)
magatama.WRecord("message", map[string]any{"text": "秘密の内容"}) // ← 平文で保存される

// NG: ATPost で internal data
magatama.ATPost(sensitiveInternalData, nil) // ← Bluesky firehose で全公開される
```

## Authoritative Sources

| 項目 | ファイル |
|---|---|
| Namespace mapping (kind → collection) | `10-protocol/wproto/core/src/record.rs` |
| AutoCrypto decision engine | `10-protocol/wproto/core/src/crypto.rs` |
| EncryptionState / ChannelKind enum | `10-protocol/wproto/core/src/types.rs` |
| Signal Protocol integration | `90-docs/260317-w-protocol-design.md` §Signal Protocol Integration |
| True E2E architecture | `90-docs/260318-w-protocol-sender-trust-design.md` |
| Consent / clearance model | `90-docs/260321-consent-gated-data-sharing-design.md` |
| Bluesky social API (magatama-go) | `20-actors/magatama/magatama-go/imports.go` (`ATPost`, `ATLike`, `Follow`) |
| WRecord / G() API | `20-actors/magatama/magatama-go/wproto_cqrs.go` |
