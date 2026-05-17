# gftd Hook Integration

`gftd build` と `gftd deploy` は `gftd.json` の `hooks[]` を読む。

- `post_build`: component build 成功後に dispatch
- `post_deploy`: deploy 完了後に dispatch
- transport は現時点で `http` を標準実装
- payload schema は `gftd:wproto/hook-envelope@v1`

## Design

- `deps.etzhayyim.com` 固定の分岐は置かない。hook は generic event sink として扱う
- app metadata, artifact metadata, WIT import/export, repo context を 1 つの envelope にまとめる
- `wproto` 前提で、hook 側はこの envelope を ingest して index/update/publish を行う
- 将来 hook が増えても `gftd build` / `gftd deploy` 本体は event dispatch のみを担う

## gftd.json

```json
{
  "name": "wit-deps-visualizer",
  "project": "ai-gftd-project-deps",
  "nanoid": "depsv1",
  "runtime": "worker",
  "hooks": [
    {
      "name": "deps",
      "kind": "http",
      "events": ["post_build", "post_deploy"],
      "url": "https://deps.etzhayyim.com/api/hooks/component",
      "auth_env": "GFTD_DEPS_TOKEN",
      "auth_scheme": "Bearer",
      "timeout_sec": 15,
      "headers": {
        "X-GFTD-Source": "gftd"
      }
    }
  ]
}
```

## Envelope

hook payload には少なくとも次が入る。

- `schema`, `generated_at`, `event`
- `app.name`, `app.nanoid`, `app.project`, `app.app_id`, `app.runtime`, `app.type`
- `artifacts.component_wasm`, `artifacts.component_sha256`, `artifacts.smoke_url`
- `wit.world`, `wit.imports`, `wit.exports`
- `context.git_root`, `context.relative_dir`, `context.magatama_toml`, `context.gftd_json`
- `cache.urls`, `cache.status`, `cache.message`, `cache.purged_at`

`wit.imports` / `wit.exports` は `wasm-tools component wit` から抽出する。hook consumer はこれを dependency graph, capability registry, governance checks, deploy-side indexing に使える。
`cache` は workflow/activity 向けの purge metadata。`post_build` では purge plan、`post_deploy` では purge attempt の結果が入る。

## Operational Notes

- hook failure は build/deploy failure として返す
- `auth_env` 指定時は空 env をエラーにする
- `events` 未指定時は全 event を受ける
- `component.wasm` が無い場合でも hook 自体は走るが、artifact hash と WIT refs は空になる
- cache purge は best-effort。Cloudflare token / 権限不足時も deploy 自体は継続し、結果は `cache.status` / `cache.message` に残す
- Rust guest build cache は repo root `.cargo-target/` を標準とする。`gftd build` は `CARGO_TARGET_DIR` または最寄り `.cargo/config(.toml)` を見て実際の Cargo target dir を解決する
- Rust component 出力パスの例は repo 標準では `.cargo-target/wasm32-wasip2/release/*.wasm`。component 配下の `target/` は legacy local cache とみなす

## Local Agent Organism Status

`gftd agent organism status` は local artificial organism / active inference loop の status entrypoint。

```bash
gftd agent organism status
gftd agent organism status --json
gftd agent organism status --web
gftd agent verify --did did:web:kami-agent.etzhayyim.com
```

- default は `magatama-agent-status` を passthrough し、health / viability / process / knowledge graph fitness を表示する
- `--json` は automation 向け。例: `gftd agent organism status --json | jq '.healthEvaluation'`
- `--web` は `http://127.0.0.1:8765` を確認し、未起動なら `magatama-agent-status-web` を foreground 起動する
- `verify` は ERC-8004 token、IPFS registration、ActorRuntimeRegistry artifact/receipt、RisingWave projection、organism status をまとめて検証する
- `AGENT_DAEMON_ENV_FILE` 未指定時は repo root の `ops/local-agent/agent-daemon.env` を読む

## CI: deps score gate (`gftd build`)

`gftd build` には `deps.etzhayyim.com` の app-mesh/governance スコア評価を組み込める。
評価モデルは 2 段階で、主評価軸は `app-to-app provider/export link`、副次評価軸は `runtime host link`。
これに `RACI` / `RBAC` / `capabilities` を加味し、`DoDAF v2` と `NIST CSF v2` の準拠指標を合成して overall を算出する。

```bash
gftd build --deps-score --deps-score-min 40
```

- `--deps-score`: build 後に `deps.etzhayyim.com` を評価
- `--deps-score-min`: 最低スコア閾値。下回ると build を fail
- `--deps-score-url`: 評価先 URL（default: `https://deps.etzhayyim.com/`）
- `--deps-score-timeout-sec`: HTTP timeout 秒数

build ログには以下を表示する:
- `overall score`
- `build linker score` (`app mesh` / provider-export link score)
- `runtime linker score` (runtime host-link baseline)
- `app mesh score` (app-to-app provider/export coverage)
- `runtime host score` (`wasi:` / `magatama:` host coverage only)
- `link blend score` (`50% build_linker + 20% runtime_linker + 30% app_mesh`)
- `DoDAF v2 score`
- `NIST CSF v2 score`

`runtime_linker_score` と `runtime_host_score` は別物。
- `runtime_linker_score`: runtime で解決される link 全体。host link に加えて app2app link も含む
- `runtime_host_score`: `wasi:` / `magatama:` の host-provided surface だけを見る

## deps audit (`gftd deps audit`)

full-audit を 1 コマンドで実行したい場合は `gftd deps audit` を使う。
このコマンドは `deps.etzhayyim.com/api/hooks/component` へ `manual_refresh` を送信し、
待機後に score 評価を取得する。

```bash
gftd deps audit --full-audit --top 20
gftd deps audit --format json > deps-audit.json
```

## deps export (`gftd deps export`)

`gftd deps` を `ai-gftd-project-deps` の正規 export 入口として使う。
このコマンドは graph を更新し、`wit-graph.json` に加えて `deps-score.json`, `deps-audit.json`, `wit-quality-audit.json`, `wit-quality-improvement-plan.md` を同じ data ディレクトリへ出力する。
評価の中心は `wasmtime` host linker そのものではなく、`App` 間の provider/export link が成立しているかどうかに置く。`runtime linker` は `wasi:` / `magatama:` host 側の健全性を測る補助軸として扱う。

```bash
gftd deps export --project-dir 60-apps/ai-gftd-project-deps/wasm/wit-deps-visualizer/svelte
```

`deps.etzhayyim.com` の配信方針は static asset を正とする。

- export 後に `src/lib/data/*` を `static/deps/*` へ同期する
- UI は `/api/deps/graph` を lazy fetch する
- `/api/deps/graph`, `/api/deps/score`, `/api/deps/audit` は server bundle に JSON を埋め込まず、`/deps/*.json` へ redirect する
- snapshot 配信だけが要件なので、`Durable Object` や `KV` は使わない
