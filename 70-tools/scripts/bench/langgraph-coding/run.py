"""LangGraph coding bench runner (ADR-2605250400 §1.5).

Reads prompts.jsonl, generates code via the configured model endpoint,
grades each generation via the matching grader in graders/, emits
lm-eval-harness-compatible JSONL to --out.

Status: scaffold. The prompt set + grader registry are TODO; this file
defines the interface so the distill loop and Ansible push runbook can
wire to it now.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PROMPTS_PATH = Path(__file__).parent / "prompts.jsonl"
GRADERS_DIR = Path(__file__).parent / "graders"


@dataclass
class PromptSpec:
    id: str
    category: str  # stategraph / reducer / node / conditional / interrupt / send / subgraph / tool / error / streaming
    prompt: str
    grader_module: str  # e.g. "graders.s01_stategraph_basic"
    max_tokens: int = 1024


@dataclass
class GradeResult:
    id: str
    category: str
    passed: bool
    reason: str
    generation: str


def load_prompts() -> list[PromptSpec]:
    if not PROMPTS_PATH.exists():
        return []
    out: list[PromptSpec] = []
    with PROMPTS_PATH.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            out.append(PromptSpec(**row))
    return out


_LOCAL_CACHE: dict[str, tuple] = {}


def _local_load(model_dir: str):
    if model_dir in _LOCAL_CACHE:
        return _LOCAL_CACHE[model_dir]
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    tok = AutoTokenizer.from_pretrained(model_dir)
    dtype = torch.bfloat16 if torch.cuda.is_available() else torch.float32
    model = AutoModelForCausalLM.from_pretrained(model_dir, dtype=dtype)
    if torch.cuda.is_available():
        model = model.to("cuda")
    model.eval()
    _LOCAL_CACHE[model_dir] = (tok, model)
    return tok, model


def generate(endpoint: str, model_id: str, prompt: str, max_tokens: int) -> str:
    """Dispatch on endpoint scheme:
    - http://...  → OpenAI-compat (LiteLLM gateway / Ollama)
    - file://...  → load HF model dir locally via transformers
    """
    if endpoint.startswith("http"):
        from openai import OpenAI
        client = OpenAI(base_url=endpoint + "/v1", api_key="lan-only")
        resp = client.chat.completions.create(
            model=model_id,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0.0,
        )
        return resp.choices[0].message.content or ""
    elif endpoint.startswith("file://"):
        model_dir = endpoint[len("file://"):]
        tok, model = _local_load(model_dir)
        import torch
        if getattr(tok, "chat_template", None):
            prompt_str = tok.apply_chat_template(
                [{"role": "user", "content": prompt}],
                tokenize=False, add_generation_prompt=True,
            )
        else:
            prompt_str = prompt
        enc = tok(prompt_str, return_tensors="pt").to(model.device)
        with torch.no_grad():
            out = model.generate(
                **enc, max_new_tokens=max_tokens, do_sample=False, temperature=1.0,
                pad_token_id=tok.eos_token_id,
            )
        # Strip the prompt prefix from the generated tokens
        gen_tokens = out[0][enc["input_ids"].shape[1]:]
        return tok.decode(gen_tokens, skip_special_tokens=True)
    else:
        raise ValueError(f"unknown endpoint scheme: {endpoint}")


def grade(spec: PromptSpec, generation: str) -> GradeResult:
    """Import the per-prompt grader and run its check().

    Grader contract:
      def check(generation: str) -> tuple[bool, str]
    """
    import importlib
    try:
        mod = importlib.import_module(spec.grader_module)
        ok, reason = mod.check(generation)
    except Exception as e:
        return GradeResult(
            id=spec.id, category=spec.category, passed=False,
            reason=f"grader-crash: {e!r}", generation=generation,
        )
    return GradeResult(
        id=spec.id, category=spec.category, passed=ok, reason=reason,
        generation=generation,
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True, help="endpoint URL or file:// HF dir")
    ap.add_argument("--model-id", required=True, help="model id served at endpoint")
    ap.add_argument("--out", required=True, help="output JSONL path")
    ap.add_argument("--limit", type=int, default=0, help="0 = all prompts")
    args = ap.parse_args()

    sys.path.insert(0, str(Path(__file__).parent))

    specs = load_prompts()
    if not specs:
        print("[langgraph-coding] no prompts.jsonl yet — see README §Status", file=sys.stderr)
        return 2
    if args.limit:
        specs = specs[: args.limit]

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    n_pass = 0
    with out_path.open("w") as fout:
        for spec in specs:
            gen = generate(args.model, args.model_id, spec.prompt, spec.max_tokens)
            res = grade(spec, gen)
            n_pass += int(res.passed)
            row: dict[str, Any] = {
                "bench": "langgraph-coding",
                "adr": "2605250400",
                "model_id": args.model_id,
                "id": res.id,
                "category": res.category,
                "passed": res.passed,
                "reason": res.reason,
                "generation": res.generation,
            }
            fout.write(json.dumps(row, ensure_ascii=False) + "\n")
            print(f"[{spec.id}] {'PASS' if res.passed else 'FAIL'} {res.reason}", file=sys.stderr)

    print(f"\n{n_pass}/{len(specs)} pass ({100*n_pass/len(specs):.1f}%)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
