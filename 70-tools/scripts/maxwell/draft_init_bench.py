"""maxwell-diffusion warm-start (draft-initialized denoising) — speed+quality bench.

Speculative-style drafter for the block-diffusion TARGET. DiffusionGemma's sampler seeds
its canvas from `decoder_input_ids` if provided, else from a uniform-RANDOM canvas
(generation_diffusion_gemma.py ~985:
    current_canvas = model_kwargs.pop("decoder_input_ids", sampler.initialize_canvas(...)))
A cheap AR drafter proposes a canvas; we hand it to the denoiser as the starting point.
A draft close to the target sits at low effective diffusion-time t, so the entropy-bound
sampler's adaptive stopping should converge in fewer decoder forward passes. A draft FAR
from the target makes the sampler thrash (low acceptance -> repeated renoise) and is SLOWER
than random init -- exactly the speculative-decoding acceptance-rate dependence.

Two modes (run draft first, free the drafter, then bench -- avoids 52GB+drafter co-residency):
  --mode draft  --drafter google/gemma-4-E4B-it --drafts ~/maxwell/drafts.jsonl
  --mode bench  --drafts ~/maxwell/drafts.jsonl --out ~/maxwell/specdiff_results.jsonl

PARTIAL warm-start: only the draft's real length seeds the canvas; the tail stays uniform-
random (so short answers aren't penalised by a forced full 256-token content canvas).

Speed is reported as honest wall-clock seconds and derived decoder-forward passes (NOT just
`tokens_per_forward`, which is confounded by output length). Quality uses the SAME e7m micro
PROMPTS/scorers that produced the 80% diffusion base bench (ADR-2606171100).

Murakumo-only (ADR-2605215000): gad (EVO-X2), CPU bf16. No commercial GPU / external API.
"""
import argparse
import json
import pathlib
import sys
import time

import torch

MID = "google/diffusiongemma-26B-A4B-it"

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import microbench as mb  # noqa: E402


# ---- mode: draft -----------------------------------------------------------
def run_draft(drafter_id, drafts_path):
    from transformers import AutoModelForCausalLM, AutoTokenizer
    torch.set_num_threads(16)
    print(f"[draft] load {drafter_id}", flush=True)
    tok = AutoTokenizer.from_pretrained(drafter_id)
    model = AutoModelForCausalLM.from_pretrained(drafter_id, dtype=torch.bfloat16)
    model.eval()
    rows = []
    for p in mb.PROMPTS:
        if tok.chat_template:
            enc = tok.apply_chat_template([{"role": "user", "content": p.prompt}],
                                          add_generation_prompt=True, return_tensors="pt",
                                          return_dict=True)
        else:
            enc = tok(p.prompt, return_tensors="pt")
        t0 = time.perf_counter()
        with torch.no_grad():
            out = model.generate(**enc, max_new_tokens=min(p.max_tokens, 256),
                                 do_sample=False, pad_token_id=tok.eos_token_id)
        dt = time.perf_counter() - t0
        text = tok.decode(out[0][enc["input_ids"].shape[1]:], skip_special_tokens=True)
        rows.append({"id": p.id, "draft": text, "draft_sec": round(dt, 2)})
        print(f"  [{p.category:11}] {p.id:18} {dt:5.1f}s  {text[:60]!r}", flush=True)
    pathlib.Path(drafts_path).write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in rows), encoding="utf-8")
    print(f"[draft] wrote {len(rows)} drafts -> {drafts_path}", flush=True)


# ---- mode: bench -----------------------------------------------------------
def warm_canvas(proc, draft_text, canvas_len, vocab_size):
    """Partial warm start: draft ids as prefix over an otherwise uniform-random canvas."""
    gtok = getattr(proc, "tokenizer", proc)
    ids = gtok(draft_text, return_tensors="pt", add_special_tokens=False)["input_ids"][0][:canvas_len]
    canvas = torch.randint(0, vocab_size, (canvas_len,), dtype=torch.long)  # = sampler default
    canvas[: len(ids)] = ids
    return canvas.unsqueeze(0), len(ids)


def diff_generate(proc, model, prompt, max_new_tokens, draft_canvas, pad_id):
    enc = proc.apply_chat_template([{"role": "user", "content": prompt}], tokenize=True,
                                   add_generation_prompt=True, return_tensors="pt",
                                   return_dict=True).to(model.device)
    in_len = enc["input_ids"].shape[1]
    kw = dict(enc); kw["max_new_tokens"] = max_new_tokens
    if draft_canvas is not None:
        kw["decoder_input_ids"] = draft_canvas.to(model.device)
    t0 = time.perf_counter()
    with torch.no_grad():
        out = model.generate(**kw)
    dt = time.perf_counter() - t0
    seq = getattr(out, "sequences", out)
    gen = seq[0][in_len:]
    valid = int((gen != pad_id).sum().item())
    tpf = getattr(out, "tokens_per_forward", None)
    if hasattr(tpf, "float"):
        tpf = float(tpf.float().mean().item())
    elif tpf is not None:
        tpf = float(tpf)
    fwd = round(valid / tpf) if tpf else None      # decoder forward passes (derived)
    text = proc.decode(gen, skip_special_tokens=True)
    return text, dt, valid, fwd, tpf


def run_bench(drafts_path, out_path):
    from transformers import AutoProcessor, DiffusionGemmaForBlockDiffusion
    torch.set_num_threads(16)
    drafts = {}
    if drafts_path and pathlib.Path(drafts_path).exists():
        for line in pathlib.Path(drafts_path).read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line); drafts[r["id"]] = r["draft"]
    print(f"[bench] {len(drafts)} drafts loaded; load {MID} (CPU bf16)", flush=True)
    proc = AutoProcessor.from_pretrained(MID)
    model = DiffusionGemmaForBlockDiffusion.from_pretrained(MID, dtype=torch.bfloat16)
    model.eval()
    canvas_len = model.config.canvas_length
    vocab = model.config.text_config.vocab_size
    pad_id = getattr(model.config.text_config, "pad_token_id", 0) or 0
    print(f"[bench] canvas={canvas_len} vocab={vocab} pad={pad_id}", flush=True)

    outp = pathlib.Path(out_path); outp.parent.mkdir(parents=True, exist_ok=True)
    agg = {"base": {"ok": 0, "fwd": 0, "t": 0.0}, "warm": {"ok": 0, "fwd": 0, "t": 0.0}, "n": 0}
    print(f"\n{'cat':12} {'id':18} {'fwd b>w':12} {'ok':5} {'sec b>w':14} drafted", flush=True)
    with outp.open("w", encoding="utf-8") as f:
        for p in mb.PROMPTS:
            dc, dlen = (warm_canvas(proc, drafts[p.id], canvas_len, vocab)
                        if p.id in drafts else (None, 0))
            b_text, b_dt, b_val, b_fwd, b_tpf = diff_generate(proc, model, p.prompt, p.max_tokens, None, pad_id)
            b_ok, b_why = p.scorer(b_text)
            w_text, w_dt, w_val, w_fwd, w_tpf = diff_generate(proc, model, p.prompt, p.max_tokens, dc, pad_id)
            w_ok, w_why = p.scorer(w_text)
            f.write(json.dumps({"id": p.id, "cat": p.category, "draft_len": dlen,
                "base": {"ok": bool(b_ok), "fwd": b_fwd, "sec": round(b_dt, 2), "valid": b_val,
                         "tpf": b_tpf, "why": b_why, "resp": b_text},
                "warm": {"ok": bool(w_ok), "fwd": w_fwd, "sec": round(w_dt, 2), "valid": w_val,
                         "tpf": w_tpf, "why": w_why, "resp": w_text}}, ensure_ascii=False) + "\n")
            f.flush()
            agg["n"] += 1
            agg["base"]["ok"] += int(b_ok); agg["base"]["fwd"] += (b_fwd or 0); agg["base"]["t"] += b_dt
            agg["warm"]["ok"] += int(w_ok); agg["warm"]["fwd"] += (w_fwd or 0); agg["warm"]["t"] += w_dt
            print(f"{p.category:12} {p.id:18} {b_fwd or 0:4}>{w_fwd or 0:<4}     "
                  f"{int(b_ok)}>{int(w_ok)}  {b_dt:5.1f}>{w_dt:6.1f}   dlen={dlen}", flush=True)

    n = agg["n"]
    print(f"\n=== SUMMARY (n={n}) ===", flush=True)
    for k in ("base", "warm"):
        s = agg[k]
        print(f"  {k:5}  quality {s['ok']}/{n}={100*s['ok']/n:4.1f}%   "
              f"fwd_total={s['fwd']:5}   wall={s['t']:7.1f}s", flush=True)
    if agg["base"]["fwd"]:
        dfwd = (1 - agg["warm"]["fwd"] / agg["base"]["fwd"]) * 100
        dwall = (1 - agg["warm"]["t"] / agg["base"]["t"]) * 100 if agg["base"]["t"] else 0
        print(f"  warm-start: forward passes {dfwd:+.1f}%, wall-clock {dwall:+.1f}% (negative = slower)",
              flush=True)
    print(f"  rows -> {out_path}", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["draft", "bench"], required=True)
    ap.add_argument("--drafter", default="google/gemma-4-E4B-it")
    ap.add_argument("--drafts", default=str(pathlib.Path.home() / "maxwell" / "drafts.jsonl"))
    ap.add_argument("--out", default=str(pathlib.Path.home() / "maxwell" / "specdiff_results.jsonl"))
    a = ap.parse_args()
    if a.mode == "draft":
        run_draft(a.drafter, a.drafts)
    else:
        run_bench(a.drafts, a.out)


if __name__ == "__main__":
    main()
