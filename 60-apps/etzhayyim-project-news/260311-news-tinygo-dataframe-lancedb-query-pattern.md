# news.etzhayyim.com: TinyGo cypher graph + cypher graph Query Pattern

## Scope

`news.etzhayyim.com` の article list/get、quality evaluation、translation、semantic lookup を
TinyGo component から `cypher graph/cypher graph` に問い合わせるための標準設計。

対象 component:

- `wasm/news-jobs-component`
- `wasm/news-quality-component`
- `wasm/news-translator-component`
- `wasm/news-ui-hytt1wm3`

## Current Problems

現状は row-store 互換の SQL table mental model が残っている。

- `wasm/news-jobs-component/db_articles.go`: `news_articles` に raw SQL を直接投げている
- `wasm/news-quality-component/db_sqlc.go`: `sqlc` + MySQL wire を open している
- `wasm/news-translator-component/db_sqlc.go`: 同上
- `wasm/news-ui-hytt1wm3/db_articles.go`: UI 側まで raw SQL に依存している
- `schema.hcl`, `atlas.hcl`, `internal/sqlc` が component ごとに散っていて、Arrow schema が source of truth になっていない

この形の問題は 3 つある。

1. TinyGo handler が table 設計より SQL 文字列に引っ張られる
2. quality / translation / list page の read path が projection 分離されていない
3. 列指向 storage なのに `SELECT ... FROM news_articles FINAL ...` という行思考が前面に出る

## Design Decision

### Source of Truth

- source of truth は `Arrow schema / Arrow Table`
- 永続化は `cypher graph/cypher graph`
- TinyGo runtime access は `performer/nata.Client`
- 更新モデルは `append event` + `merge_insert current` + `projection rebuild/incremental update`
- 既存移行コストを抑えるため、`article_id` は現行の `nanoid` をそのまま使う。翻訳記事は `{source_nanoid}-{lang}` を article key の基本形にする

cypher graph の用語は公式の `API reference`, `merge_insert`, `scalar indexes` を基準にする。

- https://docs.cypher graph.com/api-reference/
- https://cypher graph.github.io/cypher graph/guides/tables/merge_insert/
- https://cypher graph.github.io/cypher graph/guides/tables/scalar_indexes/

### TinyGo cypher graph Definition

TinyGo で使う cypher graph は「cypher graph の query 結果を列指向 slice に詰めた薄い view」とする。
DuckDB や pandas のような任意集計 engine を WASM に持ち込まない。

責務はここまでに限定する。

- query 結果の列指向 materialize
- typed access (`[]string`, `[]int64`, `[]float64`, `[]bool`)
- page 内だけの sort / group-count / top-k / light window
- proto response への整形

やらないこと:

- full-table scan
- ad-hoc join
- cross-table aggregation
- quality report のような重い集計を毎回 live scan

### Key Arrow Types

- `article_id`, `translation_of`, `language`, `category`, `source`, `image_blob_key`: `Utf8`
- `published_at`, `created_at`, `updated_at`: `Timestamp`
- `published_at_unix`, `priority`: `Int64`
- `quality_score`: `Int64`
- `needs_quality`: `Bool`
- `embedding`: `list<float32>`

## Target Table Model

### 1. `news_article_events`

append-only event log。`_doc_id = event_id`

主列:

- `_doc_id`
- `org_id`, `user_id`, `actor_id`
- `event_id`
- `article_id`
- `event_type`
- `source_id`
- `source_kind`
- `language`
- `category`
- `status`
- `quality_state`
- `quality_score`
- `translation_of`
- `published_at`
- `created_at`
- `payload_json`

用途:

- ingestion history
- publish/unpublish history
- quality score update history
- translation save history

### 2. `news_articles_current`

article の canonical current state。`_doc_id = article_id`

主列:

- `_doc_id`
- `org_id`, `user_id`, `actor_id`
- `article_id`
- `source_article_id`
- `translation_of`
- `language`
- `canonical_lang`
- `scope_prefix`
- `title`
- `summary`
- `content`
- `category`
- `title_slug`
- `published_at`
- `published_day`
- `published_at_unix`
- `url`
- `identifier`
- `image_blob_key`
- `source`
- `writer_persona`
- `quality_score`
- `quality_grade`
- `quality_state`
- `status`
- `updated_at`

方針:

- 翻訳記事も current row を別に持つ
- 画像 bytes は row に置かず blob に逃がし、row は `image_blob_key` だけ持つ
- UI と API の正本参照はこの table

### 3. `news_article_listing_current`

list page / homepage / sitemap 用 projection。`_doc_id = article_id`

主列:

- `_doc_id`
- `org_id`
- `article_id`
- `language`
- `scope_prefix`
- `category`
- `title`
- `summary`
- `title_slug`
- `image_blob_key`
- `source`
- `published_at`
- `published_at_unix`
- `status`
- `quality_score`

方針:

- heavy field (`content`) を持たない
- `ListArticles` はこの table だけを読む
- `language`, `scope_prefix`, `status`, `published_at_unix` に寄せた scalar index を前提にする

### 4. `news_quality_queue`

quality evaluation 用 projection。`_doc_id = article_id`

主列:

- `_doc_id`
- `org_id`
- `article_id`
- `language`
- `category`
- `title`
- `summary`
- `content_excerpt`
- `quality_score`
- `quality_grade`
- `quality_state`
- `needs_quality`
- `published_at_unix`
- `updated_at`

方針:

- `EvaluateBatch` は `needs_quality = 1` のみを page する
- LLM に全文が不要なら `content_excerpt` だけを持たせる
- `quality_state` は `pending`, `scored`, `needs_review` 程度に絞る

### 5. `news_quality_rollup`

quality report 用 projection。`_doc_id = language:category:published_day`

主列:

- `_doc_id`
- `org_id`
- `language`
- `category`
- `published_day`
- `total_count`
- `evaluated_count`
- `high_count`
- `low_count`
- `pending_count`
- `updated_at`

方針:

- `GetQualityReport` は live count せずこの table を読む

### 6. `news_translation_queue`

translation backlog projection。`_doc_id = article_id:target_lang`

主列:

- `_doc_id`
- `org_id`
- `article_id`
- `source_lang`
- `target_lang`
- `title`
- `summary`
- `content_excerpt`
- `translation_state`
- `priority`
- `published_at_unix`
- `updated_at`

### 7. `news_article_embeddings`

semantic assist 専用 vector table。`_doc_id = chunk_id`

主列:

- `_doc_id`
- `org_id`
- `article_id`
- `language`
- `chunk_index`
- `chunk_text`
- `published_at_unix`
- `embedding`

方針:

- `embedding` は `list<float32>`
- 類似記事候補の取得専用
- search 結果だけで article を返さず、必ず `news_articles_current` を引き直す

## TinyGo Query Layer

### Package Boundary

`news.etzhayyim.com` では `performer/nata.Client` の上に薄い `newsframe` layer を置く。
最初は project local (`60-apps/etzhayyim-project-news/wasm/internal/newsframe`) でよい。
複数 project に広がった時点で shared package に上げる。

```go
type QuerySpec struct {
	Table   string
	Filter  string
	OrderBy string
	Limit   int
	Offset  int

	StringCols []string
	IntCols    []string
	FloatCols  []string
	BoolCols   []string
}

type Frame struct {
	Rows    int
	Strings map[string][]string
	Ints    map[string][]int64
	Floats  map[string][]float64
	Bools   map[string][]bool
}

func LoadFrame(db *nata.Client, spec QuerySpec) (*Frame, error)
func (f *Frame) Slice(offset, limit int) *Frame
func (f *Frame) SortByInt(col string, desc bool)
func (f *Frame) GroupCount(col string) map[string]int
```

### Query Pipeline

1. cypher graph 側で scalar filter, order, paging を確定する
2. TinyGo 側は返ってきた page だけを `Frame` に詰める
3. handler は `Frame` から proto/connect response を組み立てる

この順序を崩さない。先に全部取得してから TinyGo で filter する設計は不可。

### Why Frame

`[]map[string]string` のままだと:

- field typo が runtime まで出ない
- 同一列アクセスで map lookup が繰り返される
- list page / quality batch のような列中心処理に向かない

`Frame` 化すると:

- `published_at_unix`, `quality_score` を数値列で扱える
- `title`, `summary`, `language` を列単位で一気に処理できる
- page 内 sort, group-count, top-k が安くなる

## Component Query Patterns

### `news-jobs-component`

#### `ListArticles`

- table: `news_article_listing_current`
- filter:
  - `org_id = ?`
  - `language = ?`
  - `scope_prefix = ?` optional
  - `status = 'published'`
- order: `published_at_unix DESC`
- page: mandatory `offset + limit`
- frame columns:
  - string: `article_id`, `title`, `summary`, `category`, `language`, `title_slug`, `image_blob_key`, `source`
  - int: `published_at_unix`, `quality_score`

#### `GetArticle`

- table: `news_articles_current`
- filter: `_doc_id = article_id AND org_id = ?`
- limit: 1
- no SQL join

### `news-quality-component`

#### `EvaluateBatch`

- table: `news_quality_queue`
- filter:
  - `org_id = ?`
  - `language = ?`
  - `needs_quality = 1`
- order: `published_at_unix DESC`
- limit: max 10

処理:

1. queue projection を読む
2. page を `Frame` 化
3. LLM evaluate
4. `news_article_events` に `quality-scored` event append
5. `news_articles_current`, `news_quality_queue`, `news_quality_rollup` を更新

#### `GetQualityReport`

- table: `news_quality_rollup`
- filter: `org_id = ? AND language = ?`
- live count query はしない

### `news-translator-component`

#### `TranslateArticle`

- source read: `news_articles_current`
- existence check:
  - `news_articles_current` where `translation_of = source_article_id AND language = target_lang`
  - あるいは translated article の `_doc_id`
- save:
  - `news_article_events` append (`translation-created`)
  - translated `news_articles_current` merge-insert
  - `news_article_listing_current` merge-insert
  - `news_translation_queue` を completed に更新

翻訳保存先を別 SQL table に分けない。

### `news-ui-hytt1wm3`

- UI component 自身は raw SQL を持たない
- article list / get は Connect query service 経由に寄せる
- UI fallback 用の static content は別として、runtime DB access は `news-jobs-component` か query 専用 component に集約する

## Index Strategy

key 参照が多い列は scalar index 前提で設計する。

必須:

- `news_articles_current.article_id`
- `news_articles_current.translation_of`
- `news_articles_current.language`
- `news_article_listing_current.language`
- `news_article_listing_current.scope_prefix`
- `news_article_listing_current.status`
- `news_quality_queue.language`
- `news_quality_queue.needs_quality`
- `news_translation_queue.target_lang`

## Event → Projection Rules

- `article-ingested`
  - append: `news_article_events`
  - merge-insert: `news_articles_current`
  - merge-insert: `news_article_listing_current`
  - merge-insert: `news_quality_queue`
  - merge-insert: `news_translation_queue` (target lang ごと)

- `quality-scored`
  - append: `news_article_events`
  - merge-insert: `news_articles_current`
  - merge-insert: `news_quality_queue`
  - merge-insert/update: `news_quality_rollup`

- `translation-created`
  - append: `news_article_events`
  - merge-insert: translated `news_articles_current`
  - merge-insert: translated `news_article_listing_current`
  - merge-insert: `news_translation_queue` state update

## What To Remove

新設計では以下を増やさない。

- `schema.hcl`
- `atlas.hcl`
- `sqlc.yaml`
- `internal/sqlc`
- MySQL store open helper
- raw `SELECT ... FROM news_articles FINAL ...`

移行完了後に削除対象となる代表箇所:

- `wasm/news-jobs-component/db_articles.go`
- `wasm/news-jobs-component/db_sqlc.go`
- `wasm/news-quality-component/db_articles.go`
- `wasm/news-quality-component/db_sqlc.go`
- `wasm/news-translator-component/db_articles.go`
- `wasm/news-translator-component/db_sqlc.go`
- `wasm/news-ui-hytt1wm3/db_articles.go`

## Migration Order

1. `news-jobs-component` の `ListArticles` / `GetArticle` を `news_article_listing_current` / `news_articles_current` 読みへ置換
2. `news-quality-component` の batch/report を `news_quality_queue` / `news_quality_rollup` に置換
3. `news-translator-component` の existence check / save を event + current/projection 更新に置換
4. `news-ui-hytt1wm3` の raw SQL を除去し、query service 呼び出しへ寄せる
5. 旧 `schema.hcl` / `atlas.hcl` / `sqlc` を削除

## Short Conclusion

`news.etzhayyim.com` での TinyGo + cypher graph 設計は、

- Arrow table を source of truth にする
- current/projection を明示的に分ける
- TinyGo の cypher graph を `nata.Client` の上の薄い列指向 layer に限定する
- SQL row-table mental model を component から消す

この 4 点で統一する。
