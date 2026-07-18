#!/usr/bin/env python3
"""Loop C R1 cohort-bench — run a HF causal-LM (optionally base+LoRA) through the
SAME e7m microbench set (70-tools/scripts/bench/baien-microbench/microbench.py) and
report a real pass-rate + tok/s, so Loop C's genotypes.edn t2 signals are comparable.

Murakumo-only (run on gad / EVO-X2). Usage on gad:
  scp 70-tools/scripts/bench/baien-microbench/microbench.py gad:~/maxwell/
  scp 70-tools/scripts/maxwell/bench_micro.py               gad:~/maxwell/
  ssh gad 'cd ~/maxwell && HSA_OVERRIDE_GFX_VERSION=11.5.1 HF_HUB_OFFLINE=1 \
    venv-train/bin/python bench_micro.py --base google/gemma-4-E4B-it \
      --adapter ~/maxwell/out/m1-r1 --label maxwell-1 --out maxwell1_micro.json'
Then fold {score, tok_s} into orgs/etzhayyim/com-etzhayyim-shinka/loop_c/genotypes.edn and `bb rank.clj`.
"""
import os, sys, time, json, argparse, pathlib
os.environ.setdefault("TORCH_COMPILE_DISABLE","1"); os.environ.setdefault("TORCHINDUCTOR_DISABLE","1")
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path.home()/"maxwell"))  # gad scp target
import microbench as mb  # noqa: E402

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--adapter", default="")
    ap.add_argument("--label", default="model")
    ap.add_argument("--out", default="micro.json")
    a = ap.parse_args()
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    tok = AutoTokenizer.from_pretrained(a.base)
    model = AutoModelForCausalLM.from_pretrained(
        a.base, dtype=torch.bfloat16, device_map={"": 0}, attn_implementation="eager")
    tag = a.label
    if a.adapter and pathlib.Path(a.adapter).exists():
        from peft import PeftModel
        model = PeftModel.from_pretrained(model, a.adapter)
    else:
        tag += " (BASE — no adapter)"
    model.eval()

    def gen(prompt, mnt):
        enc = tok.apply_chat_template([{"role": "user", "content": prompt}],
            add_generation_prompt=True, return_tensors="pt", return_dict=True)
        enc = {k: v.to("cuda") for k, v in enc.items()}
        n_in = enc["input_ids"].shape[1]; t0 = time.perf_counter()
        with torch.no_grad():
            out = model.generate(**enc, max_new_tokens=mnt, do_sample=False,
                                  pad_token_id=tok.eos_token_id)
        return tok.decode(out[0][n_in:], skip_special_tokens=True), out.shape[1]-n_in, time.perf_counter()-t0

    print(f"=== {tag} on e7m micro ({len(mb.PROMPTS)} prompts) ===", flush=True)
    npass = ntok = 0; ttime = 0.0; rows = []
    for p in mb.PROMPTS:
        resp, nt, dt = gen(p.prompt, p.max_tokens)
        ok, why = p.scorer(resp); npass += ok; ntok += nt; ttime += dt
        rows.append({"name": p.name, "cat": p.category, "pass": bool(ok)})
        print(f"  {'PASS' if ok else 'FAIL'} {p.name:18s} {why[:40]}", flush=True)
    score = npass/len(mb.PROMPTS); toks = ntok/ttime if ttime else 0.0
    print(json.dumps({"model": tag, "score": round(score,4), "pass": npass,
        "n": len(mb.PROMPTS), "tok_s": round(toks,2)}), flush=True)
    pathlib.Path(a.out).write_text(json.dumps({"label": a.label, "score": score,
        "tok_s": toks, "rows": rows}))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
