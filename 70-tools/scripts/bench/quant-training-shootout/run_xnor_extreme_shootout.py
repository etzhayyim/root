"""Progressive trick-stacking shootout for the XNOR-popcount max-TOPS path.

7 rows by default — each adds one trick on top of the previous:
  R0 baseline       : bf16 + AdamW (no binarization)
  R1 +WX            : binary weights (sign+STE) on q/k/v/o, master fp32
  R2 +WX_act        : + binary activations (XNOR-popcount equivalent matmul)
  R3 +GRAD          : + binary backward gradient (BinaryConnect alg-2 STE)
  R4 +NORM          : + L1 ApproxRMSNorm replacing RMSNorm
  R5 +SOFTMAX       : + 2^x piecewise-linear softmax in attention
  R6 +OPT (max-TOPS): + SignSGD (1-bit stateless optimizer)

Each row in a fresh subprocess for cuda + monkey-patch isolation.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).parent.resolve()

ROWS = [
    {"label": "R0-baseline-bf16",       "tricks": "",                            "opt": "adamw",   "master": "bf16"},
    {"label": "R1-W-bin",               "tricks": "WX",                          "opt": "adamw",   "master": "bf16"},
    {"label": "R2-W+X-bin-XNOR",        "tricks": "WX,WX_act",                   "opt": "adamw",   "master": "bf16"},
    {"label": "R3-+norm+softmax",       "tricks": "WX,WX_act,NORM,SOFTMAX",      "opt": "adamw",   "master": "bf16"},
    {"label": "R4-max-TOPS-signsgd",    "tricks": "WX,WX_act,GRAD,NORM,SOFTMAX,OPT", "opt": "signsgd", "master": "bf16"},
]


def run_one(row: dict, base: str, dataset: str, n_rows: int, n_steps: int,
            grad_accum: int, out_dir: Path) -> dict:
    env = {**os.environ,
           "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8",
           "TORCH_COMPILE_DISABLE": "1", "TORCHINDUCTOR_DISABLE": "1"}
    cmd = [sys.executable, "-u", str(HERE / "xnor_extreme_train.py"),
           "--tricks", row["tricks"],
           "--opt", row["opt"],
           "--master", row["master"],
           "--base", base, "--dataset", dataset,
           "--rows", str(n_rows), "--steps", str(n_steps),
           "--grad-accum", str(grad_accum),
           "--out", str(out_dir)]
    print(f"\n[xnor-extreme] === {row['label']} ===  tricks={row['tricks']!r} "
          f"opt={row['opt']} master={row['master']}", flush=True)
    t0 = time.time()
    # Inherit stdout/stderr so the child can write freely without filling
    # a capture buffer (which would deadlock on PowerShell/Windows for
    # long-running child processes with lots of warnings).
    cp = subprocess.run(cmd, env=env)
    wall = round(time.time() - t0, 2)
    # locate result file
    label_path = f"xnor-{row['master']}-{row['opt']}-{','.join(sorted(set(t for t in row['tricks'].split(',') if t)))}.json"
    if not row["tricks"]:
        label_path = f"xnor-{row['master']}-{row['opt']}-baseline.json"
    res_path = out_dir / label_path
    if res_path.exists():
        result = json.loads(res_path.read_text(encoding="utf-8"))
    else:
        # try a broader fallback
        candidates = list(out_dir.glob(f"xnor-{row['master']}-{row['opt']}-*.json"))
        if candidates:
            result = json.loads(candidates[-1].read_text(encoding="utf-8"))
        else:
            result = {"status": "crash", "tricks": row["tricks"],
                      "opt": row["opt"], "master": row["master"],
                      "exit_code": cp.returncode}
    result["row_label"] = row["label"]
    result["wall_total_sec"] = wall
    result["exit_code"] = cp.returncode
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="Qwen/Qwen2.5-0.5B-Instruct")
    ap.add_argument("--dataset", default="lordx64/reasoning-distill-opus-4-7-max-sft")
    ap.add_argument("--rows", type=int, default=8)
    ap.add_argument("--steps", type=int, default=2)
    ap.add_argument("--grad-accum", type=int, default=4)
    ap.add_argument("--out", type=Path, default=Path("./xnor-extreme-out"))
    args = ap.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    print(f"[xnor-extreme] base={args.base} rows={args.rows} steps={args.steps} "
          f"out={args.out}", flush=True)
    print(f"[xnor-extreme] rows to run: {len(ROWS)}", flush=True)

    results = []
    for row in ROWS:
        r = run_one(row, args.base, args.dataset, args.rows, args.steps,
                    args.grad_accum, args.out)
        results.append(r)
        summary = {k: v for k, v in r.items() if k in [
            "row_label", "status", "final_loss", "step_warm_sec",
            "sustained_tflops_est", "peak_vram_gb", "n_trainable",
            "wall_total_sec", "exit_code",
        ]}
        print(f"[xnor-extreme] {row['label']} => "
              f"{json.dumps(summary, ensure_ascii=False)}", flush=True)

    summary_path = args.out / "xnor_extreme_results.json"
    summary_path.write_text(json.dumps({
        "base": args.base, "dataset": args.dataset,
        "rows": args.rows, "steps": args.steps,
        "grad_accum": args.grad_accum,
        "results": results,
    }, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n[xnor-extreme] wrote {summary_path}", flush=True)

    print("\n## XNOR-popcount max-TOPS shootout summary")
    print()
    print("| row | trainable | step_warm_s | sustained TFLOPS | peak VRAM | "
          "final loss | losses |")
    print("|---|---|---|---|---|---|---|")
    for r in results:
        if r.get("status") == "ok":
            losses = ",".join(f"{l:.2f}" for l in r.get("losses", []))
            print(f"| {r['row_label']:30} | {r['n_trainable']:>10,} | "
                  f"{r.get('step_warm_sec', '—'):>6} | "
                  f"{r.get('sustained_tflops_est', '—'):>6} | "
                  f"{r.get('peak_vram_gb', '—'):>5} | "
                  f"{r.get('final_loss', '—'):>6} | {losses} |")
        else:
            err = r.get("error_type", r.get("status", "?"))
            msg = (r.get("error_msg") or r.get("stderr_tail") or "")[:80]
            print(f"| {r['row_label']:30} | ERROR ({err}) | — | — | — | — | "
                  f"{msg} |")


if __name__ == "__main__":
    main()
