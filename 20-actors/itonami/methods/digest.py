#!/usr/bin/env python3
"""itonami 営み — R4 daily operations digest + Murakumo narration (ADR-2606082300).

The synthesis layer that makes itonami an actual "AI Factory Brain": it FUSES the four cells
(ingest → analyze → optimize → inspect) into ONE operator-facing daily digest, and attaches a
Murakumo-narrated summary. This is the charter-clean form of the FOX "AI Factory Brain" daily
report — one screen the line lead reads each morning.

  build_digest       — fuse line OEE + routed findings + energy proposal + quality/vision
  narration_prompt   — the prompt that would be sent to Murakumo (LiteLLM 127.0.0.1:4000)
  fallback_narration — deterministic, OFFLINE narration (no external LLM) used when Murakumo
                       is unreachable; itonami is never blocked on inference

CONSTITUTIONAL (read before any change):
  G7 — Murakumo-only narration (ADR-2605215000). Narration routes ONLY through the Murakumo
    fleet (LiteLLM gateway); there is NO OpenAI/Anthropic-direct/Vertex/RunPod path. When
    Murakumo is unreachable the digest falls back to a deterministic template, never an
    external LLM. NARRATION_BACKEND is fixed to "murakumo".
  G1 — the digest RECOMMENDS; it never actuates. G2 — station/line scale only (no worker
    dimension flows through). G3 — KPIs/narration are read-time, never durable verdicts.

Pure stdlib (no numpy). Usage:
    python3 digest.py [ops_seed.edn] [--detections det.edn] [--out OUTDIR] [--tx N]
"""
from __future__ import annotations
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from analyze import load, analyze  # noqa: E402
import optimize  # noqa: E402
import inspect as vis  # noqa: E402

# Narration routes ONLY through the Murakumo fleet (ADR-2605215000). Fixed by construction.
NARRATION_BACKEND = "murakumo"
MURAKUMO_GATEWAY = "http://127.0.0.1:4000"   # LiteLLM loopback; never an external endpoint


def _label(stations, sid):
    return stations.get(sid, {}).get(":station/label", sid) if sid else "—"


def build_digest(stations: dict, ticks: list, detections: list) -> dict:
    res = analyze(stations, ticks)
    opt = optimize.optimize(stations, ticks, res)
    req = vis.inspection_request(stations, res, detections)
    rec = vis.reconcile(detections, res)
    qtarget = req["station"]
    return {
        "line": res["_line"],
        "recommend": res["_recommend"],
        "energy": opt["idle_powerdown"],
        "bottleneck": opt["bottleneck_relief"],
        "quality": {
            "station": qtarget,
            "label": _label(stations, qtarget),
            "scrap_rate": res[qtarget]["scrap_rate"],
            "top_defect": rec.get(qtarget, {}).get("top_defect"),
            "inspect_sample_rate": req["sample_rate"],
        },
        "_stations": stations,
    }


def _facts(d: dict) -> dict:
    st = d["_stations"]
    return {
        "line_oee": d["line"]["oee"],
        "energy_reduction": d["energy"]["energy_reduction_frac"],
        "bottleneck": _label(st, d["bottleneck"]["bottleneck"]),
        "oee_uplift": d["bottleneck"]["oee_uplift_frac"],
        "quality_label": d["quality"]["label"],
        "scrap_rate": d["quality"]["scrap_rate"],
        "top_defect": (d["quality"]["top_defect"] or ":none").lstrip(":"),
    }


def narration_prompt(d: dict) -> str:
    """The prompt sent to Murakumo (G7). Facts only; the model writes 2-3 plain sentences."""
    f = _facts(d)
    return (
        "You are itonami, a factory-operations brain. Narrate today's line digest in 2-3 plain "
        "sentences for a line lead. State facts only; recommend, never command; describe only "
        "stations and the line as a whole, never an individual. Facts:\n"
        f"- line OEE: {f['line_oee']:.1%}\n"
        f"- bottleneck: {f['bottleneck']} (relieving it lifts line OEE +{f['oee_uplift']:.1%})\n"
        f"- energy: powering down idle windows recovers ~{f['energy_reduction']:.1%} of line energy\n"
        f"- quality: {f['quality_label']} scrap {f['scrap_rate']:.1%}, "
        f"top defect {f['top_defect']} (route to vision inspection)\n"
    )


def fallback_narration(d: dict) -> str:
    """Deterministic offline narration (no external LLM) — used when Murakumo is unreachable."""
    f = _facts(d)
    return (
        f"Line OEE is {f['line_oee']:.1%}; the gating station is {f['bottleneck']}, and "
        f"relieving it would lift line OEE by about {f['oee_uplift']:.1%}. "
        f"Powering down idle windows could recover roughly {f['energy_reduction']:.1%} of line "
        f"energy. Quality attention: {f['quality_label']} at {f['scrap_rate']:.1%} scrap "
        f"(top defect {f['top_defect']}) — route to vision inspection."
    )


def narrate(d: dict, murakumo_call=None) -> dict:
    """Narrate via Murakumo if a caller is supplied (G7); else deterministic fallback.

    `murakumo_call` is an injected fn(prompt:str)->str that MUST hit the Murakumo gateway.
    It is never wired to an external LLM. In R4 / tests it is None → fallback.
    """
    prompt = narration_prompt(d)
    if murakumo_call is not None:
        try:
            return {"backend": NARRATION_BACKEND, "text": murakumo_call(prompt), "prompt": prompt}
        except Exception:
            pass  # Murakumo unreachable → deterministic fallback; never an external LLM
    return {"backend": "fallback-deterministic", "text": fallback_narration(d), "prompt": prompt}


def report_md(d: dict, narration: dict) -> str:
    st = d["_stations"]
    f = _facts(d)
    L = []
    L.append("# itonami 営み — daily operations digest\n")
    L.append(f"> _Narration backend: {narration['backend']} (Murakumo-only, G7). "
             "Recommends, never actuates (G1); station-scale, no worker dimension (G2)._\n")
    L.append(f"\n**{narration['text']}**\n")
    L.append(f"\n| metric | value |")
    L.append("|---|---|")
    L.append(f"| line OEE | {f['line_oee']:.1%} |")
    L.append(f"| bottleneck | {f['bottleneck']} (+{f['oee_uplift']:.1%} if relieved) |")
    L.append(f"| energy reduction (idle power-down) | {f['energy_reduction']:.1%} |")
    L.append(f"| quality target | {f['quality_label']} · scrap {f['scrap_rate']:.1%} · "
             f"top defect {f['top_defect']} |")
    L.append("\n---\n_itonami 営み R4 · ADR-2606082300 · Murakumo-only narration · "
             "recommends-not-actuates · station-scale._\n")
    return "\n".join(L)


def emit(d: dict, narration: dict, tx: int = 1) -> str:
    """Transient EAVT digest datoms (computed on read, never durable — G3)."""
    f = _facts(d)
    L = [";; itonami R4 daily digest — TRANSIENT (:bond/is-transient true), G1/G3/G7.", "["]
    L.append(f"[:line.sarutahiko-a :ops/digest-line-oee {f['line_oee']:g} {tx} :derived] ;; :bond/is-transient true")
    L.append(f"[:line.sarutahiko-a :ops/digest-energy-reduction {f['energy_reduction']:g} {tx} :derived] ;; :bond/is-transient true")
    L.append(f"[:line.sarutahiko-a :ops/digest-narration-backend :{narration['backend'].replace('-', '.')} {tx} :derived] ;; :bond/is-transient true")
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
    detections = vis.load_detections(det_path)
    d = build_digest(stations, ticks, detections)
    narration = narrate(d)  # R4: no Murakumo caller wired → deterministic fallback
    (outdir / "daily-digest.md").write_text(report_md(d, narration), encoding="utf-8")
    (outdir / "itonami-digest.kotoba.edn").write_text(emit(d, narration, tx), encoding="utf-8")
    print(f"itonami R4 digest [{narration['backend']}]: {narration['text'][:90]}... → {outdir}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
