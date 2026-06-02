# packages/rust/wproto

W Protocol core logic crate。AT Protocol + Signal Protocol を Bytecode Alliance wRPC 標準で統合し、yata-mdag で content-addressed sync を提供。

## Design Docs

- `docs/260317-w-protocol-wrpc-design.md` — wRPC 標準適合設計 (primary)
- `docs/260317-w-protocol-design.md` — 初版設計 (参考)
- `docs/260317-yoro-w-protocol-messenger-design.md` — メッセンジャー実装設計

## Module 役割

| Module | 役割 |
|---|---|
| `at.rs` | AT Protocol re-exports (`pub use yata_at::*`) — AtClient, AtFirehose, AtFirehoseBridge |
| `signal.rs` | Signal Protocol re-exports (`pub use yata_signal::*`) — X3DH, Ratchet, SenderKey, host_api, SignalStorage |
| `firehose.rs` | WFirehoseClassifier — W Protocol collection classification for AT Firehose |
| `types.rs` | WEnvelope, WChannel, WMember, EncryptionState, ChannelKind |
| `blocks.rs` | MDAG blocks: EnvelopeBlock, EnvelopeGroupBlock, ChannelRootBlock, MemberBlock, WRootBlock |
| `channel.rs` | ChannelStore — Cypher graph + MDAG。A2A identity/capability graph queries |
| `session.rs` | SessionManager — Signal crypto (yata-signal direct) + SignalStorage persistence |
| `pipeline.rs` | WPipeline — core orchestrator: send/create-channel + A2A session/task/message |
| `commit.rs` | WCommitLog — channel-scoped MDAG commit chain (time-travel, checkout, history) |
| `diff.rs` | `w_diff()` — Merkle diff between channel commits O(changed kinds) |
| `crypto.rs` | AutoCrypto — encryption decision engine (host/client/passthrough) |
| `record.rs` | RecordMapper — CBOR primary + Lexicon JSON derived。`kind` → `com.etzhayyim.w.{kind}` |
| `serve.rs` | WrpcRouter — wRPC instance/method routing constants |
| `invoke.rs` | FederationInvoke — wRPC federation call helpers |
| `transport.rs` | NatsSubjects — NATS subject mapping (for yata-wrpc) |

## WIT Interface

`wit/gftd-w/w.wit` — `gftd:w@0.1.0`

| Interface | 責務 |
|---|---|
| `w-command` | mutations → AT Record + MDAG commit + Signal auto-encrypt |
| `w-query` | reads → KV/CAS/Cypher + MDAG sync state + diff + block fetch |
| `w-federation` | announce / request-diff / pull-blocks / push-blocks / sync-channel |
| `w-handler` | component export — inbound envelope processing |

## Wire Format 3 層

| Layer | Format | Purpose |
|---|---|---|
| **wRPC wire** | Component Model binary | RPC dispatch (Invoke/Serve)。ephemeral |
| **MDAG CAS** | CBOR (Blake3 CID) | Content-addressed storage。durable。federation diff |
| **AT Lexicon** | JSON (camelCase) | AT Protocol federation surface。derived only |

**CRITICAL: Internal dispatch に JSON を使わない。** CBOR (MDAG CAS) が primary storage format。JSON は AT Protocol federation のみ。

## Crypto Decision Flow (CRITICAL)

```
AutoCrypto::decide_encrypt(channel, sender_is_bot)
  ├─ Plaintext channel         → Passthrough (payload as-is)
  ├─ Signal1to1 + bot/a2a     → HostEncrypt1to1 (host が bot DID で暗号化)
  ├─ Signal1to1 + human       → ClientEncrypted (人間が client で暗号化済み)
  ├─ SignalGroup + bot/a2a    → HostEncryptGroup (host が Sender Key で暗号化)
  └─ SignalGroup + human      → ClientEncrypted (人間が client で暗号化済み)
```

**人間の encrypted message は `contentType: "application/x-signal-envelope"` で判定。**

## MagatamaApp SDK (magatama-go)

W Protocol を使う app は以下の SDK 関数を使用:

| 操作 | SDK 関数 |
|---|---|
| メッセージ送信 | `magatama.WSend(channelID, kind, payload, contentType, replyTo, threadID)` |
| チャンネル作成 | `magatama.WCreateChannel(name, description, kind, inviteDIDs)` |
| DM 作成 | `magatama.WCreateDM(peerDID, kind, payload, contentType)` |
| メッセージ一覧 | `magatama.WListEnvelopes(channelID, page, beforeRkey, afterRkey)` |
| スレッド取得 | `magatama.WGetThread(channelID, rootRkey)` |
| 検索 | `magatama.WSearch(query, channelID, page)` |
| 未読数 | `magatama.WGetUnread()` |
| 既読マーク | `magatama.WMarkRead(channelID, lastRkey)` |
| プレゼンス | `magatama.WUpdatePresence(status, statusText)` |

**禁止**: W Protocol 対象の操作で `magatama.KvPut/KvGet` + JSON marshal を手動で行うこと。host が KV/CAS/AT Record を自動管理する。

## MDAG Integration

- WEnvelope → CBOR block → Blake3 CID (content-addressed, dedup)
- Channel ごとの commit chain (`WRootBlock.parent`)
- `w_diff()`: Merkle diff O(changed kinds) — 未変更 kind group は CID 比較で O(1) skip
- `WChannel.mdag_root_cid`: channel state hash — federation sync anchor
- Time-travel: `checkout_envelopes(old_root_cid)` で任意時点の state 取得

## wRPC Transport (yata-wrpc)

| | yata-wrpc (embedded) | wrpc-transport-nats (external) |
|---|---|---|
| Latency | **583µs** | ~2-5ms |
| Overhead | **400B** | ~2.5KB |
| External deps | **None** | NATS server |

**CRITICAL: yata-wrpc (embedded broker) が primary transport。** 外部 NATS は使用しない。wRPC over QUIC は federation (P2P) のみ。

## AT/Signal/A2A Single Source of Truth (CRITICAL)

wproto is the unified import point for AT Protocol, Signal Protocol, and A2A communication:

| 機能 | import path | 元 crate |
|---|---|---|
| AT Protocol client/firehose | `wproto::at::*` | `yata-at` (re-export) |
| Signal Protocol crypto | `wproto::signal::*` | `yata-signal` (re-export) |
| Signal host API (WIT) | `wproto::signal::host_api::*` | `yata-signal::host_api` |
| Signal storage trait | `wproto::signal::SignalStorage` | `yata-signal::store` |
| W Protocol firehose | `wproto::firehose::WFirehoseClassifier` | wproto native |

**禁止**: `magatama-engine` / `magatama-server` が `yata-at` / `yata-signal` を直接依存すること。`wproto` 経由で import する。

### SessionManager (direct Signal integration)

`SessionManager` は `yata_signal::store::SignalStorage` を直接保持し、X3DH/Ratchet/SenderKey を自前で管理する。
旧 `SignalStore` トレイト (7 methods) は削除済み — 中間 adapter 不要。

### A2A conversation → W Protocol

`conversation` WIT interface は W Protocol `WChannel { kind: A2a }` 経由:
- `create_session()` → `dispatch("create-channel", {kind: "a2a", ...})`
- `send_message()` → `dispatch("send", {kind: "a2a-message", ...})`
- `get_history()` → `dispatch("list-envelopes", {channelId, ...})`

MDAG commit chain, Merkle diff, auto-encryption が自動適用。

## Key Rules

- **kind → AT collection は自動**: `RecordMapper::kind_to_collection("message")` → `com.etzhayyim.w.message`
- **A2A/governance passthrough**: `a2a-task` → `com.etzhayyim.a2a.task` (既存 collection)
- **MDAG CID = envelope identity**: 同一内容 → 同一 CID (dedup)
- **Commit chain per channel**: `WRootBlock.parent` で time-travel
- **Merkle diff O(changed)**: 未変更 kind group は CID 比較で O(1) skip
- **Human participation**: Connect gRPC facade → wRPC bridge。real-time = AT Firehose WebSocket
- **Bot/Agent participation**: WIT import (in-process)。real-time = w-handler callback
