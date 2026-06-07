---
id: wit-lexicon-typed-alignment
title: "WIT Lexicon Typed Alignment — AT Protocol 型体系の WIT 直接写像 [SUPERSEDED 2026-04-13]"
status: superseded
doc_type: explanation
topic: wit-lexicon-alignment
authoritative: false
last_verified: 2026-04-13
authoritative_for: []
related:
  - w-protocol-at-superset-architecture
  - did-path-lexicon-correspondence
  - pds-yata-r2-lexicon-process-map
supersedes: []
superseded_by:
  - f-plan-lexicon-as-contract
---

> **⚠️ SUPERSEDED 2026-04-13 (F-Plan: Lexicon-as-Contract)**
>
> This document described a WIT-Lexicon dual-SSoT alignment strategy. The F-Plan migration
> consolidated host capability surface to **Lexicon JSON only** (`00-contracts/lexicons/com/etzhayyim/host/`,
> 37 capability lexicons across 21 groups). WIT files for TS Native (DEFAULT) apps were archived
> to `_archive/wit-2026-04-13/` (3007 files across 936 component dirs). Two T3 components retain
> in-tree wit/ for legacy compat: `cad/cd4dview` (Container) + `hoge/contract-jco` (Rust).
>
> The codegen pipeline matches atproto's official `lex gen-api` pattern:
>
> | Layer | Path |
> |---|---|
> | SSoT | `00-contracts/lexicons/com/etzhayyim/host/**/*.json` |
> | Codegen (lex-cli analog) | `70-tools/scripts/contract/gen-host-client-from-lexicon.mjs` |
> | Generated client | `40-engine/kotoba/crates/kotoba-kotodama/sdk/kotodama-host-sdk/src/generated/host-client.ts` |
> | Dispatch (BindingTransport NSID router) | `40-engine/kotoba/crates/kotoba-kotodama/sdk/kotodama-host-sdk/src/host-dispatcher.ts` |
> | Authoritative current ref | `40-engine/kotoba/crates/kotoba-kotodama/CLAUDE.md` §Host Capability Contract |
>
> Shannon η for host capability surface = **1.0** (single SSoT, all other layers are derived).
>
> The historical content below describes the original dual-SSoT thinking and is preserved for
> reference only. **Do not use it as a guide for new work.**

---

# WIT Lexicon Typed Alignment — AT Protocol 型体系の WIT 直接写像

## Goal

AT Protocol Lexicon の **noun 層 (record schema)** を WIT record 型として直接定義し、現在の opaque `string` (JSON blob) 透過設計から **typed WIT** に移行する。

## Scope

- `kotodama:wproto` package 内に AT Protocol Lexicon の core 型を WIT record として追加
- `kotodama:bsky` package を新設し、`app.bsky.*` Lexicon 型を WIT で定義
- `etzhayyim wit-gen` の Lexicon JSON 生成を WIT record 定義から自動導出に切り替え
- Guest SDK (kotodama-go, kotodama-guest-rust, kotodama-ts, kotodama-py) の型安全 API 提供

## Executive Summary

**方針 A: WIT に Lexicon 型を追加する。**

現在の WIT は AT Protocol の **verb 層** (write/update/delete/query) を完全に定義しているが、**noun 層** (post/profile/facet/embed/label の型構造) は `string` (opaque JSON) として透過している。これは federation 互換性を制限し、guest code にボイラープレート JSON 組み立てを強制する。

WIT に Lexicon 型を直接写像することで:
1. **Compile-time type safety** — guest SDK が型安全な record 構築を提供
2. **Federation validation** — PDS facade 層で record body を WIT 型に基づき検証
3. **Code generation 精度向上** — `etzhayyim wit-gen` が WIT record → Lexicon JSON Schema を正確に導出
4. **AT Protocol spec 追従** — Lexicon 変更時に WIT record を更新、全 component が rebuild で型不整合を検出

## Decision

### Phase 1: AT Protocol Core Types (`kotodama:atproto`) ✅

`00-contracts/wit/deps/kotodama-atproto/package.wit`。Authoritative source は WIT ファイル本体。以下は概要。

**定義済み型:** `at-uri` (`@format at-uri`)、`cid` (`@format cid`)、`at-did` (`@format did`)、`datetime` (`@format datetime`)、`strong-ref`、`blob-ref`、`create-record-input` (`@format at-identifier`/`@format nsid`)、`self-label` (`@max-length 128`)、`label` (9 fields, `@max-length 128` on val, `@default false` on neg)

### Phase 2: Bluesky Social Types (`kotodama:bsky`) ✅

`00-contracts/wit/deps/kotodama-bsky/package.wit`。Authoritative source は WIT ファイル本体。以下は constraint annotation カバレッジ概要。

**Constraint annotation カバレッジ (upstream Lexicon JSON 100%):**

| Record | Field | Annotations |
|---|---|---|
| **post** | text | `@max-length 3000` `@max-graphemes 300` |
| | langs | `@max-items 3` |
| | labels | `@max-items 10` |
| | tags | `@max-items 8` `@max-length 640` `@max-graphemes 64` |
| **profile** | display-name | `@max-length 640` `@max-graphemes 64` |
| | description | `@max-length 2560` `@max-graphemes 256` |
| | pronouns | `@max-length 200` `@max-graphemes 20` |
| | website | `@format uri` |
| | avatar/banner | `@accept image/png,image/jpeg` `@max-size 1000000` |
| **images** | images | `@max-items 4` |
| **image** | image | `@accept image/*` `@max-size 1000000` |
| | alt | `@max-length 10000` `@max-graphemes 1000` |
| **video** | video | `@accept video/mp4` `@max-size 100000000` |
| | captions | `@max-items 20` |
| | alt | `@max-length 10000` `@max-graphemes 1000` |
| **caption** | lang | `@format language` |
| | file | `@accept text/vtt` `@max-size 20000` |
| **external-link** | uri | `@format uri` |
| | thumb | `@accept image/*` `@max-size 1000000` |
| **generator** | did | `@format did` |
| | display-name | `@max-length 240` `@max-graphemes 24` |
| | description | `@max-length 3000` `@max-graphemes 300` |
| | accepts-interactions | `@default false` |
| **list** | name | `@min-length 1` `@max-length 64` |
| | description | `@max-length 3000` `@max-graphemes 300` |
| | avatar | `@accept image/png,image/jpeg` `@max-size 1000000` |
| **starterpack** | name | `@min-length 1` `@max-length 500` `@max-graphemes 50` |
| | description | `@max-length 3000` `@max-graphemes 300` |
| | feeds | `@max-items 3` |
| **threadgate** | allow | `@max-items 5` |
| | hidden-replies | `@max-items 300` |
| **postgate** | detached-embedding-uris | `@max-items 50` |
| | embedding-rules | `@max-items 5` |
| **byte-slice** | byte-start/end | `@minimum 0` |
| **mention** | did | `@format did` |
| **link** | uri | `@format uri` |
| **tag** | tag | `@max-length 640` `@max-graphemes 64` |
| **notification-item** | is-read | `@default false` |
| **notification-reason** | (enum) | 13 values (like/repost/follow/mention/reply/quote/starterpack-joined/verified/unverified/like-via-repost/repost-via-repost/subscribed-post/contact-match) |

**対象外 (WIT record schema に含まれない):** view/query response の `knownValues` (labelValue, contentMode, severity, blurs, defaultSetting) — view 型は WIT 未定義 (Exceptions 参照)

### Phase 3: Typed SDK Functions

現在の opaque `string` API を typed API に拡張 (backward compat 維持)。

**w-record interface 拡張:**

```wit
/// com-atproto:repo/repo@1.0.0 — AT Protocol record CRUD + typed writes
interface com-atproto-repo {
    use kotodama:bsky/app-bsky-feed.{post, like, repost};
    use kotodama:bsky/app-bsky-actor.{profile};
    use kotodama:bsky/app-bsky-graph.{follow};

    /// @nsid com.atproto.repo.createRecord
    create-record: func(collection: string, record-json: string) -> result<string, string>;
    /// @nsid com.atproto.repo.putRecord
    put-record: func(collection: string, rkey: string, record-json: string) -> result<_, string>;
    /// @nsid com.atproto.repo.deleteRecord
    delete-record: func(collection: string, rkey: string) -> result<_, string>;

    /// @nsid app.bsky.feed.post
    post: func(post: post) -> result<string, string>;

    /// @nsid app.bsky.feed.like
    like: func(like: like) -> result<string, string>;

    /// @nsid app.bsky.feed.repost
    repost: func(repost: repost) -> result<string, string>;

    /// @nsid app.bsky.graph.follow
    follow: func(follow: follow) -> result<string, string>;

    /// @nsid app.bsky.actor.profile
    profile: func(profile: profile) -> result<string, string>;
}
```

**Guest SDK (Go) 型安全 API:**

```go
// Before (opaque JSON)
kotodama.ATPost(did, text, `{"embed":{"$type":"app.bsky.embed.images","images":[...]}}`)

// After (typed)
kotodama.ATPost(did, kotodama.Post{
    Text:  text,
    Embed: &kotodama.ImagesEmbed{
        Images: []kotodama.Image{
            {Image: blobRef, Alt: "description"},
        },
    },
    Facets: []kotodama.Facet{
        {Index: kotodama.ByteSlice{Start: 0, End: 5}, Features: []kotodama.FacetFeature{
            kotodama.MentionFeature{DID: targetDID},
        }},
    },
    Langs: []string{"ja", "en"},
})
```

### Phase 4: PDS Validation Middleware (Doc Comment Annotation 自動導出)

PDS XRPC facade 層で WIT doc comment annotation に基づく record body 検証を追加。検証ルールは手動定義ではなく `etzhayyim wit-gen` が WIT から自動生成する。

```
etzhayyim wit-gen --constraints
  → WIT doc comment (@max-length, @format, ...) をパース
  → validation-rules.generated.ts を出力

XRPC /xrpc/com.atproto.repo.createRecord
  → validateRecordBody(collection, record)  // generated rules
  → Pipeline.send() + mergeRecord()
```

WIT doc comment から自動導出される検証ルール例:
- `app.bsky.feed.post.text`: `@max-length 3000` + `@max-graphemes 300`
- `app.bsky.embed.images.images`: `@max-items 4`
- `app.bsky.actor.profile.displayName`: `@max-length 640` + `@max-graphemes 64`
- `app.bsky.graph.follow.subject`: `@format did`
- `app.bsky.feed.post.facets[].index`: cross-field (runtime hand-written — annotation 対象外)

## AT Protocol Lexicon Style Guide 準拠状況

[Lexicon Style Guide](https://atproto.com/ja/guides/lexicon-style-guide) との対応。

### 準拠項目

| Style Guide ルール | WIT 実装 | 状態 |
|---|---|---|
| **Schema/属性は lowerCamelCase** | XRPC method は camelCase。WIT field は kebab-case (WIT 仕様制約) → host-sdk が camelCase JSON に変換 | ✅ |
| **Record は単数名詞** | `post`, `like`, `follow`, `profile` | ✅ |
| **Query/Procedure は動詞+名詞** | `post`, `like`, `repost` (NSID method kebab) → XRPC `createRecord` | ✅ |
| **NSID 階層グルーピング** | `app.bsky.feed.*`, `com.etzhayyim.apps.{app}.*`, `com.etzhayyim.convo.*` | ✅ |
| **Record 参照は DID (handle 不可)** | `at-did` type alias、`subject: string` (DID) | ✅ |
| **大バイナリは blob 参照** | `blob-ref` record (FormData+multipart) | ✅ |
| **Pagination は `limit` + `cursor`** | XRPC 428 methods で cursor-based | ✅ |
| **Subscription は `cursor` + `seq`** | `subscribeRepos` SSE で `seq` + `cursor` | ✅ |
| **Hydrated Views** | `buildPostView` で record + metadata 一括 | ✅ |
| **Union は open (third-party 拡張可)** | WIT `variant` — closed だが W Protocol Extension で拡張可能 | ⚠️ |
| **Reusable definitions (`.defs`)** | WIT `use` import で cross-package 再利用 | ✅ |
| **Rich Text は facet** | `kotodama:bsky/richtext` に完全定義 (`byte-slice`, `facet-feature` variant, `facet`) | ✅ |
| **Sidecar Records** | path-based DID + separate collection で同一パターン | ✅ |
| **Modality Signals (declaration record)** | `kotodama.jsonld` `profile` + `performerType` + `contentMode` | ✅ |

### 意図的逸脱

| Style Guide ルール | WIT 実装 | 理由 |
|---|---|---|
| **String constants は `kebab-case`** | `snake_case` 標準 (`cohort_person`) | Cypher backtick 不要、Go identifier 互換、DID path escape 不要 |
| **Lexicon JSON schema 定義** | WIT が Single Source (手動 Lexicon JSON 禁止) | Shannon 冗長排除。`etzhayyim wit-gen` で WIT → NSID map 自動導出 |
| **closed enum 回避 → `knownValues`** | WIT `enum` (closed) | WASM Component Model 型安全優先。拡張は WIT version bump |

### WIT で表現できない Lexicon 制約 → Doc Comment Annotation で解決

WIT 型システムには Lexicon JSON の制約アノテーション相当がない。構造 (record/variant/enum) は 1:1 だが、制約は WIT grammar では表現不可能。

| Lexicon 制約 | WIT grammar | Doc comment annotation |
|---|---|---|
| `maxLength` (bytes) | ❌ なし | `/// @max-length 3000` |
| `maxGraphemes` | ❌ なし | `/// @max-graphemes 300` |
| `minLength` | ❌ なし | `/// @min-length 1` |
| `format` (at-uri, did, datetime, handle) | ⚠️ type alias のみ | `/// @format at-uri` |
| `maxItems` (e.g. images max 4) | ❌ `list<T>` に上限なし | `/// @max-items 4` |
| `default` (optional boolean → false) | ❌ None/Some のみ | `/// @default false` |
| Cross-field constraint | ❌ なし | 対象外 (runtime validation のみ) |

#### Decision: Doc Comment Annotation (WIT grammar 拡張は不採用)

**WIT grammar 拡張 vs doc comment annotation の比較:**

| 比較軸 | WIT grammar 拡張 | Doc comment annotation |
|---|---|---|
| **実装コスト** | wit-parser + wit-bindgen fork 保守 | `wit_gen.go` に数十行追加 |
| **upstream 追従** | fork 分岐で全 WIT toolchain version lock-in | 影響ゼロ (`///` は WIT spec 安定部分) |
| **既存実績** | なし | `@nsid` で稼働中 (`wit_gen.go` L113-122) |
| **compile-time 検証** | ✅ parser が reject | ❌ 不可 |
| **実効性** | Lexicon 制約は本質的に runtime (3000 bytes 超過は実行時 reject) | 同じ |
| **toolchain 互換** | fork 必須 | 影響なし |

**不採用理由**: `maxLength`/`maxGraphemes`/`format` は本質的に **runtime constraint** — コンパイル時に「この string は 3000 bytes 以下」を証明する型システムは WIT にも Lexicon にもない。Lexicon JSON 自体が「schema は宣言、enforcement は実装側」の設計。WIT grammar 拡張で得られるのは parse-time syntax check のみで、`etzhayyim wit-gen` の validation で同等に実現可能。fork 保守コスト対ゼロで doc comment annotation が圧倒的に優位。

WIT spec 公式アノテーションは `@unstable`, `@since`, `@deprecated` の 3 つのみ (Component Model spec)。Custom annotation の proposal は存在しない。

#### Constraint Annotation 仕様

`@nsid` と同じく `///` doc comment 内に記述。`etzhayyim wit-gen` がパースし 3 層に自動導出。

**記法:**

```wit
/// Post record (app.bsky.feed.post).
record post {
    /// @max-length 3000
    /// @max-graphemes 300
    text: string,
    /// @max-items 4
    facets: option<list<facet>>,
    reply: option<reply-ref>,
    /// @max-items 1
    embed: option<post-embed>,
    langs: option<list<string>>,
    labels: option<list<self-label>>,
    /// @max-items 8
    /// @max-length 640
    tags: option<list<string>>,
    /// @format datetime
    created-at: datetime,
}
```

**サポートするアノテーション:**

| Annotation | Lexicon 対応 | 値の型 | 例 |
|---|---|---|---|
| `@max-length` | `maxLength` | `u64` (bytes) | `/// @max-length 3000` |
| `@max-graphemes` | `maxGraphemes` | `u64` | `/// @max-graphemes 300` |
| `@min-length` | `minLength` | `u64` (bytes) | `/// @min-length 1` |
| `@max-items` | `maxLength` (array) | `u64` | `/// @max-items 4` |
| `@min-items` | `minLength` (array) | `u64` | `/// @min-items 1` |
| `@minimum` | `minimum` | number | `/// @minimum 0` |
| `@maximum` | `maximum` | number | `/// @maximum 100` |
| `@format` | `format` | string | `/// @format at-uri` / `did` / `handle` / `datetime` / `at-identifier` / `nsid` / `uri` / `language` / `cid` |
| `@default` | `default` | literal | `/// @default false` |
| `@known-values` | `knownValues` | CSV | `/// @known-values show,warn,hide` (open enum — WIT `enum` は closed、これは string field 用) |
| `@accept` | `accept` (blob) | MIME CSV | `/// @accept image/png,image/jpeg` |
| `@max-size` | `maxSize` (blob) | `u64` (bytes) | `/// @max-size 1000000` |
| `@field` | (proto field number) | `u32` | `/// @field 1` |
| `@reserved` | (proto reserved numbers) | `u32` CSV | `/// @reserved 3,5,8` |
| `@reserved-name` | (proto reserved names) | string CSV | `/// @reserved-name reply,langs` |
| `@zero-omit` | (proto3 zero value omission) | `true`/`false` | `/// @zero-omit true` |

**導出先 4 層:**

1. **Lexicon JSON 生成** (`etzhayyim wit-gen`) — `maxLength`, `maxGraphemes`, `format` 等を自動付与
2. **PDS validation middleware** (Phase 4) — 同じ annotation から検証ルールを導出。手動 rule 定義不要
3. **Guest SDK** — Go struct tag / TS JSDoc / Rust `#[validate]` に constraint metadata 付与 (将来)
4. **Schema evolution codec** (Phase 6) — `@field` number で wire-stable encoding、unknown field preservation、`@reserved` で番号保護

**Single Source of Truth**: WIT doc comment が制約の唯一の定義。Lexicon JSON・PDS validation・SDK は全て自動導出。手動で制約を別ファイルに書くことを禁止。

**結論**: WIT は Lexicon JSON の**構造層 (type shape)** を WIT grammar で同等に表現。**制約層 (validation rules)** は doc comment annotation で WIT ファイル内に共存させ、`etzhayyim wit-gen` で Lexicon JSON + PDS validation + SDK に自動導出する。

## Rationale

### なぜ Option A (WIT に型追加) か

| 比較軸 | Option A (WIT 型追加) | Option B (wit-gen 生成) | Option C (validation middleware) |
|---|---|---|---|
| **Compile-time safety** | ✅ WIT binding で型検査 | ❌ runtime JSON のみ | ❌ runtime のみ |
| **Guest SDK 体験** | ✅ 型安全 API | ❌ opaque string | ❌ opaque string |
| **Federation validation** | ✅ WIT → validation 自動導出 | ⚠️ 手動 Lexicon 参照 | ✅ middleware で検証 |
| **AT Protocol spec 追従** | ⚠️ WIT 更新コスト | ✅ Lexicon JSON 更新のみ | ⚠️ validation rule 更新 |
| **Shannon redundancy** | ✅ WIT = Single Source | ⚠️ WIT + Lexicon 二重管理 | ⚠️ WIT + middleware 二重管理 |
| **WIT 変更時の全 rebuild** | ⚠️ 既存ルール通り全 rebuild | ✅ 影響なし | ✅ 影響なし |

**AT Protocol spec 追従コストの緩和策:**
- AT Protocol の core 型 (post/like/follow/profile) は安定しており変更頻度が低い
- `etzhayyim wit-gen` が公式 Lexicon JSON → WIT record の逆変換も提供 (spec 変更時の自動更新)
- WIT record の optional field は Lexicon の optional property と 1:1 対応

### AT Protocol Lexicon spec との型対応

| Lexicon 型 | WIT 型 | 備考 |
|---|---|---|
| `string` | `string` | |
| `integer` | `s64` / `u64` | |
| `boolean` | `bool` | |
| `bytes` | `list<u8>` | |
| `cid-link` | `cid` (= `string`) | CID は文字列表現 |
| `blob` | `blob-ref` record | `$type` + `ref.$link` + `mimeType` + `size` |
| `at-uri` | `at-uri` (= `string`) | `at://{did}/{collection}/{rkey}` |
| `datetime` | `datetime` (= `string`) | RFC 3339 |
| `object` | `record` | named fields |
| `array` | `list<T>` | |
| `union` | `variant` | discriminated union |
| `ref` | `use` import | cross-package reference |
| `unknown` | `string` (JSON) | escape hatch |

## Package Structure

```
00-contracts/wit/deps/
├── kotodama-atproto/          # AT Protocol core types + constraint annotations
│   └── package.wit            # types (@format), repo, labels (@max-length)
├── kotodama-bsky/             # Bluesky social types + constraint annotations (100% coverage)
│   └── package.wit            # richtext, embed, feed, actor, graph, notification
├── kotodama-wproto/           # W Protocol operations (verb layer)
│   └── package.wit            # invoke, serve, repo (typed extension), query, did, follow
└── ...
```

## Migration Path

1. **Phase 1** ✅ done: `kotodama:atproto` package — core types + constraint annotations
2. **Phase 2** ✅ done: `kotodama:bsky` package — social types + constraint annotations (upstream Lexicon 100% カバレッジ)
3. **Phase 3** (in progress): com-atproto-repo typed extension — `post()`, `like()`, `repost()`, `follow()`, `profile()`
4. **Phase 4** ✅ done (annotation 追記): Doc comment annotation (`@max-length`, `@format`, `@accept`, `@max-size` 等) を全 record field に追記完了。`etzhayyim wit-gen --constraints` の実装は next
5. **Phase 5** (ongoing): `etzhayyim wit-gen` reverse — Lexicon JSON → WIT record + annotation 自動生成
6. **Phase 6** ✅ done (annotation + evolution interface): `@field` number を全 record field に付与 + `@reserved` + `kotodama:atproto/evolution` interface。`etzhayyim wit-gen --evolution` の codec 生成は next

### Phase 6: Schema Evolution — Field Numbers + Version Envelope

Proto のスキーマ進化耐性を WIT に導入する。WIT grammar は変えず doc comment annotation (`@field`, `@reserved`) で実現。

#### 6a. `@field` Annotation (Proto Field Number 相当)

全 record field に `@field N` を付与。N は record 内で一意の u32。wire format の stable key として機能し、field の追加・削除・並べ替えで ABI が壊れない。

```wit
record post {
    /// @field 1
    /// @max-length 3000
    /// @max-graphemes 300
    text: string,
    /// @field 2
    facets: option<list<facet>>,
    /// @field 3
    reply: option<reply-ref>,
    /// @field 4
    embed: option<post-embed>,
    /// @field 5
    /// @max-items 3
    langs: option<list<string>>,
    /// @field 6
    /// @max-items 10
    labels: option<list<self-label>>,
    /// @field 7
    /// @max-items 8
    /// @max-length 640
    /// @max-graphemes 64
    tags: option<list<string>>,
    /// @field 8
    /// @format datetime
    created-at: datetime,
}
```

**ルール (proto 準拠):**

| ルール | 説明 |
|---|---|
| **番号は 1 始まり** | 0 は無効 (proto 互換) |
| **record 内で一意** | 重複は `etzhayyim wit-gen` が reject |
| **一度割り当てた番号は変更不可** | wire compat 保証。field 削除時は `@reserved` + `@reserved-name` に移動 |
| **19000-19999 は予約** | proto 互換 (internal use) |
| **variant case にも付与** | discriminant の stable encoding |
| **削除時は番号と名前の両方を reserve** | `@reserved N` + `@reserved-name name` で番号と名前の再利用を防止 (JSON wire は name key のため名前衝突も breaking) |

#### 6b. `@reserved` Annotation (Proto Reserved 相当)

削除した field の番号を保護し、再利用を防止する。

```wit
/// @reserved 3,5
/// @reserved-name reply,langs
record updated-post {
    /// @field 1
    text: string,
    /// @field 2
    facets: option<list<facet>>,
    // field 3 was 'reply' — removed, number + name reserved
    /// @field 4
    embed: option<post-embed>,
    // field 5 was 'langs' — removed, number + name reserved
    /// @field 6
    labels: option<list<self-label>>,
    /// @field 7
    tags: option<list<string>>,
    /// @field 8
    created-at: datetime,
    /// @field 9
    thread-context: option<string>,
}
```

`etzhayyim wit-gen` が `@reserved` 番号および `@reserved-name` 名前への再割り当てを reject。

#### 6c. Version Envelope (`kotodama:atproto/evolution`)

Unknown field preservation + version negotiation のための runtime envelope。

```wit
interface evolution {
    /// Unknown field entry — field number + CBOR-encoded value.
    /// Enables round-trip of fields added by newer schema versions.
    record unknown-field {
        /// @field 1 — proto field number from newer schema
        field-num: u32,
        /// @field 2 — CBOR wire bytes (opaque, preserved for relay)
        wire-bytes: list<u8>,
    }

    /// Version envelope — wraps any typed record with schema evolution metadata.
    /// Similar to google.protobuf.Any (type_url + value) but with versioning + unknown field list.
    record versioned-envelope {
        /// @field 1 — fully qualified record type (e.g. "kotodama:bsky/feed.post")
        /// Analogous to google.protobuf.Any.type_url.
        record-type: string,
        /// @field 2 — schema version (monotonic, record-type-scoped)
        version: u32,
        /// @field 3 — typed record body (JSON for now, CBOR when Phase 7)
        body-json: string,
        /// @field 4 — unknown fields from newer versions (preserved for relay)
        unknown-fields: list<unknown-field>,
    }

    /// Schema compatibility check result.
    enum compat-result {
        /// Fully compatible — all fields known.
        full,
        /// Forward compatible — unknown fields present but preserved.
        forward,
        /// Breaking — required field missing.
        breaking,
    }

    /// Check compatibility between local schema version and received envelope.
    check-compat: func(envelope: versioned-envelope) -> compat-result;
}
```

**`@reserved-name` annotation**: 削除した field の名前も保護する (JSON wire で name key を使うため名前衝突は breaking)。

```wit
/// @reserved 3,5
/// @reserved-name reply,langs
record updated-post { ... }
```

**`@zero-omit` annotation**: Proto3 の zero value omission に相当。CBOR/JSON encoding で zero value (0, "", false, empty list) を省略するか制御。

```wit
record like {
    /// @field 1
    subject: strong-ref,
    /// @field 2
    /// @zero-omit true
    created-at: datetime,
}
```

#### 6d. Wire Format (CBOR field-number encoding)

Wire 上では `@field` 番号を CBOR map key として使用。JSON wire (AT Protocol 標準) では field name を key とし、`@field` は codec の internal mapping。

| Wire | Key | Unknown field handling |
|---|---|---|
| **CBOR (W Protocol internal)** | `@field` number (u32) | unknown key → `unknown-fields` に保持 |
| **JSON (XRPC / AT Protocol)** | field name (string) | unknown key → `unknown-fields` に保持 (name→number は schema map で逆引き) |

**Forward compat**: 新 schema で追加された field は旧 node で `unknown-fields` に入り、relay 時に復元。
**Backward compat**: 新 node が旧 schema record を受信 → 新 field は `option<T>` (None) + `unknown-fields` 空。

#### 6e. `etzhayyim wit-gen` 拡張

```
etzhayyim wit-gen --evolution
  → @field annotation をパース
  → field-number-map.generated.json を出力 (record → {field_name: field_num})
  → @reserved 検証 (番号衝突 reject)
  → evolution codec (CBOR ↔ typed record + unknown-fields) を TS/Go/Rust に生成
```

#### Proto との達成対比

**2 層に分離して評価する。** Proto は独自 wire format を持つ。WIT は ABI specification。本質的に異なる層を扱うため、互換性の意味が異なる。

##### Wire Level (JSON/CBOR over XRPC — federation/relay 互換)

| Proto 機能 | WIT + @field 実装 | 状態 |
|---|---|---|
| **Field number (wire stability)** | `@field N` → CBOR map key (u32) / JSON name key + schema map | ✅ |
| **Reserved fields** | `@reserved N,M` doc comment | ✅ |
| **Reserved names** | `@reserved-name` doc comment | ✅ |
| **Unknown field preservation** | `versioned-envelope.unknown-fields` | ✅ |
| **Optional field 追加 (backward compat)** | `option<T>` + 新 `@field` 番号 | ✅ |
| **Field 削除 (forward compat)** | `@reserved` + `@reserved-name` + unknown-fields round-trip | ✅ |
| **Version negotiation** | `versioned-envelope.version` + `check-compat()` | ✅ |
| **Variant case 追加** | `@field` on variant case + unknown discriminant → `unknown-fields` | ✅ |
| **Oneof (union) evolution** | WIT `variant` + `@field` per case | ✅ |
| **Nested message evolution** | Recursive `versioned-envelope` | ✅ |
| **Type discriminant in envelope** | `versioned-envelope.record-type` | ✅ |
| **Wire type self-description** | CBOR self-describing (proto wire type tag より冗長だが正確) | ✅ |
| **Zero value omission** | `@zero-omit` annotation → CBOR/JSON 省略ルール | ✅ |
| **Map field** | `list<map-entry<K,V>>` + `@field` (proto `map<K,V>` = repeated entry message と同型) | ⚠️ WIT に native map なし、`list<record>` で代替 |

##### WASM ABI Level (component boundary — rebuild 要否)

| Proto 機能 | WIT 状態 | 評価 |
|---|---|---|
| **Optional field 追加** | ABI break → 全 component rebuild | ⚠️ Proto は wire 互換で rebuild 不要。WIT は structural ABI のため rebuild 必須 |
| **Required → Optional 変更** | ABI break → 全 component rebuild | ❌ Proto3 は全 field 暗黙 optional。WIT の non-option → option は structural 変更 |
| **Type widening (u32 → u64)** | ABI break → 全 component rebuild | ❌ Proto は wire type 互換で自動変換。WIT は型変更 = ABI break |
| **Field 並べ替え** | ABI break → 全 component rebuild | ⚠️ `@field` は wire 安定だが WIT ABI は field 順序依存 |

##### 構造的限界 (WIT の本質的制約)

Proto は独自 wire format (varint + field tag) を持ち、**decoder が型定義なしで未知 field を skip できる**。WIT は WASM Component Model の **ABI specification** であり、field の型・順序・数が canonical ABI を決定する。

**結論**: `@field` + `versioned-envelope` で **wire level** は proto 相当の forward/backward compat を達成。**WASM ABI level** は WIT の structural 性質により rebuild が必要。これは proto と WIT の設計目的の差であり、解消不可能。実運用では wire compat (federation/relay) が critical path であり、WASM rebuild は CI で自動化できるため、実害は限定的。

**Backward compat**: 既存の `write(collection, record-json)` は維持。typed API は追加 (additive)。

## Exceptions

- `app.bsky.unspecced.*` (experimental) は WIT 型定義しない (JSON 透過維持)
- `tools.ozone.*` (moderation tooling) は WIT 型定義しない (admin 用途)
- `com.atproto.temp.*` は WIT 型定義しない (一時的)
- Lexicon の `unknown` 型フィールドは `string` (JSON) で透過

## References

- [AT Protocol Lexicon Style Guide](https://atproto.com/ja/guides/lexicon-style-guide) — 命名規約・設計パターン準拠状況は上記セクション参照
- [AT Protocol Lexicon Specification](https://atproto.com/specs/lexicon)
- [Bluesky Lexicon Definitions](https://github.com/bluesky-social/atproto/tree/main/lexicons)
- `00-contracts/wit/deps/kotodama-atproto/package.wit` — AT Protocol core types + constraints
- `00-contracts/wit/deps/kotodama-bsky/package.wit` — Bluesky social types + constraints (100% coverage)
- `00-contracts/wit/deps/kotodama-wproto/package.wit` — W Protocol operations (verb layer)
- `10-protocol/wproto/core/src/record.rs` — RecordMapper (kind ↔ NSID)
- `90-docs/260324-w-protocol-at-superset-architecture.md` — W Protocol = AT superset
- `90-docs/260324-did-path-lexicon-correspondence.md` — DID ↔ Lexicon NSID
