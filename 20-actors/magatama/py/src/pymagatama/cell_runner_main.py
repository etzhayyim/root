"""
magatama-cell-runner — Murakumo fleet cell daemon entrypoint.

Per ADR-2605192415 §7.1 (Daemon Architecture — Murakumo Fleet Tier 1 launchd 常駐).

Reads `50-infra/murakumo/fleet.toml` to determine which cells to host
on the current node, then spawns each cell as a managed subprocess.

Each cell:
  - Loads its LangGraph StateGraph (from `20-actors/magatama/cells/<name>/cell.py`)
  - Connects MstCheckpointSaver sidecar (ADR-2605191559)
  - Subscribes to MST listener for its triggering Lexicon
  - Exposes healthz HTTP endpoint
  - Participates in swarm leader election (ADR-2605191603)

Usage:
    uv run magatama-cell-runner --node naphtali
    uv run magatama-cell-runner --node naphtali --cell-only CharterAttestationRequestCell  # debug

Configuration:
    fleet.toml: 50-infra/murakumo/fleet.toml
"""

from __future__ import annotations

import argparse
import logging
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

try:
    import tomllib  # Python 3.11+
except ImportError:
    import tomli as tomllib  # type: ignore[no-redef]


REPO_ROOT = Path(__file__).resolve().parents[5]
FLEET_TOML = REPO_ROOT / "50-infra" / "murakumo" / "fleet.toml"
CELLS_DIR = REPO_ROOT / "20-actors" / "magatama" / "cells"

logger = logging.getLogger("magatama-cell-runner")

# Registry of spawned cell subprocesses (cell_name → Popen).
_cell_processes: dict[str, subprocess.Popen] = {}


def load_fleet_config(path: Path = FLEET_TOML) -> dict:
    """Load fleet.toml configuration."""
    if not path.exists():
        raise FileNotFoundError(f"fleet config not found: {path}")
    with path.open("rb") as f:
        return tomllib.load(f)


def get_node_cells(config: dict, node_name: str) -> list[str]:
    """Get list of cells assigned to the given node."""
    for node in config.get("nodes", []):
        if node["name"] == node_name:
            return node.get("cells", [])
    raise ValueError(f"node not found in fleet config: {node_name}")


def get_cell_config(config: dict, cell_name: str) -> dict:
    """Get per-cell configuration block."""
    return config.get("cells", {}).get(cell_name, {})


def _cell_dir(cell_name: str) -> Path:
    """Map CamelCase cell name to its directory.

    Delegates to pymagatama.cell_host._cell_dir for the SSoT mapping so
    runner + host stay in sync.
    """
    from pymagatama.cell_host import _cell_dir as host_cell_dir

    return host_cell_dir(cell_name)


def start_cell(node_name: str, cell_name: str, cell_config: dict, log_dir: Path) -> subprocess.Popen | None:
    """Spawn a cell as a managed subprocess via `python -m pymagatama.cell_host`.

    Per ADR-2605202200 §4. Returns the Popen handle (or None on skip).

    Each subprocess:
      - Imports cell.py from 20-actors/magatama/cells/<name>/cell.py
      - Builds CellDeps + invokes build_graph(deps)
      - Starts the trigger loop declared in fleet.toml [cells.<name>]
      - Serves /healthz on cell_config['healthz_port']
      - Listens for SIGTERM → graceful drain → exit 0
    """
    healthz_port = cell_config.get("healthz_port")
    trigger = cell_config.get("trigger", "unknown")
    listens_to = cell_config.get("listens_to", [])
    cron = cell_config.get("cron", "")
    api_port = cell_config.get("api_port", 0)

    logger.info(
        "[%s] starting cell %s (trigger=%s, healthz_port=%s)",
        node_name,
        cell_name,
        trigger,
        healthz_port,
    )

    cell_dir = _cell_dir(cell_name)
    cell_py = cell_dir / "cell.py"
    if not cell_py.exists():
        logger.warning("[%s] cell.py not found for %s (looked at %s); skipping", node_name, cell_name, cell_py)
        return None

    if healthz_port is None:
        logger.warning("[%s] %s: healthz_port not configured in fleet.toml; skipping", node_name, cell_name)
        return None

    # Build the cell_host subprocess command
    cmd = [
        sys.executable,  # the same Python interpreter that's running cell-runner
        "-m",
        "pymagatama.cell_host",
        "--cell", cell_name,
        "--node", node_name,
        "--healthz-port", str(healthz_port),
        "--trigger", trigger,
        "--log-level", logger.getEffectiveLevel().__class__.__name__ if False else os.environ.get("LOG_LEVEL", "INFO"),
    ]
    for nsid in listens_to:
        cmd.extend(["--listens-to", nsid])
    if cron:
        cmd.extend(["--cron", cron])
    if api_port:
        cmd.extend(["--api-port", str(api_port)])

    log_dir.mkdir(parents=True, exist_ok=True)
    stdout_path = log_dir / f"cell-{cell_name}.stdout.log"
    stderr_path = log_dir / f"cell-{cell_name}.stderr.log"

    # Inherit env, allow per-cell env overrides via fleet.toml [cells.<name>.env] (future)
    env = os.environ.copy()
    env.setdefault("ETZHAYYIM_NODE", node_name)
    env.setdefault("ETZHAYYIM_CELL", cell_name)

    try:
        # Open log files; subprocess writes directly (avoids parent stdio buffer)
        stdout_f = stdout_path.open("ab", buffering=0)
        stderr_f = stderr_path.open("ab", buffering=0)
        proc = subprocess.Popen(
            cmd,
            stdout=stdout_f,
            stderr=stderr_f,
            stdin=subprocess.DEVNULL,
            env=env,
            cwd=str(REPO_ROOT),
        )
    except Exception as e:
        logger.exception("[%s] failed to spawn %s: %s", node_name, cell_name, e)
        return None

    _cell_processes[cell_name] = proc
    logger.info("[%s] spawned %s pid=%d (healthz=127.0.0.1:%s)", node_name, cell_name, proc.pid, healthz_port)
    return proc


def stop_all_cells(timeout: float = 30.0) -> None:
    """Send SIGTERM to all spawned cell subprocesses, then SIGKILL after timeout."""
    if not _cell_processes:
        return
    logger.info("propagating SIGTERM to %d cell subprocesses", len(_cell_processes))
    for cell_name, proc in _cell_processes.items():
        if proc.poll() is None:
            try:
                proc.terminate()
                logger.info("  - %s pid=%d SIGTERM sent", cell_name, proc.pid)
            except Exception:
                logger.exception("  - %s SIGTERM failed", cell_name)
    deadline = time.time() + timeout
    for cell_name, proc in list(_cell_processes.items()):
        remaining = max(0.0, deadline - time.time())
        try:
            proc.wait(timeout=remaining)
            logger.info("  - %s exited with code %s", cell_name, proc.returncode)
        except subprocess.TimeoutExpired:
            logger.warning("  - %s did not exit within timeout; SIGKILL", cell_name)
            try:
                proc.kill()
            except Exception:
                pass


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="magatama-cell-runner")
    parser.add_argument("--node", required=True, help="Murakumo node name (e.g., naphtali)")
    parser.add_argument("--cell-only", default=None, help="Run only this single cell (debug)")
    parser.add_argument("--fleet-toml", default=str(FLEET_TOML), help="Path to fleet.toml")
    parser.add_argument("--health", action="store_true", help="Print health status and exit")
    parser.add_argument("--log-level", default="INFO")
    parser.add_argument(
        "--log-dir",
        default=os.environ.get("ETZHAYYIM_LOG_DIR", str(Path.home() / ".etzhayyim" / "log")),
        help="Directory for per-cell stdout/stderr log files",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=args.log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    try:
        config = load_fleet_config(Path(args.fleet_toml))
        cells = get_node_cells(config, args.node)
    except (FileNotFoundError, ValueError) as e:
        logger.error("config error: %s", e)
        return 1

    if args.cell_only:
        if args.cell_only not in cells:
            logger.error("cell %s not assigned to node %s (assigned: %s)", args.cell_only, args.node, cells)
            return 1
        cells = [args.cell_only]

    if args.health:
        print(f"node: {args.node}")
        print(f"cells assigned: {len(cells)}")
        for c in cells:
            print(f"  - {c}")
        return 0

    log_dir = Path(args.log_dir)
    logger.info("starting %d cells on node %s (log_dir=%s)", len(cells), args.node, log_dir)
    for cell_name in cells:
        cell_config = get_cell_config(config, cell_name)
        start_cell(args.node, cell_name, cell_config, log_dir)

    # Signal handlers for clean shutdown
    shutdown_requested = False

    def handle_sigterm(signum, frame):
        nonlocal shutdown_requested
        logger.info("shutdown signal received (%d)", signum)
        shutdown_requested = True

    signal.signal(signal.SIGTERM, handle_sigterm)
    signal.signal(signal.SIGINT, handle_sigterm)

    logger.info("cell-runner active on %s; awaiting signals", args.node)
    while not shutdown_requested:
        time.sleep(1)
        # Reap dead children + log; full restart policy is launchd's job
        for cell_name, proc in list(_cell_processes.items()):
            rc = proc.poll()
            if rc is not None and rc != 0:
                logger.warning("[%s] cell %s exited unexpectedly with code %s", args.node, cell_name, rc)
                del _cell_processes[cell_name]

    logger.info("cell-runner exiting on %s — propagating SIGTERM to %d cells", args.node, len(_cell_processes))
    stop_all_cells(timeout=30.0)
    logger.info("cell-runner exited on %s", args.node)
    return 0


if __name__ == "__main__":
    sys.exit(main())
