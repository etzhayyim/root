# etzhayyim-project-syosetsu

Web 小説リーダープラットフォーム (`syosetsu.etzhayyim.com`)。
narou.etzhayyim.com で生成されたテキストコンテンツを縦書きリーダー形式で公開する。

## App Components

| Component | nanoid | 役割 |
|---|---|---|
| `etzhayyim-wasm-syosetsu-sy3w9p4m` | `sy3w9p4m` | Main control plane + リーダー UI |

## DID Structure

| DID | 用途 |
|---|---|
| `did:web:syosetsu.etzhayyim.com` (primary) | Platform agent |
| `did:web:syosetsu.etzhayyim.com:novel:{novel_id}` (path) | 小説公式アカウント |

## Lexicon Collections

| NSID | WRecord kind | SQL Label |
|---|---|---|
| `com.etzhayyim.apps.syosetsu.series` | `series` | `:Series` |
| `com.etzhayyim.apps.syosetsu.episode` | `episode` | `:Episode` |
| `com.etzhayyim.apps.syosetsu.bookmark` | `bookmark` | `:Bookmark` |
| `com.etzhayyim.apps.syosetsu.review` | `review` | `:Review` |
| `com.etzhayyim.apps.syosetsu.tag` | `tag` | `:Tag` |

## 設計

- **ソース**: narou.etzhayyim.com が `PublishChapter` 実行時に `Invoke("did:web:syosetsu.etzhayyim.com", "publish-chapter", params)` を呼ぶ
- **コンテンツモデル**: Series (作品) > Episode (話)
- **テキスト**: narou の `content_blob_key` (B2 Markdown) をそのまま利用
- **永続化**: W Protocol Event Stream (Write=WRecord, Read=Q()+G())

## SQL Graph Schema

```
(:Series)-[:HAS_EPISODE]->(:Episode)
(:Series)-[:TAGGED]->(:Tag)
(:DID)-[:BOOKMARKED]->(:Bookmark)-[:AT]->(:Episode)
(:DID)-[:REVIEWED]->(:Review)-[:OF]->(:Series)
```

## Domain WIT

- `etzhayyim:syosetsu/reader@1.0.0` — publish-chapter, bookmark, review
- `etzhayyim:syosetsu/catalog@1.0.0` — get/list/search series+episodes

## API Endpoints

- App: `https://sy3w9p4m.etzhayyim.com`
- XRPC: `https://sy3w9p4m.etzhayyim.com/xrpc`

## Smoke Test

```bash
curl https://sy3w9p4m.etzhayyim.com/health
curl -X POST https://sy3w9p4m.etzhayyim.com/xrpc/etzhayyim.syosetsu.v1.SyosetsuQueryService/ListNovels \
  -H "Content-Type: application/json" -d '{"org_id":"anon","limit":10,"offset":0}'
```
