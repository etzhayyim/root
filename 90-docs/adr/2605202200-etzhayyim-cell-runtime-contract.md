---
id: adr-2605202200-etzhayyim-cell-runtime-contract
title: "ADR-2605202200: kotodama cell.py runtime contract — build_graph + CellDeps + state_from_event + thread_id_from_event + healthz; cell-runner subprocess spawn implementation"
status: proposed
doc_type: adr
topic: cell-runtime-contract
authoritative: true
last_verified: 2026-05-20
priority: 6.5
axis: operations
weight: 0.65
priority_note: "ADR-2605202100 で cell-runner の launchd boot path を closure したが、`start_cell` は scaffold で subprocess spawn は実行されない。本 ADR は cell.py が export すべき symbol + dependency injection 約束 + MST event → state mapping + thread_id 規約 + healthz contract を pin し、`start_cell` を実装 closing する。既存 5 religious-corp cell が現状従っている convention をそのまま正典化、kuni-umi 6 cell + 残り 10 religious-corp cell が今後従う contract として確定。"
authoritative_for:
  - cell.py module-level export contract
  - CellDeps dependency injection shape
  - state_from_event + thread_id_from_event helpers
  - cell-runner subprocess lifecycle (spawn / SIGTERM / restart)
  - per-cell healthz HTTP contract
  - MST listener wiring (fleet.toml.listens_to → cell)
depends_on:
  - adr-2605192415-etzhayyim-religious-corp-daemon-architecture
  - adr-2605202100-etzhayyim-kotodama-cell-runner-launchd
  - 2605191559-ameno-mst-checkpointer-stage-2-activation
  - adr-2605171800-langgraph-mst-ipfs-l2-anchor-pipeline
  - 2605191603-ameno-swarm-leader-election
related:
  - 40-engine/kotoba/crates/kotoba-kotodama/cells/
  - 40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/cell_runner_main.py
supersedes: []
superseded_by: []
---

# ADR-2605202200: kotodama cell.py runtime contract

**Status**: proposed
**Date**: 2026-05-20
**Deciders**: Jun Kawasaki

# Context

ADR-2605202100 で launchd plist + installer + `kotodama-cell-runner` CLI を ship したが、`cell_runner_main.start_cell` は logging-only scaffold で:

- cell.py を import しない
- subprocess を spawn しない
- MST listener を subscribe しない
- healthz HTTP を expose しない
- SIGTERM 時の graceful shutdown を実装しない

つまり「launchd が cell-runner プロセスを keep-alive する」状態は実現したが、「cell-runner が各 cell.py を実際に駆動する」 までは届いていない。

既存 5 religious-corp cell.py (charter_attestation_request / land_donation_processing / ethics_content_classifier / tithe_routing / council_deliberation) は **convention で揃っている**:

- module-level docstring に ADR ref + trigger NSID + Murakumo node + effect
- `TypedDict` ベースの State
- `build_graph(checkpointer, *deps) -> CompiledStateGraph` 形式の DI signature
- node 関数群 (local pure functions or `lambda s: f(s, dep)` for injected deps)

ただし dep の **shape / 順序 / 命名** が cell ごとに ad-hoc:

- `charter_attestation_request` は `build_graph(checkpointer, llm_client, council_dispatcher, charter_registry_port)`
- `tithe_routing` は `build_graph(checkpointer, base_port, constitution_port)`
- `land_donation_processing` は別 signature

このまま `start_cell` を実装すると cell ごとに switch / case が必要で extensibility 低い。本 ADR は **dependency injection shape を contract に格上げ** + MST event handling + lifecycle を formalize する。

# Decision

## 1. Module-level export contract

各 cell.py module は次の **3 symbol** を必ず export する:

| Symbol | Type | Required? | Purpose |
|---|---|---|---|
| `build_graph` | `(deps: CellDeps) -> CompiledStateGraph` | **必須** | LangGraph StateGraph を build して compile 済み (checkpointer wired in) を返す |
| `state_from_event` | `(event_record: dict, nsid: str) -> dict` | **必須** | MST event record (`{"uri":..., "value":...}`) を初期 State dict に mapping |
| `thread_id_from_event` | `(event_record: dict, nsid: str) -> str` | **必須** | deterministic checkpoint thread id を返す (idempotency 保証) |

Optional (cell-specific extension hooks):

| Symbol | Type | Purpose |
|---|---|---|
| `on_startup` | `(deps: CellDeps) -> None` | cell launch 時に 1 回呼ばれる (e.g., warm-up cache, register ports) |
| `on_shutdown` | `(deps: CellDeps) -> None` | SIGTERM 時 graceful shutdown 用 |
| `healthz_extra` | `(deps: CellDeps) -> dict` | `/healthz` response に merge する cell-specific status |

## 2. CellDeps dependency injection shape

新規 module `40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/cell_runtime.py` を導入し、次の dataclass を定義:

```python
# kotodama/cell_runtime.py
from dataclasses import dataclass, field
from typing import Any, Optional

@dataclass(frozen=True)
class CellDeps:
    """Dependency injection container passed to every cell's build_graph.

    cell-runner instantiates one CellDeps per cell at startup and threads
    it through build_graph. Individual cells access only the fields they
    need; unused fields stay None.
    """

    # Always populated
    cell_name: str
    node_name: str
    checkpointer: Any   # MstCheckpointSaver or fallback FileCheckpointSaver

    # Substrate ports (lazy-loaded, None if not wired yet)
    sdk: Any = None              # @etzhayyim/sdk facade via subprocess RPC
    base_l2_port: Any = None     # web3.py to Base L2
    geth_private_port: Any = None  # web3.py to geth-private (chainId 260425)
    pds_client: Any = None       # atproto.PDS client

    # LLM clients (only populated for cells that need them)
    llm_primary: Any = None      # claude-sonnet-4-6 or configured primary
    llm_fallback_local: Any = None  # Murakumo Gemma fallback

    # Cell-specific extension (config from fleet.toml [cells.<name>])
    config: dict[str, Any] = field(default_factory=dict)
```

`cell-runner` populates CellDeps from:
- `cell_name`, `node_name` = CLI args / fleet.toml lookup
- `checkpointer` = `MstCheckpointSaver(socket_env="MST_CHECKPOINT_SOCKET")` if sidecar reachable, else `FileCheckpointSaver(~/.etzhayyim/checkpointer/<cell_name>/`)`
- `sdk` = SDK facade via Unix socket to `@etzhayyim/sdk` TS sidecar (ADR-2605171800 §Stage 1)
- `base_l2_port` / `geth_private_port` = `web3.HTTPProvider(...)` with chain config from `deps.toml`
- `pds_client` = `atproto.Client("https://pds.etzhayyim.com")`
- `llm_primary` / `llm_fallback_local` = LiteLLM gateway client (per ADR-2605191358) — only if cell config has `llm_primary` field
- `config` = `fleet.toml [cells.<cell_name>]` block as dict

## 3. state_from_event + thread_id_from_event

MST event record shape (per `@etzhayyim/sdk` MST subscription):

```python
{
    "uri": "at://did:web:.../com.etzhayyim.apps.etzhayyim.kuniUmi.defineDeploymentSite/3kxyz...",
    "cid": "bafyrei...",
    "collection": "com.etzhayyim.apps.etzhayyim.kuniUmi.defineDeploymentSite",
    "rkey": "3kxyz...",
    "value": { ... lexicon input shape ... },
    "indexedAt": "2026-05-20T14:30:00Z",
}
```

`state_from_event(event_record, nsid)` 規約:
- `event_record["value"]` から State dict の input field を抽出
- すべての optional field は `dict.get(...)` パターンで安全に取り出す
- MST event の場合 `event_record["uri"]` を initial state に保存 (audit trail)

`thread_id_from_event(event_record, nsid)` 規約:
- **deterministic** (同じ event は同じ thread_id) — checkpointer idempotency 保証
- default 実装: `f"{nsid}:{event_record['rkey']}"` (e.g., `"com.etzhayyim.apps.etzhayyim.kuniUmi.defineDeploymentSite:3kxyz..."`)
- cell が自前 override 可能 (e.g., 複数 NSID を 1 thread で merge する場合)

`cell_runtime.py` に default 実装を提供し、cell は override only when needed:

```python
# kotodama/cell_runtime.py (continued)

def default_state_from_event(event_record: dict, nsid: str) -> dict:
    """Default: pass through event_record['value'] + audit fields."""
    return {
        "_event_uri": event_record.get("uri"),
        "_event_cid": event_record.get("cid"),
        "_event_indexed_at": event_record.get("indexedAt"),
        **event_record.get("value", {}),
    }


def default_thread_id_from_event(event_record: dict, nsid: str) -> str:
    """Default: f'{nsid}:{rkey}'."""
    return f"{nsid}:{event_record.get('rkey', 'unknown')}"
```

## 4. cell-runner subprocess lifecycle

`cell_runner_main.start_cell` を次に拡張:

```python
def start_cell(node_name: str, cell_name: str, cell_config: dict, log_dir: Path) -> subprocess.Popen | None:
    """Spawn cell as a managed subprocess and return the Popen handle.

    Subprocess command:
        uv run python -m kotodama.cell_host \
            --cell <cell_name> \
            --node <node_name> \
            --healthz-port <port> \
            --listens-to <NSID> ... \
            --trigger <trigger_type>

    Each subprocess:
      - Imports the cell module from 40-engine/kotoba/crates/kotoba-kotodama/cells/<cell_name>/cell.py
      - Builds CellDeps + invokes cell.build_graph(deps)
      - Starts MST listener if trigger == "mst-listener"
      - Starts cron scheduler if trigger == "cron"
      - Exposes /healthz HTTP on cell_config['healthz_port']
      - Listens for SIGTERM → drains in-flight invocations → exits 0
    """
    # ... (implementation in kotodama/cell_runner_main.py — this ADR is spec)
```

`cell_host` (new) is a thin per-cell sub-process module: import target cell, build CellDeps, run the chosen trigger loop (MST listener / cron / synchronous API), serve healthz on configured port.

`cell_runner_main` (top-level) keeps the cell ↔ subprocess registry and propagates SIGTERM/SIGINT to all children.

## 5. healthz contract

Each cell subprocess exposes `GET /healthz` on `cell_config['healthz_port']` (from fleet.toml). Response shape:

```json
{
  "cell": "CharterAttestationRequestCell",
  "node": "naphtali",
  "uptime_seconds": 12345,
  "trigger": "mst-listener",
  "listens_to": ["com.etzhayyim.apps.etzhayyim.charter-attestation-request"],
  "checkpointer": {"type": "mst", "ok": true, "last_write_seconds_ago": 7},
  "swarm_role": "leader",
  "witness_min": 2,
  "cell_extra": { ... whatever healthz_extra() returns ... }
}
```

Status code:
- 200 if all dependencies healthy + in-flight queue depth < threshold
- 503 if checkpointer disconnected OR queue overflow OR cell-specific critical signal

cell-runner aggregates per-cell healthz into a single `GET /healthz` on a **node-level** port (default 12999) which sums all sub-cell statuses. Prometheus scrape via that port (per fleet.toml `[monitoring]`).

## 6. SIGTERM graceful shutdown

cell-runner receives SIGTERM (launchctl unload / manual stop) → propagates SIGTERM to all child cell processes → each child:

1. stops accepting new MST events / cron triggers
2. flushes checkpointer write queue (`checkpointer.flush()`)
3. drains in-flight `app.invoke()` loops (max 30s timeout)
4. exits 0

If a child doesn't exit within 30s, cell-runner SIGKILLs and logs the timeout to stderr.

## 7. MST listener wiring

cell with `trigger = "mst-listener"` in fleet.toml:

```python
# inside cell_host subprocess
from kotodama.listener import MstListener

listener = MstListener(
    nsids=cell_config["listens_to"],          # from fleet.toml
    pds_client=deps.pds_client,
    on_event=lambda event_record: invoke_cell(graph, event_record, cell_name),
)


def invoke_cell(graph, event_record, cell_name):
    """Invoke compiled graph with event-derived state + thread_id."""
    state = cell_module.state_from_event(event_record, event_record["collection"])
    thread_id = cell_module.thread_id_from_event(event_record, event_record["collection"])
    graph.invoke(state, config={"configurable": {"thread_id": thread_id}})


listener.run()  # blocks; signal-handler interrupts via SIGTERM
```

`MstListener` itself is a separate small module (not in this ADR — see ADR-2605171800 §Stage 1 listener spec) — for now the contract on this side is: cell-runner has a working `kotodama.listener.MstListener` that subscribes to PDS subscribeRepos for the given NSIDs and calls `on_event` for matches.

## 8. cron + synchronous-API triggers

For `trigger = "cron"`: cell_host uses `croniter` to schedule `graph.invoke({})` with `thread_id = f"{cell_name}:{utc_iso_minute()}"`.

For `trigger = "synchronous API"` (only `EthicsContentClassifierCell` currently): cell_host serves `POST /classify` on `api_port` from fleet.toml; request body becomes initial state; response is final state.

## 9. Backward compatibility for existing 5 cells

既存 5 cell.py が現状の ad-hoc `build_graph(checkpointer, *deps)` signature を使っているため、**non-breaking migration**:

- Phase A (本 ADR の immediate scope): `cell_runtime.CellDeps` を導入、`default_state_from_event` + `default_thread_id_from_event` を export、cell-runner が **adapter** を介して既存 cell を起動 (legacy signature を inspect → CellDeps から該当 field を unpack して positional 渡し)
- Phase B (本 ADR の secondary scope, follow-up PR): 既存 5 cell の `build_graph` を `def build_graph(deps: CellDeps) -> CompiledStateGraph` に refactor、`state_from_event` / `thread_id_from_event` を各 cell に追加
- Phase C: legacy adapter を削除、すべての cell が contract に従う

新規 cell (kuni-umi 6) は最初から contract に従う (= Phase B 状態でスタート)。

## 10. Implementation in this PR

本 ADR landing と同時に:

- `40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/cell_runtime.py` (新規) — `CellDeps`, `default_state_from_event`, `default_thread_id_from_event`
- `40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/cell_host.py` (新規) — per-cell subprocess entrypoint
- `40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/cell_runner_main.py` — `start_cell` 拡張で subprocess spawn を実装
- `40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/listener.py` (scaffold if not exists) — `MstListener` thin stub
- `40-engine/kotoba/crates/kotoba-kotodama/cells/<6 kuni-umi cells>/cell.py` (新規) — contract に従う stub 実装

`kotodama.listener.MstListener` は本 ADR 範囲では subscribeRepos integration は scaffold; 完全実装は ADR-2605171800 §Stage 1 listener spec 別 PR。

# Consequences

## 正の効果

- `cell_runner.start_cell` が実装される → `kotodama-cell-runner` が launchd で起動した時 cell が **actually** 動く path が成立 (依然 MstListener が scaffold だが、その上の subprocess spawn + healthz + 既存 5 cell 起動は完成)
- 新規 cell 作成 cost が単一 contract に従う 1 ファイルで済む — 18,000 UNSPSC agent fleet pattern (ADR-2605171300) と整合
- Dependency injection が `CellDeps` に集約 → testing が容易 (mock deps)
- thread_id contract が deterministic で idempotency 保証 → MST event 重複処理対策
- healthz contract が均一 → Prometheus scrape + dashboard が cell ごと switch 不要

## 負の効果 / コスト

- 既存 5 cell の `build_graph` signature を遅かれ早かれ refactor 必要 (Phase B) — backward-compat adapter で短期 mitigate
- `cell_host` subprocess 分離 = 各 cell が独立 Python process → memory overhead (10 cell node で +200-400 MB)。Mitigation: cell-runner が thin supervisor、heavy lifting は cell process 内
- `MstListener` の完全実装が別 ADR 依存 → 本 ADR landing 直後は MST listener が scaffold で実 event drive せず (cron / synchronous trigger は動く)
- `cell_runtime.CellDeps` が too-broad container (sdk + base + geth + pds + llm 等) — YAGNI risk。Mitigation: dataclass で field 全 Optional、cell は使う field のみ touch

## Constitutional 整合

- ADR-2605192415 §7.1 launchd 常駐化 を operational に成立させる
- ADR-2605172000 RW-free substrate boundary 維持 (cell.py は substrate client 直接 import せず、CellDeps.sdk 経由)
- ADR-2605191559 MstCheckpointSaver 統合 path を CellDeps.checkpointer で formalize

# Alternatives Considered

## A. cell.py を class-based protocol (`class Cell(Protocol):`) に強制

- Pro: type safety + OOP composability
- Con: 既存 5 cell が function-based、refactor cost 大。LangGraph 自身が StateGraph + node function pattern → class wrapper は冗長
- **却下**: function + DI で十分

## B. cell-runner を 1 process で all cells を asyncio coroutine として動かす (subprocess 分離せず)

- Pro: memory overhead 小、Python import 1 回
- Con: 1 cell の panic / leak が全 cell 巻き込み、healthz crash isolation がない、launchd の per-process restart 粒度が失われる
- **却下**: subprocess 分離は production hygiene、cost worth paying

## C. MstListener の完全実装も本 ADR scope に含める

- Pro: 1 ADR で end-to-end actual running 状態
- Con: ADR が肥大化 + atproto.PDS subscribeRepos integration は独立 work item、ADR-2605171800 §Stage 1 listener spec で separately
- **却下**: scope keep small — 本 ADR は contract + subprocess spawn のみ

## D. Phase B (既存 cell refactor) を別 ADR に分離

- Pro: 本 ADR が pure-additive (新規 contract + adapter)、既存 cell 触らない
- Con: legacy adapter が永久に居着くリスク → Phase B/C 確実遂行のため本 ADR に含めるのが Shannon 最適
- **採用** (mixed): adapter は本 ADR で着地、Phase B の 5 cell refactor は本 ADR の secondary scope (本 ADR PR 内 or 直後 follow-up PR、両方許容)

# Open Questions

1. **cell-host CLI module 命名** — `kotodama.cell_host` vs `kotodama.runtime.cell_host`。Decision (本 ADR): top-level `kotodama.cell_host` (consistency with `cell_runner_main`)
2. **CellDeps への new field 追加 policy** — 新規 dependency (e.g., NATS client for swarm broadcast) を追加する時 frozen dataclass の immutability を維持。Decision: 新規 field は本 ADR の `[Open Question 2 amendment]` で個別追加、dataclass version bump で track
3. **healthz aggregation node-level port** — fleet.toml `[monitoring]` で default `:12999` を pin するか per-node config 可能にするか。Decision (本 ADR): default `:12999`、`[cells.defaults]` overridable
4. **swarm_role determination timing** — ADR-2605191603 swarm leader election と cell-host startup の interaction。Decision (本 ADR): cell-host が起動時 swarm broadcast に join、`swarm_role` は eventual consistency (起動直後は `unknown` で healthz reflect)
5. **既存 5 cell の Phase B refactor PR scope** — 本 ADR PR に含めるか、直後 follow-up PR か。Decision: 本 ADR は contract + adapter + 6 kuni-umi stub のみ、Phase B は separate PR (5 cell × build_graph signature refactor は cell-by-cell review-friendly な単位)

# References

- ADR-2605192415 §7.1 (Religious-Corp Daemon Architecture — Tier 1 launchd 常駐) — 上位 spec
- ADR-2605202100 (cell-runner launchd plist + installer) — 直前 ADR、本 ADR が closure する scaffold を ship
- ADR-2605171800 §Stage 1 (MstListener spec) — `MstListener` 完全実装の依存 spec
- ADR-2605191559 (MstCheckpointSaver) — CellDeps.checkpointer 経由
- ADR-2605191603 (Swarm leader election) — healthz の `swarm_role` field
- `40-engine/kotoba/crates/kotoba-kotodama/cells/charter_attestation_request/cell.py` — convention reference
- `40-engine/kotoba/crates/kotoba-kotodama/cells/tithe_routing/cell.py` — convention reference
- `40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/cell_runner_main.py` — `start_cell` 実装対象
