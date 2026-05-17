#!/usr/bin/env python3
"""
LLM comparison runner: sends the same prompts to all models sequentially.

Usage:
  # 1. Start a model:  ./serve.sh qwen3-32b
  # 2. Run comparison: python compare.py --model qwen3-32b
  # 3. Repeat for each model, results accumulate in results.jsonl

  python compare.py --model qwen3-32b
  python compare.py --model gemma4-31b
  python compare.py --model deepseek-r1-32b
  python compare.py --model llama4-scout
  python compare.py --model claude-sonnet-4-6   # uses ANTHROPIC_API_KEY

  # After all models done, print summary:
  python compare.py --summary
"""

import argparse
import json
import os
import time
from datetime import datetime
from pathlib import Path

import openai

RESULTS_FILE = Path(__file__).parent / "results.jsonl"

PROMPTS = [
    {
        "id": "reasoning_math",
        "category": "reasoning",
        "prompt": "A bat and a ball cost $1.10 in total. The bat costs $1.00 more than the ball. How much does the ball cost? Show your reasoning step by step.",
    },
    {
        "id": "code_python",
        "category": "coding",
        "prompt": "Write a Python function that finds all prime numbers up to n using the Sieve of Eratosthenes. Include type hints and a brief docstring.",
    },
    {
        "id": "summarization_jp",
        "category": "japanese",
        "prompt": "以下を3行で要約してください：「人工知能の急速な発展により、多くの産業で自動化が進んでいる。特に製造業では、ロボットが人間の代わりに単純作業を行うようになり、労働市場に大きな変化をもたらしている。一方で、AIを活用した新しい職種も生まれており、人間とAIの協働が新たな産業を創出している。」",
    },
    {
        "id": "instruction_follow",
        "category": "instruction",
        "prompt": "List exactly 5 European capitals, one per line, in alphabetical order. No additional text.",
    },
    {
        "id": "creative_writing",
        "category": "creative",
        "prompt": "Write a haiku about artificial intelligence in English. Then write the same haiku translated into Japanese.",
    },
]

DEFAULT_MODEL = "gemma4-31b"

MODEL_CONFIGS = {
    "qwen3-32b":       {"base_url": "http://localhost:8000/v1", "api_key": "dummy"},
    "gemma4-31b":      {"base_url": "http://localhost:8000/v1", "api_key": "dummy"},
    "deepseek-r1-32b": {"base_url": "http://localhost:8000/v1", "api_key": "dummy"},
    "llama4-scout":    {"base_url": "http://localhost:8000/v1", "api_key": "dummy"},
    "claude-sonnet-4-6": {
        "base_url": "https://api.anthropic.com/v1",
        "api_key": os.environ.get("ANTHROPIC_API_KEY", ""),
    },
}


def run_prompt(client: openai.OpenAI, model_name: str, prompt: str) -> dict:
    t0 = time.perf_counter()
    try:
        resp = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=512,
            temperature=0.0,
        )
        elapsed = time.perf_counter() - t0
        content = resp.choices[0].message.content or ""
        usage = resp.usage
        return {
            "ok": True,
            "content": content,
            "elapsed_sec": round(elapsed, 3),
            "prompt_tokens": usage.prompt_tokens if usage else None,
            "completion_tokens": usage.completion_tokens if usage else None,
        }
    except Exception as e:
        return {"ok": False, "error": str(e), "elapsed_sec": round(time.perf_counter() - t0, 3)}


def run_model(model_key: str) -> None:
    cfg = MODEL_CONFIGS.get(model_key)
    if not cfg:
        print(f"Unknown model: {model_key}. Available: {list(MODEL_CONFIGS)}")
        return

    if model_key == "claude-sonnet-4-6" and not cfg["api_key"]:
        print("ERROR: ANTHROPIC_API_KEY not set")
        return

    client = openai.OpenAI(base_url=cfg["base_url"], api_key=cfg["api_key"])
    print(f"\n{'='*60}")
    print(f"Model: {model_key}  |  {datetime.now().isoformat()}")
    print(f"{'='*60}")

    for p in PROMPTS:
        print(f"\n[{p['id']}] ", end="", flush=True)
        result = run_prompt(client, model_key, p["prompt"])

        if result["ok"]:
            tokens = result.get("completion_tokens") or "?"
            print(f"{result['elapsed_sec']}s  {tokens} tokens")
            print(result["content"][:300] + ("…" if len(result["content"]) > 300 else ""))
        else:
            print(f"ERROR: {result['error']}")

        row = {
            "model": model_key,
            "prompt_id": p["id"],
            "category": p["category"],
            "timestamp": datetime.now().isoformat(),
            **result,
        }
        with RESULTS_FILE.open("a") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def print_summary() -> None:
    if not RESULTS_FILE.exists():
        print("No results yet.")
        return

    rows = [json.loads(l) for l in RESULTS_FILE.read_text().splitlines() if l.strip()]
    models = sorted({r["model"] for r in rows})
    prompts = sorted({r["prompt_id"] for r in rows})

    print(f"\n{'='*80}")
    print("SUMMARY  (elapsed seconds per prompt)")
    print(f"{'='*80}")

    header = f"{'prompt_id':<25}" + "".join(f"{m:<20}" for m in models)
    print(header)
    print("-" * len(header))

    for pid in prompts:
        line = f"{pid:<25}"
        for m in models:
            match = [r for r in rows if r["model"] == m and r["prompt_id"] == pid]
            if match:
                r = match[-1]
                val = f"{r['elapsed_sec']}s" if r["ok"] else "ERR"
            else:
                val = "-"
            line += f"{val:<20}"
        print(line)

    print(f"\nFull results: {RESULTS_FILE}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Model key to run (default: gemma4-31b)")
    parser.add_argument("--summary", action="store_true", help="Print summary table")
    args = parser.parse_args()

    if args.summary:
        print_summary()
    else:
        run_model(args.model)
