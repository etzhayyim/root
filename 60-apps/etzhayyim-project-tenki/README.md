# etzhayyim-project-tenki

`etzhayyim-project-tenki` は `tenki.etzhayyim.com` 向けの天気情報表示プロジェクトです。

## 目的

- 地名検索から現在天気と短期予報を表示する
- 同一コンポーネントで Web UI と MCP API を提供する
- App 上で軽量に運用できる構成にする

## 構成

- `wasm/tenki-weather-component`
  - `GET /` : 天気表示 UI
  - `POST /api/mcp` : MCP (`tools/list`, `tools/call`)
  - 外部天気 API : Open-Meteo

## 主な MCP ツール

- `weather.search_city`
- `weather.current`
- `weather.forecast_daily`

## Deploy (wasm route only)

```bash
cd 60-apps/etzhayyim-project-tenki/wasm/tenki-weather-component
etzhayyim build
kubectl apply -f <repo-deploy-config>
kubectl apply -f k8s/http-routes.yaml
```
