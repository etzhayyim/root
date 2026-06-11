# etzhayyim-project-gakko

kotodama runtime 上で稼働する LMS (Learning Management System) です。以下を提供します。

- コース管理 (`lms.course.*`)
- 受講登録管理 (`lms.enrollment.*`)
- 学習進捗管理 (`lms.progress.*`)
- ISCO / CPC / APQC の分類連携 (`lms.taxonomy.lookup`)

## アーキテクチャ

- 実行基盤: kotodama runtime (`core.kotodama-runtime.dev/v1alpha1` App)
- API エントリ: `POST /xrpc`
- ヘルスチェック: `/healthz`, `/readyz`
- ルーティング: Gateway API `HTTPRoute` (`edge-router-performers` namespace)

## 分類連携

環境変数で外部連携先を指定します。

- `GAKKO_ISCO_ENDPOINT` (例: `https://<nanoid>.etzhayyim.com/xrpc`)
- `GAKKO_CPC_ENDPOINT` (例: `https://<nanoid>.etzhayyim.com/xrpc`)
- `GAKKO_APQC_ENDPOINT` (例: `https://<nanoid>.etzhayyim.com/xrpc`)
- `GAKKO_TAXONOMY_TIMEOUT_MS` (default: `5000`)

`lms.taxonomy.lookup` は framework (`isco|cpc|apqc`) と code/query を受け取り、指定 endpoint へ連携します。

## デプロイ

```bash
kubectl apply -f 60-apps/etzhayyim-project-gakko/wasm/gakko-lms-mcp-component/<repo-deploy-config>
kubectl apply -f 60-apps/etzhayyim-project-gakko/wasm/gakko-lms-mcp-component/k8s/http-routes.yaml
```

## コンテナイメージ

- `ghcr.io/etzhayyim/gakko-lms-mcp-component:kotodama-runtime-0.1.0`
