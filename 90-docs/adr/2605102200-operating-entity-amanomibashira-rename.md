---
id: adr-2605102200-operating-entity-etzhayyim-rename
title: Operating entity canonical name = `etzhayyim` / 天御柱
status: active
doc_type: adr
topic: operating-entity
authoritative: true
last_verified: 2026-05-10
authoritative_for:
  - operating-entity-canonical-name
related:
  - 90-docs/adr/0019-atproto-native-identifier-topology.md
supersedes: []
superseded_by: []
---

# Context

`deps.toml [platform.operating_entity]` の SSoT で運営法人を `etz hayim`
(Hebrew "tree of life" のローマ字綴り) として固定していた。Footer / legal
doc / `vertex_actor.operator` / JSON-LD publisher / contact email
(`office@etzhayim.etzhayyim.com`) / CF Worker route (`etzhayim.etzhayyim.com/*`) など
repo 内 251 ファイル + DNS / Cloudflare DNS / M365 メール経路まで
波及していた。

CEO 河崎の判断 (2026-05-10) で、運営法人の canonical name を **日本語名
ローマ字** `etzhayyim` (漢字: 天御柱) に切替える。意味論的には
"天と地を繋ぐ柱" = "Tree of Life" と等価であり、日本語コンテキストで
読まれる public surface (yoro Footer / lawfirm 契約 PDF / legal doc /
Footer credit) を一貫させるための rebrand。

Hebrew 表記 (`עץ חיים`) と romanized form (`etz hayim`) は legacy alias
として保持し、過去 ledger / commit / 受信 mail 等の参照は壊さない。

# Decision

1. **canonical name**: `etzhayyim` (lowercase ASCII, 1 word, no
   space). `name_ja = "天御柱"`。Footer / publisher / `vertex_actor.operator`
   / `OPERATOR` constant の表示文字列は全て `etzhayyim` を使う。
2. **legacy alias 保持**: `[platform.operating_entity].aliases =
   ["etz hayim", "etz_hayim", "etzhayim", "エツ・ハイム"]`、
   `name_hebrew = "עץ חיים"`、`name_hebrew_romanized = "etz hayim"`。
   AT Profile / vertex / 既存契約 PDF からの逆引きは alias 経由で許容。
3. **DNS / 公開 surface 切替** (ADR 適用後の operator action):
   - `etzhayim.etzhayyim.com` → `etzhayyim.etzhayyim.com` の CF DNS レコード
     新設 + organism-status Worker の route pattern と内部 URL を更新
     (`50-infra/cloudflare/workers/organism-status/wrangler.jsonc:13`,
     `src/index.ts:43,330,1153`)。
   - 旧 `etzhayim.etzhayyim.com/*` route は 12 ヶ月並走 (301 redirect) で
     legacy bookmark / 過去メール本文の link を回復可能に保つ。
   - `office@etzhayim.etzhayyim.com` → `office@etzhayyim.etzhayyim.com` の
     M365 / CF Email Routing 切替。旧 address は forward で 12 ヶ月並走。
4. **graph backfill**: 既存 backfill migration
   `30-graph/graph-schema/migrations/20260427150000_backfill_operator_etz_hayim.ts`
   を `..._etzhayyim.ts` にファイルリネーム + `vertex_actor.operator
   = 'etzhayyim'` を再走行 (旧 'etz hayim' 値が残っていれば update)。
   alembic revision ID (`r_20260427150000`) は不変なので
   `alembic_version` テーブルとの整合は崩れない。
5. **AT Profile records**: `at_record_audit = "no-stale-operator-strings
   (2026-04-27)"` 通り公開 record 内に `etz hayim` 文字列は無い。
   再 publish 不要。新規 record は `vertex_actor.operator = 'etzhayyim'`
   から自動投影。
6. **Hebrew 識別の維持理由**: 創設経緯が religious voluntary association
   としての `עץ חיים` (Tree of Life) であり、on-chain 憲章には Hebrew
   表記が刻まれている。ローマ字綴り変更は表示層 rebrand のみで、
   on-chain identity (Hebrew + member roster) は不変。

# Consequences

**Positive**
- Footer / 契約 PDF / lawfirm 顧客向け doc の表示が日本語コンテキスト
  と整合し、海外 Hebrew 綴りの読みづらさが解消。
- legal entity boundary (`etzhayyim` = principal / etzhayyim Japan =
  vendor) の説明が日本語顧客に通じやすくなる。
- on-chain Hebrew identity と display name が分離されるため、表示層の
  将来 rebrand は ADR 1 本で完結する (on-chain change は別 ADR 必須)。

**Negative / リスク**
- DNS 切替期間中は `etzhayim.etzhayyim.com` の public link を含む過去メール /
  ブックマークが redirect 経由になる。
- 過去 ADR / commit message / DECISION-LOG iter22-130 内の `etz hayim`
  参照は alias として読み替え必要 (検索性は alias 一覧でカバー)。
- CXO-LEDGER 表記揺れ: iter130 までの ledger 行は repository sed で
  既に `etzhayyim` に書き換えたが、原本テキストは過去時点で
  `etz hayim` だった旨を本 ADR で明示する。

**Pending operator actions** (deps.toml `[[migrations]]
operating-entity-etzhayyim-rename-2026-05-10` で追跡):
1. CF DNS `etzhayyim.etzhayyim.com` 作成 + organism-status Worker route
   bind
2. CF Email Routing `office@etzhayyim.etzhayyim.com` 設定 + 旧 address
   forward
3. `vertex_actor.operator` rebackfill (旧値があれば; 4,821 row scan)
4. yoro / hc / lawfirm Footer の SSR キャッシュ purge
5. lawfirm 契約 PDF テンプレート (handlebars) 内 publisher 文字列の
   rebuild

# Alternatives Considered

- **A. 漢字 `天御柱` を canonical name にする**: yoro 契約 PDF 等
  ASCII 必須箇所で再エスケープが要り、JSON-LD `publisher` の URI
  fragment 化が困難。display layer は `name_ja` で十分。**却下**。
- **B. 両併記 (`etzhayyim / 天御柱`)**: Footer 1 行が長くなり、
  契約 PDF の差出人欄崩れ。display は `name` 優先、`name_ja` は
  ja locale のみで併記する方針で十分。**却下**。
- **C. rename せず `etz hayim` 維持**: 海外 Hebrew 綴りが日本国内
  顧客 (lawfirm pilot India tier-2 + JP 顧客) に読みづらい問題が継続。
  **却下**。

# References

- `deps.toml [platform.operating_entity]` (SSoT、本 ADR 同期)
- `deps.toml [[migrations]] operating-entity-etzhayyim-rename-2026-05-10`
- `90-docs/adr/0019-atproto-native-identifier-topology.md` (path-based
  DID; on-chain identity vs display layer separation)
- `_working/etzhayyim-revenue/DECISION-LOG.md iter131`
- `_working/keiei/CXO-LEDGER.md seq 10` (Class A — operating entity
  rename, executed per CEO 河崎 directive)
