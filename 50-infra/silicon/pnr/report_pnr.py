#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Per /CHARTER-RIDER.md v2.0
#
# Extract the headline P&R + timing metrics from the latest OpenLane2 run of a
# design and print a compact summary (clock period set, worst slack → achieved
# f_max, area/utilization, DRC/LVS, antenna). Reads the final metrics.json that
# OpenLane writes per run.

from __future__ import annotations

import glob
import json
import os
import sys


def latest_metrics(design_dir: str) -> tuple[str, dict]:
    runs = sorted(glob.glob(os.path.join(design_dir, "runs", "*")))
    if not runs:
        raise SystemExit(f"no runs under {design_dir}/runs")
    run = runs[-1]
    # OpenLane2 writes the cumulative metrics to runs/<tag>/final/metrics.json
    cands = [
        os.path.join(run, "final", "metrics.json"),
        os.path.join(run, "metrics.json"),
    ]
    for c in cands:
        if os.path.exists(c):
            with open(c) as f:
                return run, json.load(f)
    # Fallback: deepest metrics.json in the run
    ms = sorted(glob.glob(os.path.join(run, "**", "metrics.json"), recursive=True))
    if ms:
        with open(ms[-1]) as f:
            return run, json.load(f)
    raise SystemExit(f"no metrics.json under {run}")


def g(m: dict, *keys):
    for k in keys:
        if k in m and m[k] is not None:
            return m[k]
    return None


def main(design_dir: str):
    run, m = latest_metrics(design_dir)
    print(f"# P&R report — {os.path.basename(design_dir)}")
    print(f"run: {os.path.relpath(run)}")

    # Clock period actually constrained (ns) — read from config.json (metrics
    # does not always carry it back).
    period = g(m, "clock__period", "design__clock_period", "ckt__clock_period")
    if period is None:
        cfg = os.path.join(design_dir, "config.json")
        if os.path.exists(cfg):
            with open(cfg) as f:
                period = json.load(f).get("CLOCK_PERIOD")

    def fmax(wns):
        if period is None or wns is None:
            return None
        t = float(period) - float(wns)
        return 1000.0 / t if t > 0 else None

    print("\n## Timing (post-route, parasitic-aware STA)")
    if period is not None:
        print(f"- clock period constrained: {period} ns "
              f"({1000.0/float(period):.0f} MHz target)")
    # Per-corner setup slack → f_max = 1/(T - WNS).
    corners = [
        ("typical  tt_025C_1v80", "timing__setup__ws__corner:nom_tt_025C_1v80"),
        ("fast     ff_n40C_1v95", "timing__setup__ws__corner:nom_ff_n40C_1v95"),
        ("slow     ss_100C_1v60", "timing__setup__ws__corner:nom_ss_100C_1v60"),
    ]
    for label, key in corners:
        wns = g(m, key)
        if wns is not None:
            fm = fmax(wns)
            fmstr = f" → f_max ≈ {fm:.0f} MHz" if fm else " (does not close at this T)"
            print(f"- setup WNS [{label}]: {float(wns):+.3f} ns{fmstr}")
    worst = g(m, "timing__setup__ws")
    if worst is not None:
        print(f"- worst-corner setup WNS (sign-off): {float(worst):+.3f} ns")
    hold = g(m, "timing__hold__ws")
    if hold is not None:
        print(f"- worst-corner hold WNS: {float(hold):+.3f} ns "
              f"({'OK' if float(hold) >= 0 else 'VIOLATION'})")

    print("\n## Area / utilization")
    for label, keys in [
        ("die area (µm²)", ("design__die__area",)),
        ("core area (µm²)", ("design__core__area",)),
        ("cell area (µm²)", ("design__instance__area", "design__core__area__stdcell")),
        ("std cells", ("design__instance__count__stdcell", "design__instance__count")),
        ("utilization (%)", ("design__instance__utilization", "design__instance__utilization__stdcell")),
    ]:
        v = g(m, *keys)
        if v is not None:
            print(f"- {label}: {v}")

    print("\n## Sign-off")
    for label, keys in [
        ("DRC violations", ("magic__drc_error__count", "route__drc_errors")),
        ("LVS errors", ("magic__illegal_overlap__count", "lvs__total__errors")),
        ("antenna violations", ("route__antenna_violation__count",)),
        ("wirelength (µm)", ("route__wirelength",)),
    ]:
        v = g(m, *keys)
        if v is not None:
            print(f"- {label}: {v}")

    # GDS path
    gds = sorted(glob.glob(os.path.join(run, "final", "gds", "*.gds")))
    if gds:
        print(f"\nGDSII: {os.path.relpath(gds[0])}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "pe_array")
