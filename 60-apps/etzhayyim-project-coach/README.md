# etzhayyim-project-coach

`etzhayyim-project-coach` は、coaching を目的とした AI-agent chat app です。

## 目的

- ゴール設定 (Goal)
- 現状整理 (Reality)
- 打ち手設計 (Options)
- 実行コミット (Will)

## 機能スコープ

- セッション管理 (`coach.session.*`)
- メッセージ追加 (`coach.chat.send`)
- コーチ応答生成 (`coach.chat.reply`)
- アクションアイテム管理 (`coach.action.*`)
- セッション要約 (`coach.session.summary`)

## UI/UX (Svelte)

- Svelte フロントエンド (`wasm/coach-ui-component/svelte`)
- iPad 優先 4 段階レイアウト (`<768`, `md`, `lg`, `xl`)
- Safe Area (`viewport-fit=cover`, `env(safe-area-inset-*)`)
- 44px タップターゲット / `touch-action: manipulation`
- `coach.etzhayyim.com` の `/` で公開、API は同一オリジン `/xrpc`

## API

- エンドポイント: `POST /xrpc`
- ヘルスチェック: `/healthz`, `/readyz`
- 認証コンテキスト:
  - `Authorization: Bearer <JWT>` (payload の `org_id`, `user_id` 利用)
  - または `X-etzhayyim-ORG-ID`, `X-etzhayyim-USER-ID`

## kotodama runtime 配備

```bash
kubectl apply -f 60-apps/etzhayyim-project-coach/wasm/coach-chat-mcp-component/<repo-deploy-config>
kubectl apply -f 60-apps/etzhayyim-project-coach/wasm/coach-chat-mcp-component/k8s/http-routes.yaml
kubectl apply -f 60-apps/etzhayyim-project-coach/wasm/coach-ui-component/<repo-deploy-config>
kubectl apply -f 60-apps/etzhayyim-project-coach/wasm/coach-ui-component/k8s/http-routes.yaml
```

## ルーティング

- Host: `coach.etzhayyim.com`
- HTTPRoute namespace: `edge-router-performers`
- Gateway namespace: `edge-gateway-system`
- Service namespace: `kotodama-runtime`
