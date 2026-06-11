#!/usr/bin/env python3
"""post_quantum-compat — kotoba Datom-log emitter (canonical EAVT state,
ADR-2605312345).

Projects the pqh-v1 migration registry into append-only kotoba Datoms
[e a v tx op]. Two strata (inochi pattern, ADR-2606073000):

  GROUND (durable, op :add) — one datom per (layer, attribute, value) and per
    suite component: the migration state IS the Datom log.

  DERIVED (transient, :pq/is-transient true) — the coverage readout
    (migrated-fraction etc.) is computed on READ and emitted in a flagged
    block so a reader never mistakes it for persisted state.

Pure stdlib — runnable inside the kotoba pywasm actor.
Usage:
    python3 datom_emit.py [--tx N]
"""
from __future__ import annotations
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from suite import LAYERS, SUITES, coverage_report  # noqa: E402

LAYER_ATTRS = [":layer/primitive", ":layer/quantum-attack", ":layer/status",
               ":layer/suite", ":layer/adr", ":layer/note"]


def _fmt(v) -> str:
    if v is True:
        return "true"
    if v is False:
        return "false"
    if v is None:
        return "nil"
    if isinstance(v, str):
        return v if v.startswith(":") else '"' + v.replace('\\', '\\\\').replace('"', '\\"') + '"'
    if isinstance(v, float):
        return f"{v:g}"
    if isinstance(v, list):
        return "[" + " ".join(_fmt(x) for x in v) + "]"
    return str(v)


def emit(tx: int = 1) -> str:
    L = []
    L.append(";; post_quantum-compat — GENERATED kotoba Datom log (ADR-2606111300). DO NOT hand-edit.")
    L.append(";; Canonical EAVT state (ADR-2605312345). [e a v tx op].")
    L.append(";; GROUND op :add = durable. DERIVED :pq/is-transient = computed on read.")
    L.append("")
    for layer in LAYERS:
        e = layer[":layer/id"]
        for a in LAYER_ATTRS:
            if a in layer:
                L.append(f"[{e} {a} {_fmt(layer[a])} {tx} :add]")
        if ":layer/pr" in layer:
            L.append(f"[{e} :layer/pr {_fmt(layer[':layer/pr'])} {tx} :add]")
    L.append("")
    for sid, suite in SUITES.items():
        for a, v in suite.items():
            if isinstance(v, dict):
                for ka, kv in v.items():
                    L.append(f"[{sid} {ka} {_fmt(kv)} {tx} :add]")
            else:
                L.append(f"[{sid} {a} {_fmt(v)} {tx} :add]")
    L.append("")
    L.append(";; ── DERIVED (transient — recompute on read, do not persist) ──")
    cov = coverage_report()
    for a, v in cov.items():
        L.append(f"[:pq/coverage {a} {_fmt(v)} {tx} :add] ;; :pq/is-transient true")
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    tx = 1
    if "--tx" in sys.argv:
        tx = int(sys.argv[sys.argv.index("--tx") + 1])
    sys.stdout.write(emit(tx))
