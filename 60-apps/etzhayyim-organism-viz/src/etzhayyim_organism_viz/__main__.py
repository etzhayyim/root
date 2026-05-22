"""etzhayyim-viz CLI.

Subcommands:
  static  — render aliveness.json + bonsai.svg + dashboard.html (one-shot)
  serve   — run the FastAPI realtime server (interactive)

Usage:
    python -m etzhayyim_organism_viz serve --repo /repo --port 8081
    python -m etzhayyim_organism_viz static --repo /repo
    python -m etzhayyim_organism_viz                       # alias of `static`
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sys
from pathlib import Path


_AXIS_ROW = re.compile(
    r"^\|\s*\d+\s*\|\s*\*{0,2}([A-Za-z][A-Za-z\- ]*[A-Za-z])\*{0,2}[^\|]*\|\s*\*{0,2}(\d+)\s*/\s*10",
    re.MULTILINE,
)
_LABEL_TO_KEY = {
    "autopoiesis": "autopoiesis", "metabolism": "metabolism", "homeostasis": "homeostasis",
    "active inference": "active_inference", "active-inference": "active_inference",
    "reproduction": "reproduction", "symbiosis": "symbiosis", "diversity": "diversity",
    "wellbecoming": "wellbecoming", "anti-fragility": "antifragility",
    "antifragility": "antifragility", "sanctification": "sanctification",
}


def _latest_axis_scores(repo: Path) -> dict[str, int]:
    obs = repo / "_observations"
    files = sorted(obs.glob("*-cycle-*.md"))
    if not files:
        return {}
    body = files[-1].read_text(encoding="utf-8", errors="ignore")
    scores: dict[str, int] = {}
    for label, val in _AXIS_ROW.findall(body):
        key = _LABEL_TO_KEY.get(label.strip().lower())
        if key:
            scores[key] = int(val)
    return scores


def cmd_static(args: argparse.Namespace) -> int:
    from .aliveness import compute, in_healthy_band
    from .bonsai import render as render_bonsai, render_to as write_bonsai
    from .dashboard import render_to as write_dashboard

    repo = Path(args.repo).resolve()
    if not (repo / "README.md").exists():
        logging.error("repo missing README.md anchor: %s", repo)
        return 2

    a = compute(repo)
    bands = in_healthy_band(a)
    axis_scores = _latest_axis_scores(repo)

    out = Path(args.out) if args.out else (repo / "60-apps" / "etzhayyim-organism-viz" / "static")
    out.mkdir(parents=True, exist_ok=True)
    payload = {"tuple": a.as_dict(), "in_band": bands, "axis_scores": axis_scores}
    (out / "aliveness.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    svg = render_bonsai(axis_scores, a)
    write_bonsai(out, axis_scores, a)
    write_dashboard(out, a, axis_scores, svg)

    print(f"=== aliveness — {a.timestamp} ===")
    for k, v in a.as_dict().items():
        if k in ("timestamp", "notes"):
            continue
        ok = bands.get(k.split("_")[0], None)
        print(f"  {'✅' if ok else '❌'} {k:18s} = {v}")
    print(f"\nin band: {sum(bands.values())}/5  →  {out}")
    return 0


def cmd_serve(args: argparse.Namespace) -> int:
    import uvicorn  # type: ignore
    os.environ["ETZ_REPO"] = str(Path(args.repo).resolve())
    logging.info("etzhayyim-viz serve: repo=%s host=%s port=%d", args.repo, args.host, args.port)
    uvicorn.run(
        "etzhayyim_organism_viz.server:app",
        host=args.host, port=args.port, log_level="info", reload=False,
    )
    return 0


def main() -> int:
    logging.basicConfig(level="INFO", format="%(asctime)s %(levelname)s %(message)s")
    p = argparse.ArgumentParser(prog="etzhayyim-viz")
    sub = p.add_subparsers(dest="cmd")
    p_static = sub.add_parser("static", help="emit static artefacts")
    p_static.add_argument("--repo", default=os.environ.get("ETZ_REPO", "/repo"))
    p_static.add_argument("--out", default=None)
    p_serve = sub.add_parser("serve", help="run realtime FastAPI server")
    p_serve.add_argument("--repo", default=os.environ.get("ETZ_REPO", "/repo"))
    p_serve.add_argument("--host", default=os.environ.get("ETZ_VIZ_HOST", "0.0.0.0"))
    p_serve.add_argument("--port", type=int, default=int(os.environ.get("ETZ_VIZ_PORT", "8081")))
    p.add_argument("--repo-fallback", dest="repo", default=os.environ.get("ETZ_REPO", "/repo"),
                   help=argparse.SUPPRESS)
    args = p.parse_args()
    if args.cmd in (None, "static"):
        if not hasattr(args, "out"):
            args.out = None
        return cmd_static(args)
    if args.cmd == "serve":
        return cmd_serve(args)
    p.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
