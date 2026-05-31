"""gemma-coder-distill CLI entrypoint.

Usage:
  python -m gemma_coder_distill --bench-dir ../../90-docs/baien --max-iter 1 [--quick] [--dry-run]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .graph import build_graph
from .state import init_state


def main() -> int:
    ap = argparse.ArgumentParser(prog="gemma-coder-distill")
    ap.add_argument("--bench-dir", required=True,
                    help="dir containing langgraph-coding bench JSONL files")
    ap.add_argument("--max-iter", type=int, default=1)
    ap.add_argument("--quick", action="store_true",
                    help="1 epoch, small n_examples")
    ap.add_argument("--dry-run", action="store_true",
                    help="plan only — no fetch, no train")
    ap.add_argument("--student", default="google/gemma-4-e4b-it",
                    help="HF model id (default per ADR §1.1)")
    args = ap.parse_args()

    state = init_state(
        bench_dir=Path(args.bench_dir),
        max_iter=args.max_iter,
        quick=args.quick,
        dry_run=args.dry_run,
        student_model_id=args.student,
    )

    g = build_graph()
    final = g.invoke(state)

    for note in final.get("notes", []):
        print(note)
    return 0 if final.get("decision") != "abort" else 1


if __name__ == "__main__":
    sys.exit(main())
