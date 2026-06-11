#!/usr/bin/env python3
"""kotoba py-WASM migration BAKE-OFF — agentic CLI orchestrator.

Each candidate is a full coding-agent CLI (not a single LLM call). Per cell, the
CLI agent autonomously: reads the original cell, writes a kotoba_langgraph port,
runs build-pywasm.sh, fixes build errors, and iterates until a .wasm is produced.
We measure quality + cost of that whole agentic loop.

Candidates (codex deferred — usage-limited; rerun with --clis codex when credits return):
  claude  -> Claude Code CLI, model claude-haiku-4-5   (cost+usage via --output-format json)
  gemini  -> Gemini CLI,      model gemini-2.5-flash    (wall-clock cost; no per-call USD)

Shared toolchain: .venv (componentize-py 0.23) is put on PATH so all agents build
on equal footing. kotoba :8077 must be live for the optional deploy probe.

Constitutional note: these CLIs call commercial APIs directly (Anthropic/Google),
NOT via Murakumo. Permissible as DEV-TIME migration tooling; the winning model's
standing pipeline must still respect ADR-2605215000 (Murakumo SSoT) at runtime.
"""
from __future__ import annotations
import json, os, re, ast, sys, time, shutil, subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
VENV_BIN = HERE / ".venv/bin"
BUILD = ROOT / "40-engine/kotoba/scripts/build-pywasm.sh"
GOLD_EXAMPLE = ROOT / "40-engine/kotoba/examples/kotoba-langgraph-final-sign-off/final_sign_off_kotoba.py"
RUNS = HERE / "runs"
PER_RUN_TIMEOUT = int(os.environ.get("BAKEOFF_TIMEOUT", "900"))

GREEN, RED, YEL, DIM, RST = "\033[32m", "\033[31m", "\033[33m", "\033[2m", "\033[0m"

CLIS = {
    "claude": {"model": "claude-haiku-4-5"},
    "gemini": {"model": "gemini-3-flash-preview"},
    "gemma":  {"model": "gemma-4-26B-A4B-it"},   # local llama-server, agentic via python feedback loop
    # "codex": {"model": "gpt-5.5"},   # deferred: usage limit
}
GEMMA_ENDPOINT = os.environ.get("GEMMA_ENDPOINT", "http://127.0.0.1:8090/v1/chat/completions")
GEMMA_MAX_ITERS = int(os.environ.get("GEMMA_MAX_ITERS", "4"))


def task_prompt(cell, buildscript, example_text):
    return f"""You are migrating a LangGraph actor cell to a Kotoba WASM component.

In THIS directory you have `original_cell.py` (the source). Produce a file named
`agent.py` that is a standalone kotoba_langgraph port, then BUILD it to `agent.wasm`.

Follow the API shown in this reference port (study it, mirror its structure):
```python
{example_text}
```

Hard requirements for agent.py:
1. `import wit_world`; `from kotoba_langgraph import StateGraph, KotobaCheckpointer, START, END, handle_invoke`;
   `import kotoba_langgraph._cbor`; `import kotoba_langgraph._entry`.
2. Node functions + graph builder at MODULE level (NOT inside a class).
2b. STATE SCHEMA — CRITICAL for runtime equivalence: pass `dict` to StateGraph exactly like
   the original cell does — `_g = StateGraph(dict)`. Do NOT introduce a custom TypedDict state
   schema. A TypedDict that declares input-only keys (e.g. projectId) makes langgraph RETAIN those
   input keys in the output state, whereas the original `StateGraph(dict)` drops keys no node writes
   — that divergence breaks invoke-equivalence with the original even though it still builds.
3. Module-global `compiled = _g.compile(checkpointer=KotobaCheckpointer())`.
4. Exactly: `class WitWorld(wit_world.WitWorld):` with `def run(self, ctx_cbor: bytes) -> bytes: return handle_invoke(ctx_cbor, compiled)`.
5. Mock away relative imports (`from .state_machine import ...`) with inline constants so it compiles standalone.
6. Replace `__end__` with END. Preserve the original node logic and state-dict shapes EXACTLY.

BUILD COMMAND (run it; componentize-py is already on PATH):
    bash {buildscript} agent.py agent.wasm

If the build fails, READ the error, fix agent.py, and rebuild. Iterate until
`agent.wasm` exists. Do not stop until the build succeeds or you are certain it cannot.
When done, output a one-line status: BUILD_OK or BUILD_FAILED."""


def structural_ok(src):
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        return False, f"syntax:{e}"
    if "__end__" in src:
        return False, "__end__"
    has_ww = any(isinstance(n, ast.ClassDef) and n.name == "WitWorld" for n in ast.walk(tree))
    has_c = any(isinstance(n, ast.Assign) and any(getattr(t, "id", "") == "compiled" for t in n.targets)
                for n in tree.body)
    return (has_ww and has_c), ("ok" if has_ww and has_c else "missing WitWorld/compiled")


def run_claude(workdir, prompt):
    env = {**os.environ, "PATH": f"{VENV_BIN}:{os.environ['PATH']}"}
    t0 = time.time()
    p = subprocess.run(
        ["claude", "-p", prompt, "--model", CLIS["claude"]["model"],
         "--output-format", "json", "--permission-mode", "bypassPermissions", "--add-dir", "."],
        cwd=workdir, env=env, capture_output=True, text=True, timeout=PER_RUN_TIMEOUT)
    wall = time.time() - t0
    usd = turns = tin = tout = None
    try:
        j = json.loads(p.stdout)
        usd = j.get("total_cost_usd"); turns = j.get("num_turns")
        u = j.get("usage", {}); tin = u.get("input_tokens"); tout = u.get("output_tokens")
    except Exception:
        pass
    return {"wall_s": round(wall, 1), "usd": usd, "turns": turns,
            "tokens_in": tin, "tokens_out": tout, "raw_tail": (p.stdout or p.stderr)[-400:]}


def run_gemini(workdir, prompt):
    env = {**os.environ, "PATH": f"{VENV_BIN}:{os.environ['PATH']}",
           "GEMINI_CLI_TRUST_WORKSPACE": "true"}
    t0 = time.time()
    p = subprocess.run(
        ["gemini", "-p", prompt, "-m", CLIS["gemini"]["model"], "--approval-mode", "yolo"],
        cwd=workdir, env=env, capture_output=True, text=True, timeout=PER_RUN_TIMEOUT)
    wall = time.time() - t0
    # Gemini CLI does not emit per-call USD; cost proxy = wall_s. Token usage parsed if present.
    return {"wall_s": round(wall, 1), "usd": None, "turns": None,
            "tokens_in": None, "tokens_out": None, "raw_tail": (p.stdout or p.stderr)[-400:]}


def run_gemma(workdir, prompt):
    """Local gemma-4-26B via llama-server. gemma is NOT a CLI agent, so the harness
    supplies the agentic loop: generate -> write agent.py -> build -> feed build error
    back -> retry, up to GEMMA_MAX_ITERS. Asymmetry vs claude/gemini (which drive their
    own tools autonomously) is noted in SUMMARY caveats. Cost = wall-s (local, $0)."""
    import urllib.request
    env = {**os.environ, "PATH": f"{VENV_BIN}:{os.environ['PATH']}"}
    agent_py = Path(workdir) / "agent.py"
    messages = [{"role": "system", "content": "Output ONLY raw python (no markdown fences)."},
                {"role": "user", "content": prompt}]
    tin = tout = 0
    wall = 0.0
    iters = 0
    for it in range(1, GEMMA_MAX_ITERS + 1):
        iters = it
        # gemma4 emits huge reasoning_content; with thinking ON it exhausts max_tokens
        # before emitting code (empty content) AND is ~20min/call. Disable thinking:
        # quality stays faithful (verified) and latency drops ~5x.
        body = json.dumps({"model": CLIS["gemma"]["model"], "messages": messages,
                           "temperature": 0.0, "max_tokens": 4096,
                           "chat_template_kwargs": {"enable_thinking": False}}).encode()
        req = urllib.request.Request(GEMMA_ENDPOINT, data=body, method="POST",
                                     headers={"Content-Type": "application/json"})
        t0 = time.time()
        with urllib.request.urlopen(req, timeout=PER_RUN_TIMEOUT) as r:
            j = json.loads(r.read())
        wall += time.time() - t0
        u = j.get("usage", {}); tin += u.get("prompt_tokens", 0); tout += u.get("completion_tokens", 0)
        code = j["choices"][0]["message"]["content"].strip()
        if code.startswith("```"):
            code = re.sub(r"^```[a-zA-Z]*\n", "", code); code = re.sub(r"\n```$", "", code)
        agent_py.write_text(code.strip())
        proc = subprocess.run(["bash", str(BUILD), "agent.py", "agent.wasm"],
                              cwd=workdir, env=env, capture_output=True, text=True)
        if proc.returncode == 0 and (Path(workdir) / "agent.wasm").exists():
            break
        err = (proc.stderr or proc.stdout)[-1200:]
        messages += [{"role": "assistant", "content": code},
                     {"role": "user", "content": f"componentize-py build FAILED:\n{err}\nFix and re-output ONLY the python."}]
    return {"wall_s": round(wall, 1), "usd": 0.0, "turns": iters,
            "tokens_in": tin, "tokens_out": tout, "raw_tail": ""}


RUNNERS = {"claude": run_claude, "gemini": run_gemini, "gemma": run_gemma}


def judge(original, port_text):
    """Cheap LLM-judge via claude haiku: 1-5 on readability/faithfulness/mock-soundness."""
    env = {**os.environ}
    prompt = ("Score this WASM port of a LangGraph cell 1-5 (integer only) on readability, "
              "faithfulness to original logic, and soundness of mocked imports.\n\n"
              f"ORIGINAL:\n```python\n{original}\n```\n\nPORT:\n```python\n{port_text}\n```\n\nOutput ONLY a digit 1-5.")
    try:
        p = subprocess.run(["claude", "-p", prompt, "--model", "claude-haiku-4-5"],
                           env=env, capture_output=True, text=True, timeout=180)
        m = re.search(r"[1-5]", p.stdout)
        return int(m.group()) if m else None
    except Exception:
        return None


def migrate(cli, cell, example_text):
    cid = cell["id"].lstrip(":")
    workdir = RUNS / cid / cli
    if workdir.exists():
        shutil.rmtree(workdir)
    workdir.mkdir(parents=True)
    original = (ROOT / cell["src"]).read_text()
    (workdir / "original_cell.py").write_text(original)
    prompt = task_prompt(cell, BUILD, example_text)

    metrics = RUNNERS[cli](str(workdir), prompt)

    wasm = workdir / "agent.wasm"
    agent_py = workdir / "agent.py"
    build_pass = wasm.exists() and wasm.stat().st_size > 0
    struct = (False, "no agent.py")
    jscore = None
    if agent_py.exists():
        port_text = agent_py.read_text()
        struct = structural_ok(port_text)
        jscore = judge(original, port_text)

    row = {"cli": cli, "model": CLIS[cli]["model"], "cell": cell["id"],
           "build_pass": build_pass, "structural_ok": struct[0], "structural_why": struct[1],
           "judge_score": jscore, **metrics}
    row.pop("raw_tail", None)

    tag = f"{GREEN}build✓{RST}" if build_pass else f"{RED}build✗{RST}"
    usd = f"${metrics['usd']}" if metrics["usd"] is not None else "$ n/a"
    print(f"  {cli:8s} {CLIS[cli]['model']:20s} {tag} struct={struct[0]} "
          f"judge={jscore} turns={metrics['turns']} {usd} {DIM}{metrics['wall_s']}s{RST}")
    return row


def edn(v, ind=0):
    pad = "  " * ind
    if isinstance(v, dict):
        return "{\n" + "\n".join(f"{pad}  :{k} {edn(val, ind+1)}" for k, val in v.items()) + "}"
    if isinstance(v, (list, tuple)):
        return "[" + " ".join(edn(x, ind) for x in v) + "]"
    if isinstance(v, bool): return "true" if v else "false"
    if v is None: return "nil"
    if isinstance(v, str): return '"' + v.replace('"', '\\"') + '"'
    if isinstance(v, float): return f"{v:.6g}"
    return str(v)


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--clis", default="claude,gemini")
    ap.add_argument("--cells", default="", help="comma ids, e.g. service-request,elv-body-shred (default: all)")
    args = ap.parse_args()
    clis = [c for c in args.clis.split(",") if c in CLIS]

    corpus = json.loads((HERE / "corpus.json").read_text())["corpus"]
    if args.cells:
        want = set(args.cells.split(","))
        corpus = [c for c in corpus if c["id"].lstrip(":") in want]
    example_text = GOLD_EXAMPLE.read_text()

    rows = []
    for cell in corpus:
        print(f"{cell['id']}  ({cell['tier']}, {cell['loc']}L/{cell['nodes']}n)")
        for cli in clis:
            try:
                rows.append(migrate(cli, cell, example_text))
            except subprocess.TimeoutExpired:
                print(f"  {cli:8s} {RED}TIMEOUT{RST}")
                rows.append({"cli": cli, "cell": cell["id"], "error": "timeout"})
            except Exception as e:
                print(f"  {cli:8s} {RED}ERROR{RST} {e}")
                rows.append({"cli": cli, "cell": cell["id"], "error": str(e)[:200]})

    rollup = {}
    for cli in clis:
        rs = [r for r in rows if r.get("cli") == cli and "error" not in r]
        n = len(rs) or 1
        usds = [r["usd"] for r in rs if r.get("usd") is not None]
        rollup[cli] = {
            "build_pass_rate": round(sum(bool(r["build_pass"]) for r in rs) / n, 3),
            "struct_ok_rate": round(sum(bool(r["structural_ok"]) for r in rs) / n, 3),
            "avg_judge": round(sum((r.get("judge_score") or 0) for r in rs) / n, 2),
            "total_usd": round(sum(usds), 4) if usds else None,
            "total_wall_s": round(sum((r.get("wall_s") or 0) for r in rs), 1),
        }

    out = {"meta": {"clis": clis, "cells": len(corpus), "deferred": ["codex(usage-limit)"]},
           "rollup": rollup, "results": rows}
    (HERE / "results").mkdir(exist_ok=True)
    (HERE / "results/cli-results.edn").write_text(edn(out))
    (HERE / "results/cli-results.json").write_text(json.dumps(out, indent=2))
    print(f"\n{GREEN}wrote results/cli-results.edn{RST}\nROLLUP:")
    for cli, r in rollup.items():
        print(f"  {cli:8s} build={r['build_pass_rate']} struct={r['struct_ok_rate']} "
              f"judge={r['avg_judge']} ${r['total_usd']} {r['total_wall_s']}s")


if __name__ == "__main__":
    main()
