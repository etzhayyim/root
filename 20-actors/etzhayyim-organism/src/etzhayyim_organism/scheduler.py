"""Tick scheduler — daemon loop with sleep-based cadence.

Default cadence: ETZ_TICK_INTERVAL seconds (default 86400 = daily, matching
the rotation chosen in ADR-2605220810 cycle 18). One-shot mode runs a single
tick and exits (used by CronJob / Job manifests).
"""

from __future__ import annotations

import logging
import os
import signal
import time
from pathlib import Path

from .cns import tick
from .emitter import emit


log = logging.getLogger("etzhayyim-organism.scheduler")


_stop = False


def _handle_signal(signum, _frame):
    global _stop
    log.info("received signal %d, stopping after current tick", signum)
    _stop = True


def run_once(repo: Path, source: str) -> Path:
    result = tick(repo)
    out = emit(result, repo / "_observations", source=source)
    log.info(
        "tick %d emitted → %s | total=%d/100 (Δ=%+d) | target=%s",
        result.cycle, out.name, result.total,
        (result.total - result.prev_total) if result.prev_scores else 0,
        result.chosen_axis,
    )
    return out


def run_forever(repo: Path, interval_s: int, source: str) -> None:
    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)
    log.info("etzhayyim-organism scheduler online (interval=%ds, repo=%s)", interval_s, repo)
    while not _stop:
        try:
            run_once(repo, source=source)
        except Exception:
            log.exception("tick failed")
        # sleep in small slices so SIGTERM is responsive
        slept = 0
        while slept < interval_s and not _stop:
            time.sleep(min(5, interval_s - slept))
            slept += 5
    log.info("scheduler exiting cleanly")
