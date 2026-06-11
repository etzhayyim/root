"""Run the binary-XNOR + non-Adam shootout matrix.

5-6 rows: {fp32, fp16, bf16} master × {sgd, signsgd, lion} optimizer.
Each row in a fresh python subprocess for cuda state isolation.

Output: JSON files at out/binary-<master>-<opt>.json + a markdown summary.
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


def run_one(master: str, opt: str, base: str, dataset: str,
            n_rows: int, n_steps: int, grad_accum: int, out_dir: Path) -> dict:
    env = {**os.environ,
           "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8",
           "TORCH_COMPILE_DISABLE": "1", "TORCHINDUCTOR_DISABLE": "1"}
    cmd = [sys.executable, "-u", str(HERE / "binary_xnor_train.py"),
           "--master", master, "--opt", opt, "--base", base,
           "--dataset", dataset, "--rows", str(n_rows),
           "--steps", str(n_steps), "--grad-accum", str(grad_accum),
           "--out", str(out_dir)]
    print(f"\n[binary-shootout] === master={master} opt={opt} ===", flush=True)
    t0 = time.time()
    cp = subprocess.run(cmd, env=env, capture_output=True, text=True)
    wall = round(time.time() - t0, 2)
    # Tail the log
    print((cp.stdout or "")[-1200:], flush=True)
    if cp.returncode != 0:
        print(f"--- STDERR tail ---\n{(cp.stderr or '')[-800:]}", flush=True)
    res_path = out_dir / f"binary-{master}-{opt}.json"
    if res_path.exists():
        row = json.loads(res_path.read_text(encoding="utf-8"))
    else:
        row = {"status": "crash", "master": master, "optimizer": opt,
               "stderr_tail": (cp.stderr or "")[-400:]}
    row["wall_total_sec"] = wall
    row["exit_code"] = cp.returncode
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="Qwen/Qwen2.5-0.5B-Instruct")
    ap.add_argument("--dataset", default="lordx64/reasoning-distill-opus-4-7-max-sft")
    ap.add_argument("--rows", type=int, default=8)
    ap.add_argument("--steps", type=int, default=3)
    ap.add_argument("--grad-accum", type=int, default=4)
    ap.add_argument("--out", type=Path, default=Path("./binary-shootout-out"))
    ap.add_argument("--combos", nargs="+",
                    default=["fp32:sgd", "fp32:signsgd", "fp32:lion",
                             "fp16:lion", "bf16:lion"])
    args = ap.parse_args()

    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    print(f"[binary-shootout] base={args.base} rows={args.rows} steps={args.steps} "
          f"combos={args.combos} out={out}", flush=True)

    rows = []
    for combo in args.combos:
        master, opt = combo.split(":", 1)
        row = run_one(master, opt, args.base, args.dataset,
                      args.rows, args.steps, args.grad_accum, out)
        rows.append(row)
        print(f"[binary-shootout] {combo} => {json.dumps({k: v for k, v in row.items() if k in ['status','final_loss','step_warm_sec','peak_vram_gb','n_trainable','wall_total_sec']}, ensure_ascii=False)}",
              flush=True)

    summary_path = out / "binary_shootout_results.json"
    summary_path.write_text(json.dumps({
        "base": args.base, "dataset": args.dataset,
        "rows": args.rows, "steps": args.steps,
        "grad_accum": args.grad_accum,
        "results": rows,
    }, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n[binary-shootout] wrote {summary_path}", flush=True)

    print("\n## Binary XNOR + non-Adam shootout summary")
    print()
    print("| master | optimizer | trainable | step_warm_s | peak_vram_gb | "
          "final_loss | avg_loss | losses |")
    print("|---|---|---|---|---|---|---|---|")
    for r in rows:
        if r.get("status") == "ok":
            losses = ",".join(f"{l:.2f}" for l in r.get("losses", []))
            print(f"| {r['master']:4} | {r['optimizer']:7} | "
                  f"{r['n_trainable']:>10,} | {r.get('step_warm_sec', '—'):>5} | "
                  f"{r.get('peak_vram_gb', '—'):>5} | "
                  f"{r.get('final_loss', '—'):>6} | "
                  f"{r.get('avg_loss', '—'):>6} | {losses} |")
        else:
            print(f"| {r.get('master', '?'):4} | {r.get('optimizer', '?'):7} | "
                  f"{r.get('status', '?')} | — | — | — | — | — |")


if __name__ == "__main__":
    main()
