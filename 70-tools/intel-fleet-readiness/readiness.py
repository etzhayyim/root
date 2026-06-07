#!/usr/bin/env python3
"""intel-fleet-readiness — pre-flight checklist for deploying the intel/OSINT actor cohort
to the Murakumo Mac-mini fleet.

The Murakumo fleet places religious-corp Pregel cells as k3s DaemonSets driven by
50-infra/murakumo/fleet.toml (→ 70-tools/fleet-to-kustomize → kustomize → k3s). LIVE
placement of an actor's cells, and any live ingest/publish/promotion, is OUTWARD-GATED
(per-actor G10/G7/G14 = Council Lv6+ + operator). This tool does NOT deploy — it answers
the question an operator must answer BEFORE flipping that gate: is each actor actually
deploy-ready (suite green, artifacts materialised), and exactly which gate still blocks it?

Verdict per actor:
  READY-PENDING-GATE — suite green AND ≥1 persisted Datom artifact present; the ONLY thing
                       left is the human/Council outward gate.
  NOT-READY          — suite missing/red or no materialised intel artifact.

stdlib only, read-only (runs each actor's own run_tests.sh). Usage:
    python3 readiness.py [--out OUTDIR]
"""
from __future__ import annotations

import pathlib
import re
import subprocess
import sys

_ROOT = pathlib.Path(__file__).resolve().parents[2]
_ACTORS = _ROOT / "20-actors"

# (actor, the per-actor outward gate that blocks LIVE deploy/ingest/publish)
COHORT = [
    ("mitooshi", "G10 — live promotion = Council Lv6+ + operator"),
    ("watari", "G7 — live AIS/ADS-B ingest = WATARI_OPERATOR_GATE=1 + Council"),
    ("watatsuna", "G7 — live cable-bulletin ingest = operator + Council"),
    ("kabuto", "G7 — live supply-chain ingest = operator + Council"),
    ("kanjo", "G7 — live EDGAR/EDINET fetch = KANJO_OPERATOR_GATE=1 + Council"),
    ("tadori", "live write = operator-staged + case-id + Council (passive-only)"),
    ("danjo", "G3/G10 — live gov-corpus ingest + named-party publish = Council + 1 SBT=1 vote"),
    ("himotoki", "G14/G10 — dispatch = verified target + HIMOTOKI_OPERATOR_GATE=1 + Council"),
]

_COUNT_RE = re.compile(r"(\d+)\s*/\s*(\d+)(?:\s+tests?)?\s+passed|Ran\s+(\d+)\s+tests?")


def _count_tests(output: str) -> int:
    total = 0
    for m in _COUNT_RE.finditer(output):
        total += int(m.group(1) or m.group(3) or 0)
    return total


def check_actor(name: str, gate: str) -> dict:
    adir = _ACTORS / name
    runner = adir / "run_tests.sh"
    suite_ok, n_tests, note = False, 0, ""
    if runner.exists():
        try:
            r = subprocess.run(["bash", str(runner)], cwd=str(adir),
                               capture_output=True, text=True, timeout=180)
            out = r.stdout + r.stderr
            suite_ok = r.returncode == 0
            n_tests = _count_tests(out)
            if not suite_ok:
                note = "suite RED"
        except Exception as e:  # noqa: BLE001
            note = f"suite error: {e}"
    else:
        note = "no run_tests.sh"

    artifacts = []
    for sub in ("data/persisted", "data/fixtures", "out"):
        d = adir / sub
        if d.exists():
            artifacts += [str(p.relative_to(adir)) for p in sorted(d.glob("*.kotoba.edn"))]

    ready = suite_ok and n_tests > 0 and bool(artifacts)
    return {"actor": name, "suite_ok": suite_ok, "n_tests": n_tests,
            "artifacts": artifacts, "gate": gate, "note": note,
            "verdict": "READY-PENDING-GATE" if ready else "NOT-READY"}


def render_md(rows: list[dict]) -> str:
    ready = sum(1 for r in rows if r["verdict"] == "READY-PENDING-GATE")
    total_tests = sum(r["n_tests"] for r in rows)
    L = ["# intel-fleet-readiness — Murakumo deploy pre-flight", "",
         f"> {ready}/{len(rows)} intel actors READY-PENDING-GATE · {total_tests} tests green · "
         "**this tool never deploys** — live placement/ingest/publish is per-actor outward-gated "
         "(Council Lv6+ + operator). It reports what is ready and which gate remains.", "",
         "| actor | suite | tests | artifacts | verdict | blocking gate |",
         "|---|---|---:|---:|---|---|"]
    for r in rows:
        s = "green" if r["suite_ok"] else (r["note"] or "red")
        L.append(f"| {r['actor']} | {s} | {r['n_tests']} | {len(r['artifacts'])} | "
                 f"{r['verdict']} | {r['gate']} |")
    return "\n".join(L) + "\n"


def render_edn(rows: list[dict]) -> str:
    L = [";; intel-fleet-readiness.kotoba.edn — Murakumo deploy pre-flight per intel actor.",
         ";; READY-PENDING-GATE = suite green + artifacts present; ONLY the outward gate remains.",
         ";; This tool NEVER deploys; live placement/ingest/publish is Council Lv6+ + operator.", "", "["]
    for r in rows:
        arts = " ".join(f'"{a}"' for a in r["artifacts"])
        L.append(
            f' {{:fleet.ready/actor :{r["actor"]} :fleet.ready/suite-ok {str(r["suite_ok"]).lower()} '
            f':fleet.ready/n-tests {r["n_tests"]} :fleet.ready/artifact-count {len(r["artifacts"])} '
            f':fleet.ready/artifacts [{arts}] :fleet.ready/verdict :{r["verdict"].lower()} '
            f':fleet.ready/blocking-gate "{r["gate"]}"}}')
    L.append("]")
    return "\n".join(L) + "\n"


def run() -> list[dict]:
    return [check_actor(name, gate) for name, gate in COHORT]


def main(argv: list[str]) -> int:
    rows = run()
    if "--out" in argv:
        outdir = pathlib.Path(argv[argv.index("--out") + 1])
        outdir.mkdir(parents=True, exist_ok=True)
        (outdir / "intel-fleet-readiness.md").write_text(render_md(rows))
        (outdir / "intel-fleet-readiness.kotoba.edn").write_text(render_edn(rows))
    ready = sum(1 for r in rows if r["verdict"] == "READY-PENDING-GATE")
    print(f"intel-fleet-readiness: {ready}/{len(rows)} READY-PENDING-GATE "
          f"({sum(r['n_tests'] for r in rows)} tests green). This tool never deploys.")
    for r in rows:
        print(f"  {r['actor']:11s} {r['verdict']:18s} tests={r['n_tests']:3d} "
              f"artifacts={len(r['artifacts'])}  ← {r['gate'].split(' — ')[0]}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
