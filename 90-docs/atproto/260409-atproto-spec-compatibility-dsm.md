# AT Protocol 互換性カバレッジ DSM（Repo-wide）

更新日: 2026-04-09

## 前提

- 仕様ソースは `https://atproto.com/ja/specs` を起点に確認。
- 2026-04-09 時点で `https://atproto.com/ja/specs` は `404` のため、同サイトの `/specs/*` 一覧を評価軸に採用。
- 仕様項目一覧は `https://atproto.com/docs` から抽出した `/specs/*` 19 項目を使用。

## 凡例

- `H`: 高カバレッジ（設計/実装の中心に存在）
- `M`: 中カバレッジ（部分実装、または簡略実装）
- `L`: 低カバレッジ（限定対応）
- `-`: ほぼ対象外

## DSM（仕様 × 実装責務）

| Spec | XRPC Core (`10-protocol/xrpc`) | PDS Surface (`pds-app/dispatch`) | Auth/Identity | Repo/Sync/Data | Relay/Mod | Tests | 判定 |
|---|---|---|---|---|---|---|---|
| `atp` | M | H | M | M | M | M | M |
| `xrpc` | H | H | M | M | M | M | H |
| `nsid` | H | H | - | M | M | M | H |
| `lexicon` | M | M | - | L | - | L | M |
| `did` | M | H | H | M | - | M | H |
| `handle` | M | M | M | M | - | L | M |
| `account` | - | M | H | M | - | M | M |
| `oauth` | - | H | H | - | - | L | M |
| `permission` | - | H | H | M | - | M | M |
| `data-model` | M | M | - | H | - | M | H |
| `record-key` | M | M | - | H | - | M | H |
| `tid` | H | M | - | H | - | L | H |
| `at-uri-scheme` | M | M | M | H | - | M | M |
| `repository` | M | M | M | H | M | H | H |
| `sync` | M | M | - | H | H | M | H |
| `event-stream` | - | M | - | M | M | L | M |
| `blob` | M | H | M | H | - | M | M |
| `label` | - | M | M | M | H | M | M |
| `cryptography` | M | M | H | M | - | M | M |

## 根拠（主要）

- NSID/XRPC 基盤
  - `10-protocol/xrpc/src/nsid.ts`
  - `10-protocol/xrpc/src/dispatch.ts`
- PDS の XRPC 入口と well-known/OAuth
  - `50-infra/cloudflare/workers/atproto/src/pds-app.ts`
  - `50-infra/cloudflare/workers/atproto/src/pds-dispatch.ts`
- OAuth / Permission / Auth
  - `50-infra/cloudflare/workers/atproto/src/pds-handlers-oauth.ts`
  - `50-infra/cloudflare/workers/atproto/src/pds-scope.ts`
  - `50-infra/cloudflare/workers/atproto/src/pds-auth-verify.ts`
- Repository / Sync / Label / Data model
  - `50-infra/cloudflare/workers/atproto/src/pds-core.ts`
  - `50-infra/cloudflare/workers/atproto/src/pds-validation.ts`
  - `50-infra/cloudflare/workers/atproto/src/pds-handlers-repo.ts`
  - `50-infra/cloudflare/workers/atproto/src/pds-helpers.ts`
- Relay / Moderation 分離
  - `50-infra/cloudflare/workers/relay/worker.ts`
  - `50-infra/cloudflare/workers/moderation/worker.ts`
- テスト根拠
  - `50-infra/cloudflare/workers/atproto/src/pds-e2e-coverage.test.ts`
  - `50-infra/cloudflare/workers/atproto/src/pds-security-hardening.test.ts`
  - `50-infra/cloudflare/workers/atproto/src/pds-dispatch.test.ts`

## 互換性ギャップ（優先度順）

1. `sync`/`event-stream` の配信順序・CAR 再構成は改善済み。残差分は高負荷時の運用チューニング（poll 間隔/深さ）中心。
2. `blob` の CIDv1 化と legacy key 互換読み出しは実装済み。残差分は legacy key の段階的削除運用のみ。
3. `lexicon` の `schemas` は生成済み Lexicon JSON を返却する構成へ改善済み。残差分は lexicon 追加時の再生成運用のみ。
4. `cryptography` は署名/チェーン検証に加え strict reject（`strict` / `requireVerified`）を実装済み。残差分はクライアント適用方針のみ。

## 2026-04-09 改善反映

- `lexicon`:
  - `com.atproto.lexicon.resolveLexicon` を固定配列レスポンスから、ハンドラ集合ベースの動的解決へ更新。
  - `id` / `ids` 指定による絞り込みと `notFound` 返却を追加。
  - 実装: `50-infra/cloudflare/workers/atproto/src/pds-handlers-infra.ts`
- `blob`:
  - `com.atproto.repo.listMissingBlobs` を実装（`cids` 入力に対して B2 実在チェックを実施）。
  - `did/repo` を使った key 候補探索で欠損 CID を返却。
  - 実装: `50-infra/cloudflare/workers/atproto/src/pds-handlers-repo.ts`
- `sync/event-stream`:
  - `subscribeRepos` / `subscribeLabels` の `cursor` 解析を強化（`seq`/`timestamp`/ISO 文字列対応）。
  - backfill クエリを timestamp カーソルで安定化。
  - live poll を timestamp ウォーターマーク方式へ変更し、広域再走査（90日窓）を廃止。
  - イベント順序を timestamp ソートで安定化。
  - `subscribeRepos` を graph query ポーリング中心から、`atproto/repo-head/*` + `atproto/commits/*` を使う commit-log 追従方式へ変更。
  - `prev` チェーンを辿って欠落 commit を補完してから配信するよう改善。
  - commit に `valueJson` を保持し、`blocks`（CBOR/base64）を可能な範囲で再構成。
  - 実装: `50-infra/cloudflare/workers/atproto/src/pds-handlers-repo.ts`
  - 実装: `50-infra/cloudflare/workers/atproto/src/pds-core.ts`
- `blob`:
  - `com.atproto.repo.listMissingBlobs` の入力正規化を強化（`cids` 文字列配列に加え、`{cid}` / `{ref.$link}` 形式も解決）。
  - `com.atproto.repo.uploadBlob` の `blob.ref.$link` を CIDv1（raw/sha2-256）へ変更。
  - B2 保存 key を `blobs/{repo}/{cid}` に統一。
  - `sync.getBlob` / `listMissingBlobs` / `listBlobs` で legacy sha256hex key 互換読取（CID⇄hex 変換）を追加。
  - 実装: `50-infra/cloudflare/workers/atproto/src/pds-app.ts`
  - 実装: `50-infra/cloudflare/workers/atproto/src/pds-handlers-repo.ts`
- `lexicon`:
  - lexicon registry generator に runtime schema map (`LEXICON_SCHEMA_BY_ID`) を追加。
  - `resolveLexicon.schemas` で生成済み実 Lexicon JSON を優先返却。
  - 実装:
    - `70-tools/scripts/contract/gen-pds-lexicon-registry.mjs`
    - `50-infra/cloudflare/workers/atproto/src/pds-lexicon-registry.gen.ts`
    - `50-infra/cloudflare/workers/atproto/src/pds-handlers-infra.ts`
- `repository` / `cryptography`:
  - `writeRecord` で commit head を生成し、`RepoHead` + B2 (`atproto/repo-head/*`, `atproto/commits/*`) へ永続化。
  - `prev/rev/seq/tsMs` を commit メタとして保持。
  - `SS_AT_SESSION_SECRET` がある場合、commit メタに署名 (`sig`) を付与。
  - `com.atproto.sync.getLatestCommit` / `getRepoStatus` で `verified.signatureValid` と `verified.chainValid` を返却。
  - `strict` / `requireVerified` 指定時、検証失敗なら `409 RepoIntegrityError` で拒否。
  - 実装: `50-infra/cloudflare/workers/atproto/src/pds-core.ts`
  - 実装: `50-infra/cloudflare/workers/atproto/src/pds-handlers-repo.ts`
- `oauth` / `cryptography`:
  - `authorizationCode` 交換で PKCE (`codeVerifier`) を必須化（保存済み `codeChallenge` がある場合）。
  - `clientId` と authorization code の整合検証を追加。
  - `AUTH_SERVICE` 障害時、`SS_AT_SESSION_SECRET` があればローカル JWT セッション発行へフォールバック。
  - refresh token でも同様にローカル検証・再発行フォールバックを追加。
  - 実装: `50-infra/cloudflare/workers/atproto/src/pds-handlers-oauth.ts`

## サマリ

- 高カバレッジ: 8/19（`xrpc`, `nsid`, `did`, `data-model`, `record-key`, `tid`, `repository`, `sync`）
- 中カバレッジ: 11/19
- 低カバレッジ: 0/19（ただし中カバレッジ領域に仕様厳密化の未完了項目あり）

現状は「AT Protocol 互換を土台に実運用できる」段階で、厳密互換（特に `lexicon`, `event-stream`, `blob` 参照整合）の仕上げが次のボトルネック。
