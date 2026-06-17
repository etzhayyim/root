#!/usr/bin/env python3
"""
baien microbench — minimal verifiable bench for BitNet b1.58 2B-4T (baien).

15 prompts across IFEval-like instruction following, MMLU-style multiple choice,
and JP/EN reasoning. Each prompt has a rule-based scorer so we get a single
numeric pass-rate per category, comparable to the frontier-LLM bench table.

Usage (on EVO-X2 / wherever baien is loaded):
  python microbench.py --model microsoft/bitnet-b1.58-2B-4T-bf16
  python microbench.py --model microsoft/bitnet-b1.58-2B-4T-bf16 --out results.jsonl
"""

from __future__ import annotations

import os

os.environ.setdefault("TORCH_COMPILE_DISABLE", "1")
os.environ.setdefault("TORCHINDUCTOR_DISABLE", "1")

import argparse
import json
import re
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

EU_CAPITALS = {
    "amsterdam","athens","berlin","bratislava","brussels","bucharest","budapest",
    "copenhagen","dublin","helsinki","lisbon","ljubljana","london","luxembourg",
    "madrid","monaco","nicosia","oslo","paris","prague","reykjavik","riga",
    "rome","sofia","stockholm","tallinn","valletta","vienna","vilnius","warsaw",
    "zagreb","bern",
}


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def _lines(s: str) -> list[str]:
    return [l.strip() for l in s.strip().splitlines() if l.strip()]


# ----- scorers ------------------------------------------------------------

def s_ifeval_5caps(out: str) -> tuple[bool, str]:
    ls = _lines(out)
    if len(ls) != 5:
        return False, f"want 5 lines, got {len(ls)}"
    if [l.lower() for l in ls] != sorted([l.lower() for l in ls]):
        return False, "not alphabetical"
    bad = [l for l in ls if l.lower() not in EU_CAPITALS]
    if bad:
        return False, f"non-EU-capital: {bad}"
    return True, "ok"


def s_ifeval_haiku(out: str) -> tuple[bool, str]:
    ls = _lines(out)
    if len(ls) != 3:
        return False, f"haiku must be 3 lines, got {len(ls)}"
    return True, "3-line ok"


def s_ifeval_uppercase(out: str) -> tuple[bool, str]:
    o = _norm(out)
    if not o:
        return False, "empty"
    if o != o.upper():
        return False, "not all-uppercase"
    return True, "ok"


def s_ifeval_json(out: str) -> tuple[bool, str]:
    m = re.search(r"\{.*\}", out, re.DOTALL)
    if not m:
        return False, "no JSON object"
    try:
        d = json.loads(m.group(0))
    except Exception as e:
        return False, f"json parse: {e}"
    for k in ("name", "age", "city"):
        if k not in d:
            return False, f"missing key: {k}"
    return True, "ok"


def s_ifeval_wordcount(out: str) -> tuple[bool, str]:
    n = len(out.split())
    return (10 <= n <= 20), f"words={n} (want 10-20)"


def _mc_pick(out: str) -> str | None:
    # accept "A" / "Answer: A" / "(A)" etc
    m = re.search(r"\b([ABCD])\b", out)
    return m.group(1) if m else None


def make_mc_scorer(correct: str) -> Callable[[str], tuple[bool, str]]:
    def f(out: str) -> tuple[bool, str]:
        p = _mc_pick(out)
        if p is None:
            return False, "no choice found"
        return (p == correct), f"picked={p} correct={correct}"
    return f


def s_math_bat_ball(out: str) -> tuple[bool, str]:
    # bat-ball puzzle correct answer: ball = $0.05
    if re.search(r"0?\.05|5\s*cents|five\s*cents|\$0\.05", out, re.I):
        return True, "got 0.05"
    return False, "missing 0.05"


def s_translate_jp_capital(out: str) -> tuple[bool, str]:
    # accept Tokyo / 東京
    if re.search(r"tokyo|東京", out, re.I):
        return True, "tokyo present"
    return False, "no tokyo"


def s_translate_en_thank(out: str) -> tuple[bool, str]:
    if re.search(r"thank\s*you|thanks", out, re.I):
        return True, "thanks present"
    return False, "no thanks"


# ----- prompt set ---------------------------------------------------------

@dataclass
class Prompt:
    id: str
    category: str
    prompt: str
    scorer: Callable[[str], tuple[bool, str]]
    max_tokens: int = 256


PROMPTS: list[Prompt] = [
    # IFEval-like (instruction following, verifiable)
    Prompt("ifeval_5caps", "IFEval",
           "List exactly 5 European capitals, one per line, in alphabetical order. "
           "No additional text, no numbering, no explanations.",
           s_ifeval_5caps),
    Prompt("ifeval_haiku", "IFEval",
           "Write a haiku about autumn in English. Exactly 3 lines, no title, no extra text.",
           s_ifeval_haiku),
    Prompt("ifeval_uppercase", "IFEval",
           "Reply with the sentence 'I LOVE TOKYO' in all uppercase letters. "
           "No other text.",
           s_ifeval_uppercase, max_tokens=32),
    Prompt("ifeval_json", "IFEval",
           "Return a JSON object with keys name, age, city for a fictional person. "
           "Only the JSON, no markdown fences, no commentary.",
           s_ifeval_json),
    Prompt("ifeval_wordcount", "IFEval",
           "Write a single sentence about the ocean using between 10 and 20 words. "
           "No quotation marks.",
           s_ifeval_wordcount),

    # MMLU-style multiple choice (one each from 5 domains; canonical questions)
    Prompt("mmlu_geo_jp", "MMLU",
           "What is the capital of Japan?\n(A) Osaka (B) Kyoto (C) Tokyo (D) Sapporo\n"
           "Answer with the single letter only.",
           make_mc_scorer("C"), max_tokens=16),
    Prompt("mmlu_chem_h2o", "MMLU",
           "Which element has atomic number 1?\n(A) Helium (B) Hydrogen (C) Lithium (D) Oxygen\n"
           "Answer with the single letter only.",
           make_mc_scorer("B"), max_tokens=16),
    Prompt("mmlu_phys_speed", "MMLU",
           "What is the approximate speed of light in vacuum?\n"
           "(A) 3e6 m/s (B) 3e7 m/s (C) 3e8 m/s (D) 3e9 m/s\n"
           "Answer with the single letter only.",
           make_mc_scorer("C"), max_tokens=16),
    Prompt("mmlu_hist_ww2", "MMLU",
           "In which year did World War II end?\n"
           "(A) 1918 (B) 1939 (C) 1945 (D) 1950\n"
           "Answer with the single letter only.",
           make_mc_scorer("C"), max_tokens=16),
    Prompt("mmlu_math_prime", "MMLU",
           "Which of the following is a prime number?\n"
           "(A) 9 (B) 15 (C) 17 (D) 21\n"
           "Answer with the single letter only.",
           make_mc_scorer("C"), max_tokens=16),

    # Reasoning
    Prompt("reason_batball", "Reasoning",
           "A bat and a ball cost $1.10 in total. The bat costs $1.00 more than the ball. "
           "How much does the ball cost? Answer in one short line.",
           s_math_bat_ball, max_tokens=128),

    # Multilingual basics
    Prompt("mling_jp_capital", "Multilingual",
           "日本の首都は何ですか? 短く一語で答えてください。",
           s_translate_jp_capital, max_tokens=16),
    Prompt("mling_en_thanks", "Multilingual",
           "次の日本語を英語に訳してください: 「ありがとう」\n英語のみ、短く。",
           s_translate_en_thank, max_tokens=16),

    # General knowledge
    Prompt("gen_water", "General",
           "What is the chemical formula of water? One token only.",
           lambda o: (bool(re.search(r"H2O|H₂O", o)), "H2O" if "H2O" in o or "H₂O" in o else "missing"),
           max_tokens=8),
    Prompt("gen_continents", "General",
           "How many continents are there? Answer with a single digit only.",
           lambda o: (bool(re.search(r"\b7\b", o)), "7" if "7" in o else "missing"),
           max_tokens=8),
]


# ----- model adapter ------------------------------------------------------

def load_hf(model_id: str, diffusion: bool = False):
    import torch
    try:
        import torch._dynamo as _dyn
        _dyn.config.suppress_errors = True
        _dyn.disable()
    except Exception:
        pass
    if diffusion:
        # discrete diffusion LM (e.g. google/diffusiongemma-26B-A4B-it): needs the
        # DiffusionGemma class + a processor. device_map="auto" leaves it on meta
        # tensors (accelerate gap), so load plain on CPU (ADR-2606171100 verification).
        from transformers import DiffusionGemmaForBlockDiffusion, AutoProcessor
        torch.set_num_threads(16)
        proc = AutoProcessor.from_pretrained(model_id)
        model = DiffusionGemmaForBlockDiffusion.from_pretrained(model_id, dtype=torch.bfloat16)
        model.eval()
        return proc, model
    from transformers import AutoModelForCausalLM, AutoTokenizer
    tok = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(
        model_id, dtype=torch.bfloat16
    )
    model.eval()
    return tok, model


def generate(tok, model, prompt: str, max_new_tokens: int, diffusion: bool = False) -> tuple[str, float]:
    import torch
    if diffusion:
        enc = tok.apply_chat_template(
            [{"role": "user", "content": prompt}],
            tokenize=True, add_generation_prompt=True,
            return_tensors="pt", return_dict=True,
        ).to(model.device)
        in_len = enc["input_ids"].shape[1]
        t0 = time.perf_counter()
        with torch.no_grad():
            out = model.generate(**enc, max_new_tokens=max_new_tokens)  # diffusion: no do_sample/pad
        dt = time.perf_counter() - t0
        seq = getattr(out, "sequences", out)
        if not hasattr(seq, "shape"):
            seq = next(v for v in vars(out).values() if hasattr(v, "shape"))
        text = tok.decode(seq[0][in_len:], skip_special_tokens=True)
        return text, dt
    if hasattr(tok, "apply_chat_template") and tok.chat_template:
        enc = tok.apply_chat_template(
            [{"role": "user", "content": prompt}],
            add_generation_prompt=True, return_tensors="pt", return_dict=True,
        )
    else:
        enc = tok(prompt, return_tensors="pt")
    input_ids = enc["input_ids"]
    t0 = time.perf_counter()
    with torch.no_grad():
        out = model.generate(
            **enc, max_new_tokens=max_new_tokens,
            do_sample=False,
            pad_token_id=tok.eos_token_id,
        )
    dt = time.perf_counter() - t0
    new = out[0, input_ids.shape[1]:]
    text = tok.decode(new, skip_special_tokens=True)
    return text, dt


# ----- main ---------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="microsoft/bitnet-b1.58-2B-4T-bf16")
    ap.add_argument("--out", default="results.jsonl")
    ap.add_argument("--limit", type=int, default=0,
                    help="if >0, run only the first N prompts (debug)")
    ap.add_argument("--diffusion", action="store_true",
                    help="load as a DiffusionGemma block-diffusion LM (ADR-2606171100)")
    args = ap.parse_args()

    print(f"[load] {args.model} (diffusion={args.diffusion})", flush=True)
    tok, model = load_hf(args.model, diffusion=args.diffusion)
    print(f"[load] done", flush=True)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    n_total = 0
    n_ok = 0
    by_cat: dict[str, list[bool]] = {}

    prompts = PROMPTS[: args.limit] if args.limit > 0 else PROMPTS

    with out_path.open("a", encoding="utf-8") as f:
        for p in prompts:
            try:
                resp, dt = generate(tok, model, p.prompt, p.max_tokens, diffusion=args.diffusion)
                ok, reason = p.scorer(resp)
                row = {
                    "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    "model": args.model, "id": p.id, "category": p.category,
                    "ok": ok, "reason": reason, "elapsed_sec": round(dt, 2),
                    "response": resp,
                }
            except Exception as e:
                import traceback
                tb = traceback.format_exc()
                row = {
                    "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    "model": args.model, "id": p.id, "category": p.category,
                    "ok": False, "reason": f"EXC: {type(e).__name__}: {e!r}",
                    "traceback": tb,
                    "elapsed_sec": 0.0, "response": "",
                }
                print(tb, file=sys.stderr, flush=True)
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            f.flush()
            n_total += 1
            n_ok += int(row["ok"])
            by_cat.setdefault(p.category, []).append(bool(row["ok"]))
            mark = "PASS" if row["ok"] else "FAIL"
            print(f"  {mark:4} [{p.category:12}] {p.id:20} {row['reason']}", flush=True)

    print()
    print(f"[summary] {n_ok}/{n_total} = {100*n_ok/n_total:.1f}%")
    for cat, oks in sorted(by_cat.items()):
        print(f"  {cat:14} {sum(oks)}/{len(oks)} = {100*sum(oks)/len(oks):.1f}%")
    return 0


if __name__ == "__main__":
    sys.exit(main())
