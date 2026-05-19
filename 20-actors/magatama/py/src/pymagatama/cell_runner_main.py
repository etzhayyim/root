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
import signal
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


def start_cell(node_name: str, cell_name: str, cell_config: dict) -> None:
    """Start a single cell as a managed subprocess.

    In production: launches `cell.py` in a subprocess with:
      - MstCheckpointSaver sidecar connection
      - MstListener subscription
      - healthz HTTP endpoint on cell_config['healthz_port']
      - swarm heartbeat (ADR-2605191645)

    For now (scaffold): logs intent and returns.
    """
    logger.info(
        "[%s] starting cell %s "
        "(trigger=%s, healthz_port=%s)",
        node_name,
        cell_name,
        cell_config.get("trigger"),
        cell_config.get("healthz_port"),
    )

    cell_dir = CELLS_DIR / cell_name.replace("Cell", "").lower().replace("phenotypeagent", "phenotype_agent")
    # NOTE: name mapping is heuristic; production uses an explicit mapping table.

    cell_py = cell_dir / "cell.py"
    if not cell_py.exists():
        logger.warning("[%s] cell.py not found for %s (looked at %s)", node_name, cell_name, cell_py)
        return

    # TODO: spawn subprocess: uv run python -c "from <cell_dir>.cell import build_graph; ..."
    # TODO: register swarm heartbeat
    # TODO: subscribe MST listener
    # TODO: serve healthz on cell_config['healthz_port']


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="magatama-cell-runner")
    parser.add_argument("--node", required=True, help="Murakumo node name (e.g., naphtali)")
    parser.add_argument("--cell-only", default=None, help="Run only this single cell (debug)")
    parser.add_argument("--fleet-toml", default=str(FLEET_TOML), help="Path to fleet.toml")
    parser.add_argument("--health", action="store_true", help="Print health status and exit")
    parser.add_argument("--log-level", default="INFO")
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

    logger.info("starting %d cells on node %s", len(cells), args.node)
    for cell_name in cells:
        cell_config = get_cell_config(config, cell_name)
        start_cell(args.node, cell_name, cell_config)

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
        # In production: poll subprocess health, propagate swarm heartbeat, etc.

    logger.info("cell-runner exiting on %s", args.node)
    return 0


if __name__ == "__main__":
    sys.exit(main())
