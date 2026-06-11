> **DEPRECATED**: Actor migrated to `20-actors/media-gamers/actor-manifest.jsonld` (T1 MCP-Compose). This project wasm/*/src/app.ts is retained as T3 fallback only.

# etzhayyim-project-media-gamers — Project Runbook

## Project Overview

`media-gamers.etzhayyim.com` — ゲーム情報 intelligence メディア。1 Worker + N path-based DID。

**Component**: `wasm/media-gamers-7m8oocsn/`
**nanoid**: `a7m8oocs`
**Runtime**: Single Worker (account-level)

## Multi-DID Architecture (app ≠ profile)

**1 app = 1 primary DID (controller) + N game title DIDs + N publisher DIDs + N developer DIDs。**

| DID | 用途 |
|---|---|
| `did:web:media-gamers.etzhayyim.com` (primary) | Platform agent (controller) |
| `did:web:media-gamers.etzhayyim.com:{game-slug}` | ゲームタイトル (例: `elden-ring`, `zelda-totk`) |
| `did:web:media-gamers.etzhayyim.com:publisher:{slug}` | パブリッシャー (例: `publisher:nintendo`) |
| `did:web:media-gamers.etzhayyim.com:developer:{slug}` | デベロッパー (例: `developer:fromsoft`) |
| `did:web:media-gamers.etzhayyim.com:platform:{slug}` | プラットフォーム |
| `did:web:media-gamers.etzhayyim.com:franchise:{slug}` | フランチャイズ |
| `did:web:media-gamers.etzhayyim.com:source:{id}` | データソース (Steam, RAWG, IGDB, OpenCritic, Giant Bomb) |

```typescript
// ゲーム DID 作成 (TS Native)
const did = await ensureSubDid(sdk, "elden-ring", "Elden Ring");
// ゲーム DID として攻略ガイドを social post
await postAs(sdk, did, "New boss-guide: Malenia Boss Guide (Elden Ring)");
```

## Multilingual Architecture — Pattern C (CRITICAL)

**Primary + Translation Record。Node は primary lang (en) のみ。翻訳は別 AT Record。**

### Design

```
// Node: primary lang only (en default)
(:GameTitle {slug: "elden-ring", name: "Elden Ring", synopsis: "...", lang: "en"})

// Translation: separate AT Record per lang
media_gamers.translation {
  source_slug: "elden-ring", source_kind: "game_title",
  lang: "ja", name: "エルデンリング", synopsis: "..."
}
```

### Rules

| Rule | Detail |
|---|---|
| **Default lang = en** | 全 record の `lang` field は未指定時 `"en"` |
| **Primary on node** | `name`, `title`, `synopsis`, `body`, `description` は primary lang (en) |
| **Translation = separate record** | `media_gamers.translation` collection。`source_slug` + `source_kind` + `lang` で参照 |
| **Social post langs** | `ATPostOpts.Langs: []string{"en"}` — AT Protocol `langs` field 準拠 |
| **Translation post** | ComAtprotoSyncSubscribeRepos で translation record 受信 → 翻訳言語で自動 social post |
| **Read overlay** | `?lang=ja` → primary record + translation overlay で返却 |
| **Search fallback** | primary `name` LIKE → 0件なら translation `name` LIKE |
| **URL** | `/{lang}/game/{slug}` (例: `/en/game/elden-ring`, `/ja/game/elden-ring`) |
| **SEO** | `<link rel="alternate" hreflang="en">` + `hreflang="ja"` + `hreflang="x-default"` |
| **i18n.etzhayyim.com 連携** | Follow → ComAtprotoSyncSubscribeRepos で `com.etzhayyim.i18n.translation_completed` 受信 → translation record 自動作成 |

### Translation API

| Command | Input | Output |
|---|---|---|
| `add_translation` | `{source_slug, source_kind, lang, name, synopsis, ...}` | `{rkey, lang}` |
| `get_translated` | `{slug, source_kind, lang}` | primary + translation overlay |
| `list_translations` | `{source_slug, source_kind}` | `{available_langs: ["en","ja",...], translations: [...]}` |

### Pattern C vs Alternatives

| | A: フラット | B: Node分離 | **C: Primary + Translation Record** |
|---|---|---|---|
| Node size | 40+ props | 最小 | **適正** |
| Read | O(1) | O(N) JOIN | **O(1) + O(1) overlay** |
| 新言語追加 | schema変更 | node追加 | **Record追加のみ** |
| AT Protocol 整合 | ❌ | ❌ | **✅ (langs + 別 Record)** |

## W Protocol Lexicon (CRITICAL)

**全 AT Record は `com.etzhayyim.apps.media_gamers.*` namespace。** WIT = `etzhayyim:media-gamers@1.0.0` (`wit/media-gamers/package.wit`)。

| Kind | AT Collection NSID | 説明 |
|---|---|---|
| `media_gamers.game_title` | `com.etzhayyim.apps.media_gamers.game_title` | ゲーム作品 (primary lang) |
| `media_gamers.game_profile` | `com.etzhayyim.apps.media_gamers.game_profile` | 作品 DID profile |
| `media_gamers.developer_studio` | `com.etzhayyim.apps.media_gamers.developer_studio` | 開発会社 |
| `media_gamers.publisher_company` | `com.etzhayyim.apps.media_gamers.publisher_company` | パブリッシャー |
| `media_gamers.game_character` | `com.etzhayyim.apps.media_gamers.game_character` | キャラクター |
| `media_gamers.game_platform` | `com.etzhayyim.apps.media_gamers.game_platform` | プラットフォーム |
| `media_gamers.guide` | `com.etzhayyim.apps.media_gamers.guide` | 攻略記事 (primary lang) |
| `media_gamers.review` | `com.etzhayyim.apps.media_gamers.review` | レビュー |
| `media_gamers.franchise_group` | `com.etzhayyim.apps.media_gamers.franchise_group` | フランチャイズ |
| `media_gamers.game_event` | `com.etzhayyim.apps.media_gamers.game_event` | イベント |
| `media_gamers.translation` | `com.etzhayyim.apps.media_gamers.translation` | **翻訳 Record (Pattern C)** |
| `media_gamers.id_contract` | `com.etzhayyim.apps.media_gamers.id_contract` | **ID 正規化 contract** |
| `media_gamers.game_work` | `com.etzhayyim.apps.media_gamers.game_work` | **作品レベル canonical entity** |
| `media_gamers.game_release` | `com.etzhayyim.apps.media_gamers.game_release` | **platform/region/edition release** |
| `media_gamers.game_listing` | `com.etzhayyim.apps.media_gamers.game_listing` | **store listing / product page** |
| `media_gamers.game_sku` | `com.etzhayyim.apps.media_gamers.game_sku` | **physical SKU / GTIN/JAN/EAN/UPC** |
| `media_gamers.record.gameItem` | `com.etzhayyim.apps.media_gamers.record.gameItem` | **in-game item (道具 / 素材 / 調理器具 etc.)** |
| `media_gamers.record.itemRecipe` | `com.etzhayyim.apps.media_gamers.record.itemRecipe` | **crafting / cooking recipe** |
| `media_gamers.knowledge.publishGameItem` | `com.etzhayyim.apps.media_gamers.knowledge.publishGameItem` | **item + optional recipe 登録 procedure** |
| `media_gamers.knowledge.publishDomainKnowledge` | `com.etzhayyim.apps.media_gamers.knowledge.publishDomainKnowledge` | **任意 game_slug の domain knowledge 登録 (generic, N-game 対応)** |
| `media_gamers.record.pokemon` | `com.etzhayyim.apps.media_gamers.record.pokemon` | **Pokémon pokedex entry (species / form / base_stats / types / habitat)。moves / evolutions は edge 側** |
| `media_gamers.knowledge.publishPokemon` | `com.etzhayyim.apps.media_gamers.knowledge.publishPokemon` | **任意 game_slug の pokedex entry 登録 procedure** |
| `media_gamers.record.translationLink` | `com.etzhayyim.apps.media_gamers.record.translationLink` | **ADR-0034 social-layer translation linkage** — 1 record per `(sourceUri, lang)` pair。Graph worker `handleCollection()` が typed `vertex_translation_link` (2 URI indexes) に projection。`value_json` parse なし |
| `media_gamers.translation.listLinks` | `com.etzhayyim.apps.media_gamers.translation.listLinks` | **ADR-0034 query** — `{anyUri}` → `{sourceUri, sourceLang, links[]}`。yoro post 詳細ページで LangTabs を駆動。`createKyselyDb().selectFrom("vertex_translation_link")` typed Kysely 経由 |

## ID Normalization Contract

**原則: canonical key は自前 ID。QID や store product id は authority ref。**

### Canonical Levels

| Level | 例 | 何を表すか |
|---|---|---|
| `work` | `game:work:pokemon-legends-z-a` | 抽象作品 |
| `release` | `game:release:pokemon-legends-z-a:switch-2:jp:digital` | platform / region / edition 差分 |
| `listing` | `game:listing:nintendo-eshop-jp:70010000012345` | ストア掲載単位 |
| `sku` | `game:sku:jan:4902370...` | 物理流通単位 |

### Authority Mapping

| Authority | 正規化先 | 用途 |
|---|---|---|
| `wikidata` QID | `work` | 多言語作品同定 |
| `igdb`, `giant-bomb`, `mobygames`, `rawg` | `work` | 外部ゲームDB参照 |
| `steam`, `nintendo-eshop`, `playstation-store`, `xbox-store` | `listing` | 販売ページ / store product id |
| `gtin`, `jan`, `ean`, `upc` | `sku` | パッケージ商品 |
| `cero`, `esrb`, `pegi` | `release` | 年齢レーティング |

### Contract Rules

- `nsid` は collection/schema 識別子に使う。canonical entity ID には使わない。
- `tid` / `rkey` は record の技術的一意キーに使う。canonical business key には使わない。
- `QID` は `work` の authority ref として保持する。主キーにはしない。
- `store product id` は `listing` の authority ref として保持する。
- 1つの `work` に複数 authority ref がぶら下がるのは正常。
- `release` と `listing` を分けることで、同一作品の Switch / Switch 2 / JP / US / digital / retail を衝突なく管理する。

## SQL Graph Schema

```
// ── Core ──
(:GameTitle {slug, name, synopsis, lang:"en", ...})-[:DEVELOPED_BY]->(:DeveloperStudio)
(:GameTitle)-[:PUBLISHED_BY]->(:PublisherCompany)
(:GameTitle)-[:AVAILABLE_ON]->(:GamePlatform)
(:GameTitle)-[:HAS_CHARACTER]->(:GameCharacter)
(:GameTitle)-[:IN_FRANCHISE]->(:FranchiseGroup)
(:GameTitle)-[:HAS_GUIDE]->(:Guide)

// ── In-game items / recipes (GraphAr: vertex_game_item / vertex_item_recipe + edge tables) ──
// vertex_game_item(id, slug, game_slug, name, item_type, rarity, stackable, lang, ...)
// vertex_item_recipe(id, slug, game_slug, name, output_item_id, output_quantity, station, ...)
// edge_game_has_item(src_id=game_slug, dst_id=item_id)
// edge_item_produced_by(src_id=item_id, dst_id=recipe_id)
// edge_recipe_uses_ingredient(src_id=recipe_id, dst_id=item_id, quantity)
// edge_recipe_requires_station(src_id=recipe_id, dst_id=item_id)  // e.g. recipe → frying-pan (cooking-tool)
// Read: Kysely + Hyperdrive → RisingWave PG (`createKyselyDb(env.HYPERDRIVE)`).
//   例: db.selectFrom('vertex_game_item').where('game_slug','=','pokemon-legends-z-a')
//         .where('item_type','=','cooking-tool').selectAll().execute()

// ── Translation (Pattern C) ──
(:Translation {source_slug, source_kind, lang, name, synopsis, ...})
// No edge to source — lookup by source_slug + source_kind + lang

// ── Studio hierarchy ──
(:DeveloperStudio)-[:SUBSIDIARY_OF]->(:PublisherCompany)

// ── User interaction ──
(:DID)-[:REVIEWED {rating, gameplay, story, graphics, sound}]->(:GameTitle)

// ── ID normalization ──
(:GameWork {id, slug, contract_id})-[:HAS_RELEASE]->(:GameRelease)
(:GameRelease)-[:HAS_LISTING]->(:GameListing)
(:GameRelease)-[:HAS_SKU]->(:GameSku)
(:GameWork)-[:HAS_AUTHORITY_REF]->(:AuthorityRef)
(:GameRelease)-[:HAS_AUTHORITY_REF]->(:AuthorityRef)
(:GameListing)-[:HAS_AUTHORITY_REF]->(:AuthorityRef)
(:GameSku)-[:HAS_AUTHORITY_REF]->(:AuthorityRef)
(:GameWork)-[:USES_CONTRACT]->(:IdContract)
```

## Cross-App Integration

### Upstream (Import)

| App | Integration | 用途 |
|---|---|---|
| `legal-entity.etzhayyim.com` | `Invoke(did, "get-entity", ...)` | パブリッシャーの法人登記 |
| `media-anime.etzhayyim.com` | `Invoke(did, "get-title", ...)` | ゲーム↔アニメ原作リンク |
| `i18n.etzhayyim.com` | Follow → ComAtprotoSyncSubscribeRepos | 翻訳 Record 自動受信 |

### Downstream (Export via Invoke/Serve)

| Method | 用途 |
|---|---|
| `get-title` | タイトル情報取得 |
| `get-upcoming` | 発売予定タイトル |
| `list-by-developer` | デベロッパー作品一覧 |
| `list-by-platform` | プラットフォーム別作品 |
| `get-guide` | 攻略ガイド取得 |

## Translation Model Strategy (i18n.etzhayyim.com 連携)

**3-Tier モデル選定。コンテンツ種別と言語で最適モデルを自動ルーティング。**

### Tier 1: 高品質 (攻略記事・レビュー等の長文コンテンツ)

| 言語 | Model | Quality |
|---|---|---|
| ja, zh, zh-TW | **Qwen 2.5-72B** (Murakumo) | A — CJK ネイティブ級 |
| ko | Qwen 2.5-72B | B — CJK 内では最弱だが実用 |
| es, fr, de, pt, it, ru | **Llama 3.3-70B** or DeepSeek V3 | A — 欧州言語はプロ級 |

### Tier 2: 安定品質 (UI ラベル・短文・メタデータ)

| 言語 | Model | Quality |
|---|---|---|
| vi, id, tr, nl, pl | **Aya Expanse 32B** | B — 多言語特化で安定 |

### Tier 3: 広範カバレッジ (残り言語 + Tier 1/2 の fallback)

| 言語 | Model | Quality |
|---|---|---|
| ar, hi, bn, th + 残り 180言語 | **NLLB-200 3.3B** | A — 翻訳専用。CPU で動作。70B 汎用 LLM を凌駕 |

### Quality Gate

```
LLM 翻訳 → back-translation → COMET score check
  ≥ 0.85 → 自動公開
  0.70–0.85 → translation record 作成 + review flag
  < 0.70 → reject → NLLB fallback → human review queue
```

### Verified Quality (Murakumo + Workers AI 実測 2026-03-25)

ゲーム攻略テキスト (Elden Ring Malenia guide) を **8 モデル × 10 言語** で翻訳 + back-translation 検証。

#### Full Model × Language Matrix (実測)

| Model (実体) | ja | zh | ko | es | fr | de | ru | ar | hi | th |
|---|---|---|---|---|---|---|---|---|---|---|
| **qwen2.5-coder-32b** | **A** | **A** | B | **A** | **A** | **A** | **A** | B | B | — |
| **gemma-3-12b** | C | B | B | A | A | A | B | B | B | — |
| **llama-3.1-8b** | B | C | C | A | B | B | B | C | B | — |
| **hermes-2-pro** (Mistral 7B) | C | C | D | A | B | — | — | D | C | — |
| **llama-3.2-3b** | D | D | D | B | B | — | — | D | C | D |
| **m2m100-1.2b** (Workers AI) | C | C | C | B | B | B | B | D | C | C |
| **deepseek-r1-distill** | **F** | **F** | **F** | **F** | **F** | **F** | **F** | **F** | **F** | **F** |

**注**: `qwen3-vl-8b` = `qwen2.5-coder-32b` にルーティング (同一結果)。`qwen2.5-3b` = `llama-3.2-3b` にルーティング。

#### m2m100-1.2b (Workers AI, NLLB 系) 品質詳細

| 言語 | 品質 | 問題点 |
|---|---|---|
| **ja** | C | "走り回って走り回る" — 不自然な繰り返し。文法崩れ。意味は伝わる |
| **zh** | C | zh 途中切れ ("在第一阶段..." で終了)。短文なら OK |
| **ko** | C | "워터 포일 댄스" — 音訳は正確だが全体的にぎこちない |
| **es** | B | "baile del pájaro acuático" — 自然。固有名詞未翻訳 (許容) |
| **fr** | B | "danse des oiseaux d'eau" — 自然。固有名詞保持 |
| **de** | B | 文法やや不安定だが意味は正確 |
| **ru** | B | "танца Waterfowl" — 固有名詞未翻訳混在。意味は通じる |
| **ar** | D | 大幅な意味欠落。前半が消失。使用不可 |
| **hi** | C | "पानी के पक्षी नृत्य" — 直訳だが意味は伝わる |
| **th** | C | 概ね正確。"ล้อ" (wheel→roll) は微妙 |

#### llama-3.2-3b / hermes-2-pro 品質詳細

| Model | ja 問題 | ko 問題 | ar 問題 |
|---|---|---|---|
| **llama-3.2-3b** | "エレンランド・リング" — 固有名詞崩壊。"血吸血" — 意味不明 | "물고기 춤" (Waterfowl→魚) — 誤訳 | アラビア語+英語+ヒンディー語が混在。文として崩壊 |
| **hermes-2-pro** | "水の斬撃" — Rivers of Blood を "水の斬撃" に誤訳 | 日本語カタカナ "ダン" 混入。文として崩壊 | "سيف الحمر" — 意味が変わっている |

#### Back-Translation Accuracy (qwen2.5-coder-32b → back-translate)

| 言語 | 意味保持 | 固有名詞 | 文体 | 総合 | 問題点 |
|---|---|---|---|---|---|
| **ja** | A | B | A | **A** | "マレーニア" (許容)。"recovery frames"=正確 |
| **zh** | A | A | A | **A** | "玛莲娜"=正確。"绯红腐败"=Scarlet Rot 正確。**最高品質** |
| **ko** | B | C | B | **B** | "물병 춤" (Waterfowl→水瓶) 誤訳 |
| **es** | A | A | A | **A** | "Ríos de Sangre"=自然 |
| **fr** | A | A | A | **A** | "Fleuves de Sang"=自然 |
| **de** | A | B | A | **A** | "Scharlachroten"=正確 |
| **pt** | A | B | A | **A** | "Dança das Águias" 微誤訳だが意味通じる |
| **ru** | A | B | A | **A** | "Реки Крови"=正確 |
| **ar** | B | C | B | **B** | 固有名詞の音訳不安定 |
| **hi** | B | C | B | **B** | 音訳主体。意味は伝わる |

#### Key Findings (実測)

| Finding | Detail |
|---|---|
| **qwen2.5-coder-32b が全言語で最強** | CJK (A/A/B) + 欧州全 A。ゲーム固有名詞精度も最高 |
| **m2m100 (NLLB系) は期待以下** | 1.2B の小型版のため、ベンチマーク上の NLLB-200 (3.3B) とは品質差大。ar は使用不可 (D) |
| **< 7B モデルは翻訳不可** | llama-3.2-3b, hermes-2-pro は CJK/ar で文として崩壊。欧州言語のみ辛うじて B |
| **deepseek-r1-distill は翻訳不可** | `<think>` タグ出力。翻訳せず reasoning を出力。**全言語 F** |
| **gemma-3-12b は CJK 固有名詞致命的** | Malenia→ミケラ (別キャラ) 誤訳。ゲームドメイン不適 |
| **ko は全モデル弱い** | Waterfowl Dance の韓国語訳が全モデルで不安定 |
| **Workers AI m2m100 は短文向き** | 長文で品質劣化。UI ラベル翻訳には使える。攻略記事には不適 |

### Murakumo 利用可能モデル — 翻訳推奨度 (実測確定)

| Model | 実体 | 翻訳適性 | 推奨用途 |
|---|---|---|---|
| `qwen2.5-coder-32b` | @cf/qwen/qwen2.5-coder-32b-instruct | **A — 最推奨** | 全言語の攻略記事・レビュー翻訳 |
| `qwen3-vl-8b` | 同上 (alias) | **A** | 同上 (同一モデル) |
| `gemma-3-12b` | @cf/google/gemma-3-12b-it | **C** | 欧州言語の短文のみ。CJK 禁止 |
| `llama-3.1-8b` | @cf/meta/llama-3.1-8b-instruct | **B** | 欧州言語は良好。CJK は B- |
| `hermes-2-pro` | @hf/nousresearch/hermes-2-pro-mistral-7b | **D** | CJK/ar 崩壊。欧州 es/fr のみ辛うじて可 |
| `llama-3.2-3b` | @cf/meta/llama-3.2-3b-instruct | **D** | 全言語で品質不足。使用非推奨 |
| `m2m100-1.2b` | Workers AI @cf/meta/m2m100-1.2b | **C** | 短文 UI ラベル向き。長文攻略記事は不適 |
| `deepseek-r1-distill` | @cf/deepseek-ai/deepseek-r1-distill-qwen-32b | **F — 使用禁止** | reasoning model。翻訳タスク不適 |

### Article Generation Quality Evaluation (記事生成品質)

**`media_gamers.eval_models` コマンドで全 Murakumo モデルの記事生成品質を 5 軸 (accuracy/detail_depth/structure/actionability/game_term_precision) × 20点 = 100点満点で評価。**

評価方法:
1. 各モデルに同一プロンプト (ボス攻略記事) を投入
2. qwen2.5-coder-32b がクロス評価 (judge)
3. 結果は `com.etzhayyim.apps.media_gamers.model_evaluation` record に永続化

**評価軸:**

| 軸 | 重み | 判定基準 |
|---|---|---|
| accuracy | 20 | ゲーム仕様に忠実か。存在しないメカニクスの hallucination がないか |
| detail_depth | 20 | HP、ダメージ、タイミング等の具体的数値があるか |
| structure | 20 | セクション分割、スキャン可能なフォーマット、論理的流れ |
| actionability | 20 | 読者がこの記事を読んで実際にボスを倒せるか |
| game_term_precision | 20 | キャラ名、アイテム名、スキル名が公式ローカライズ準拠か |

**期待結果 (翻訳品質から類推):**

| Model | 記事生成適性 (推定) | 理由 |
|---|---|---|
| `qwen2.5-coder-32b` | **A — 最推奨** | 翻訳 A, CJK 高品質, ゲーム固有名詞精度最高 |
| `gemma-3-12b` | **B** | 12B で良好な文章生成だが CJK 固有名詞に誤訳あり |
| `llama-3.1-8b` | **B-** | 英語記事は良好。日本語は品質不安定 |
| `hermes-2-pro` | **C** | 短文は可。長文構造化が弱い |
| `llama-3.2-3b` | **D** | 3B は記事生成に不十分。固有名詞崩壊 |
| `deepseek-r1-distill` | **F** | `<think>` タグ出力。記事を書かず reasoning を出力 |

**実測は `media_gamers.eval_models` で取得。上記は翻訳品質からの推定値。**

### 結論: 翻訳パイプライン (実測確定)

```
攻略記事・レビュー (長文)  → qwen3.5-4b (Murakumo on-prem MLX, zero cost)
UI ラベル・メタデータ (短文) → qwen3.5-4b (同上)
全言語 fallback            → qwen3.5-4b (Murakumo hayate fleet direct fetch)
```

### NLLB-200 Fleet Deploy 検証結果 (2026-03-25)

**NLLB-200 は seq2seq (encoder-decoder) であり、MLX `mlx_lm` (causal LM 専用) では動作しない。** Fleet daemon は `mlx_lm.load()` ベースのため、NLLB を直接 deploy 不可。

PyTorch + transformers で NLLB-200-distilled-1.3B をローカル検証:

| 言語 | NLLB 1.3B | qwen2.5-32b | 勝者 | NLLB 問題点 |
|---|---|---|---|---|
| **ja** | C | **A** | qwen | "血の川で造られた血" — 意味崩壊。"ウォーターフール" 誤記 |
| **zh** | C | **A** | qwen | "埃尔登戒指马列尼亚" — "Elden Ring" を "戒指(指輪)" に誤訳 |
| **ko** | C | **B** | qwen | "피의 강으로 만들어진 피" — 意味崩壊 |
| **es** | B | **A** | qwen | 概ね正確だが小文字のみ (文法的に不自然) |
| **fr** | B | **A** | qwen | "il évite" — she を he に誤訳 (性別エラー) |
| **de** | B | **A** | qwen | 概ね正確。"Blutbau" はやや不自然 |
| **ru** | B | **A** | qwen | "качаясь" (swinging) — rolling の誤訳 |
| **ar** | **F** | B | qwen | **翻訳せず英語をそのまま出力** + 無限ループ |
| **hi** | B | B | 同等 | 意味は伝わる。音訳主体 |
| **th** | B | — | NLLB | 概ね正確。固有名詞は英語保持 |

**速度**: 30-70s/文 (CPU)。qwen2.5-coder-32b (Workers AI GPU) は <3s/文。

#### 結論: NLLB Fleet Deploy は **不要**

| 理由 | Detail |
|---|---|
| **MLX 非対応** | seq2seq は `mlx_lm` で動かない。daemon.go に新 backend (PyTorch subprocess) が必要 |
| **品質が qwen 以下** | CJK 全敗 (C vs A)。欧州語も B vs A。ar は F (出力崩壊) |
| **速度 10-20x 遅い** | CPU 30-70s vs GPU <3s。Fleet Mac Mini でも Apple Silicon GPU なし (seq2seq は Metal 未最適化) |
| **3.3B 版も同傾向** | 1.3B distilled は 3.3B の 95% 品質。ドメイン特化テキストでは LLM が圧倒的に有利 |
| **NLLB の優位性は汎用短文のみ** | FLORES ベンチマーク (短文ニュース) では強いが、ゲーム攻略のような domain-specific 長文では LLM が勝つ |

### Qwen3-8B-4bit (MLX, ローカル実測 2026-03-26)

**`enable_thinking=False` 必須。** デフォルトは thinking mode ON で `<think>` タグを出力する。

| 言語 | Qwen3-8B | Qwen2.5-32B | 勝者 | Qwen3 問題点 |
|---|---|---|---|---|
| **ja** | B | **A** | qwen2.5 | "エルドンリング" (誤)。"ウォーターフォールダンス" (Waterfowl→Waterfall) |
| **zh** | **A** | **A** | **同等** | "水禽之舞"=正確。"猩红腐蚀"=正確。最高品質 |
| **ko** | C | B | qwen2.5 | "물고기 춤" (Waterfowl→魚 誤訳) |
| **es** | A | A | 同等 | — |
| **fr** | B | **A** | qwen2.5 | "sang des rivières" やや不自然 |
| **de** | B | **A** | qwen2.5 | "Blutvergiftungsbuild" (blood poisoning 誤訳) |
| **ru** | B | **A** | qwen2.5 | 固有名詞未翻訳混在 |
| **ar** | **B** | B | 同等 | qwen2.5 と同等。"رقصة الطيور" 正確 |
| **hi** | B | B | 同等 | — |
| **th** | **B** | — | Qwen3 | 初テスト。概ね正確 |
| **速度** | 1.5-6.4s (MLX) | <3s (Workers AI) | 同等 | Apple Silicon で高速 |

**評価**: 8B で 32B の 80% 品質。zh は同等 A。ja/ko/de で固有名詞誤訳 (8B の限界)。
**用途**: Fleet ノードの軽量翻訳 (5GB RAM で動作)。高品質が必要な CJK は qwen2.5-32B 推奨。

**最終結論: qwen3.5-4b (Murakumo on-prem MLX) が翻訳・記事生成 primary。** Zero cost (hayate fleet direct fetch)。qwen2.5-coder-32b (Workers AI) は fallback。NLLB deploy は品質・互換性の両面で不要。

## Reactive Pipeline (Design E Layer 1)

`handleComAtprotoSyncSubscribeReposCommit()` processes inbound commits from `subscribeRepos`:

| Collection | Action |
|---|---|
| `com.etzhayyim.apps.media_gamers.guide` | quality evaluation → translate if score >= 70 |
| `com.etzhayyim.apps.media_gamers.translation` | social announce |
| `com.etzhayyim.apps.media_gamers.game_title` | event recording |

### Shinka (Layer 3) — joucho 情緒 cadence-driven

**joucho cadence 初リファレンス実装。** `resolveHeartbeatCadence()` が mood → 行動を解決。固定 `heartbeatCount % N` タイマー禁止。

| Flag | Action |
|---|---|
| `shouldPost` | mood-driven ゲーム選択 → `generateGuideForGame()` (LLM 生成 + 品質評価 + T2 domain write + T1 social post + score>=70 で 7 言語翻訳) |
| `shouldEngage` | follower KPI reward (wellness/dojo 上昇検出 → like/love) |
| `shouldAnalyze` | guide coverage stats → social analytics post |
| `shouldDrill` | kyumei-koji 自己省察 |
| `shouldValidate` | low-quality guide 検出 |

**Game selection**: mood affinity mapping。focused/calm → elden-ring, black-myth-wukong。joyful/grateful → zelda-totk, pokoa-world, dq3-hd2d。contentSource (inbound commit/reaction/record_analysis) で対象ゲームを動的決定。

Seed games: elden-ring, zelda-totk, monster-hunter-wilds, black-myth-wukong, pokoa-world, metaphor-refantazio, ff7-rebirth, stellar-blade, dq3-hd2d, gta-vi。

### Write Path (PDS XRPC)

Write は PDS XRPC (`https://atproto.etzhayyim.com/xrpc/*`) が標準パス。worker.ts に ES256 JWT ServiceAuthSigner (`SS_SIGNING_KEY` Secrets Store binding) を組み込み認証。

禁止:
- `legacy internal HTTP paths`

2026-04-02 live logs:
- legacy internal caller は `404`
- canonical XRPC path は成功
- ボトルネックは Yata index より registration `entries` 側 (`agent-register-tools`, `identity-register`, `capability-declare`, `governance-manifest`)

## Build & Deploy

```bash
cd 60-apps/etzhayyim-project-media-gamers/wasm/media-gamers-7m8oocsn
etzhayyim deploy       # account-level Worker
```

## API Endpoints

- App: `https://a7m8oocs.etzhayyim.com`
- XRPC: `https://a7m8oocs.etzhayyim.com/xrpc/com.etzhayyim.apps.media_gamers.{command}`
- Route: `https://media-gamers.etzhayyim.com`
- Health: `https://a7m8oocs.etzhayyim.com/health`
- Heartbeat: `POST https://a7m8oocs.etzhayyim.com/_heartbeat`

## Claude Code Agent — etzhayyim xrpc

Claude Code (this chat agent) can trigger commands via `etzhayyim xrpc`:

```bash
# Step-by-step seed (run each in order after previous completes)
etzhayyim xrpc com.etzhayyim.apps.media_gamers.catalog.seedAll -d '{"step":"platforms"}' --app a7m8oocs
etzhayyim xrpc com.etzhayyim.apps.media_gamers.catalog.seedAll -d '{"step":"developers"}' --app a7m8oocs
etzhayyim xrpc com.etzhayyim.apps.media_gamers.catalog.seedAll -d '{"step":"publishers"}' --app a7m8oocs
etzhayyim xrpc com.etzhayyim.apps.media_gamers.catalog.seedAll -d '{"step":"franchises"}' --app a7m8oocs

# Seed games in batches (current seed: 53 total)
etzhayyim xrpc com.etzhayyim.apps.media_gamers.catalog.seedGames -d '{"offset":0,"limit":10}' --app a7m8oocs
etzhayyim xrpc com.etzhayyim.apps.media_gamers.catalog.seedGames -d '{"offset":10,"limit":10}' --app a7m8oocs
etzhayyim xrpc com.etzhayyim.apps.media_gamers.catalog.seedGames -d '{"offset":20,"limit":10}' --app a7m8oocs
etzhayyim xrpc com.etzhayyim.apps.media_gamers.catalog.seedGames -d '{"offset":30,"limit":10}' --app a7m8oocs
etzhayyim xrpc com.etzhayyim.apps.media_gamers.catalog.seedGames -d '{"offset":40,"limit":10}' --app a7m8oocs
etzhayyim xrpc com.etzhayyim.apps.media_gamers.catalog.seedGames -d '{"offset":50,"limit":10}' --app a7m8oocs

# Register JP release candidates from in-app seed catalog into normalization records
etzhayyim xrpc com.etzhayyim.apps.media_gamers.normalization.registerJapanReleasedFromSeed -d '{}' --app a7m8oocs

# Generate guides for a single game
etzhayyim xrpc com.etzhayyim.apps.media_gamers.catalog.generateAll -d '{"slug":"elden-ring"}' --app a7m8oocs

# Generate guides in batches of 5
etzhayyim xrpc com.etzhayyim.apps.media_gamers.catalog.generateAll -d '{"offset":0,"limit":5}' --app a7m8oocs

# Query — check game data
etzhayyim xrpc com.etzhayyim.apps.media_gamers.catalog.getGame --app a7m8oocs --json
```

`etzhayyim xrpc` source: `70-tools/etzhayyim/etzhayyim/xrpc.go`

## RisingWave KG State (2026-04-19, iter #40)

Direct-INSERT expansion via `/loop ドメイン知識、カバレッジを向上` self-paced curator. Phase scripts at `/tmp/mkphase{6-42}.py` (single-row INSERT pattern, RisingWave silent multi-VALUES loss workaround).

| Vertex Table | Count | Coverage |
|---|---|---|
| `vertex_game_title` | 13,337 | Wikidata JP releases + AAA 2023-2025 + DLC + remasters |
| `vertex_game_character` | 1,217 | Konami/Nintendo/Pokemon/SE/From/Capcom/Atlus/Bethesda/MS/Sony/MH/Marvel rosters |
| `vertex_game_item` | 945 | Weapons, abilities, personas, Eikons, Zonai devices, stratagems, archetypes, jokers |
| `vertex_actor` (T0 logical) | 2,277+ | `did:etzhayyim:gameactor/gamechar/gameitem:*` synthetic DIDs (DB-only, no jsonld) |

**T0 sync pattern** (idempotent, run after each phase ingest):
```sql
INSERT INTO public.vertex_actor (did, handle, display_name, created_at, classification, execution_tier)
SELECT vertex_id, replace(vertex_id, 'did:etzhayyim:gamechar:', '') || '.gamechar.etzhayyim.com', name, now(), 'tier-0-db-only', 'T0'
FROM public.vertex_game_character
WHERE vertex_id NOT IN (SELECT did FROM public.vertex_actor WHERE did LIKE 'did:etzhayyim:gamechar:%');
-- mirror for vertex_game_item via vertex_id (legacy items have NULL did, use vertex_id)
```

**Cluster guardrails** (applied 2026-04 after compute-0 OOM crashloop):
- `barrier_interval_ms = 1000`, `checkpoint_frequency = 10`
- `adaptive_parallelism_strategy = 'BOUNDED(2)'`, `streaming_parallelism = 2`
- Result: streaming actors 28,793 → 4,229 (-85%); CPU 99.9% → 94%; Mem 89% → 66%
- MV freshness lag 60-120s post-INSERT; `vertex_actor` count snapshot lags real INSERT count (acceptable)

**Domain coverage** (iter #1-#40):
- **Konami**: MGS全作 + Castlevania + Silent Hill (incl. SH2R 2024) + Bomberman + Frogger
- **Nintendo**: Mario/Zelda BOTW+TOTK (sages/champions/scientists) + Pokemon Gen I-IX (legendaries/paradox/SV DLC roster) + Splatoon 3 (Deep Cut/weapons) + Smash Ultimate + Mario Kart World 2025
- **Sony**: Stellar Blade, Helldivers 2 (stratagems/factions), GoW Ragnarok
- **Square Enix**: FF14 Endwalker/Dawntrail (Zenos/Emet-Selch/Venat/Wuk Lamat/Sphene), FF16 (Eikons), FF7 Rebirth, Visions of Mana, DQ3 HD-2D
- **From Software**: Elden Ring SOTE (Miquella/Promised Consort Radahn/Messmer/Bayle/Rellana), Dark Souls trilogy
- **Atlus**: Persona 5 Royal (Phantom Thieves + personas), Metaphor: ReFantazio (archetypes)
- **Capcom**: MH Wilds (Arkveld/Rey Dau/Uth Duna/Nu Udra/Zoh Shia), SF6 (newcomers + drive system), Tekken 8 (Reina/Victor/Azucena/Clive guest), Dragon's Dogma 2
- **Indie/Misc**: Balatro (jokers), Animal Well, Hades II (Melinoë + Olympians + Chronos), Black Myth: Wukong (chapter bosses + 72 transformations), Marvel Rivals (heroes + team-ups), Star Wars Outlaws, Indiana Jones Great Circle, Avowed, Expedition 33
- **Genshin Impact**: 5★ named weapons (Mistsplitter/Aqua Simulacra/Engulfing Lightning/Tulaytullah/Uraku Misugiri/Light of Foliar Incision)
- **DOOM**: Eternal arsenal + Dark Ages 2025 (Shield Saw/Atlan Mech/Cyber Dragon)
- **LoL**: Champion roster (Aatrox/Akali/Jhin/Kayn/Sett/Zed et al.)

## RisingWave Direct Ingest Runbook (Fallback)

When app XRPC write path returns `Worker hung` / transient 5xx, use direct RisingWave scripts:

```bash
# 1) Bulk ingest JP-related games from Wikidata to vertex_game_title
python3 70-tools/scripts/media_gamers_ingest_jp_releases.py --page-size 500

# 2) Backfill release year/date from Wikidata P577
python3 70-tools/scripts/media_gamers_backfill_release_year.py

# 3) Enrich source refs in external_ids (igdb/steam/official), optionally Steam date fallback
python3 70-tools/scripts/media_gamers_enrich_sources.py --steam-backfill
```

Recommended verification:

```bash
psql "$RW_CONN" -c "select count(*) from vertex_game_title;"
psql "$RW_CONN" -c "select count(*) filter (where release_year is not null) as with_year, count(*) as total from vertex_game_title;"
psql "$RW_CONN" -c "select count(*) filter (where external_ids like '%igdb:%') as has_igdb, count(*) filter (where external_ids like '%steam:%') as has_steam, count(*) filter (where external_ids like '%official:%') as has_official from vertex_game_title;"
```
