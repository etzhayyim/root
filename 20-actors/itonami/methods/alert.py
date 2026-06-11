#!/usr/bin/env python3
"""itonami 営み — R9 operational threshold alerts (ADR-2606082300).

The alarm half of a factory-operations HMI, made charter-clean. Distinct from the other cells:
`optimize`/`plan` find the WORST station, `trend` finds DRIFT — `alert` checks the current KPIs
against ABSOLUTE configured thresholds and raises graded {info/warn/critical} flags.

THE CHARTER DISTINCTION (G1): an itonami alert is ADVISORY to a human / Council. It raises a
flag; it NEVER trips an e-stop, halts the line, or writes anything to the OT bus. Line-safety
interlocks live in the PLC / safety system (kotoba-os, IEC-61508), not here — itonami has no
actuation path and emits no halt/e-stop/trip command, by construction.

  evaluate — per line + station, compare each KPI to its (warn, critical) threshold → alerts
  emit / report — graded alert list as transient datoms + markdown

CONSTITUTIONAL (read before any change):
  G1 — advisory only; NEVER actuates / halts / trips. No :estop / :halt / :trip token is
    representable in the output.
  G2 — line/station scope only (no worker dimension).
  G3 — non-adjudicating. Alerts are read-time comparisons; thresholds are DOCUMENTED config
    (G5), not facts, and are caller-overridable.

Pure stdlib (no numpy). Usage:
    python3 alert.py [ops_seed.edn] [--out OUTDIR] [--tx N]
"""
from __future__ import annotations
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from analyze import load, analyze  # noqa: E402

# Documented thresholds (G5 — :representative config, caller-overridable; NOT measured facts).
# polarity True = higher-better (alert when BELOW); False = lower-better (alert when ABOVE).
DEFAULT_THRESHOLDS = {
    "oee":              {"polarity": True,  "warn": 0.60, "critical": 0.45},
    "scrap_rate":       {"polarity": False, "warn": 0.05, "critical": 0.15},
    "energy_per_good":  {"polarity": False, "warn": 40.0, "critical": 80.0},
    "idle_energy_frac": {"polarity": False, "warn": 0.10, "critical": 0.25},
}


def _severity(value: float, spec: dict) -> str | None:
    """Return 'critical' | 'warn' | None for a value against a (warn, critical) threshold."""
    if value is None or value == float("inf"):
        return None
    if spec["polarity"]:  # higher-better → alert when below
        if value < spec["critical"]:
            return "critical"
        if value < spec["warn"]:
            return "warn"
    else:                 # lower-better → alert when above
        if value > spec["critical"]:
            return "critical"
        if value > spec["warn"]:
            return "warn"
    return None


def evaluate(stations: dict, res: dict, thresholds: dict | None = None) -> list:
    """Compare each scope's KPIs to thresholds → graded alert list (worst-first)."""
    th = thresholds or DEFAULT_THRESHOLDS
    scopes = [(":line.sarutahiko-a", res["_line"])]
    scopes += [(s, res[s]) for s in res if not s.startswith("_")]

    alerts = []
    for scope, kpis in scopes:
        for kpi, spec in th.items():
            if kpi not in kpis:
                continue
            sev = _severity(kpis[kpi], spec)
            if sev:
                alerts.append({
                    "scope": scope, "kpi": kpi, "value": kpis[kpi],
                    "threshold": spec["critical"] if sev == "critical" else spec["warn"],
                    "severity": sev,
                    "label": stations.get(scope, {}).get(":station/label", scope),
                })
    order = {"critical": 0, "warn": 1}
    return sorted(alerts, key=lambda a: (order[a["severity"]], a["scope"], a["kpi"]))


def counts(alerts: list) -> dict:
    return {"critical": sum(1 for a in alerts if a["severity"] == "critical"),
            "warn": sum(1 for a in alerts if a["severity"] == "warn"), "total": len(alerts)}


def report_md(alerts: list) -> str:
    c = counts(alerts)
    L = []
    L.append("# itonami 営み — R9 operational alerts (advisory)\n")
    L.append("> **G1 — ADVISORY ONLY.** An itonami alert raises a flag for a human / Council; it "
             "NEVER stops the line, commands the safety system, or sends anything to the OT bus. "
             "Safety interlocks live in the PLC / safety system, not here. Thresholds are "
             "documented config (G5), not facts; station/line scope only (G2).\n")
    L.append(f"\n**{c['critical']} critical · {c['warn']} warn** ({c['total']} total)\n")
    L.append("| severity | scope | KPI | value | threshold |")
    L.append("|---|---|---|---:|---:|")
    for a in alerts:
        L.append(f"| {a['severity']} | {a['label']} | {a['kpi']} | {a['value']:.3g} | "
                 f"{a['threshold']:.3g} |")
    L.append("\n---\n_itonami 営み R9 · ADR-2606082300 · advisory · informs-only · "
             "documented-thresholds · station-scale._\n")
    return "\n".join(L)


def emit(alerts: list, tx: int = 1) -> str:
    """Transient EAVT alert datoms (computed on read, never durable — G3)."""
    L = [";; itonami R9 alerts — TRANSIENT (:bond/is-transient true), G1/G3. ADVISORY only.", "["]
    for a in alerts:
        L.append(f"[{a['scope']} :alert/{a['kpi'].replace('_', '-')} :{a['severity']} {tx} :derived] "
                 ";; :bond/is-transient true")
    L.append("]")
    return "\n".join(L) + "\n"


def main(argv):
    here = pathlib.Path(__file__).resolve().parent.parent
    seed = pathlib.Path(argv[1]) if len(argv) > 1 and not argv[1].startswith("--") \
        else here / "data" / "seed-factory-ops.kotoba.edn"
    outdir = here / "out"
    if "--out" in argv:
        outdir = pathlib.Path(argv[argv.index("--out") + 1])
    tx = int(argv[argv.index("--tx") + 1]) if "--tx" in argv else 1
    outdir.mkdir(parents=True, exist_ok=True)

    stations, ticks = load(seed)
    res = analyze(stations, ticks)
    alerts = evaluate(stations, res)
    (outdir / "alerts.md").write_text(report_md(alerts), encoding="utf-8")
    (outdir / "itonami-alerts.kotoba.edn").write_text(emit(alerts, tx), encoding="utf-8")
    c = counts(alerts)
    print(f"itonami R9: {c['critical']} critical · {c['warn']} warn → {outdir}")
    for a in alerts:
        print(f"  [{a['severity']}] {a['scope']} {a['kpi']} = {a['value']:.3g}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
