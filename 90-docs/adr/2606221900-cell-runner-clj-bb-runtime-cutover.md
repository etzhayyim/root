# ADR-2606221900 — cell-runner clj/bb runtime cutover (lite_runner.py → lite_runner.cljc)

- **Status**: Accepted (additive landed; per-node production switch = operator step)
- **Date**: 2026-06-22
- **Supersedes (runtime layer)**: the Python `lite_runner.py` supervisor (kept until per-node cutover)
- **Relates**: ADR-2606161645 (lite_runner), 2605192415 §7.1 (cell placement), 2605312345
  (kotoba Datom log = first-class state); root CLAUDE.md §"Operational code = clj/bb over the
  kotoba Datom log"

## Context

The session-long py→cljc actor wave ported the actors' **cell logic + methods** to cljc, but
the **runtime that fires them** — `50-infra/cluster/murakumo/cell-runner/lite_runner.py`, the
per-node Tier-1 cron supervisor — remained Python. The root CLAUDE.md repo-wide rule is explicit:
operational/daemon/loop code SHOULD be **clj/bb over the kotoba Datom log**, not Python. The
supervisor is exactly such a daemon. Pruning the actors' Python cell wrappers was always
"blocked on the cell_host→cljc runtime cutover" — this ADR is that cutover for the lite_runner
tier.

## Decision

`lite_runner.cljc` (ns `lite-runner`) is a **1:1 cljc/bb port** of `lite_runner.py`, landing
**additively** alongside it. Both read the SAME `cells.edn` registry.

The cutover is made **safe by construction** through one invariant:

> **The ops commit-DAG is byte-identical between the two runners.**

Each fire is recorded as a `:cell.run/*` tx on a content-addressed, append-only kotoba ops log.
The cljc port reproduces the python's `_tx_cid` (`"b" + sha256(`canonical sort-keys JSON of
`{prev,datoms}`)`)`) and its `_edn_val` line rendering exactly — verified by a **live byte-parity
test** (`test_lite_runner.cljc::live-ops-log-byte-parity` runs the real `lite_runner.py` and the
cljc on identical inputs and asserts the ops files are byte-identical). Because the audit trail is
identical, the two runners are **drop-in interchangeable**: a node can switch from python to bb (or
back) with no discontinuity in its commit-DAG.

### What the bb runner does differently (the cutover capability)

- The python runner fires a cell via `importlib.import_module(:module)` — a **Python** module.
- The bb runner fires a cell **natively as cljc**: `(require :module)` + `(requiring-resolve
  :module/:entry)` + call. This is what lets the fleet run the now-cljc cells without Python.
- For any cell **not yet ported** to cljc, the bb runner falls back to shelling the Python cell via
  `babashka.process` (a `:lang "python"` registry hint), so a node can run a mixed fleet during the
  transition. Shelling a system binary is explicitly allowed by the operational-code rule.
- A failing cell returns `:error` and never kills the supervisor (same contract as python).

### Components

- `lite_runner.cljc` — EDN registry read (native `clojure.edn`, no hand-rolled parser), cron-minute
  scheduling, the byte-parity ops commit-DAG (`tx-cid` / `append-run`), `fire-cell` (native cljc +
  python fallback + error-safe), httpkit `/healthz`, `run` loop (injectable `clock` for tests), `-main`.
- `test_lite_runner.cljc` — 6 deftests / 19 assertions: tx-cid content-addressing, cron semantics,
  cells.edn loading, native cljc fire + error-safety, chained tx log, and the **live byte-parity** check.
- `test_fixtures/sample_cell.cljc` — a trivial cljc cell (`fire` → `{:cid …}`) exercising the native path.

## Migration (additive, no big-bang)

1. **Landed (this ADR)**: the bb runner + tests, alongside the unchanged python runner. Verified:
   ops-log byte-identical, cron/load-cells parity, native cljc fire works, suite green.
2. **Per-node operator step (NOT in this PR)**: switch a node's LaunchDaemon plist
   (`com.etzhayyim.kotodama-cell-runner.plist`) from `python3 lite_runner.py …` to
   `bb --classpath … -m lite-runner …`, after a `--once` dry-run shows a byte-identical tx on that
   node's real `cells.edn`. Roll node-by-node; the python runner is the rollback.
3. **After all nodes are on bb + all their cells are cljc**: the per-actor Python cell wrappers
   (`cell.py`) and `lite_runner.py` become prunable — a later cleanup, once no node imports them.

## Consequences

- The supervisor tier now satisfies the clj/bb-over-kotoba operational-code rule; the ops log
  remains the canonical, content-addressed audit trail (unchanged format).
- The Python cell-wrapper prune is **unblocked at the lite_runner tier** (still gated on each node's
  plist switch — an operator action, deliberately not automated here).
- No charter/invariant change: this is an **実装/engineering** runtime decision (substrate-boundary
  layer), changeable without a Tier-1 amendment; the kotoba Datom log stays first-class state.

## Honest limits

- The production switch is intentionally an operator step (touching a live LaunchDaemon on the
  fleet) — not performed here. The kami/`murakumo` GPU tier and tailscale network tier are untouched.
- Healthz uses httpkit (bb-bundled) instead of python's `http.server`; the JSON body shape matches.
