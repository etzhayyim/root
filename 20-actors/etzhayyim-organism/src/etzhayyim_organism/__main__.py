"""etzhayyim-organism entrypoint.

Usage:
    python -m etzhayyim_organism                 # daemon, default interval
    python -m etzhayyim_organism --once          # single tick, exit
    python -m etzhayyim_organism --interval 1800 # 30-min cadence
    python -m etzhayyim_organism --repo /repo    # explicit repo path
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

from .scheduler import run_once, run_forever


def main() -> int:
    p = argparse.ArgumentParser(prog="etzhayyim-organism")
    p.add_argument("--repo", default=os.environ.get("ETZ_REPO", "/repo"),
                   help="Path to the etzhayyim monorepo body (default: /repo or $ETZ_REPO).")
    p.add_argument("--once", action="store_true", help="Run one tick and exit.")
    p.add_argument("--interval", type=int,
                   default=int(os.environ.get("ETZ_TICK_INTERVAL", "86400")),
                   help="Seconds between ticks (default 86400 = daily).")
    p.add_argument("--source", default=os.environ.get("ETZ_SOURCE", "etzhayyim-organism pod"),
                   help="Free-text tag recorded in each observation file.")
    p.add_argument("--log-level", default=os.environ.get("ETZ_LOG_LEVEL", "INFO"))
    args = p.parse_args()

    logging.basicConfig(
        level=args.log_level.upper(),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    repo = Path(args.repo).resolve()
    if not repo.exists():
        logging.error("repo path does not exist: %s", repo)
        return 2
    if not (repo / "README.md").exists():
        logging.error("repo path missing README.md (constitutional anchor): %s", repo)
        return 2

    if args.once:
        run_once(repo, source=args.source)
        return 0
    run_forever(repo, interval_s=args.interval, source=args.source)
    return 0


if __name__ == "__main__":
    sys.exit(main())
