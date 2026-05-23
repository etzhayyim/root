"""CLI entry: `python -m baien_distill ...` and `baien-distill ...`."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .graph import compile_graph
from .state import new_state


def main() -> int:
    ap = argparse.ArgumentParser(prog="baien-distill")
    ap.add_argument("--bench-dir", type=Path, required=True,
                    help="path to 90-docs/baien/")
    ap.add_argument("--max-iter", type=int, default=3)
    ap.add_argument("--n-per-category", type=int, default=200)
    ap.add_argument("--source", choices=["hf", "teacher"], default="hf",
                    help="distill data source: 'hf' (default, ADR §3a — pull from "
                         "public HF SFT datasets like lordx64/reasoning-distill-opus-4-7-max-sft) "
                         "or 'teacher' (ADR §3b fallback — generate via on-fleet OSS teacher).")
    ap.add_argument("--quick", action="store_true",
                    help="N=50, epochs=1 — fast iteration")
    ap.add_argument("--dry-run", action="store_true",
                    help="walk the graph without fetching/calling teacher or trainer")
    args = ap.parse_args()

    graph = compile_graph()
    state = new_state(
        bench_dir=args.bench_dir,
        max_iter=args.max_iter,
        n_per_category=args.n_per_category,
        source=args.source,
        quick=args.quick,
        dry_run=args.dry_run,
    )

    final = graph.invoke(state)

    print("\n=== ReAct trace ===")
    for n in final.get("notes", []):
        print(" ", n)
    print("\n=== Score history ===")
    for h in final.get("score_history", []):
        print(" ", h)
    print(f"\nFinal decision: {final.get('decision')}")
    return 0 if final.get("decision") in ("commit", "abort") else 1


if __name__ == "__main__":
    sys.exit(main())
