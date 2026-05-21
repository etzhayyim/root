---
id: runbook-2605212130-yorishiro-cell-runner-deploy
title: "Runbook 2605212130: deploy yorishiro cells onto Murakumo cell-runner"
status: active
doc_type: how-to
topic: yorishiro-cell-runner-deploy
authoritative: true
last_verified: 2026-05-21
priority: 5.5
axis: operations
weight: 0.55
related:
  - 90-docs/adr/2605211900-etzhayyim-yorishiro-external-actor-bridge.md
  - 90-docs/adr/2605202200-etzhayyim-cell-runtime-contract.md
  - 90-docs/adr/2605202100-etzhayyim-magatama-cell-runner-launchd.md
  - 50-infra/cluster/murakumo/cell-runner/cells.toml
  - 50-infra/cluster/murakumo/cell-runner/com.etzhayyim.magatama-cell-runner.plist
  - 20-actors/magatama/py/src/pymagatama/cell_runner_main.py
---

# Runbook 2605212130: deploy yorishiro cells onto Murakumo cell-runner

**Purpose**: take a yorishiro that was generated on a workstation and
make its L2 Pregel cell actually run on a Murakumo node. After bdc0dab5
("cell-runner auto-discovery"), the cell-runner picks up every
`20-actors/magatama/cells/yorishiro_*/cells.toml.fragment` it can see
on disk — there is no manual `cells.toml` edit. The deploy is therefore
a checkout + restart sequence, nothing more.

## Pre-flight on the operator workstation

```bash
cd /path/to/etzhayyim/root
git checkout <branch with the yorishiro you want to deploy>

# Sanity:
tsx 70-tools/etzhayyim-cli/yorishiro/src/cli.ts audit   # → ok
node 70-tools/scripts/lint/no-external-purchase-purpose.mjs \
  00-contracts/lexicons/ai/etzhayyim/yorishiro/*/*.json
# regen idempotency check (Phase 5 CI gate runs the same)
for r in 70-tools/etzhayyim-cli/yorishiro/registry/*.json; do
  tsx 70-tools/etzhayyim-cli/yorishiro/src/cli.ts regen "$(basename "$r" .json)"
done
git diff --quiet -- \
  ':(glob)00-contracts/lexicons/ai/etzhayyim/yorishiro/**' \
  ':(glob)20-actors/magatama/cells/yorishiro_**' \
  ':(glob)20-actors/magatama/mcp/yorishiro-**' \
  ':(glob)skills/etzhayyim-yorishiro-**' \
  ':(glob)70-tools/etzhayyim-cli/yorishiro/registry/**' \
  && echo "[OK] regen idempotent"
```

If any of the above fails, **do not deploy** — fix the upstream and
re-PR.

## Per-Murakumo-node deploy

```bash
# (1) SSH to the node
ssh murakumo-<tribe>           # e.g. murakumo-levi

# (2) Refresh the checkout. ETZHAYYIM_ROOT is set by the launchd plist
#     (com.etzhayyim.magatama-cell-runner.plist) to the on-host clone path.
cd "$ETZHAYYIM_ROOT"
git fetch origin
git checkout main               # or the explicit deploy branch
git pull --ff-only

# (3) Install Python runtime requirements for binary-cli / browser-only
#     yorishiri. Skip whichever line doesn't apply.
uv sync --directory 20-actors/magatama/py    # langgraph + langgraph-checkpoint
# binary-cli yorishiro requirements (one per yorishiro that needs a binary)
brew install poppler                          # pdftotext yorishiro
# browser-only yorishiro requirements
20-actors/magatama/py/.venv/bin/playwright install chromium

# (4) Restart the cell-runner so load_cell_registry() re-scans the
#     yorishiro_*/cells.toml.fragment files.
launchctl unload ~/Library/LaunchAgents/com.etzhayyim.magatama-cell-runner.plist
launchctl   load ~/Library/LaunchAgents/com.etzhayyim.magatama-cell-runner.plist

# (5) Verify cell-runner picked them up.
curl -s "http://127.0.0.1:13000/healthz" | jq '.cells | map(.name) | sort'
# Expected output includes every Yorishiro<Name>Cell for which the
# fragment is on disk AND the cell module imports cleanly.
```

The cell-runner's `healthz` (default port 13000) only lists cells whose
`importlib.import_module(...)` succeeded. If a yorishiro is missing
from the catalog, check the runner log:

```bash
tail -50 /var/log/etzhayyim/cells/cell-runner.stderr.log | \
  grep -E "(yorishiro|import|module)"
```

Typical failures:

| Symptom | Likely cause | Fix |
|---|---|---|
| `import failed: No module named 'playwright'` | browser-only yorishiro on a node without Playwright | run `playwright install chromium` |
| `binary not found on PATH: pdftotext` | binary-cli yorishiro on a node without the binary | install via the kami's package manager |
| `import failed: No module named 'langgraph'` | venv not synced after fresh checkout | `uv sync --directory 20-actors/magatama/py` |
| Healthz lists fewer cells than fragment files on disk | `_walk_no_funcs` / `__init__.py` problem | verify the cell dir has `__init__.py` and `cell.py` |

## Per-yorishiro post-deploy probe

For each yorishiro that exposes an XRPC trigger, the gateway dispatch
target is `ai.etzhayyim.yorishiro.<name>.<op>`. Smoke-call it via
`magatama-host-sdk`'s in-cluster client, or by invoking the cell's
`build_graph()` directly:

```bash
# (on the Murakumo node, in a python3 REPL with the venv active)
import sys
sys.path.insert(0, "20-actors/magatama/cells")
from yorishiro_bls.cell import build_graph, state_from_event
graph = build_graph()
out = graph.invoke(state_from_event({
    "op": "fetchTimeseries",
    "params": {},
    "body": {
        "seriesid": ["LNS14000000"],
        "startyear": "2024",
        "endyear": "2024",
    },
}))
print(out["http_status"], len(out.get("json", {})), out.get("error"))
```

A clean run prints `200 <nonzero> None`.

## Rollback

The cell-runner does not retain in-memory state across launchctl
unload/load, so rollback is `git checkout <previous>` + restart. No
schema migration is required; yorishiri are stateless apart from the
language-graph checkpointer (`ameno` / `mst-projector` checkpointer
sidecar — ADR-2605191559) which is keyed by `thread_id_from_event` so
duplicate events deduplicate naturally.

## See also

- ADR-2605211900 — yorishiro architecture
- ADR-2605202100 — launchd plist (the actual restart unit)
- ADR-2605202200 — cell.py runtime contract
- ADR-2605191559 — MST checkpointer (state retention across restarts)
- `20-actors/magatama/py/src/pymagatama/cell_runner_main.py` — runner source
