---
id: adr-2605141800-etzhayyim-email-wire-protocol
title: "ADR-2605141800: etzhayyim Email Wire Protocol (GEWP) v1.0 — Open Standard"
status: accepted
doc_type: adr
topic: etzhayyim-email-wire-protocol
authoritative: true
last_verified: 2026-05-14
priority: 7.5
axis: architecture
weight: 0.75
priority_note: "LLM agent 間・グループメール・人間との Pregel メッセージパッシングを SMTP/MIME で実現するワイヤプロトコル。Apache-2.0 + CC-BY-4.0 のオープン規格として公開。"
authoritative_for:
  - GEWP v1.0 仕様 (Core + Extension)
  - MIME multipart wire format (application/vnd.gewp+json)
  - GEWP JSON payload core schema
  - ext:pregel / ext:atproto / ext:langgraph 拡張仕様
  - 既存 W3C / IETF / FIPA 規格との関係
  - MIME type 登録ロードマップ
depends_on:
  - adr-2605131800-pregel-triage-langgraph-email-intent-routing
  - adr-2605080000-distributed-cognitive-actor-system
  - adr-0095-simplified-3layer-identity-rw-vault
related:
  - adr-0032-gmail-direct-ingest-yabai-classifier
  - adr-2605072000-langgraph-agent-loop-pattern
  - adr-2605091400-mcp-as-cell-membrane-lexicon-xrpc-demotion
---

# ADR-2605141800: etzhayyim Email Wire Protocol (GEWP) v1.0

## Goal

LLM agent どうし・グループメール・人間が **SMTP/MIME を transport** として
Pregel スタイルのメッセージパッシングを行うための wire protocol を規格化する。

本仕様は **etzhayyim Japan が策定・維持するオープン規格** であり、
etzhayyim 固有の実装への依存を Core から排除することで第三者実装を可能にする。

---

## Governance & License

| 項目 | 値 |
|---|---|
| Maintainer | etzhayyim Japan 株式会社 |
| Spec URL | `https://spec.etzhayyim.com/gewp/v1/` |
| Schema URL | `https://spec.etzhayyim.com/gewp/v1/schema.json` |
| Spec text license | **CC-BY-4.0** |
| Schema / code license | **Apache-2.0** |
| Versioning | semver (`major.minor`) — minor は後方互換、major は breaking |
| Issue tracker | `github.com/etzhayyim/gewp-spec` (予定) |

---

## 先行規格との関係

GEWP は以下の規格の語彙・パターンを参照しているが、適合 (conformance) を主張しない。
各規格の必須フィールド要件を完全には満たさない箇所があるため。

| 参照規格 | 採用した要素 | 未採用・差分 |
|---|---|---|
| **ActivityPub** (W3C Rec 2018) | Actor inbox モデル、`to` / `cc` 意味論 | HTTP transport → SMTP に変更。`@context` は省略可 |
| **ActivityStreams 2.0** (W3C Rec 2017) | `actor`, `to`, `cc`, `inReplyTo` 語彙、`@type: Person/Service/Application` | AS2.0 必須の `@context` は Core では任意 |
| **Linked Data Notifications** (W3C Rec 2017) | `inbox` = メールアドレス、送信 = SMTP、受信 = IMAP/JMAP の概念的対応 | LDP Container 要件は課さない |
| **Schema.org Gmail Markup** | `application/ld+json` の概念を参照 | Gmail は `<script>` タグを削除するため Layer 2 では不採用 |
| **FIPA-ACL** (FIPA SC00061) | performative 語彙 (`inform`, `request` 等)。FIPA 仕様は SMTP を正式 transport と規定 | FIPA-ACL の全フィールド要件は課さない |
| **RFC 5322** Internet Message Format | `Message-ID`, `References`, `In-Reply-To` によるスレッド追跡 | そのまま採用 |
| **RFC 2045–2049** MIME | `multipart/mixed` コンテナ | そのまま採用 |

---

## ヘッダーの生存率と信頼レベル

```
信頼 HIGH  : Message-ID, References, In-Reply-To  (全 MTA で保存)
信頼 HIGH  : MIME part application/vnd.gewp+json   (Gmail/Outlook で保存)
信頼 MEDIUM: HTML comment <!-- GEWP:{base64url} --> (MTA・クライアントは削除しない)
信頼 LOW   : X-GEWP-* カスタムヘッダー             (転送・返信で消えうる)
```

> **注意**: Gmail・Outlook は `<script>` タグをセキュリティ上無条件に削除する。
> Layer 2 fallback に `<script type="application/ld+json">` は使用不可。
> Schema.org Gmail Markup はホワイトリスト企業専用であり任意送信者には利用不可。

**プロトコルの正規データは MIME part に置く。X-GEWP-* ヘッダーを routing の正規ソースとして使ってはならない。**

### 3-layer redundancy

```
Layer 1 (正規)     : MIME part  application/vnd.gewp+json
Layer 2 (fallback) : HTML comment  <!-- GEWP:{base64url(JSON payload)} -->
Layer 3 (hint)     : X-GEWP-Thread / X-GEWP-Step / X-GEWP-Type headers
```

---

## Wire Format

### MIME 構造

```
MIME-Version: 1.0
Message-ID: <{uuid}@{sender-domain}>
From: {sender-address}
To: {recipient1}, {recipient2}
Subject: {human_readable_subject}
In-Reply-To: <{parent_message_id}>
References: <{root_id}> <{parent_id}>

X-GEWP-Thread: {thread_id}           ← routing hint (best-effort)
X-GEWP-Step: {superstep}             ← routing hint (best-effort)
X-GEWP-Type: pregel.message          ← routing hint (best-effort)

Content-Type: multipart/mixed; boundary="GEWP_BOUNDARY"

--GEWP_BOUNDARY
Content-Type: text/plain; charset=utf-8

{人間が読めるテキスト本文}

--GEWP_BOUNDARY
Content-Type: text/html; charset=utf-8

<div>{人間向け HTML 本文}</div>

<!-- Layer 2: HTML comment fallback -->
<!-- GEWP:{base64url(JSON payload)} -->

--GEWP_BOUNDARY
Content-Type: application/vnd.gewp+json; charset=utf-8
Content-Disposition: inline; filename="gewp.json"

{← Layer 1 正規 JSON payload}

--GEWP_BOUNDARY--
```

---

## Core JSON Payload Schema

Core は実装者が etzhayyim に依存せず実装できる最小集合。

```jsonc
{
  // === Protocol version (REQUIRED) ===
  "gewp": "1.0",

  // === メッセージ種別 (REQUIRED) ===
  "type": "pregel.message",
  // "pregel.message" : agent/human から次頂点へのメッセージ
  // "pregel.barrier" : superstep 完了通知
  // "human.intent"   : 受信 agent が人間メールから合成 (送信には使わない)

  // === FIPA-ACL performative (agent→agent 時 REQUIRED) ===
  // inform / request / query-if / propose / confirm / refuse / failure
  "performative": "inform",

  // === Thread (REQUIRED) ===
  "thread": {
    "id": "thd_01HXK3M",            // partition key。スレッド全体で不変
    "step": 3                        // superstep counter。単調増加
  },

  // === Sender (REQUIRED) ===
  // ActivityStreams 2.0 actor 語彙を参照
  "sender": {
    "@type": "Service",              // Person | Service | Application
    "id": "https://example.com/agent/shinshi"  // actor IRI (URI)
  },

  // === Recipients (REQUIRED: to に最低 1 件) ===
  // role: "vertex" = 次 Pregel 頂点、"observer" = CC のみ、"human" = ペイロード除去
  "to": [
    {
      "@type": "Service",
      "id": "https://example.com/agent/jukyu",
      "email": "jukyu@example.com",
      "role": "vertex"
    }
  ],
  "cc": [],

  // === Application payload (REQUIRED, schema は graph 定義側) ===
  "payload": {},

  // === Vertex state (OPTIONAL) ===
  "state": {
    "inline": null,                  // < 4KB: ここに展開
    "ref": { "url": "..." }          // 大サイズ: URI 参照
  },

  // === Integrity (OPTIONAL) ===
  "auth": {
    "nonce": "...",
    "issued_at": "2026-05-14T09:00:00Z",
    "sig": "..."                     // HMAC-SHA256(canonical payload, thread.id+nonce)
  }
}
```

---

## Extension: ext:pregel

Pregel BSP バリアセマンティクスを追加する。

```jsonc
{
  "gewp": "1.0",
  "extensions": ["ext:pregel"],

  "thread": {
    "id": "thd_01HXK3M",
    "step": 3,
    // ext:pregel が追加するフィールド:
    "root_message_id": "<abc@mail.example.com>",  // RFC 5322 Message-ID
    "barrier": {
      "total_vertices": 3,           // このステップで送信すべき頂点数
      "timeout_seconds": 300         // バリアタイムアウト
    }
  }
}
```

**バリア解放条件**: `thread.id` × `thread.step` の組み合わせで `barrier.total_vertices` 件のメッセージが揃った時点。

---

## Extension: ext:atproto  *(etzhayyim 固有)*

AT Protocol DID によるアクターアドレッシング。

```jsonc
{
  "extensions": ["ext:atproto"],
  "sender": {
    "id": "https://pregel.etzhayyim.com",
    // ext:atproto が追加:
    "did": "did:plc:shinshi123",
    "handle": "shinshi.lawfirm.etzhayyim.com"
  },
  "payload": {
    "document_cid": "bafyrei..."     // AT Protocol CID 参照
  }
}
```

---

## Extension: ext:langgraph  *(etzhayyim 固有)*

LangGraph Server との紐付け。

```jsonc
{
  "extensions": ["ext:langgraph"],
  "thread": {
    "id": "thd_01HXK3M",
    "step": 3,
    // ext:langgraph が追加:
    "graph": "legal-corpus-review",
    "run_id": "run_01HXK3M"
  },
  "to": [
    {
      "role": "vertex",
      "node": "review_node"          // LangGraph ノード名
    }
  ],
  "sender": {
    "model": "claude-sonnet-4-6"     // resolveModelId() 経由で設定
  }
}
```

---

## 送受信パターン

### Agent → Agent

```
sender → SMTP 送信 → recipient のメールアドレス
recipient pod: IMAP IDLE / Outlook webhook でポーリング
  → MIME Layer 1 parse → PregelMessage
  → thread.step が期待値と一致しない場合は discard
```

### Human → Agent (人間が普通のメールを書く)

```
人間は JSON 不要。通常メールを送信するだけ。
agent 側 ingest_email():
  1. Layer 1 MIME part があれば正規パース
  2. なければ Layer 2 HTML comment の base64url を試みる
  3. どちらもなければ LLM で intent 抽出
     → PregelMessage(type="human.intent", performative="request")
```

### Agent → Human (返信)

```
to[role="human"] の受信者には state / payload の業務データを渡さない。
text/plain + text/html のみに人間向けサマリを書く。
Layer 1 は送信するが payload を空オブジェクトにする。
```

---

## IANA Considerations

- 現行: `application/vnd.gewp+json` (vendor tree — IANA 登録なしで使用可)
- 拡張型: `application/vnd.gewp.{ext-name}+json`
- 将来: IETF RFC を経て `application/gewp+json` (standards tree) への昇格を検討。
  現時点では登録手続きを開始しない。

---

## Conformance

| レベル | 条件 |
|---|---|
| **Core Conformant** | Layer 1 MIME part を送受信できる。Core Schema の REQUIRED フィールドを満たす |
| **Layer-2 Conformant** | Core に加え HTML comment fallback を正しく読み書きできる |
| **ext:pregel Conformant** | バリア解放ロジックを実装している |

---

## BEC 暗号化との共存 *(etzhayyim 固有)*

BEC Tier-2 環境では subject / body が暗号化される:
- `payload` に平文を書かない
- `payload.document_cid` (ext:atproto) で AT Protocol record を参照し pod 側で復号
- `payload` 全体を `signal:v1:{ciphertext}` で暗号化することも可

---

## Forbidden Patterns

| 禁止 | 理由 |
|---|---|
| `X-GEWP-*` ヘッダーを正規データソースとして使う | 転送で消えるため。Layer 1 が SSoT |
| Layer 2 に `<script type="application/ld+json">` を使う | Gmail/Outlook が無条件削除。HTML comment を使う |
| `human` role の受信者に payload / state を含める | 業務データ漏洩リスク |
| `thread.step` を単調増加以外の値で設定する | Pregel superstep 整合性破壊 |
| `gewp` フィールドを省略する | バージョン互換性の検出不能 |
| LLM model 名をハードコードする (ext:langgraph) | `resolveModelId()` / `MURAKUMO_DEFAULT_MODEL` を使う |
| Core Schema に etzhayyim 固有フィールドを混入する | extension に分離する |

---

## References

### 採用規格
- [ActivityPub (W3C Rec 2018)](https://www.w3.org/TR/activitypub/)
- [ActivityStreams 2.0 (W3C Rec 2017)](https://www.w3.org/TR/activitystreams-core/)
- [Linked Data Notifications (W3C Rec 2017)](https://www.w3.org/TR/ldn/)
- [FIPA-ACL SC00061](http://www.fipa.org/specs/fipa00061/) — SMTP transport binding
- RFC 5322 Internet Message Format
- RFC 2045–2049 MIME

### 内部参照
- ADR-2605131800 (pregel triage LangGraph)
- ADR-2605080000 (Distributed Cognitive Actor System)
- ADR-2605091400 (MCP as Cell Membrane)
- `00-contracts/schemas/etzhayyim-email-wire-protocol.schema.json`
- `40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/pregel/`
- `60-apps/etzhayyim-project-pregel/`
