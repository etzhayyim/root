# kagami Cypher Builder — neo4j/cypher-builder 完全互換設計

## 背景
現行 `@etzhayyim/kagami-query-builder` の `G` は、Kagami 運用要件（selective WHERE 強制、禁止 predicate、strict mode、`exec/execCached` 直結）を内包している。
その結果、次の問題がある。

- `@neo4j/cypher-builder` の API/概念モデルとズレる
- 独自文法・独自制約がクエリ組み立て API に混在する
- Neo4j 標準のサンプル/知見をそのまま適用しにくい

## 目標
`neo4j/cypher-builder` (v3.x) と **完全互換** の `kagami cypher builder` を設計する。

完全互換の定義:

1. 同一入力コードで同一の `build()` 振る舞い（`{ cypher, params }`）
2. 公式 API（`Cypher.Node`, `Cypher.Pattern`, `Cypher.Match`, `Cypher.Param`, `Cypher.Merge`, `Cypher.OptionalMatch`, `Call/Yield` など）をそのまま利用可能
3. Cypher バージョン設定・BuildConfig を公式仕様準拠で適用可能
4. 独自機能は API 本体に混ぜず、**後段ポリシー/実行レイヤー**に分離

## 非目標

- `G` 独自メソッドの API を新コアへ持ち込む（例: `whereStartsWith` 禁止ロジック内蔵）
- `@neo4j/cypher-builder` の fork 維持
- 1リリースで全呼び出しを一括移行

## 前提（公式仕様）

- `@neo4j/cypher-builder` 3.x は Node.js 20+ を要件とする
- v3 は Cypher 25 をターゲット（Cypher 5 もサポート）
- 基本構文は `new Cypher.Node/Pattern/Match/...` + `.build()`

## 提案アーキテクチャ

### 1. Core レイヤー（完全互換）
新パッケージ: `@etzhayyim/kagami-cypher-builder`

- `@neo4j/cypher-builder` を **そのまま再 export**
- 追加クラス/追加メソッドは原則禁止
- import 互換:
  - 推奨: `import Cypher from "@etzhayyim/kagami-cypher-builder"`
  - 既存 Neo4j サンプル移植時: `import Cypher from "@neo4j/cypher-builder"` と等価

実装方針:

- `export { default } from "@neo4j/cypher-builder"`
- 必要なら named export も 1:1 re-export
- 型定義は upstream 型を直接透過

### 2. Policy レイヤー（Kagami 制約の分離）
新モジュール: `@etzhayyim/kagami-cypher-policy`

責務:

- `build()` 後の `cypher`/`params` を検証
- selective WHERE, max LIMIT, wildcard RETURN 禁止, 危険 predicate 禁止などを lint/validator 化
- 失敗時は明示的な `PolicyError`

API 例:

- `validateKagamiPolicy({ cypher, params }, policyConfig)`
- `enforceKagamiPolicy(query, policyConfig)` （内部で `build()` + validate）

ポイント:

- 制約を「クエリ生成」ではなく「クエリ受理」に移す
- Neo4j 互換 API を汚さない

### 3. Runtime レイヤー（実行責務の分離）
新モジュール: `@etzhayyim/kagami-cypher-runtime`

責務:

- `ctx.aietzhayyimKagamiCypher` / `aietzhayyimKagamiCypherCached` への送信
- appId, ttl, observability, retry, timeout

API 例:

- `executeCypher(ctx, query, { appId })`
- `executeCypherCached(ctx, query, { appId, ttlS })`

ポイント:

- `exec/execCached` を Builder インスタンスメソッドから外し、実行関数へ寄せる
- 互換上必要な期間だけ adapter で旧形式を提供

### 4. Legacy Adapter（移行用）
新モジュール: `@etzhayyim/kagami-query-builder-legacy-adapter`

責務:

- 現行 `new G(...).where(...).ret(...).limit(...).exec(ctx)` を段階移行
- 内部実装を `@neo4j/cypher-builder` ベースへ置換
- 非推奨警告（`process.emitWarning`）で移行を促進

重要:

- 旧 API は LTS 期間のみサポート
- 新規開発は禁止（lint で block）

## API 対応方針（主要）

- `G.where / whereGt / whereLte / whereIn` -> `Cypher.eq/gt/lte/in` + `Param`
- `G.whereAny/whereOrColumns` -> `Cypher.or(...)`
- `G.edge/inEdge/optionalEdge` -> `Pattern.related(...).to(...)` + `OptionalMatch`
- `G.matchAlso` -> `.match(...)` 連結
- `G.call().yield()` -> `Cypher.Call(...).yield(...)`
- `G.merge().set()` -> `Cypher.Merge(...).onCreateSet/onMatchSet` or `Set`
- `G.ret/retFields/retExpr/count` -> `Return` 句
- `G.exec/execCached` -> runtime 関数へ移譲

## 互換性保証のテスト戦略

### A. Upstream Contract Test（必須）

- `@neo4j/cypher-builder` 公式ドキュメント例を fixture 化
- `@etzhayyim/kagami-cypher-builder` で同一コードを実行
- `cypher` / `params` が一致することを snapshot 検証

### B. Differential Test（必須）

- 同じ DSL 入力を
  - `@neo4j/cypher-builder`
  - `@etzhayyim/kagami-cypher-builder`
 でビルドし、完全一致検証

### C. Policy Test（必須）

- 生成物に対して `validateKagamiPolicy` を実施
- 既存 lint ルール群（dangerous query, wildcard return 等）と同値であることを確認

### D. Legacy Adapter Test（移行期）

- 既存 `G` テストケースを adapter 経由で再実行
- 互換範囲を明文化（非互換は fail-fast）

## 移行計画

1. Phase 0: 新コア導入
- `@etzhayyim/kagami-cypher-builder` を追加（re-export only）
- contract/differential test を先に通す

2. Phase 1: 実行・ポリシー分離
- `kagami-cypher-policy` / `kagami-cypher-runtime` 実装
- `pds-helpers` の実行処理を runtime 経由へ寄せる

3. Phase 2: 互換 adapter 導入
- `G` 呼び出しの内部を新基盤へ接続
- 旧 API 利用箇所へ deprecation warning

4. Phase 3: 呼び出し側移行
- `new G(...)` を段階的に `Cypher.*` へ置換
- 置換順は hot path から（feed/search/notification）

5. Phase 4: 旧 API 廃止
- CI で `@etzhayyim/kagami-query-builder` 新規利用を禁止
- 最終的に legacy adapter を削除

## 破壊的変更の管理

- 期間中は dual-path（legacy + new core）
- Feature flag:
  - `KAGAMI_CYPHER_BUILDER_MODE=legacy|compat|strict-compat`
- 本番は `compat` から開始し、検証後 `strict-compat` へ

## リスクと対策

- リスク: 現行 `G` の暗黙制約が消えて性能劣化
  - 対策: policy レイヤー mandatory 化（runtime 実行前に必ず validate）

- リスク: 既存 whereRaw 依存クエリの移行コスト
  - 対策: adapter で暫定吸収、優先度順に Cypher AST 化

- リスク: upstream 更新で互換破壊
  - 対策: differential test を CI gate 化

## 受け入れ基準 (DoD)

- `@etzhayyim/kagami-cypher-builder` の API が `@neo4j/cypher-builder` と 1:1
- 公式サンプル fixture の 100% パス
- policy/runtime 分離後も既存 SLO（timeout/OOM 再発防止）を維持
- 旧 `G` は deprecate 状態で動作、段階移行が可能

## 実装メモ（最小スケルトン）

```ts
// packages/graph/kagami-cypher-builder/src/index.ts
export { default } from "@neo4j/cypher-builder";
export * from "@neo4j/cypher-builder";
```

```ts
// packages/graph/kagami-cypher-runtime/src/execute.ts
export async function executeCypher(ctx, query, opts) {
  const { cypher, params } = query.build();
  // validateKagamiPolicy({ cypher, params }, opts.policy)
  return ctx.aietzhayyimKagamiCypher({ cypher, params, appId: opts.appId });
}
```

