"""Maxwell corpus harvester — translate Python actor methods -> Clojure via gad.

Single-node harvester for when the fleet Ollama is down: uses gad's llama-server
(Gemma 4 26B-a4b, OpenAI /v1 over Tailscale 100.82.98.110:11434 — Murakumo-only,
ADR-2605215000) as the teacher. Discovers top-level Python functions in flat
com-etzhayyim-* west repositories that are NOT already in the corpus, translates each to an idiomatic Clojure
`defn`, and — like fleet_refactor.py — FORCES clj-kondo cleanliness via a
lint-feedback retry loop (+ deterministic closing-paren repair). Only error-free
pairs are written to maxwell-candidates.jsonl for the gate_candidates.py gate.

Usage:
    python3 harvest_gad.py [--n 20] [--retries 3] [--endpoint URL] [--model NAME]
    python3 gate_candidates.py   # clj-kondo (errors) + charter -> maxwell-sft-corpus.jsonl
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[3]
ACTORS = pathlib.Path(os.environ.get("ETZHAYYIM_WEST_ACTORS_DIR", ROOT.parent))
CORPUS = ROOT / "90-docs/baien/maxwell-sft-corpus.jsonl"
CANDIDATES = ROOT / "90-docs/baien/maxwell-candidates.jsonl"
# units that failed to produce a clean-lint translation — skipped on later runs
# so each batch starts from genuinely-new units (avoids re-attempting perma-fails)
FAILED = ROOT / "90-docs/baien/maxwell-failed.txt"
KONDO = pathlib.Path.home() / "bin" / "clj-kondo"
ENDPOINT = "http://100.82.98.110:11434/v1/chat/completions"  # gad llama-server (Tailscale)
MODEL = "gemma4-26b-a4b-q4.gguf"

SYSTEM = (
    "You are Maxwell, etzhayyim's Murakumo fleet model. Convert Python actor "
    "methods to idiomatic Clojure following kotoba Datom log conventions "
    "(namespaced keywords, pure stdlib, EAVT). Output ONLY a single top-level "
    "`(defn name [...] ...)` form inside a ```clojure block — no ns, no prose, "
    "no defn- (use defn), balanced parens."
)
INSTRUCTION = "Convert this Python method to Clojure following kotoba Datom log idioms:\n\n```python\n{py}\n```\n\nOutput only the Clojure defn form."
_FENCE = re.compile(r"```(?:clojure|clj)?\s*(.*?)```", re.DOTALL)
_ERRCOUNT = re.compile(r"errors:\s*(\d+)")


def existing_ids() -> set[str]:
    ids = set()
    if CORPUS.exists():
        for line in CORPUS.open():
            if line.strip():
                ids.add(json.loads(line)["id"])
    return ids


def failed_ids() -> set[str]:
    if not FAILED.exists():
        return set()
    return {ln.strip() for ln in FAILED.open() if ln.strip()}


def record_failed(eid: str) -> None:
    with FAILED.open("a") as f:
        f.write(eid + "\n")


def label_for(py_path: pathlib.Path) -> str:
    parts = py_path.parts
    i = next(i for i, part in enumerate(parts) if part.startswith("com-etzhayyim-"))
    return "/".join(parts[i:]).replace(".py", "")


def top_level_fns(py_path: pathlib.Path):
    try:
        src = py_path.read_text(); tree = ast.parse(src)
    except (SyntaxError, UnicodeDecodeError):
        return
    lines = src.splitlines()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.col_offset == 0:
            if node.name.startswith("__"):
                continue
            yield node.name, "\n".join(lines[node.lineno - 1: node.end_lineno])


def _repair_parens(clj: str) -> str:
    """Deterministic EOF closing-paren repair (fleet_refactor trick)."""
    bal = clj.count("(") - clj.count(")")
    return clj + (")" * bal) if bal > 0 else clj


def _lint(clj: str) -> tuple[int, str]:
    """Return (error_count, clj-kondo_output). Warnings are tolerated."""
    with tempfile.NamedTemporaryFile(suffix=".clj", mode="w", delete=False) as tf:
        tf.write(clj); p = tf.name
    try:
        r = subprocess.run([str(KONDO), "--lint", p], capture_output=True, text=True)
    finally:
        pathlib.Path(p).unlink(missing_ok=True)
    m = _ERRCOUNT.search(r.stdout)
    return (int(m.group(1)) if m else 99), r.stdout.strip()


def _call(messages: list[dict], endpoint: str, model: str) -> str | None:
    body = json.dumps({
        "model": model, "messages": messages, "temperature": 0, "max_tokens": 1024,
        "chat_template_kwargs": {"enable_thinking": False},  # Gemma reasoning off
    }).encode()
    try:
        with urllib.request.urlopen(
            urllib.request.Request(endpoint, data=body, headers={"Content-Type": "application/json"}),
            timeout=180,
        ) as r:
            return json.loads(r.read())["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"  call error: {e}", file=sys.stderr); return None


def translate(py_src: str, endpoint: str, model: str, retries: int) -> str | None:
    """Translate with a clj-kondo lint-feedback retry loop; return error-free clj."""
    messages = [{"role": "system", "content": SYSTEM},
                {"role": "user", "content": INSTRUCTION.format(py=py_src)}]
    for _ in range(retries + 1):
        txt = _call(messages, endpoint, model)
        if not txt:
            return None
        m = _FENCE.search(txt)
        clj = _repair_parens((m.group(1) if m else txt).strip())
        if not clj.lstrip().startswith("(defn"):
            messages += [{"role": "assistant", "content": txt},
                         {"role": "user", "content": "Output ONLY a single (defn ...) form in a ```clojure block."}]
            continue
        errs, out = _lint(clj)
        if errs == 0:
            return clj
        messages += [{"role": "assistant", "content": f"```clojure\n{clj}\n```"},
                     {"role": "user", "content": f"clj-kondo reported errors. Fix them, output only the corrected defn:\n{out}"}]
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--retries", type=int, default=3)
    ap.add_argument("--per-file", type=int, default=2,
                    help="max fns harvested per source file (cross-actor diversity)")
    ap.add_argument("--endpoint", default=ENDPOINT)
    ap.add_argument("--model", default=MODEL)
    args = ap.parse_args()

    # Skip units already in corpus AND units that previously failed to lint-clean,
    # so each batch advances to genuinely-new units instead of re-attempting fails.
    done = existing_ids() | failed_ids()
    # Skip generated *-compat scaffold dirs (low Charter value, repetitive CRUD);
    # cap fns/file for cross-actor diversity instead of draining one file.
    py_files = sorted(p for p in ACTORS.rglob("*.py")
                      if "test" not in p.name and "/tests/" not in str(p)
                      and "-compat" not in str(p))
    harvested = attempts = 0
    with CANDIDATES.open("a") as out:
        for py in py_files:
            if harvested >= args.n:
                break
            try:
                label = label_for(py)
            except ValueError:
                continue
            per_file = 0
            for fn_name, py_src in top_level_fns(py):
                if harvested >= args.n or per_file >= args.per_file:
                    break
                eid = f"{label}/{fn_name}"
                if eid in done or len(py_src) < 60 or len(py_src) > 4000:
                    continue
                attempts += 1
                clj = translate(py_src, args.endpoint, args.model, args.retries)
                if not clj:
                    record_failed(eid)  # don't re-attempt this unit on later batches
                    print(f"  [skip] {eid} (no clean lint)", flush=True)
                    continue
                out.write(json.dumps({
                    "label": label, "fn_name": fn_name, "clj_src": clj,
                    "py_src": py_src, "pyPath": str(py),
                }, ensure_ascii=False) + "\n")
                out.flush(); done.add(eid); harvested += 1; per_file += 1
                print(f"  [{harvested}/{args.n}] {eid}  (lint-clean)", flush=True)
    print(f"harvested {harvested} clean / {attempts} attempted -> {CANDIDATES}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
