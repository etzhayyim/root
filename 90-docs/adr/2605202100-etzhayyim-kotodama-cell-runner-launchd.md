---
id: adr-2605202100-etzhayyim-kotodama-cell-runner-launchd
title: "ADR-2605202100: kotodama-cell-runner launchd LaunchAgent — operationalising Tier 1 常駐稼働 on the Murakumo fleet"
status: proposed
doc_type: adr
topic: kotodama-cell-runner-launchd
authoritative: true
last_verified: 2026-05-20
priority: 6.0
axis: operations
weight: 0.60
priority_note: "ADR-2605192100 / 2605192415 / 2605201400-2605201900 で religious-corp daemon + kuni-umi roadmap が spec として完成。一方 `kotodama.cell_runner_main` は CLI として存在するが、Murakumo 10 Mac mini fleet 上で 常駐起動する OS-level boot path が未整備だった。本 ADR は launchd plist template + per-host installer + uninstaller を 50-infra/cluster/murakumo/cell-runner/ に固定し、cell.py 完成度とは independent に 'fleet が常駐起動できる' 状態を closure する。`start_cell` の subprocess spawn / MST listener / healthz / swarm heartbeat は引き続き staged maturity (TODO comment 残置)。"
authoritative_for:
  - launchd plist template for kotodama-cell-runner
  - Per-host installer (`install.sh --node <tribe>`) + uninstaller
  - pyproject `[project.scripts]` kotodama-cell-runner entry
  - Per-node cell assignment readback contract (fleet.toml ↔ runner CLI)
  - 常駐起動 OS-level boot path (launchd → uv → kotodama-cell-runner)
depends_on:
  - 2605182312-local-bring-up-murakumo-gemma4
  - 2605191346-etzhayyim-vultr-free-murakumo-control-plane
  - 2605191559-ameno-mst-checkpointer-stage-2-activation
  - adr-2605192415-etzhayyim-religious-corp-daemon-architecture
related:
  - 50-infra/cluster/murakumo/cell-runner/
  - 50-infra/cluster/murakumo/litellm/
  - 50-infra/murakumo/fleet.toml
  - 40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/cell_runner_main.py
supersedes: []
superseded_by: []
---

# ADR-2605202100: kotodama-cell-runner launchd LaunchAgent

**Status**: proposed
**Date**: 2026-05-20
**Deciders**: Jun Kawasaki

# Context

ADR-2605192415 §7.1 で religious-corp daemon の Tier 1 常駐稼働 substrate を Murakumo Mac mini fleet + launchd と確定し、`kotodama.cell_runner_main` CLI を実装した。ADR-2605201400 〜 2605201900 で kuni-umi 6 cell + roadmap S0-S5 も追加した。fleet.toml には religious-corp 15 cell + kuni-umi 6 cell の per-node 割り当てが書かれている。

しかし **launchd で常駐起動する OS-level boot path が未整備**:

- `[project.scripts] kotodama-cell-runner` が pyproject.toml に存在しなかった → CLI は `uv run python -m kotodama.cell_runner_main` 経由でしか起動できない
- `com.etzhayyim.kotodama-cell-runner.plist` template が存在しなかった (ameno-daemon / litellm の plist はあるが cell-runner 用は欠落)
- per-host installer (USERNAME / REPO_PATH / NODE_NAME / UV_PATH / LOG_DIR の placeholder substitution + `launchctl load`) が無かった

結果として、ADR と fleet.toml と CLI は揃っているのに **Murakumo Mac mini に SSH して install すれば常駐起動する** という single command の operational closure が未達成だった。

本 ADR は spec の最大の operational gap を埋める small focused change。

# Decision

## 1. pyproject `[project.scripts]` entry

`40-engine/kotoba/crates/kotoba-kotodama/py/pyproject.toml` に追加:

```toml
[project.scripts]
kotodama-cell-runner = "kotodama.cell_runner_main:main"
```

これで `uv run kotodama-cell-runner --node <tribe>` が CLI として呼べる。`uv pip install -e .` した venv では `kotodama-cell-runner` が PATH に直接出る。launchd の `ProgramArguments` も `uv run` 経由で呼ぶ — `uv` が venv resolution + dependency sync を担当。

## 2. launchd plist template

`50-infra/cluster/murakumo/cell-runner/com.etzhayyim.kotodama-cell-runner.plist` を **per-host placeholder template** として固定 (literal install ファイルではない):

| Placeholder | install.sh が substitute する値 |
|---|---|
| `@@NODE_NAME@@` | Murakumo 12-tribe name (validated against allowlist) |
| `@@USERNAME@@` | `id -un` (macOS user) |
| `@@REPO_PATH@@` | repo root absolute path (default: install.sh から 4 階層上) |
| `@@UV_PATH@@` | `command -v uv` (or fail with `brew install uv` hint) |
| `@@LOG_DIR@@` | `$HOME/.etzhayyim/log` |
| `@@PYTHONPATH@@` | (default empty; future extensibility) |

Plist 内容 highlights:

- `ProgramArguments`: `uv run --project @@REPO_PATH@@/40-engine/kotoba/crates/kotoba-kotodama/py kotodama-cell-runner --node @@NODE_NAME@@ --log-level INFO`
- `RunAtLoad = true` + `KeepAlive.SuccessfulExit = false` + `KeepAlive.NetworkState = true`
- `ThrottleInterval = 15` (crash-loop respawn 制限)
- `Nice = 5` (background priority)
- Stdout / stderr separate logs in `@@LOG_DIR@@/kotodama-cell-runner.{stdout,stderr}.log`

## 3. install.sh — idempotent per-host installer

`50-infra/cluster/murakumo/cell-runner/install.sh`:

1. Validate `--node` against 12-tribe allowlist (`naphtali`/`simeon`/`judah`/`zebulun`/`levi`/`joseph`/`issachar`/`dan`/`benjamin`/`asher`)
2. Resolve repo path + `uv` binary; fail-fast if either missing
3. `uv sync` to ensure kotodama venv ready
4. Run `kotodama-cell-runner --node <tribe> --health` as pre-flight config readback (no side effects)
5. Materialise plist via bash parameter expansion (safe — no shell escape issues)
6. Assert no `@@…@@` placeholders survive (sanity gate against typos)
7. Idempotent re-install: `launchctl unload` first if already loaded
8. `install -m 0644` to `~/Library/LaunchAgents/`
9. `launchctl load`
10. Verify PID via `launchctl list`

設計判断:

- **Bash parameter expansion**, not `sed -i` — sed -i has macOS / GNU divergence + escape problems
- **Sanity gate**: substituted plist が `@@` を 1 つでも残していたら fail (typo / 未定義 placeholder の早期検出)
- **`uv sync` を pre-flight に含める** — venv 未整備で常駐起動失敗を避ける
- **Pre-flight health check**: `--health` flag が fleet.toml ↔ node assignment を read-only で出力するので、install 前に config の正しさを confirm

## 4. uninstall.sh

minimal — `launchctl unload` + `rm -f $INSTALLED_PLIST`、log は retain (post-mortem 可能性)。

## 5. README runbook

`50-infra/cluster/murakumo/cell-runner/README.md` に:

- 現状の maturity マトリックス (✅ boot path / ⚠️ cell.py 完成度 / ⚠️ start_cell scaffold 状態)
- per-node cell assignment table (post-kuni-umi S0 反映)
- install + status + reload + uninstall コマンド
- fleet roll-out 手順 (8 tribe deployed + benjamin/asher WoL pending)
- runner が **NOT yet do** している list (subprocess spawn / MstCheckpointSaver / MST listener / healthz / swarm heartbeat) — 透明性

## 6. What this ADR explicitly does NOT do

- `start_cell` の subprocess spawn 実装 — scaffold のまま、`TODO` コメント残置。Subprocess spawn は cell ごとの runtime contract (cell.py の `build_graph() → app.invoke()` 呼び出し約束) を pin する別 ADR が必要
- MstCheckpointSaver sidecar 接続 — ADR-2605191559 で別 staged
- MST listener 起動 — `kotodama.listener.MstListener` の per-cell wiring
- healthz HTTP endpoint expose
- Swarm heartbeat / leader election (ADR-2605191603) registration
- 10 / 15 religious-corp cell の cell.py 実装
- 0 / 6 kuni-umi cell の cell.py 実装
- Fleet-wide deploy script (`deploy-fleet.sh --tribes ...`)

これらは 各々 small focused change で staged にできる。本 ADR は **OS-level boot path の最後の 1 マイル** に scope を絞る。

# Consequences

## 正の効果

- ADR-2605192415 / 2605201400-1900 の "Murakumo 常駐稼働" が **spec-only から OS-level boot path 完成** に進む
- `kotodama-cell-runner` が PATH-resolvable な CLI として exposed → 開発者が `uv run kotodama-cell-runner --node naphtali --health` で local dry-run 可能
- Per-host installer + uninstaller が idempotent + sanity-gated → 10 Mac mini への fleet roll-out が機械的に再現可能
- Plist が template 形式 (`@@PLACEHOLDERS@@`) で repo に commit される → secrets / personal paths が git に漏れない (ameno-daemon plist の `YOUR_USERNAME` placeholder と同じ pattern を踏襲)
- README runbook が現状の maturity matrix を透明に示す → contributor が "何が動いて何が動いていないか" を即座に把握できる

## 負の効果 / コスト

- `start_cell` の subprocess spawn が未実装のまま起動するので、launchd は cell-runner プロセス自体は keep-alive するが **cell.py は実際には呼ばれない** — "常駐起動はしているが work は していない" 状態。この状態を README で透明に明記
- Per-host install は SSH + git pull + `./install.sh --node X` の 3 step 手動オペで、自動化 (1 command で全 8 tribe) は別 work
- pyproject `[project.scripts]` 追加は `kotodama` ホイールビルドに `kotodama-cell-runner` console-script が含まれる → 既存 kotodama 利用箇所 (worker pods / langserver etc.) の wheel rebuild が必要 (但し既存 import path は無変更)

## Constitutional 整合

- ADR-2605191346 §Tier 1 = Murakumo Mac mini only / no commercial K8s に整合 (launchd は macOS native scheduler)
- ADR-2605172000 kotoba substrate boundary に整合 (Python 側は import 0、cell.py 経由で `@etzhayyim/sdk` sidecar に delegate する設計が変わらない)
- ADR-2605192415 §7.1 launchd 常駐化 の OS-level boot path を実装
- ADR-2605173100 GitGuardian incident response の precedent (secrets を git に commit しない) を踏襲 — placeholder pattern で personal paths を template 化

# Alternatives Considered

## A. plist を 10 tribe 分 literal commit (substitution なし)

- Pro: install が `cp $TRIBE.plist ~/Library/LaunchAgents/ && launchctl load`
- Con: tribe 毎にユーザー名 / repo path が異なる場合 file ごとに divergent → personal paths が git に commit される (ADR-2605173100 lesson 違反)、tribe 毎 update が 10 file 差分
- **却下**: template + installer の pattern (litellm + ameno-daemon が踏襲) と整合

## B. ansible / pyinfra 等 configuration-management tool を導入

- Pro: 10 tribe 一括 deploy + state convergence + audit log
- Con: religious-corp の repo にとって 新規 heavyweight dependency。10 mac mini scale で over-engineering。ADR-2605191346 の "no commercial K8s / lightweight stateless" stance と semantic tension
- **却下**: bash + ssh + plist で十分。Fleet-wide deploy script (`deploy-fleet.sh`) は別 small focused work

## C. systemd を採用 (macOS でも homebrew launchd shim 経由)

- Pro: Linux site (S4 edge controller NixOS RT) と unified
- Con: Murakumo は macOS、native launchd を使うのが low-friction。Linux per-site edge controller は別 ADR で systemd 採用 (kuni-umi S4 §4 既に決定)
- **却下**: tier に応じた scheduler — Tier 1 = launchd、per-site Atama = systemd

## D. `start_cell` subprocess spawn まで本 ADR に含める

- Pro: 一気に "実際に動く" 状態へ
- Con: cell.py runtime contract (build_graph signature / startup args / shutdown semantics) を含む大きい設計 → 別 ADR に分けるのが Shannon 最適。本 ADR は OS-level boot path の小さい closure に scope 限定
- **却下**: staged maturity を維持

# Open Questions

1. **Fleet-wide deploy script** — `deploy-fleet.sh --tribes naphtali,simeon,...` を 70-tools/scripts/ or 50-infra/cluster/murakumo/cell-runner/ どちらに置くか。Decision (本 ADR): deferred、別 small ADR or PR で
2. **`start_cell` subprocess spawn** の cell.py runtime contract — `cell.py` が export すべき symbol (`build_graph` / `main` / `serve` ?)、startup args (thread_id / checkpointer config ?)、shutdown semantics。Decision: 別 ADR で staged
3. **healthz HTTP port collision** — fleet.toml で per-cell `healthz_port` を割り当て済み (13001–13022) だが、`start_cell` 実装時に複数 cell が同 node にいる場合の binding 順序 + 失敗 recovery。Decision: 別 ADR で
4. **`kotodama-cell-runner` console-script 追加による wheel rebuild scope** — 既存 kotodama 利用 worker pod は impact 0 想定だが、wheel cache invalidation 順序を CI で confirm。Decision: 本 ADR 範囲外、次回 worker pod deploy で観測

# References

- ADR-2605182312 (Murakumo Tier 1 baseline) — Mac mini fleet + always-on substrate
- ADR-2605191346 (Vultr-free Murakumo) — control plane primary = launchd
- ADR-2605191559 (MstCheckpointSaver) — cell が将来 connect する sidecar
- ADR-2605192415 §7.1 (Religious-Corp Daemon Architecture) — このADR を要求した上位 spec
- ADR-2605201400-1900 (kuni-umi S0-S5) — fleet.toml の cell 割当を生成した spec set
- ADR-2605173100 (GitGuardian incident) — placeholder pattern + no-personal-paths-in-git の precedent
- `50-infra/cluster/murakumo/cell-runner/com.etzhayyim.kotodama-cell-runner.plist` — plist template
- `50-infra/cluster/murakumo/cell-runner/install.sh` — installer
- `50-infra/cluster/murakumo/cell-runner/uninstall.sh` — uninstaller
- `50-infra/cluster/murakumo/cell-runner/README.md` — runbook + maturity matrix
- `50-infra/cluster/murakumo/litellm/` — sibling launchd service (precedent pattern)
- `40-engine/kotoba/crates/kotoba-kotodama/py/pyproject.toml` `[project.scripts]` — kotodama-cell-runner CLI entry
- `40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/cell_runner_main.py` — CLI implementation (scaffold)
- `50-infra/murakumo/fleet.toml` — per-node cell assignment SSoT
