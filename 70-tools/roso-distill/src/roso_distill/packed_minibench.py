"""Minibench for packed-bit checkpoints (load via packed_infer, score via
microbench scorers). Used to compare Bonsai-calibrated vs naive sign-quant
on the same 15-prompt verifiable smoke set.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import torch

from .packed_infer import load_packed_checkpoint


# ---- inline scorers + prompts (mirrors baien-microbench) ----

def s_ifeval_5caps(o: str) -> tuple[bool, str]:
    lines = [l.strip() for l in o.strip().splitlines() if l.strip()]
    if len(lines) != 5:
        return False, f"want 5 lines got {len(lines)}"
    if lines != sorted(lines):
        return False, "not alpha order"
    return True, "ok"


def s_ifeval_haiku(o: str) -> tuple[bool, str]:
    lines = [l for l in o.strip().splitlines() if l.strip()]
    return (len(lines) == 3, f"want 3 lines got {len(lines)}")


def s_ifeval_uppercase(o: str) -> tuple[bool, str]:
    s = o.strip().strip("'\"")
    return (s == "I LOVE TOKYO", f"got {s!r}")


def s_ifeval_json(o: str) -> tuple[bool, str]:
    try:
        s = o.strip()
        if "```" in s:
            s = re.sub(r"```\w*\n?", "", s).strip("` \n")
        d = json.loads(s)
        return (set(d.keys()) >= {"name", "age", "city"}, "ok")
    except Exception as e:
        return False, f"parse: {e!r}"


def s_ifeval_wordcount(o: str) -> tuple[bool, str]:
    words = re.findall(r"[A-Za-z']+", o)
    return (10 <= len(words) <= 20, f"{len(words)} words")


def make_mc_scorer(want: str):
    def _s(o: str) -> tuple[bool, str]:
        m = re.search(r"\b([A-D])\b", o.upper())
        got = m.group(1) if m else "?"
        return (got == want, f"got {got}")
    return _s


def s_math_bat_ball(o: str) -> tuple[bool, str]:
    return (bool(re.search(r"\$?0?\.05\b|5\s*cents?\b", o.lower())), o[:60])


def s_translate_jp_capital(o: str) -> tuple[bool, str]:
    return (bool(re.search(r"東京|Tokyo|とうきょう", o)), o[:30])


def s_translate_en_thank(o: str) -> tuple[bool, str]:
    return (bool(re.search(r"thank you|thanks", o.lower())), o[:30])


PROMPTS = [
    ("ifeval_5caps", "IFEval",
     "List exactly 5 European capitals, one per line, in alphabetical order. No additional text, no numbering.",
     s_ifeval_5caps, 256),
    ("ifeval_haiku", "IFEval",
     "Write a haiku about autumn in English. Exactly 3 lines, no title, no extra text.",
     s_ifeval_haiku, 256),
    ("ifeval_uppercase", "IFEval",
     "Reply with the sentence 'I LOVE TOKYO' in all uppercase letters. No other text.",
     s_ifeval_uppercase, 32),
    ("ifeval_json", "IFEval",
     "Return a JSON object with keys name, age, city for a fictional person. Only the JSON.",
     s_ifeval_json, 256),
    ("ifeval_wordcount", "IFEval",
     "Write a single sentence about the ocean using between 10 and 20 words. No quotation marks.",
     s_ifeval_wordcount, 256),
    ("mmlu_geo_jp", "MMLU",
     "What is the capital of Japan?\n(A) Osaka (B) Kyoto (C) Tokyo (D) Sapporo\nAnswer with the single letter only.",
     make_mc_scorer("C"), 16),
    ("mmlu_chem_h2o", "MMLU",
     "Which element has atomic number 1?\n(A) Helium (B) Hydrogen (C) Lithium (D) Oxygen\nAnswer with the single letter only.",
     make_mc_scorer("B"), 16),
    ("mmlu_phys_speed", "MMLU",
     "What is the approximate speed of light in vacuum?\n(A) 3e6 m/s (B) 3e7 m/s (C) 3e8 m/s (D) 3e9 m/s\nAnswer with the single letter only.",
     make_mc_scorer("C"), 16),
    ("mmlu_hist_ww2", "MMLU",
     "In which year did World War II end?\n(A) 1918 (B) 1939 (C) 1945 (D) 1950\nAnswer with the single letter only.",
     make_mc_scorer("C"), 16),
    ("mmlu_math_prime", "MMLU",
     "Which of the following is a prime number?\n(A) 9 (B) 15 (C) 17 (D) 21\nAnswer with the single letter only.",
     make_mc_scorer("C"), 16),
    ("reason_batball", "Reasoning",
     "A bat and a ball cost $1.10 in total. The bat costs $1.00 more than the ball. How much does the ball cost?",
     s_math_bat_ball, 128),
    ("mling_jp_capital", "Multilingual",
     "日本の首都は何ですか? 短く一語で答えてください。",
     s_translate_jp_capital, 16),
    ("mling_en_thanks", "Multilingual",
     "次の日本語を英語に訳してください: 「ありがとう」\n英語のみ、短く。",
     s_translate_en_thank, 16),
    ("gen_water", "General",
     "What is the chemical formula of water? One token only.",
     lambda o: (bool(re.search(r"H2O|H₂O", o)), "H2O" if "H2O" in o or "H₂O" in o else "miss"), 8),
    ("gen_continents", "General",
     "How many continents are there? Answer with a single digit only.",
     lambda o: (bool(re.search(r"\b7\b", o)), "7" if "7" in o else "miss"), 8),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", required=True, type=Path)
    ap.add_argument("--out", default="packed_minibench.jsonl")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    print(f"[minibench] loading packed ckpt: {args.ckpt}", flush=True)
    tok, model = load_packed_checkpoint(args.ckpt)
    model.eval()
    print(f"[minibench] model loaded; running {len(PROMPTS)} prompts", flush=True)

    out_path = args.ckpt / args.out
    prompts = PROMPTS[: args.limit] if args.limit > 0 else PROMPTS
    n_ok = 0
    n_total = 0
    by_cat: dict[str, list[bool]] = {}

    with out_path.open("w", encoding="utf-8") as f:
        for pid, cat, prompt, scorer, max_tok in prompts:
            n_total += 1
            try:
                ids = tok(prompt, return_tensors="pt").input_ids
                t0 = time.time()
                with torch.no_grad():
                    out = model.generate(
                        ids, max_new_tokens=max_tok,
                        do_sample=False, pad_token_id=tok.eos_token_id)
                dt = time.time() - t0
                resp = tok.decode(out[0, ids.shape[1]:], skip_special_tokens=True)
                ok, reason = scorer(resp)
            except Exception as e:
                ok, reason, resp, dt = False, f"EXC: {type(e).__name__}: {e!r}", "", 0.0
            if ok:
                n_ok += 1
            by_cat.setdefault(cat, []).append(ok)
            row = {
                "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "id": pid, "category": cat, "ok": ok, "reason": reason,
                "elapsed_sec": round(dt, 2), "response": resp[:300],
            }
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            f.flush()
            print(f"  [{n_total}/{len(prompts)}] {pid} {'PASS' if ok else 'FAIL'} "
                  f"({reason[:50]}) {dt:.1f}s", flush=True)

    print(f"\n[minibench] exact_match: {n_ok}/{n_total} ({100*n_ok/max(n_total,1):.1f}%)")
    for cat, bools in by_cat.items():
        print(f"  {cat}: {sum(bools)}/{len(bools)}")
    print(f"  out: {out_path}")


if __name__ == "__main__":
    main()
