#!/usr/bin/env python3
"""itonami 営み — R2 vision-inspection hand-off (ADR-2606082300).

Closes the loop from the R0 quality finding to in-line vision inspection — the charter-clean
form of FOX's "vision-AI quality inspection in the production line". Two directions:

  1. REQUEST  — from itonami's quality_target (the highest-scrap station) build a vision
     inspection request routed to a manako 眼 on-device detector (ADR-2606034800).
  2. RECONCILE — ingest manako's detection log and reduce it to a defect-class Pareto +
     scrap/rework reconciliation, giving the quality finding a ROOT-CAUSE hint instead of a
     bare number, and cross-checking the vision scrap count against the scan-cycle scrap count.

CONSTITUTIONAL (read before any change):
  G1 — inspection INFORMS the human/line; it never auto-rejects a part or actuates the line.
    :detect/verdict is advisory.
  G2 — OBJECT detection only. The inspected entity is a LINE PART (:detect/unit), never a
    person; no face / biometric / worker dimension exists or is permitted (manako is
    no-biometric, on-device, no person-reID — ADR-2606034800).
  G3 — non-adjudicating. Detection classes/verdicts are DISCLOSED detector outputs, not
    itonami verdicts; the Pareto is a read-time aggregate.

Pure stdlib (no numpy). Usage:
    python3 inspect.py [ops_seed.edn] [--detections det.edn] [--out OUTDIR] [--tx N]
"""
from __future__ import annotations
import sys, pathlib
from collections import defaultdict
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from analyze import load, analyze, read_edn  # noqa: E402

PASS, REWORK, SCRAP = ":pass", ":rework", ":scrap"
NON_DEFECT_CLASS = ":ok"
# manako on-device detector invariants surfaced into the request (ADR-2606034800)
MANAKO_CONSTRAINTS = ["on-device (no cloud imagery)", "object-only (no biometric / no person)",
                      "AGPL-isolated weights", "advisory verdict (no auto-reject, G1)"]


def load_detections(path: pathlib.Path) -> list:
    forms = read_edn(path.read_text(encoding="utf-8"))
    return [f for f in forms if isinstance(f, dict) and ":detect/unit" in f]


def inspection_request(stations: dict, res: dict, detections: list | None = None) -> dict:
    """Build a vision-inspection request for the highest-scrap station (the quality_target)."""
    target = res["_recommend"]["quality_target"]["station"]
    # defect classes to watch: those already seen at the station, else a sensible default
    watch = []
    if detections:
        watch = sorted({d[":detect/class"] for d in detections
                        if d.get(":detect/station") == target
                        and d.get(":detect/class") != NON_DEFECT_CLASS})
    if not watch:
        watch = [":weld-porosity", ":spatter", ":misalignment"]
    scrap_rate = res[target]["scrap_rate"]
    return {
        "station": target,
        "label": stations.get(target, {}).get(":station/label", target),
        "defect_classes": watch,
        # sample 100% while scrap-rate is elevated, else a representative audit rate
        "sample_rate": 1.0 if scrap_rate >= 0.05 else 0.2,
        "routed_to": "actor:manako",
        "detector": "manako-yolo26-weld-defect-head",
        "constraints": MANAKO_CONSTRAINTS,
        "reason_scrap_rate": scrap_rate,
    }


def reconcile(detections: list, res: dict | None = None) -> dict:
    """Reduce manako detections to a per-station defect-class Pareto + scan-cycle cross-check."""
    by_station = defaultdict(lambda: dict(inspected=0, defect_classes=defaultdict(int),
                                          scrap=0, rework=0, passed=0))
    for d in detections:
        st = d.get(":detect/station")
        a = by_station[st]
        a["inspected"] += 1
        v = d.get(":detect/verdict")
        if v == SCRAP:
            a["scrap"] += 1
        elif v == REWORK:
            a["rework"] += 1
        elif v == PASS:
            a["passed"] += 1
        cls = d.get(":detect/class")
        if cls and cls != NON_DEFECT_CLASS:
            a["defect_classes"][cls] += 1

    out = {}
    for st, a in by_station.items():
        pareto = sorted(a["defect_classes"].items(), key=lambda kv: (-kv[1], kv[0]))
        rec = dict(
            inspected=a["inspected"], scrap=a["scrap"], rework=a["rework"], passed=a["passed"],
            defect_pareto=pareto,
            top_defect=(pareto[0][0] if pareto else None),
        )
        if res is not None and st in res:
            # cross-check: does the detector's scrap count agree with the scan-cycle scrap count?
            rec["scancycle_scrap"] = res[st]["scrap"]
            rec["scrap_agrees"] = (a["scrap"] == res[st]["scrap"])
        out[st] = rec
    return out


def report_md(stations: dict, req: dict, rec: dict) -> str:
    L = []
    L.append("# itonami 営み — R2 vision-inspection hand-off\n")
    L.append("> **G1** inspection INFORMS, never auto-rejects/actuates. **G2** object-only — "
             "the inspected entity is a line PART, never a person (manako is on-device, "
             "no-biometric, no person-reID — ADR-2606034800). **G3** detector outputs are "
             "disclosed facts, not itonami verdicts.\n")

    L.append("\n## Inspection request → manako\n")
    L.append(f"- **station**: {req['label']} (scrap-rate {req['reason_scrap_rate']:.1%})")
    L.append(f"- **detector**: {req['detector']} · sample {req['sample_rate']:.0%}")
    L.append(f"- **watch classes**: {', '.join(c.lstrip(':') for c in req['defect_classes'])}")
    L.append(f"- **constraints**: {'; '.join(req['constraints'])}")

    L.append("\n## Detection reconciliation (root-cause hint)\n")
    L.append("| station | inspected | scrap | rework | top defect | scan-cycle agrees |")
    L.append("|---|---:|---:|---:|---|:--:|")
    for st, r in rec.items():
        agree = "✓" if r.get("scrap_agrees") else ("✗" if "scrap_agrees" in r else "n/a")
        top = (r["top_defect"] or "—")
        L.append(f"| {stations.get(st, {}).get(':station/label', st)} | {r['inspected']} | "
                 f"{r['scrap']} | {r['rework']} | {str(top).lstrip(':')} | {agree} |")

    L.append("\n### Defect Pareto (worst station)\n")
    if req["station"] in rec:
        for cls, n in rec[req["station"]]["defect_pareto"]:
            L.append(f"- {cls.lstrip(':')}: {n}")

    L.append("\n---\n_itonami 営み R2 · ADR-2606082300 · vision-informs-not-actuates · "
             "object-only (no person) · root-cause hint, not a worker verdict._\n")
    return "\n".join(L)


def emit(req: dict, rec: dict, tx: int = 1) -> str:
    """Transient EAVT inspection datoms (computed on read, never durable — G3)."""
    L = [";; itonami R2 vision hand-off — TRANSIENT (:bond/is-transient true), G1/G3.", "["]
    st = req["station"]
    L.append(f"[{st} :ops/inspect-sample-rate {req['sample_rate']:g} {tx} :derived] ;; :bond/is-transient true")
    L.append(f"[{st} :ops/inspect-routed-to :actor.manako {tx} :derived] ;; :bond/is-transient true")
    if st in rec and rec[st]["top_defect"]:
        L.append(f"[{st} :quality/top-defect {rec[st]['top_defect']} {tx} :derived] ;; :bond/is-transient true")
        L.append(f"[{st} :quality/scrap-agrees {'true' if rec[st].get('scrap_agrees') else 'false'} {tx} :derived] ;; :bond/is-transient true")
    L.append("]")
    return "\n".join(L) + "\n"


def main(argv):
    here = pathlib.Path(__file__).resolve().parent.parent
    seed = pathlib.Path(argv[1]) if len(argv) > 1 and not argv[1].startswith("--") \
        else here / "data" / "seed-factory-ops.kotoba.edn"
    det_path = pathlib.Path(argv[argv.index("--detections") + 1]) if "--detections" in argv \
        else here / "data" / "seed-vision-detections.kotoba.edn"
    outdir = here / "out"
    if "--out" in argv:
        outdir = pathlib.Path(argv[argv.index("--out") + 1])
    tx = int(argv[argv.index("--tx") + 1]) if "--tx" in argv else 1
    outdir.mkdir(parents=True, exist_ok=True)

    stations, ticks = load(seed)
    res = analyze(stations, ticks)
    detections = load_detections(det_path)
    req = inspection_request(stations, res, detections)
    rec = reconcile(detections, res)
    (outdir / "vision-inspection.md").write_text(report_md(stations, req, rec), encoding="utf-8")
    (outdir / "itonami-inspect.kotoba.edn").write_text(emit(req, rec, tx), encoding="utf-8")
    top = rec.get(req["station"], {}).get("top_defect")
    print(f"itonami R2: inspect {req['station']} (sample {req['sample_rate']:.0%}) "
          f"→ manako · top defect {top} → {outdir}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
