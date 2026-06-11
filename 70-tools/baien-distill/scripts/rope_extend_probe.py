"""Stage 1 — rope_theta scaling smoke per ADR-2605231600.

Runs `microbench_long.py` against baien under 3 configurations:

  A. baseline       rope_theta = 500_000  (upstream default; sanity)
  B. linear ×4      rope_theta = 2_000_000, max_pos = 16384 (16k target)
  C. NTK-aware ×4   rope_theta ≈ 2_131_381, max_pos = 16384 (better quality)

Each run writes its JSONL to a separate path; the script then prints a
side-by-side pass-rate matrix so the operator can decide whether to
promote to Stage 2 (YaRN + LoRA) per the ADR's gate criteria.

Usage (from EVO-X2 ComfyUI python_embeded so ROCm bf16 matmul is fast):

  python rope_extend_probe.py \
      --model microsoft/bitnet-b1.58-2B-4T-bf16 \
      --out-dir 90-docs/baien/context-extend-260523
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

# baien arch constants from config.json (verified 2026-05-23).
BAIEN_HEAD_DIM = 128
BAIEN_BASE_THETA = 500_000.0
BAIEN_BASE_MAX_POS = 4096

# NTK-aware scaling: theta' = theta × extend_factor^(d / (d-2))
def ntk_theta(extend_factor: float, head_dim: int = BAIEN_HEAD_DIM,
              base_theta: float = BAIEN_BASE_THETA) -> float:
    return base_theta * (extend_factor ** (head_dim / (head_dim - 2)))


CONFIGS = [
    {
        "label": "A_baseline",
        "rope_theta": None,          # leave config default
        "max_pos": None,
        "rope_scaling_type": None,
    },
    {
        "label": "B_linear_x4",
        "rope_theta": BAIEN_BASE_THETA * 4,         # 2_000_000
        "max_pos": BAIEN_BASE_MAX_POS * 4,          # 16384
        "rope_scaling_type": None,
    },
    {
        "label": "C_ntk_x4",
        "rope_theta": ntk_theta(4.0),                # ≈ 2_131_381
        "max_pos": BAIEN_BASE_MAX_POS * 4,
        "rope_scaling_type": None,
    },
]


def find_microbench_long() -> Path:
    here = Path(__file__).resolve()
    # 70-tools/baien-distill/scripts/rope_extend_probe.py
    # → 70-tools/scripts/bench/baien-microbench/microbench_long.py
    cand = here.parents[2] / "scripts" / "bench" / "baien-microbench" / "microbench_long.py"
    if not cand.exists():
        raise FileNotFoundError(f"microbench_long.py not found at {cand}")
    return cand


def run_one(model: str, cfg: dict, out_file: Path, micro_script: Path) -> dict:
    cmd = [sys.executable, str(micro_script), "--model", model,
           "--out", str(out_file)]
    if cfg["rope_theta"] is not None:
        cmd += ["--rope-theta", str(cfg["rope_theta"])]
    if cfg["max_pos"] is not None:
        cmd += ["--max-position-embeddings", str(cfg["max_pos"])]
    if cfg["rope_scaling_type"]:
        cmd += ["--rope-scaling-type", cfg["rope_scaling_type"]]

    env = os.environ.copy()
    env.setdefault("TORCH_COMPILE_DISABLE", "1")
    env.setdefault("TORCHINDUCTOR_DISABLE", "1")

    print(f"\n[{cfg['label']}] {' '.join(cmd)}", flush=True)
    proc = subprocess.run(cmd, env=env)
    return {"label": cfg["label"], "returncode": proc.returncode,
            "out_file": str(out_file), "config": cfg}


def summarize(out_files: list[tuple[str, Path]]) -> None:
    rows: dict[str, dict[str, bool]] = {}
    prompt_ids: list[str] = []
    for label, out_file in out_files:
        if not out_file.exists():
            continue
        rows[label] = {}
        for line in out_file.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            rows[label][r["id"]] = bool(r["ok"])
            if r["id"] not in prompt_ids:
                prompt_ids.append(r["id"])

    if not rows:
        print("\n[summary] no results to compare")
        return

    print("\n" + "=" * 72)
    print(f"{'prompt':22} | " + " | ".join(f"{lbl:>12}" for lbl in rows))
    print("-" * 72)
    for pid in prompt_ids:
        cells = []
        for lbl in rows:
            v = rows[lbl].get(pid)
            cells.append("    PASS    " if v is True else ("    FAIL    " if v is False else "      -     "))
        print(f"{pid:22} | " + " | ".join(cells))
    print("-" * 72)
    totals = {lbl: sum(rows[lbl].values()) for lbl in rows}
    counts = {lbl: len(rows[lbl]) for lbl in rows}
    rates = " | ".join(
        f"{100*totals[lbl]/max(1,counts[lbl]):>10.1f}%"
        for lbl in rows
    )
    print(f"{'pass rate':22} | " + rates)
    print("=" * 72)
    print("\nADR-2605231600 §Stage 1 gate to promote → Stage 2:")
    print("  - 4k microbench Δ ≤ -5 pp")
    print("  - 16k needle recall ≥ 0.40 (needle prompts in B/C runs)")
    print("  - ppl 4k inflation ≤ +5%  (separate run, not covered by this probe)")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="microsoft/bitnet-b1.58-2B-4T-bf16")
    ap.add_argument("--out-dir", type=Path,
                    default=Path("90-docs/baien/context-extend-260523"))
    ap.add_argument("--only", default="",
                    help="comma-separated subset of labels (A_baseline,B_linear_x4,C_ntk_x4)")
    args = ap.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    micro_script = find_microbench_long()

    only = {x.strip() for x in args.only.split(",") if x.strip()}
    cfgs = [c for c in CONFIGS if not only or c["label"] in only]

    out_files: list[tuple[str, Path]] = []
    summaries: list[dict] = []
    for cfg in cfgs:
        out_file = args.out_dir / f"results_long_{cfg['label']}.jsonl"
        # truncate so re-runs don't pile rows on top of each other
        out_file.write_text("", encoding="utf-8")
        summaries.append(run_one(args.model, cfg, out_file, micro_script))
        out_files.append((cfg["label"], out_file))

    summary_path = args.out_dir / "probe_summary.json"
    summary_path.write_text(
        json.dumps({"runs": summaries}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"\n[probe_summary] {summary_path}")

    summarize(out_files)
    return 0


if __name__ == "__main__":
    sys.exit(main())
