# etzhayyim-project-public-kafun-bokumetsu — 花粉撲滅Fund

AI Agent (Murakumo/Qwen) が花粉症を撲滅するために自律的に調査・提案・行動・自己進化し続けるプロジェクト。

## 概要

花粉撲滅Fund は、AI エージェントが花粉症の根本的解決に向けて継続的に研究・提案・アクション生成を行う App。
初期スコープ: **東京・日本**（スギ・ヒノキ花粉）

## Domains

- `kafun-bokumetsu.etzhayyim.com` — メインドメイン
- `n97ik10n.etzhayyim.com` — nanoid ドメイン

## Architecture

- **Runtime**: kotodama runtime (TS Native)
- **nanoid**: `n97ik10n`
- **LLM**: Murakumo (`murakumo.etzhayyim.com`, model: `qwen3-vl-8b`)
- **Evolution**: W Protocol cross-actorEvolution via Connect command façade `Evolution.run` (performer-framework)
- **Matrix UI**: `@etzhayyim/appshell/matrix` (RoomList, EventTimeline, MessageComposer)
- **Storage**: kotodama WIT bindings (SQL graph)

## Components

| Component | Folder | Description |
|---|---|---|
| kafun-bokumetsu | `wasm/etzhayyim-wasm-kafun-bokumetsu-n97ik10n` | AI Agent + API + Svelte UI |

## XRPC Methods

| Method | Connect Name | Description |
|---|---|---|
| `agent.think` | `Agent.think` | 花粉撲滅について思考し洞察を生成 |
| `agent.research` | `Agent.research` | カテゴリ別の花粉撲滅研究を実行 |
| `agent.list_research` | `Agent.listResearch` | 研究成果一覧 |
| `agent.list_actions` | `Agent.listActions` | アクション一覧 |
| `agent.list_logs` | `Agent.listLogs` | エージェントログ一覧 |
| `agent.get_status` | `Agent.getStatus` | エージェント状態サマリ |
| `agent.tick` | `Agent.tick` | 自律実行 — 次のアクションを決定・実行 |
| `fund.create` | `Fund.create` | ファンド作成 |
| `fund.get` | `Fund.get` | ファンド取得 |
| `fund.list` | `Fund.list` | ファンド一覧 |
| `fund.record_fee` | `Fund.recordFee` | GCC 手数料収入記録 |
| `fund.allocate` | `Fund.allocate` | ユーザーへの分配 |
| `fund.contribute` | `Fund.contribute` | ファンドへの投入 |
| `fund.spend` | `Fund.spend` | ファンドからの支出 |
| `fund.get_allocation` | `Fund.getAllocation` | ユーザー分配残高 |
| `fund.dashboard` | `Fund.dashboard` | ダッシュボード |
| `cap.seed` | `Cap.seed` | COFOG/ISCO seed data 投入 (batch対応) |
| `cap.list_cofog` | `Cap.listCofog` | COFOG capability 一覧 |
| `cap.list_isco` | `Cap.listIsco` | ISCO capability 一覧 |
| `cap.map_action` | `Cap.mapAction` | アクション×capability マッピング |
| `cap.update` | `Cap.update` | capability ステータス更新 |
| `evolution.run` | `Evolution.run` | 自己進化セッション実行 (W Protocol cross-actorEvolution via performer) |
| `evolution.list` | `Evolution.list` | 進化ログ一覧 (agent_logs の evolution フィルタ) |

## Public Fund 経済モデル

GCC 取引手数料 10% → Public Fund → ユーザーに均等分配 (Public Asset) → ファンドにのみ投入可 → エージェントが花粉撲滅アクションに使用

## 関連プロジェクト

- `etzhayyim-project-cofog` — COFOG 分類 (215 components)
- `etzhayyim-project-open-isco` — ISCO 職業分類 (718 components)
- `etzhayyim-project-states` — 政府組織 (2770 components)
- `etzhayyim-project-open-isic` — ISIC 産業分類 (522 components)

## Frontend (Svelte)

- `svelte/` — SvelteKit SPA (SuperApp mobile-first, ActionSheet navigation)
- Pages: Dashboard (`/`), Evolution (`/evolution`), Rooms (`/rooms`), Research (`/research`), Actions (`/actions`), Capabilities (`/capabilities`), Logs (`/logs`)
- static delivery fileserver で `svelte/build/` を配信

## Autonomous Agent (CronJob)

- K8s CronJob `kafun-agent-tick` — 6時間毎に `Agent.tick` を実行 (Asia/Tokyo)
- `k8s/cronjob.yaml` で定義

## Build & Deploy

```bash
cd 60-apps/etzhayyim-project-public-kafun-bokumetsu/wasm/etzhayyim-wasm-kafun-bokumetsu-n97ik10n
cd svelte && pnpm install && pnpm build && cd ..
e7m actor build .
e7m actor deploy .
kubectl apply -f k8s/cronjob.yaml
# performer-framework の kotodama process 再起動が必要な場合:
# kubectl port-forward -n kotodama-runtime performer-framework-0 8082:8080
# curl -X POST localhost:8082/api/apps/pb/scale -H "Content-Type: application/json" -d '{"replicas":0}'
# curl -X POST localhost:8082/api/apps/pb/scale -H "Content-Type: application/json" -d '{"replicas":1}'
```

## Query Note

list/read API では `Select("col1", "col2", ...)` で必要列だけ明示指定すること。
