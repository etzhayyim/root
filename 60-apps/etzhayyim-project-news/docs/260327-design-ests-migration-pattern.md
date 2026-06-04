# 260327 Design ESTS Migration Pattern

対象: `news.etzhayyim.com` の今回の編集パターンを再利用可能な手順として定義する。

## Design ESTS

`ESTS = Extract -> Scaffold -> Transfer -> Switch`

1. Extract
- 既存 guest 実装 (`main.go`) から移植対象関数を抽出する。
- 先に壊れている構文を直し、`etzhayyim build` が再現可能な状態を作る。

2. Scaffold
- TS Native の最小起動点を追加する。
- `src/app.ts` (business logic)
- `src/worker.ts` (HTTP/commit/heartbeat entry)
- `build.mjs` (esbuild)

3. Transfer
- 機能を小さく分割して `main.go` -> TS へ移植する。
- read/query (`news.list`, `news.detail`)
- reactive ingest (`handleComAtprotoSyncSubscribeReposCommit`, `processInboundArticle`)
- LLM/eval/translation (`evaluateQuality`, `translateAndPublish`)
- scheduled (`GenerateDigest`, heartbeat)

4. Switch
- build/deploy/debug を順に実行し、段階切替する。
- `pnpm run build:ts-native`
- `etzhayyim build --dir .`
- `etzhayyim deploy --dir .`
- endpoint debug (`/_heartbeat`, `/_commit`, `/xrpc/...`)
- event stream は `src/worker.ts` の `/_commit` / `/_w/commit` を TS 正系として運用する。

## 今回の適用結果

- TS Native 起動点追加: 完了
- query 系移植: 完了
- reactive ingest 移植: 完了
- heartbeat/article generation 移植: 完了
- deploy runtime の完全切替 (`magatama.jsonld` build/runtime): 未完（次段）

## Build/Deploy/Debug Standard Flow

1. Build (TS)
```bash
pnpm run build:ts-native
```

2. Build (etzhayyim)
```bash
etzhayyim build --dir .
```

3. Deploy
```bash
etzhayyim deploy --dir .
```

4. Debug
```bash
curl -sS -X POST https://news.etzhayyim.com/_heartbeat | jq
curl -sS -X POST https://news.etzhayyim.com/_commit -H 'content-type: application/json' -d '{"action":"create","collection":"com.etzhayyim.apps.news.article","rkey":"test","repo":"did:web:test","seq":1,"cid":null,"rev":null,"time":"2026-03-27T00:00:00Z"}' | jq
curl -sS -X POST https://news.etzhayyim.com/xrpc/com.etzhayyim.apps.news.news.list -H 'content-type: application/json' -d '{"limit":5}' | jq
```

## 2026-03-27 実測 (news.etzhayyim.com)

- Deploy: `etzhayyim deploy --dir 60-apps/etzhayyim-project-news/wasm/news-core-component` 成功
- `GET /health`: `ok`
- quality check 警告: `2` 件 (`/_app/meta` version / deploy_sha)

## Guardrails

- `main.go` は fallback として残す（即削除しない）。
- runtime 切替は deploy 成功 + debug 成功を条件にする。
- 変更は `Extract -> Scaffold -> Transfer -> Switch` の順序を守る。
- 1 変更ごとに build を回して回帰点を固定する。

## Reuse Rule (他 app への適用)

- 新規移植時はまずこの `Design ESTS` を docs に複製し、対象関数マップだけ差し替える。
- 先に query/read を移植し、次に reactive write を移植する。
- deploy 切替は最後にまとめて行う（途中で runtime flag を変更しない）。
