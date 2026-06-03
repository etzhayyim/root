# etzhayyim-project-open-saas

`etzhayyim-project-open-saas` は、etzhayyim 系プロジェクト向けに「公開できる設計」「自己ホストできる実装」「課金と監査まで含めた SaaS 運用面」を同時に扱うための OSS SaaS スターターです。

このディレクトリには以下を含みます。

- `PROJECT.jsonld`: プロジェクト定義
- `scheduler.jsonld`: マイルストーンと blocker
- `appview/open-saas-console-os4a5s1`: static UI と配信 worker

## 目的

- OSS として監査可能な SaaS 基盤を示す
- マルチテナント、課金、監査、拡張 API を最初から設計に入れる
- Cloudflare Worker ベースで小さく開始し、将来の分割に耐える

## 実装範囲

- OSS SaaS のランディング兼オペレーション画面
- 設計ブループリントを返す JSON API
- static asset を配信する軽量 worker

## ローカル確認

ルートで次を実行します。

```sh
pnpm exec wrangler dev --config 60-apps/etzhayyim-project-open-saas/appview/open-saas-console-os4a5s1/wrangler.jsonc
```

## 補足

- 現時点では永続 DB 接続までは行わず、UI と API は設計検証用のサンプル実装です
- 本番化では tenant, subscription, usage meter, audit event を D1/Hyperdrive/graph に接続する前提です
