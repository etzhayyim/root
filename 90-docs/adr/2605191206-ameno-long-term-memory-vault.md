---
id: 2605191206-ameno-long-term-memory-vault
title: Ameno long-term encrypted memory vault — IndexedDB + AES-GCM + MiniLM index
status: proposed
doc_type: adr
topic: ameno-memory-vault
authoritative: true
last_verified: 2026-05-19
depends_on:
  - 2605191120-ameno-embedding-surprise-tier-c
  - 2605191129-ameno-browser-tool-use-react
  - 2605191135-ameno-tier2-daemon-residency
  - adr-2605181100-mst-encrypted-records-signal-keywrap
related:
  - adr-2605172000-etzhayyim-rw-free-substrate
---

# ADR 2605191206: Ameno long-term encrypted memory vault — IndexedDB + AES-GCM + MiniLM index

## Context

ameno daemon は **working memory**(LocalCheckpointer の graph state)を持つようになったが、これは「現在の会話の続き」を保つだけで、turn 間で agent が "意図的に残したい長期記憶" を保存する場所がない。

artificial-organism 文脈で言えば、Tier 2 worker は:
- 現在処理中の brief の文脈(= working state)
- 過去の処理から抽出した **学習** / **記録** / **要約**(= long-term memory)

を別管理すべき。前者は LangGraph checkpoint で実現済。本 ADR で後者を実装する。

substrate boundary(ADR-2605172000)整合性:
- 永続化は browser-local の IndexedDB。サーバ側依存ゼロ
- ADR-2605181100 の `com.etzhayyim.encrypted.record` (AEAD envelope) と同 shape — 将来 `@etzhayyim/sdk/encryptedWrite` 経由で **同じ record を MST に昇格** できる設計

## Decision

**IndexedDB + AES-GCM + MiniLM embedding index による long-term memory vault を導入。agent は `remember` / `recall_long_term` の 2 tool でこの vault を能動的に使う。**

### Storage

| 項目 | 値 |
|---|---|
| Backend | IndexedDB database `ameno-memory-v1` |
| Object store | `memories`, key = auto-incremented integer |
| Encryption | AES-256-GCM。key は既存 `private-vault.ts` の `ensureKey()` を再利用 — origin per browser、localStorage 永続 |
| Per-record fields | `id` (auto), `iv` (12-byte base64), `ciphertext` (base64), `embedding` (Float32Array base64, 384-d MiniLM), `createdAt`, `tags`(暗号化対象外、検索フィルタ用) |
| Quota | IndexedDB は Chrome で disk の 60% 程度まで使える。ameno で実用域はテキスト数千件 |

Plaintext は `{ content, tags }` の JSON。これを AES-GCM で暗号化し ciphertext に格納。tags は別 column(plaintext)に残し、検索フィルタを可能に。embedding も plaintext(検索のため。content 自体は暗号化済なので embedding 単独からの逆引きは困難)。

### Tools

| name | args | result |
|---|---|---|
| `remember` | `{ "content": string, "tags"?: string[] }` | `"saved memory #<id>"` or `error: ...` |
| `recall_long_term` | `{ "query": string, "topK"?: number }` | 上位 K 件(default 3)を `[<id>] (sim=0.xxx, ago=Nd) content...` 形式 |

両 tool とも **MiniLM ready 必須**(`isEmbeddingReady() === true`)。未 ready の場合は error 文字列で model に通知し、user に "Enable embedding surprise mode first" と伝えるよう促す。

### Agent 動作の期待

```
user: "I'm going on a trip to Kyoto next month, can you remember that?"
agent: <tool>{"name":"remember","args":{"content":"User is planning Kyoto trip next month","tags":["plan","travel"]}}</tool>
tool → "saved memory #42"
agent: "Done — I'll keep that in mind."

(後日)
user: "Did I mention any travel plans?"
agent: <tool>{"name":"recall_long_term","args":{"query":"travel plans"}}</tool>
tool → "[42] (sim=0.81, 12h ago) User is planning Kyoto trip next month [plan,travel]"
agent: "Yes — you mentioned a Kyoto trip next month."
```

### UI 表面

- Daemon panel に `Memories: N stored (encrypted)` 行を 1Hz poll で表示
- (Phase 2) memory inspector — list / delete を編集できる開閉パネル(本 ADR 範囲外)

## Consequences

- ameno は会話文脈を超えた "持続的学習" の場を獲得。Tier 1 (Murakumo) と将来 sync する場合のキャッシュとしても機能
- AES-GCM 暗号化により、devtools から IndexedDB を覗いても plaintext は見えない(IV + ciphertext + base64 のみ)
- embedding も permanent storage に含まれるため、初回保存時の MiniLM encode コスト(WASM ~10ms)が再検索時にゼロ
- 将来 substrate 連携:
  - `@etzhayyim/sdk/encryptedWrite({collection: "com.etzhayyim.memory.record", record: {...}, recipients})` で同じ ciphertext + DID-bound key wrap に変換、MST に upload
  - browser local vault は **ローカルキャッシュ**として残し、conflict resolution は CRDT で(別 ADR)
- IndexedDB quota はユーザ管理。3 MB 超えても問題なし(対して localStorage は 5-10 MB 全体 cap)

## Alternatives Considered

1. **localStorage に格納** — 容量 cap 厳しすぎ、binary 扱いに弱い。reject
2. **vector DB(Voy / FAISS-wasm)** — 数百件のスケールでは線形 cosine で十分。複雑度コスト見合わない
3. **plaintext で保存** — 会話に PII / 個人情報が混じる前提、暗号化必須
4. **直接 MST に書く(@etzhayyim/sdk 経由)** — SDK の `encryptedWrite` は scaffold/TODO 状態(README 確認済)。先に local で完結させて, SDK 実体化と同時に swap

## References

- ADR-2605191120 (MiniLM Tier C embedding)
- ADR-2605191129 (browser tool use ReAct)
- ADR-2605191135 (Tier-2 daemon residency)
- ADR-2605181100 (MST encrypted records, future substrate target)
- WHATWG IndexedDB / W3C Web Crypto AES-GCM
