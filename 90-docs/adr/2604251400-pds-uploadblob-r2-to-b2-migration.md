---
id: adr-2604251400-pds-uploadblob-r2-to-b2-migration
title: "ADR: atproto PDS uploadBlob R2 → B2 migration (high-volume)"
status: superseded
doc_type: adr
topic: blob-storage-migration
authoritative: false
last_verified: 2026-04-25
authoritative_for: []
related:
  - adr-0043-cdn-r2-to-b2-bandwidth-alliance
  - adr-0048-kotoba-vultr-b2-primary
  - adr-2604241500-cad-bim-per-game-wasm-topology
supersedes: []
superseded_by:
  - adr-0043-cdn-r2-to-b2-bandwidth-alliance
---

> **Superseded 2026-04-25.** This ADR was drafted before the author
> noticed that ADR-0043 had already executed the same migration end
> to end (Phase 5: "R2 retired, B2 sole source of truth"). The PDS
> upload/get blob path now flows through `50-infra/cloudflare/workers/
> atproto/src/cdn-b2.ts` (B2 single-write, single-read, B2 endpoint
> us-west-004 bucket `etzhayyim-cdn`). The 6-phase progressive plan
> below describes work that is already done. ADR-0043 is the
> authoritative record. Kept for history; do not re-execute.


# Context

`50-infra/cloudflare/workers/atproto/src/core.ts:3289-3309` の `uploadBlob`
/ `uploadBlobDedup` は AT Protocol 標準準拠の SHA-256 content-addressed
blob storage を提供する: object key = `blobs/{repo}/{sha256hex}`、
binding は `CDN_R2` / `GRAPH_R2` (R2Bucket type)、bucket は CF account
の `etzhayyim-cdn`。

`[[conventions]] blob-storage-b2-only` (deps.toml, ADR-0048) で B2
を新規 actor の唯一の選択肢に定めたが、PDS は **既存の高ボリューム
バケット**:

- 推定 blob 数: 数百万 (PDS は全 actor の uploadBlob 受け口、commonCrawl
  の WET / WAT chunk + manga page + ongakuka track + 全 image embed)
- bucket size 推定: 数 TiB
- 読込 hot path: `getBlob` XRPC + `app.bsky.embed.image` 配信 + AT
  Repo MST referenced blob lookup
- 書込 hot path: 全 actor の `com.atproto.repo.uploadBlob` invocation

`bim-job` / `cad-job` / `ongakuka` / `yuubin` のような Phase 0–1 の
低ボリュームバケットと違って、**1 commit で R2 → B2 一斉切替は不可**。
ledger drift / hot fallback 必要 / 認証層もまたぐ。

# Decision

PDS uploadBlob は **dual-write + 段階的 cutover** で R2 → B2 移行する。
Phase ごとに deploy + 観測ウィンドウを設け、各 phase で rollback 可能
な状態を維持する。

## Phase 0: 設計 (本 ADR)

- 本 ADR が cutover policy + recipe SSoT
- `[[migrations]] blob-storage-r2-to-b2-code` (deps.toml) の atproto
  PDS 行を本 ADR にリンク

## Phase 1: B2 bucket + dual-read 経路 (deploy 必要、無破壊)

- B2 bucket `etzhayyim-cdn` 作成 (us-east-005, lifecycle policy = 既存
  R2 と同等: no expiry、versioning = off)
- PDS `getBlob` を **R2 first / B2 fallback** に変更:
  ```
  let buf = await env.CDN_R2.get(`blobs/${repo}/${sha}`);
  if (!buf) buf = await b2Get(env, `blobs/${repo}/${sha}`);
  if (!buf) return notFound();
  ```
- 観測: B2 fallback hit 数 = 0 を確認 (Phase 1 では B2 にはまだデータが無い)
- rollback: 1 行削除で R2-only に戻る

## Phase 2: 過去 blob の一回限りミラーコピー (R2 → B2)

- B2 Bandwidth Ally (CF R2 → B2 egress 0 円) 経由で
  `aws s3 sync s3://etzhayyim-cdn/ s3://etzhayyim-cdn/ --endpoint-url=$B2`
  相当を実行
- 推定時間: 数百万 blob × 平均 100 KB = 数百 GB → ~6–24h (B2 ingest)
- 進捗ログ: per-prefix (`blobs/did:plc:{slice}/`) で並列、各 slice
  完了で `vertex_blob_mirror_progress` 行に記録 (resumable)
- データ整合: ETag (R2 = MD5、B2 = SHA-1) ではなく **SHA-256 = object
  key** で比較 (content-addressed なので key 一致 = content 一致)
- 完了判定: B2 object count = R2 object count (B2 list-objects-v2
  + R2 list-objects のサンプル比較)

## Phase 3: Dual-write (新規 uploadBlob) 開始

- `uploadBlob` を **両方向 PUT** に変更:
  ```
  await Promise.all([
    env.CDN_R2.put(key, body, opts),
    b2Put(env, key, body, opts),
  ]);
  ```
- 失敗時: R2 PUT 成功 + B2 PUT 失敗 → log + 非ブロック (ledger は
  R2 に存在するので getBlob は成功)
- B2 PUT 失敗率を観測。> 0.1% なら Phase 4 を遅らせる
- rollback: B2 PUT 行を削除して R2-only に戻る

## Phase 4: Read 経路を B2 first に反転

- `getBlob` を **B2 first / R2 fallback** に変更:
  ```
  let buf = await b2Get(env, key);
  if (!buf) buf = await env.CDN_R2.get(key);
  ```
- 観測 1 週間: R2 fallback hit 数 = 0 を確認
- もし R2 fallback が hit する → Phase 2 のミラーが取りこぼした
  blob 存在 → 該当 key を再 sync

## Phase 5: R2 read path 削除 + B2 single-write

- `getBlob` を B2 only に
- `uploadBlob` を B2 only に (R2 PUT 削除)
- wrangler.jsonc から `r2_buckets` の `CDN_R2` / `GRAPH_R2` 削除
- types.ts の `R2Bucket` 型参照削除
- 観測 1 週間: error rate 変化なしを確認

## Phase 6: R2 bucket 廃棄

- R2 bucket `etzhayyim-cdn` を `disabled` に (read-only)
- 1 ヶ月観測 → 完全削除
- 削除前に最終 backup snapshot を別 B2 bucket
  `etzhayyim-cdn-archive-2606` に取得

# Consequences

## 良い影響

- Convention `[[conventions]] blob-storage-b2-only` を実態と一致させる
- B2 統一により egress cost (Bandwidth Ally で 0 円) + storage cost
  ($6/TiB/month vs R2 $15) で年額数千 USD 節約見込
- 障害時 BCP: B2 single-region 障害でも R2 dual-read window 中は
  fallback 可

## コスト・リスク

- Dual-write window で書込レイテンシ +20–50ms (Promise.all なので並列)
- Phase 2 ミラーコピーは 1 回限りだが手動 + 観測必要 (~24h オペ)
- Phase 3–4 で R2 と B2 の object count が一時的に不一致 (新規 blob
  だけ B2 にある状態)。`getBlob` fallback で吸収するので user-facing
  impact なし
- B2 SigV4 signing は WebCrypto HMAC-SHA256 で実装済 (host-sdk
  `b2.ts`、ADR-0048 の helper PR)。新規依存なし

## 禁止事項

- Phase 4 完了前に R2 read path を削除しない
- ミラーコピー (Phase 2) を skip して dual-write (Phase 3) だけで済ませない
  — 既存 blob が永遠に R2 にしか無い状態が続く
- B2 PUT 失敗を silent skip しない (Phase 3) — `console.error` + metric
  emit は最低限の透明性

## Rollback policy

| Phase | Rollback action |
|---|---|
| 1 | 1 行削除 (B2 fallback 削除) |
| 2 | mirror script 中断 (resumable なので安全) |
| 3 | B2 PUT 行削除 |
| 4 | get 経路を R2 first に戻す |
| 5 | wrangler に r2_buckets 復活 + binding 復活 + read/write 経路復元 |
| 6 | 不可 (bucket 廃棄後) — Phase 5 までは戻せる |

# Alternatives Considered

## A. Big-bang cutover (1 commit で R2 → B2)

- pro: 移行期間最短、コード単純
- con: ミラー前 → 過去 blob 全 404、user-facing障害確実。**却下**

## B. Symlink in R2 (R2 → B2 リダイレクト)

- pro: PDS コード変更最小
- con: R2 native binding に "external redirect" 機能がない (PUT/GET
  の binding は R2 bucket bound)、独自 fetch 層でラップしないと無理。
  結局 dual-read を書くのと同じ。**却下**

## C. Lazy migration (read-on-write only)

- 既存 blob は R2 のまま、新規だけ B2 に書く。getBlob は両方 lookup。
- pro: ミラーコピー不要
- con: 永遠に R2 と B2 の二重バケット運用が続く、cost 削減効果ゼロ、
  R2 bucket を廃棄できない。**却下**

## D. 採用案 = 6 phase progressive migration

- pro: 各 phase で rollback 可能、観測ウィンドウあり、user-facing 0 障害
- con: 完了まで ~6 週間 (各 phase 1 週間観測 + Phase 2 ミラー 24h)

採用: **D**。R2 → B2 migration は 1 PR で済むものではなく
「production storage migration」の標準形 (dual-write + dual-read +
段階的 cutover) を踏襲する。

# References

- ADR-0048 — Kotoba/Datomic Vultr B2 primary (B2 を主 object storage に
  採用した最初の判断)
- ADR 2604241500 — CAD/BIM per-game WASM topology (新規 actor の B2
  バケット命名規約 `etzhayyim-{actor}`)
- `[[conventions]] blob-storage-b2-only` (deps.toml)
- `[[migrations]] blob-storage-r2-to-b2-code` (deps.toml)
- `40-engine/kotoba/crates/kotoba-kotodama/sdk/kotodama-host-sdk/src/b2.ts` (S3 SigV4 helper)
- `50-infra/cloudflare/workers/atproto/src/core.ts:3289-3309` (uploadBlob
  / uploadBlobDedup 現状実装)
- AT Protocol blob spec: https://atproto.com/specs/repository#blobs
- Backblaze B2 Bandwidth Ally (CF R2 → B2 egress 0 円):
  https://www.backblaze.com/bandwidth-alliance.html
