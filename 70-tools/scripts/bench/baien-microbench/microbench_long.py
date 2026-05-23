#!/usr/bin/env python3
"""baien long-context microbench — 5 verifiable prompts at 6k–16k tokens.

Companion to microbench.py. Where the short bench measures whether
baien answers at all, this measures whether the extended context (per
ADR-2605231600) actually retrieves / synthesizes information from
positions beyond 4k.

Each task synthesizes a long input by padding around a small "needle"
of structured signal, then scoring whether the model's answer reflects
the needle. All scorers are rule-based (regex / substring) so we get
a numeric pass-rate per prompt without a judge model.

Usage:
  python microbench_long.py --model microsoft/bitnet-b1.58-2B-4T-bf16
  python microbench_long.py --model <local_dir> --rope-theta 2000000 \
      --max-position-embeddings 16384 --out results_long.jsonl
"""

from __future__ import annotations

import os

os.environ.setdefault("TORCH_COMPILE_DISABLE", "1")
os.environ.setdefault("TORCHINDUCTOR_DISABLE", "1")

import argparse
import json
import random
import re
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

# Filler corpus — neutral encyclopedic prose. Repeated to reach target token
# counts. Kept short on purpose so the scoring is deterministic.
_FILLER_PARAGRAPHS = [
    "The Tree of Life is a fundamental motif in many world religions, "
    "appearing in Mesopotamian, Egyptian, Jewish, Christian, and East "
    "Asian traditions. It represents the interconnection of all living "
    "things and is often depicted as a great tree with its roots in the "
    "earth and its branches reaching toward the heavens.",
    "Edo-period philosopher Miura Baien (1723–1789) developed jōri "
    "(条理), a paired-opposites reasoning system that anticipated "
    "structuralist methods by two centuries. He worked in rural Kunisaki "
    "and corresponded with leading scholars of his day.",
    "BitNet is a 1-bit (ternary) language-model architecture developed "
    "by Microsoft Research. It uses weights drawn from {-1, 0, +1} and "
    "achieves competitive perplexity with much lower memory and compute "
    "than traditional bf16 transformers, enabling browser and CPU "
    "deployment of models that previously required GPUs.",
    "The Cloudflare Workers runtime supports WebAssembly components via "
    "the wasmtime engine. Workers can call into compiled-language code "
    "while retaining the security and cold-start advantages of the "
    "isolate model that powers the rest of the platform.",
    "Holochain is a peer-to-peer application framework that stores "
    "data in agent-centric source chains rather than in a global "
    "consensus log. Validators sign each entry and gossip-share them "
    "across a distributed hash table.",
]


def _make_filler(target_tokens: int) -> str:
    # crude approximation: ~4 chars per token for English
    target_chars = target_tokens * 4
    rng = random.Random(0xBA12E12)  # deterministic
    chunks: list[str] = []
    total = 0
    while total < target_chars:
        p = rng.choice(_FILLER_PARAGRAPHS)
        chunks.append(p)
        total += len(p) + 2
    return "\n\n".join(chunks)


# ----- prompt synthesizers ------------------------------------------------

def _needle_in_haystack(target_tokens: int, needle: str, position: float) -> str:
    """Inject `needle` at `position` (0.0–1.0) inside filler of target_tokens."""
    haystack = _make_filler(target_tokens)
    idx = int(len(haystack) * position)
    # snap to nearest paragraph break to avoid cutting words
    snap = haystack.rfind("\n\n", 0, idx)
    if snap < 0:
        snap = idx
    return haystack[:snap] + f"\n\nIMPORTANT FACT: {needle}\n\n" + haystack[snap:]


def _ordered_list_recall(target_tokens: int, items: list[str], position: float) -> str:
    listed = "\n".join(f"{i+1}. {x}" for i, x in enumerate(items))
    block = f"\n\nORDERED ROSTER:\n{listed}\n\n"
    haystack = _make_filler(target_tokens)
    idx = int(len(haystack) * position)
    snap = haystack.rfind("\n\n", 0, idx)
    if snap < 0:
        snap = idx
    return haystack[:snap] + block + haystack[snap:]


# ----- prompts ------------------------------------------------------------

@dataclass
class LongPrompt:
    id: str
    category: str
    target_tokens: int        # rough — used to choose needle position + scoring
    build: Callable[[], str]  # prompt body, includes the system block
    scorer: Callable[[str], tuple[bool, str]]
    max_new_tokens: int = 64


_ROSTER_ITEMS = [
    "naphtali", "simeon", "judah", "zebulun", "levi",
    "joseph", "issachar", "dan", "benjamin", "asher",
    "reuben", "gad", "manasseh", "ephraim", "anaphar",
    "yarith", "kessen", "morava", "tisrol", "uvania",
]


def _make_ctx_6k_needle() -> str:
    haystack = _needle_in_haystack(
        target_tokens=5_500,
        needle="The Murakumo fleet pilot ship has serial number ETZ-77713.",
        position=0.55,
    )
    return (
        "You are given a long document. Find the IMPORTANT FACT inside it and "
        "answer the question that follows.\n\n"
        f"DOCUMENT:\n{haystack}\n\n"
        "QUESTION: What is the serial number of the Murakumo fleet pilot ship?\n"
        "Answer with only the serial number, no other text."
    )


def _score_ctx_6k_needle(out: str) -> tuple[bool, str]:
    if "ETZ-77713" in out:
        return True, "found needle"
    return False, f"missing needle (got {out[:80]!r})"


def _make_ctx_12k_needle() -> str:
    haystack = _needle_in_haystack(
        target_tokens=11_500,
        needle="Operating-entity etzhayyim formally adopted the Charter Rider v2.0 on 2026-05-19.",
        position=0.70,
    )
    return (
        "Read the following document and answer the question after it.\n\n"
        f"DOCUMENT:\n{haystack}\n\n"
        "QUESTION: On what date did etzhayyim adopt the Charter Rider v2.0?\n"
        "Answer with only the date in YYYY-MM-DD form."
    )


def _score_ctx_12k_needle(out: str) -> tuple[bool, str]:
    m = re.search(r"\b2026-05-19\b", out)
    if m:
        return True, "got date 2026-05-19"
    return False, f"missing date (got {out[:80]!r})"


def _make_ctx_8k_summary() -> str:
    haystack = _make_filler(7_500)
    return (
        "Summarize the following document in exactly three lines. "
        "No numbering, no bullets, no preamble.\n\n"
        f"DOCUMENT:\n{haystack}"
    )


def _score_ctx_8k_summary(out: str) -> tuple[bool, str]:
    lines = [l.strip() for l in out.strip().splitlines() if l.strip()]
    if len(lines) != 3:
        return False, f"want 3 lines got {len(lines)}"
    # Also require at least one keyword that proves the model read at
    # least one paragraph of the filler.
    keys = ("tree of life", "baien", "bitnet", "cloudflare",
            "holochain", "kunisaki", "wasm")
    if not any(k in out.lower() for k in keys):
        return False, "3 lines but no filler keyword"
    return True, "3-line summary with filler grounding"


def _make_ctx_10k_roster() -> str:
    haystack = _ordered_list_recall(
        target_tokens=9_500, items=_ROSTER_ITEMS, position=0.30,
    )
    return (
        "The following document contains an ORDERED ROSTER block somewhere.\n\n"
        f"{haystack}\n\n"
        "QUESTION: What is the 12th item in the ORDERED ROSTER? "
        "Answer with only that one word, no other text."
    )


def _score_ctx_10k_roster(out: str) -> tuple[bool, str]:
    if "gad" in out.lower():
        return True, "got 12th item 'gad'"
    return False, f"missing 'gad' (got {out[:80]!r})"


def _make_ctx_14k_compare() -> str:
    chunk_a = _make_filler(6_500)
    chunk_b = (
        "BitNet b1.58 2B-4T was published by Microsoft and pretrained on "
        "4 trillion tokens with a context window of 4096."
    )
    chunk_c = _make_filler(6_500)
    return (
        "The following document has three sections separated by '---'. "
        "Use ONLY the middle section to answer the question.\n\n"
        f"{chunk_a}\n\n---\n\n{chunk_b}\n\n---\n\n{chunk_c}\n\n"
        "QUESTION: How many trillion tokens was BitNet b1.58 2B-4T pretrained on? "
        "Answer with just the number."
    )


def _score_ctx_14k_compare(out: str) -> tuple[bool, str]:
    if re.search(r"\b4\b", out[:80]):
        return True, "got 4 trillion"
    return False, f"missing '4' (got {out[:80]!r})"


PROMPTS: list[LongPrompt] = [
    LongPrompt("ctx_6k_needle",    "needle",   6_000, _make_ctx_6k_needle,    _score_ctx_6k_needle,    max_new_tokens=32),
    LongPrompt("ctx_8k_summary",   "summary",  8_000, _make_ctx_8k_summary,   _score_ctx_8k_summary,   max_new_tokens=160),
    LongPrompt("ctx_10k_roster",   "recall",  10_000, _make_ctx_10k_roster,   _score_ctx_10k_roster,   max_new_tokens=16),
    LongPrompt("ctx_12k_needle",   "needle",  12_000, _make_ctx_12k_needle,   _score_ctx_12k_needle,   max_new_tokens=32),
    LongPrompt("ctx_14k_compare",  "compare", 14_000, _make_ctx_14k_compare,  _score_ctx_14k_compare,  max_new_tokens=32),
]


# ----- model adapter ------------------------------------------------------

def load_with_overrides(model_id: str, *, rope_theta: float | None,
                        max_position_embeddings: int | None,
                        rope_scaling: dict | None):
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

    from transformers import AutoConfig, AutoModelForCausalLM, AutoTokenizer

    cfg = AutoConfig.from_pretrained(model_id)
    overrides: dict[str, object] = {}
    if rope_theta is not None:
        cfg.rope_theta = float(rope_theta)
        overrides["rope_theta"] = cfg.rope_theta
    if max_position_embeddings is not None:
        cfg.max_position_embeddings = int(max_position_embeddings)
        overrides["max_position_embeddings"] = cfg.max_position_embeddings
    if rope_scaling is not None:
        cfg.rope_scaling = rope_scaling
        overrides["rope_scaling"] = cfg.rope_scaling

    tok = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(model_id, config=cfg, dtype=torch.bfloat16)
    model.eval()
    return tok, model, overrides


def generate(tok, model, prompt: str, max_new_tokens: int) -> tuple[str, float, int]:
    import torch
    if hasattr(tok, "apply_chat_template") and tok.chat_template:
        enc = tok.apply_chat_template(
            [{"role": "user", "content": prompt}],
            add_generation_prompt=True, return_tensors="pt", return_dict=True,
        )
    else:
        enc = tok(prompt, return_tensors="pt")
    input_ids = enc["input_ids"]
    n_in = int(input_ids.shape[1])
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
    return text, dt, n_in


# ----- main ---------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="microsoft/bitnet-b1.58-2B-4T-bf16")
    ap.add_argument("--out", default="results_long.jsonl")
    ap.add_argument("--rope-theta", type=float, default=None,
                    help="override config.rope_theta (e.g. 2_000_000 for 4× extension)")
    ap.add_argument("--max-position-embeddings", type=int, default=None,
                    help="override config.max_position_embeddings (e.g. 16384)")
    ap.add_argument("--rope-scaling-type", choices=["yarn", "linear", "dynamic"],
                    default=None)
    ap.add_argument("--rope-scaling-factor", type=float, default=4.0)
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    rope_scaling = None
    if args.rope_scaling_type:
        rope_scaling = {
            "type": args.rope_scaling_type,
            "factor": args.rope_scaling_factor,
            "original_max_position_embeddings": 4096,
        }

    print(f"[load] {args.model} "
          f"rope_theta={args.rope_theta} "
          f"max_pos={args.max_position_embeddings} "
          f"rope_scaling={rope_scaling}", flush=True)
    tok, model, applied = load_with_overrides(
        args.model,
        rope_theta=args.rope_theta,
        max_position_embeddings=args.max_position_embeddings,
        rope_scaling=rope_scaling,
    )
    print(f"[load] applied overrides: {applied}", flush=True)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    n_total = 0
    n_ok = 0
    by_cat: dict[str, list[bool]] = {}
    prompts = PROMPTS[: args.limit] if args.limit > 0 else PROMPTS

    with out_path.open("a", encoding="utf-8") as f:
        for p in prompts:
            try:
                body = p.build()
                resp, dt, n_in = generate(tok, model, body, p.max_new_tokens)
                ok, reason = p.scorer(resp)
                row = {
                    "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    "model": args.model, "id": p.id, "category": p.category,
                    "target_tokens": p.target_tokens, "actual_input_tokens": n_in,
                    "rope_theta_applied": applied.get("rope_theta"),
                    "max_pos_applied": applied.get("max_position_embeddings"),
                    "rope_scaling_applied": applied.get("rope_scaling"),
                    "ok": ok, "reason": reason,
                    "elapsed_sec": round(dt, 2),
                    "response": resp,
                }
            except Exception as e:
                import traceback
                row = {
                    "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    "model": args.model, "id": p.id, "category": p.category,
                    "target_tokens": p.target_tokens, "actual_input_tokens": -1,
                    "ok": False, "reason": f"EXC: {type(e).__name__}: {e!r}",
                    "traceback": traceback.format_exc(),
                    "elapsed_sec": 0.0, "response": "",
                }
                print(row["reason"], file=sys.stderr, flush=True)
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            f.flush()
            n_total += 1
            n_ok += int(row["ok"])
            by_cat.setdefault(p.category, []).append(bool(row["ok"]))
            mark = "PASS" if row["ok"] else "FAIL"
            print(f"  {mark:4} [{p.category:8}] {p.id:18} "
                  f"actual_in={row.get('actual_input_tokens',-1):>5} tok | "
                  f"{row['reason']}", flush=True)

    print()
    print(f"[summary] {n_ok}/{n_total} = {100*n_ok/n_total:.1f}%")
    for cat, oks in sorted(by_cat.items()):
        print(f"  {cat:10} {sum(oks)}/{len(oks)} = {100*sum(oks)/len(oks):.1f}%")
    return 0


if __name__ == "__main__":
    sys.exit(main())
