"""Quantization training-efficiency shootout on a single base + LoRA on top.

Goal: measure per-step wall time, peak VRAM, quantize wall time, model VRAM,
final train_loss for the same SFT task across multiple quant treatments
of the same FROZEN base + LoRA on top.

Defaults are tuned to fit in a single ~1-hour bench window on EVO-X2
(AMD Radeon 8060S, gfx1151, 60 GB, torch 2.9.1+rocm7.2.1):
  - Zyphra/Zamba2-1.2B-Instruct (Apache-2.0)
  - 16 SFT rows from lordx64/reasoning-distill-opus-4-7-max-sft (Apache-2.0)
  - 10 optimizer steps (epochs=1, batch=1, grad_accum=4)
  - q/k/v/o LoRA r=16

Each row is fully isolated (no cross-leak in cuda memory): the script
respawns a subprocess per row so torch state, cuda cache, and quanto
hooks are torn down between runs.

Output: one JSON file at the end with all rows + a markdown summary printed
to stdout.

Per-format paths supported (this script):
  - bf16            : no quantize (baseline)
  - quanto-int8     : optimum.quanto qint8
  - quanto-int4     : optimum.quanto qint4
  - quanto-int2     : optimum.quanto qint2  (1.58-bit proxy)
  - bonsai-sign-1bit: in-place sign(W)*mean(|W|) + bf16 storage (roso stub)

Blocked on this hw (documented, not run):
  - bnb-int8 / bnb-nf4 / bnb-int4 : bitsandbytes ROCm DLL missing
  - fp8 / fp4                      : transformer-engine not installed; gfx1151
                                     has no native fp8/fp4 hw anyway
                                     (only H100 / MI300X)
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

# ---------- per-row training worker --------------------------------------

def run_one_row(quant: str, base: str, n_rows: int, n_steps: int,
                dataset_id: str, out_dir: Path) -> dict:
    """Spawn a fresh python subprocess for one row to isolate torch state."""
    payload = {
        "quant": quant,
        "base": base,
        "n_rows": n_rows,
        "n_steps": n_steps,
        "dataset_id": dataset_id,
        "out_dir": str(out_dir),
    }
    here = Path(__file__).parent.resolve()
    cmd = [sys.executable, "-u", str(here / "_one_row.py"), json.dumps(payload)]
    env = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8",
           "TORCH_COMPILE_DISABLE": "1", "TORCHINDUCTOR_DISABLE": "1"}
    t0 = time.time()
    cp = subprocess.run(cmd, env=env, capture_output=True, text=True)
    wall = time.time() - t0
    log_path = out_dir / f"row-{quant}.log"
    log_path.write_text((cp.stdout or "") + "\n--- STDERR ---\n" + (cp.stderr or ""),
                        encoding="utf-8")
    # Worker writes its result row to out_dir/row-<quant>.json
    res_path = out_dir / f"row-{quant}.json"
    if res_path.exists():
        row = json.loads(res_path.read_text(encoding="utf-8"))
    else:
        row = {"quant": quant, "status": "crash", "stderr_tail": (cp.stderr or "")[-400:]}
    row["wall_total_sec"] = round(wall, 1)
    row["exit_code"] = cp.returncode
    return row


def main():
    ap = argparse.ArgumentParser(prog="quant-training-shootout")
    ap.add_argument("--base", default="Zyphra/Zamba2-1.2B-Instruct")
    ap.add_argument("--dataset", default="lordx64/reasoning-distill-opus-4-7-max-sft")
    ap.add_argument("--rows", type=int, default=16, help="dataset rows used as SFT examples")
    ap.add_argument("--steps", type=int, default=10, help="optimizer steps per row")
    ap.add_argument("--out", type=Path, default=Path("./shootout-out"))
    ap.add_argument("--methods", nargs="+",
                    default=["bf16", "quanto-int8", "quanto-int4", "quanto-int2",
                             "bonsai-sign-1bit"])
    args = ap.parse_args()

    out: Path = args.out
    out.mkdir(parents=True, exist_ok=True)
    print(f"[shootout] base={args.base} rows={args.rows} steps={args.steps} "
          f"methods={args.methods} out={out}", flush=True)

    rows: list[dict] = []
    for method in args.methods:
        print(f"\n[shootout] === {method} ===", flush=True)
        row = run_one_row(method, args.base, args.rows, args.steps,
                          args.dataset, out)
        rows.append(row)
        print(f"[shootout] {method} result: {json.dumps(row, ensure_ascii=False)}",
              flush=True)

    summary_path = out / "shootout_results.json"
    summary_path.write_text(json.dumps({
        "base": args.base, "dataset": args.dataset,
        "rows": args.rows, "steps": args.steps,
        "results": rows,
    }, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n[shootout] wrote {summary_path}", flush=True)

    # markdown summary
    print("\n## Shootout summary")
    print()
    print("| method | status | quantize_s | model_gb | trainable | "
          "step_warm_s | peak_vram_gb | final_loss |")
    print("|---|---|---|---|---|---|---|---|")
    for r in rows:
        if r.get("status") == "ok":
            print(f"| {r['quant']:18} | OK | "
                  f"{r.get('quantize_sec', '—'):>6} | "
                  f"{r.get('model_gb', '—'):>6} | "
                  f"{r.get('trainable_params', '—')} | "
                  f"{r.get('step_warm_sec', '—'):>6} | "
                  f"{r.get('peak_vram_gb', '—'):>6} | "
                  f"{r.get('final_loss', '—')} |")
        else:
            print(f"| {r['quant']:18} | {r.get('status', '?')} | — | — | — | — | — | — |")


if __name__ == "__main__":
    main()
