"""aburi 炙り actor — personal-tracking-exposure analysis, as a WASI component.

Per ADR-2606161630 + ADR-2606014600. The *executable* face of aburi, built with componentize-py
into a WASM Component-Model component that runs in the kotoba WASM runtime. It mirrors the core of
`methods/analyze.py` over the embedded representative seed (the member's OWN live graph is supplied
by the host at R1; the sandbox has no FS/network — G7/no-server-key).

THE DEFINING INVARIANTS:
  own_data=true (G1) — the readout is an own-exposure map, never a profile of any other person.
  reciprocity_restoring=true (G4) — it makes the asymmetric ad-watcher visible to the watched;
    it never tracks, sells, or profiles.
  non-adjudicating (G3) — naming a collector is a DISCLOSED catalogue fact, never a verdict.
"""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import analyze  # `bb aburi:build-wasm` (tools/build.clj) copies methods/analyze.py beside this file  # noqa: E402
import datom_emit  # noqa: E402
import coverage_report  # noqa: E402


def _seed_text() -> str:
    try:
        from _seed import SEED_EDN  # `bb aburi:build-wasm` (tools/build.clj) generates _seed.py
        return SEED_EDN
    except Exception:
        return (HERE / "seed-tracker-exposure.kotoba.edn").read_text(encoding="utf-8")


def _graph():
    forms = analyze.read_edn(_seed_text())
    nodes, edges = {}, []
    for f in forms:
        if not isinstance(f, dict):
            continue
        if ":organism/id" in f:
            nodes[f[":organism/id"]] = f
        elif ":en/from" in f and ":en/to" in f:
            edges.append(f)
    return nodes, edges


def _result() -> dict:
    nodes, edges = _graph()
    res = analyze.analyze(nodes, edges)

    def rows(d, limit):
        return [{"id": nid, "label": label, "value": round(v, 4)}
                for nid, label, v in analyze._rank(d, nodes, limit)]

    return {
        "actor": "aburi",
        "own_data": True,                 # G1
        "reciprocity_restoring": True,    # G4
        "non_adjudicating": True,         # G3
        "who_tracks_you": rows(res["net_exposure"], 14),
        "surface_leak": rows(res["surface_leak"], 10),
        "data_spread": rows(res["spread"], 10),
        "reciprocity_gap": res["unrouted_permissions"],
    }


def compute() -> str:
    """Plain entry point (used by the offline build sanity check)."""
    return json.dumps(_result(), ensure_ascii=False)


# componentize-py binds the WIT world's exports to a class named `WitWorld`.
class WitWorld:
    def analyze(self) -> str:
        return json.dumps(_result(), ensure_ascii=False)

    def datoms(self, tx: int) -> str:
        nodes, edges = _graph()
        res = analyze.analyze(nodes, edges)
        return datom_emit.emit(nodes, edges, res, tx=int(tx))

    def coverage(self) -> str:
        nodes, edges = _graph()
        return coverage_report.report(nodes, edges)
