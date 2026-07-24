# kotodama-cell-runner — Murakumo Mac-mini Resident Daemon

Per [ADR-2605192415](../../../../90-docs/adr/2605192415-etzhayyim-religious-corp-daemon-architecture.md) §7.1 (Religious-Corp Daemon Architecture — Tier 1 launchd 常駐).

Each Mac mini in the [etzhayyim Murakumo fleet](../../../murakumo/fleet.toml) runs `kotoba-kotodama-cell-runner` as a **launchd LaunchAgent**. The runner reads `fleet.toml` to decide which religious-corp + kuni-umi cells to host on its node and supervises them as managed subprocesses.

## Status (2026-05-20)

- ✅ launchd plist template + install / uninstall scripts (this directory)
- ✅ `kotoba-kotodama-cell-runner` CLI shipped (`40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/cell_runner_main.py` + `[project.scripts]` entry in pyproject.toml)
- ✅ 5 / 15 religious-corp cells have `cell.py` (CharterAttestationRequest / LandDonationProcessing / EthicsContentClassifier / TitheRouting / CouncilDeliberation)
- ⚠️ 10 / 15 religious-corp cells still scaffold-only (no `cell.py`)
- ⚠️ 0 / 6 kuni-umi cells have `cell.py` ([ADR-2605201400](../../../../90-docs/adr/2605201400-etzhayyim-kuni-umi-planetary-infra-fleet.md) and S1–S5 are spec-only)
- ⚠️ `start_cell` in `cell_runner_main.py` is a logging-only scaffold — does not yet spawn subprocesses, register MST listener, or expose healthz

So this directory ships **the OS-level boot path** (launchd → uv → kotodama-cell-runner). What the runner *does* once running is a separate maturity track tracked in ADR-2605192415 §S0–S11 roadmap.

## Files

| File | Purpose |
|---|---|
| [`com.etzhayyim.kotodama-cell-runner.plist`](com.etzhayyim.kotodama-cell-runner.plist) | launchd plist template with `@@PLACEHOLDERS@@` |
| [`install.sh`](install.sh) | Per-host installer — substitutes placeholders, loads via launchctl |
| [`uninstall.sh`](uninstall.sh) | Unload + remove plist |

## Install (run on the target Mac mini)

```bash
# Prereq: brew install uv (one-time)
brew install uv

# Pull the repo (one-time)
git clone https://github.com/etzhayyim/root.git ~/etzhayyim-root
cd ~/etzhayyim-root

# Install for this tribe
./50-infra/cluster/murakumo/cell-runner/install.sh --node naphtali
```

The installer:
1. Validates `--node` is one of the 12 tribes (`naphtali` / `simeon` / `judah` / `zebulun` / `levi` / `joseph` / `issachar` / `dan` / `benjamin` / `asher`)
2. Resolves repo path (default = 4 levels up from the script)
3. Resolves the `uv` binary
4. Runs `uv sync` to ensure the kotodama venv is ready
5. Runs `kotoba-kotodama-cell-runner --node <NODE> --health` as a pre-flight check (config readback)
6. Materialises the plist with placeholders substituted (no `@@…@@` survives)
7. Writes `~/Library/LaunchAgents/com.etzhayyim.kotodama-cell-runner.plist`
8. Issues `launchctl load`
9. Verifies the service registered a PID

## Per-node cell assignment

The runner reads [`50-infra/murakumo/fleet.toml`](../../../murakumo/fleet.toml) to determine which cells to host. Current assignments (post-kuni-umi S0):

| Node | Cells (current) |
|---|---|
| `naphtali` | CharterAttestationRequestCell / CharterAttestationFinalizationCell / CharterRehabilitationCell / **SiteSurveyCell** (kuni-umi P1) |
| `simeon` | LandStewardshipMonitoringCell / **CommissioningCell** (kuni-umi P4) |
| `judah` | LandDonationProcessingCell / LandDisputeResolutionCell / StewardSuccessionCell |
| `zebulun` | EligibilityCell / TreasuryRebalanceCell / PublicFundGrantCell / TitheRoutingCell / **DeploymentPlanningCell** (kuni-umi P2) |
| `levi` | AdherentAttestationCell / CouncilLevelAdvancementCell / CouncilDeliberationCell / **AuditWitnessCell** (kuni-umi) |
| `joseph` | PhenotypeAgent (shard 0) / **ConstructionOrchestrationCell** (kuni-umi P3) |
| `issachar` | PhenotypeAgent (shard 1) |
| `dan` | PhenotypeAgent (shard 2) / **DecommissionCell** (kuni-umi) |
| `benjamin` | ForceAuthorizationCell / ForceLogMonitoringCell / EthicsContentClassifierCell |
| `asher` | replica / failover |

To change assignments, edit `fleet.toml` and reload:

```bash
launchctl unload ~/Library/LaunchAgents/com.etzhayyim.kotodama-cell-runner.plist
launchctl load   ~/Library/LaunchAgents/com.etzhayyim.kotodama-cell-runner.plist
```

## Operational commands

| What | Command |
|---|---|
| Status | `launchctl list \| grep kotodama-cell-runner` |
| stdout | `tail -f ~/.etzhayyim/log/kotodama-cell-runner.stdout.log` |
| stderr | `tail -f ~/.etzhayyim/log/kotodama-cell-runner.stderr.log` |
| Manual run | `cd 40-engine/kotoba/crates/kotoba-kotodama/py && uv run kotoba-kotodama-cell-runner --node <NODE>` |
| Health probe (offline) | `cd 40-engine/kotoba/crates/kotoba-kotodama/py && uv run kotoba-kotodama-cell-runner --node <NODE> --health` |
| Reload | `launchctl unload ~/Library/LaunchAgents/com.etzhayyim.kotodama-cell-runner.plist && launchctl load ~/Library/LaunchAgents/com.etzhayyim.kotodama-cell-runner.plist` |
| Uninstall | `./uninstall.sh` |

## Fleet roll-out (10 Mac minis)

The deploy script in [`orgs/etzhayyim/com-etzhayyim-first-breath/deploy.sh`](https://github.com/etzhayyim/com-etzhayyim-first-breath/blob/main/deploy.sh) (used for the cell-fleet heartbeat anchor per ADR-2605171800) is the closest existing pattern, but it deploys a different daemon. For kotodama-cell-runner, the per-node sequence is:

```bash
# From a control machine with ssh access to the tribe Mac mini:
ssh <tribe>nomac-mini.local
# (on the mac mini)
cd ~/etzhayyim-root  # or wherever your checkout lives
git pull
./50-infra/cluster/murakumo/cell-runner/install.sh --node <tribe>
exit
```

Repeat for each of the 8 currently-deployed tribes (`benjamin` / `asher` pending WoL per `fleet.toml`).

A fleet-wide deploy script (`./deploy-fleet.sh --tribes naphtali,simeon,judah,zebulun,levi,joseph,issachar,dan`) is a useful next addition but is out of scope here.

## What the runner does NOT yet do

The runner's `start_cell` function (in [`40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/cell_runner_main.py`](../../../../40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/cell_runner_main.py)) currently:

- ✅ Reads `fleet.toml`
- ✅ Maps node name → assigned cells
- ✅ Maps cell name → directory under `40-engine/kotoba/crates/kotoba-kotodama/cells/`
- ✅ Checks `cell.py` existence + logs warning if missing
- ❌ Does NOT spawn the cell as a subprocess
- ❌ Does NOT connect MstCheckpointSaver sidecar
- ❌ Does NOT subscribe MST listener for the cell's NSID
- ❌ Does NOT expose `/healthz` HTTP
- ❌ Does NOT register swarm heartbeat

Closing each `❌` is its own bounded change. The `TODO` comments in `start_cell` mark the path.

## Substrate boundary reminder

Per [ADR-2605172000](../../../../90-docs/adr/2605172000-etzhayyim-kotoba-substrate.md) the runner and all cells must **only** import substrate clients via `@etzhayyim/sdk` (TS sidecar) — Python side stays kotoba / DB-free per ADR-2605191559.

## See also

- [ADR-2605192415](../../../../90-docs/adr/2605192415-etzhayyim-religious-corp-daemon-architecture.md) — Master design (Tier A / B / C, Murakumo placement)
- [ADR-2605182312](../../../../90-docs/adr/2605182312-local-bring-up-murakumo-gemma4.md) — Murakumo Tier 1 baseline
- [ADR-2605191346](../../../../90-docs/adr/2605191346-etzhayyim-vultr-free-murakumo-control-plane.md) — Murakumo is the only Tier-1 substrate (no commercial K8s)
- [ADR-2605191559](../../../../90-docs/adr/2605191559-ameno-mst-checkpointer-stage-2-activation.md) — MST checkpoint pipeline
- [`50-infra/cluster/murakumo/litellm/`](../litellm/) — sibling launchd service (LiteLLM gateway)
- [`orgs/etzhayyim/com-etzhayyim-first-breath/deploy.sh`](https://github.com/etzhayyim/com-etzhayyim-first-breath/blob/main/deploy.sh) — existing per-tribe deploy script (for the heartbeat anchor daemon, ADR-2605171800)

## lite_runner — pure-stdlib node cell-runner (ADR-2606161645)

`lite_runner.py` is the **deployable** Tier-1 supervisor: same `cells.edn` registry, but **only
system `python3`** — no `uv` / venv / monorepo / DB migrations (which blocked the canonical
`kotoba-kotodama-cell-runner` on the unprovisioned fleet Macs, whose cells are pure-stdlib).

- **One supervisor per node, not one daemon per actor.** It reads `cells.edn`, fires every CRON
  cell assigned to `$ETZHAYYIM_NODE_NAME` whose minute matches, records each fire as a
  `:cell.run/*` datom on a local kotoba ops commit-DAG, and serves a healthz JSON.
- **Runs as ONE system LaunchDaemon** (`com.etzhayyim.cell-runner.daemon.plist`, `KeepAlive=true`
  → crash-restart; system domain → no Aqua GUI session needed). It supersedes the per-actor
  `*-heartbeat` daemons.
- **Layering (honest):** tailscale = network · `kotoba` = state/runtime (`kotoba server` :8077) ·
  `murakumo` (`gftd-murakumo`) = GPU/MLX inference cluster · lite_runner = cron supervision. None
  duplicates another.

```bash
bb test:cell-runner                            # offline tests (11)
bb murakumo:deploy --node issachar --dry-run   # show the plan
bb murakumo:deploy --node issachar             # stage lite_runner + cells.edn + assigned actors → install daemon (Tailscale SSH + sudo)
```

Staged on each node under `~/.etzhayyim/`: `lite_runner.py`, `cells.edn`, `cells/<actor>/…`. LIVE
on **issachar** since 2026-06-16 (healthz 13081 → `cells:[SukashiObservatoryHeartbeatCell]`).

### bb runtime cutover (ADR-2606221900)

`lite_runner.cljc` (ns `lite-runner`) is the **clj/bb 1:1 port** of `lite_runner.py`, per the
repo-wide rule that operational/daemon code be clj/bb over the kotoba Datom log. The daemon plist
(`com.etzhayyim.cell-runner.daemon.plist`) now invokes the **bb** runner:

```
@@BB_PATH@@ --classpath @@HOME@@/.etzhayyim -m lite-runner --node @@NODE@@ --registry … --cells-root … --healthz-port 13081
```

Why the cutover is **safe** (drop-in, node-by-node, reversible):

- **Byte-identical ops log.** The bb runner reproduces the python runner's content-addressed
  commit-DAG exactly (same `tx-cid` = `"b"+sha256(`canonical JSON`)`, same `_edn_val` line
  rendering) — `test_lite_runner.cljc::live-ops-log-byte-parity` runs the **real** `lite_runner.py`
  + the cljc on identical inputs and asserts byte-equality. So a node's audit trail is continuous
  across the switch.
- **Auto-fallback for existing cells.** `fire-cell` tries the cljc ns natively, and if it is simply
  not on the classpath (a python-only cell like the LIVE `sukashi.cell`), it **shells the python
  module exactly as the python runner did** — no `cells.edn` re-annotation needed. cljc cells fire
  natively; `:lang "python"` forces the shell explicitly. Verified end-to-end: the bb runner fires a
  python cell via fallback and records `:ok` to the ops log.
- **`@@BB_PATH@@` is an absolute path.** launchd has a minimal PATH, so a bare `bb` exits 127
  (bb-not-found). `deploy_node.py --bb-path` defaults to the Apple-silicon brew location
  (`/opt/homebrew/bin/bb`).

**Per-node operator runbook** (run from a control machine with Tailscale SSH + sudo to the node —
the live `launchctl` reload happens ON the fleet Mac, not from CI):

```bash
# 1. stage the bb runner + install the bb plist (also keeps lite_runner.py as rollback)
python3 deploy_node.py --node issachar --dry-run     # review the plan
python3 deploy_node.py --node issachar               # stage + bootstrap the bb daemon

# 2. validate the switch (a once-run must fire + record byte-identically)
ssh issachar@<ip> 'bb --classpath ~/.etzhayyim -m lite-runner --node issachar \
  --registry ~/.etzhayyim/cells.edn --cells-root ~/.etzhayyim/cells \
  --ops-log ~/.etzhayyim/cells/cell-ops.kotoba.edn --once'
curl -s 127.0.0.1:13081 | python3 -m json.tool       # healthz

# 3. rollback (if needed): revert the plist ProgramArguments to python3 ~/.etzhayyim/lite_runner.py
```

The bb runner + plist + `deploy_node.py` cutover machinery land here; the actual per-node
`launchctl bootstrap` on each live fleet Mac is the operator step (those nodes are reachable only
over the fleet's Tailscale SSH, not from this repo's CI).
