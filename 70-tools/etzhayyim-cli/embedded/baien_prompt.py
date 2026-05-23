"""Single-prompt baien inference — embedded by `e7m baien prompt`.

Read prompt from --prompt (CLI) or stdin. Print response + lightweight
timing on stdout. Designed to be CPU-safe (default) so it can run
alongside a ROCm bench job on EVO-X2 without GPU contention.

Usage (on the host where baien is loadable, e.g. EVO-X2):
  python baien_prompt.py --prompt "日本の首都は?"
  echo "explain BitNet 1.58" | python baien_prompt.py --max-new 128

Flags:
  --model       HuggingFace id or local dir (default: bitnet-b1.58-2B-4T-bf16)
  --max-new     max new tokens (default 256)
  --temperature 0.0=greedy (default), >0=sampling
  --system      optional system prompt (default: none)
  --json        emit a single JSON object on stdout instead of plain text
"""

from __future__ import annotations

import os

os.environ.setdefault("TORCH_COMPILE_DISABLE", "1")
os.environ.setdefault("TORCHINDUCTOR_DISABLE", "1")

import argparse
import json
import sys
import time
from datetime import datetime, timezone


def _load(model_id: str):
    import torch
    try:
        import torch._dynamo as _dyn
        _dyn.config.suppress_errors = True
        _dyn.disable()
    except Exception:
        pass
    try:
        from torch._inductor import cpu_vec_isa
        cpu_vec_isa.valid_vec_isa_list = lambda: []  # type: ignore[assignment]
    except Exception:
        pass

    from transformers import AutoModelForCausalLM, AutoTokenizer
    tok = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(model_id, dtype=torch.bfloat16)
    model.eval()
    return tok, model


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt", default=None, help="prompt text (or omit to read stdin)")
    ap.add_argument("--model", default="microsoft/bitnet-b1.58-2B-4T-bf16")
    ap.add_argument("--max-new", type=int, default=256)
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--system", default=None, help="optional system prompt")
    ap.add_argument("--json", action="store_true", help="emit single JSON object")
    args = ap.parse_args()

    prompt = args.prompt
    if prompt is None:
        prompt = sys.stdin.read().strip()
    if not prompt:
        print("error: empty prompt (pass --prompt or pipe text on stdin)",
              file=sys.stderr)
        return 2

    if not args.json:
        print(f"[baien-prompt] loading {args.model} ...", file=sys.stderr, flush=True)
    t_load0 = time.perf_counter()
    tok, model = _load(args.model)
    t_load = time.perf_counter() - t_load0

    import torch

    messages = []
    if args.system:
        messages.append({"role": "system", "content": args.system})
    messages.append({"role": "user", "content": prompt})

    if hasattr(tok, "apply_chat_template") and tok.chat_template:
        enc = tok.apply_chat_template(
            messages, add_generation_prompt=True,
            return_tensors="pt", return_dict=True,
        )
    else:
        enc = tok(prompt, return_tensors="pt")

    input_ids = enc["input_ids"]
    n_in = int(input_ids.shape[1])

    gen_kwargs = dict(
        max_new_tokens=args.max_new,
        pad_token_id=tok.eos_token_id,
    )
    if args.temperature > 0:
        gen_kwargs.update(do_sample=True, temperature=args.temperature)
    else:
        gen_kwargs.update(do_sample=False)

    t_gen0 = time.perf_counter()
    with torch.no_grad():
        out = model.generate(**enc, **gen_kwargs)
    t_gen = time.perf_counter() - t_gen0

    new_ids = out[0, input_ids.shape[1]:]
    n_out = int(new_ids.shape[0])
    response = tok.decode(new_ids, skip_special_tokens=True)
    tok_per_s = (n_out / t_gen) if t_gen > 0 else 0.0

    if args.json:
        json.dump({
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "model": args.model,
            "prompt": prompt,
            "system": args.system,
            "response": response,
            "input_tokens": n_in,
            "output_tokens": n_out,
            "load_sec": round(t_load, 2),
            "gen_sec": round(t_gen, 2),
            "tokens_per_sec": round(tok_per_s, 2),
        }, sys.stdout, ensure_ascii=False)
        sys.stdout.write("\n")
    else:
        print(response)
        print(
            f"\n[baien-prompt] {n_in} in / {n_out} out, "
            f"load {t_load:.1f}s, gen {t_gen:.1f}s ({tok_per_s:.1f} tok/s)",
            file=sys.stderr, flush=True,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
