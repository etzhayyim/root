#!/usr/bin/env python3
"""kotoba py-WASM migration BAKE-OFF harness.

Migrates each corpus cell 1-by-1, AGENTICALLY (build-error feedback loop, not
single-shot), independently with each candidate model, then scores quality + cost.

Models are reached ONLY through the Murakumo LiteLLM gateway (127.0.0.1:4000) by
logical model_name (ADR-2605215000 inference SSoT). See litellm-routes.bakeoff.yaml.

QUALITY metrics (per ADR-2605310200 maturity goal):
  - build_pass        : componentize-py produced a .wasm
  - iters_to_build    : agentic iterations needed (1 = first try; lower = more mature)
  - deploy_pass       : :8077 kotoba_wasm_run accepted the component
  - invoke_equiv      : invoke output byte-equals the gold reference
  - judge_score       : 1-5 code-quality rubric scored by JUDGE_MODEL

COST metrics:
  - tokens_in / tokens_out (summed across agentic iterations)
  - usd               : tokens x model price (0 for local gemma)
  - wall_s            : total generation wall-clock (cost proxy for local models)

Output: results/results.edn  (+ per-(model,cell) port under ports/).

Run prerequisites (see README.md) — harness FAILS FAST with a clear message if unmet:
  1. LiteLLM :4000 up with the 3 bakeoff-* routes + keys in env
  2. kotoba :8077 up (wasm_executor ready)
  3. componentize-py>=0.23 installed (build-pywasm.sh auto-installs if pip available)
"""
from __future__ import annotations
import json, os, re, ast, sys, time, base64, subprocess, urllib.request, urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]                       # repo root
HERE = Path(__file__).resolve().parent
BUILD = ROOT / "40-engine/kotoba/scripts/build-pywasm.sh"
GATEWAY = os.environ.get("KOTOBA_GATEWAY", "http://127.0.0.1:4000/v1/chat/completions")
GATEWAY_KEY = os.environ.get("KOTOBA_GATEWAY_KEY", "sk-etzhayyim-litellm-local")
KOTOBA = os.environ.get("KOTOBA_SERVER", "http://localhost:8077")
OPERATOR_DID = os.environ.get("KOTOBA_OPERATOR_DID", "did:key:ze2e169933f9bcc6cb218e083b3d2a80c5a5a2b92fbf3cb41b4d5283ce3f6939f")

MODELS = ["bakeoff-claude-haiku", "bakeoff-gemini-flash", "bakeoff-gemma-26b"]
JUDGE_MODEL = os.environ.get("BAKEOFF_JUDGE_MODEL", "bakeoff-claude-haiku")
MAX_ITERS = int(os.environ.get("BAKEOFF_MAX_ITERS", "3"))

# price table mirrors litellm-routes.bakeoff.yaml model_info (verify at run time)
PRICE = {
    "bakeoff-claude-haiku": (1.00, 5.00),
    "bakeoff-gemini-flash": (0.30, 2.50),
    "bakeoff-gemma-26b":    (0.0, 0.0),
}

SYSTEM_PROMPT = """You are migrating a LangGraph actor cell to a Kotoba WASM component.
Output ONLY raw python (no markdown fences, no prose). The port MUST:
1. `import wit_world` and `from kotoba_langgraph import StateGraph, KotobaCheckpointer, START, END, handle_invoke`
   plus `import kotoba_langgraph._cbor` and `import kotoba_langgraph._entry`.
2. Define node functions + the graph builder at MODULE level (NOT inside any class).
3. Build a module-global: `compiled = _g.compile(checkpointer=KotobaCheckpointer())`.
4. Define exactly:
   class WitWorld(wit_world.WitWorld):
       def run(self, ctx_cbor: bytes) -> bytes:
           return handle_invoke(ctx_cbor, compiled)
5. Mock away relative imports like `from .state_machine import ...` with inline
   constants/dicts so the module compiles standalone.
6. Replace `__end__` with END; use `START`/`END` for entry/terminal edges.
7. Preserve the original node logic and state-dict shapes EXACTLY."""

GREEN, RED, DIM, RST = "\033[32m", "\033[31m", "\033[2m", "\033[0m"


# ── EDN (minimal writer) ─────────────────────────────────────────────────────
def edn(v, ind=0):
    pad = "  " * ind
    if isinstance(v, dict):
        items = "\n".join(f"{pad}  {_k(k)} {edn(val, ind + 1)}" for k, val in v.items())
        return "{\n" + items + "}"
    if isinstance(v, (list, tuple)):
        return "[" + " ".join(edn(x, ind) for x in v) + "]"
    if isinstance(v, bool):
        return "true" if v else "false"
    if v is None:
        return "nil"
    if isinstance(v, str):
        return '"' + v.replace("\\", "\\\\").replace('"', '\\"') + '"'
    if isinstance(v, float):
        return f"{v:.6g}"
    return str(v)


def _k(k):
    return ":" + str(k) if not str(k).startswith(":") else str(k)


# ── gateway call ─────────────────────────────────────────────────────────────
def chat(model, messages, temperature=0.0):
    body = json.dumps({"model": model, "messages": messages, "temperature": temperature}).encode()
    req = urllib.request.Request(
        GATEWAY, data=body, method="POST",
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {GATEWAY_KEY}"})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=180) as r:
        data = json.loads(r.read())
    wall = time.time() - t0
    usage = data.get("usage", {})
    text = data["choices"][0]["message"]["content"]
    return text, usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0), wall


def strip_fences(s):
    s = s.strip()
    if s.startswith("```"):
        s = re.sub(r"^```[a-zA-Z]*\n", "", s)
        s = re.sub(r"\n```$", "", s)
    return s.strip()


# ── structural pre-check (cheap, AST-based) ──────────────────────────────────
def structural_ok(src):
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        return False, f"syntax: {e}"
    has_witworld = any(isinstance(n, ast.ClassDef) and n.name == "WitWorld" for n in ast.walk(tree))
    has_compiled = any(isinstance(n, ast.Assign) and any(
        isinstance(t, ast.Name) and t.id == "compiled" for t in n.targets) for n in tree.body)
    if "__end__" in src:
        return False, "contains __end__ (must be END)"
    if not has_witworld:
        return False, "missing module-level WitWorld"
    if not has_compiled:
        return False, "missing module-level `compiled =`"
    return True, "ok"


# ── deploy + invoke on :8077 ─────────────────────────────────────────────────
def deploy_and_invoke(wasm_path, program_cid, ref_input):
    wasm_b64 = base64.b64encode(Path(wasm_path).read_bytes()).decode()
    # ctx is CBOR in production; harness sends JSON ref_input and lets the server
    # default-encode. Adjust ctx_cbor_b64 once the prod CBOR envelope is wired.
    payload = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
               "params": {"name": "kotoba_wasm_run",
                          "arguments": {"program_cid": program_cid, "program_type": "wasm-node",
                                        "agent_did": OPERATOR_DID, "wasm_b64": wasm_b64,
                                        "input_json": json.dumps(ref_input)}}}
    req = urllib.request.Request(
        f"{KOTOBA}/mcp", data=json.dumps(payload).encode(), method="POST",
        headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            res = json.loads(r.read())
        if "error" in res:
            return False, None, str(res["error"])
        return True, res.get("result"), None
    except urllib.error.HTTPError as e:
        return False, None, f"HTTP {e.code}: {e.read().decode()[:200]}"


# ── host-python reference (ground truth for :host-python cells) ──────────────
def host_reference(cell):
    """Best-effort: import the original Cell and call <entry>(ref-input)."""
    src = ROOT / cell["src"]
    pkg_dir = src.parent
    sys.path.insert(0, str(pkg_dir))
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("_ref_cell", src)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)             # may fail on relative imports — caught by caller
        inst = getattr(mod, cell["class"])()
        return getattr(inst, cell["entry"])(dict(cell["ref_input"]))
    finally:
        sys.path.pop(0)


# ── one agentic migration (model x cell) ─────────────────────────────────────
def migrate(model, cell):
    src_path = ROOT / cell["src"]
    original = src_path.read_text()
    out_dir = HERE / "ports" / cell["id"].lstrip(":")
    out_dir.mkdir(parents=True, exist_ok=True)
    py_out = out_dir / f"{model}.py"
    wasm_out = out_dir / f"{model}.wasm"

    messages = [{"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Original cell:\n```python\n{original}\n```"}]
    tin = tout = 0
    wall = 0.0
    build_err = None
    iters_used = 0

    for it in range(1, MAX_ITERS + 1):
        iters_used = it
        text, pt, ct, w = chat(model, messages)
        tin += pt; tout += ct; wall += w
        port = strip_fences(text)
        py_out.write_text(port)

        ok, why = structural_ok(port)
        if not ok:
            build_err = f"structural: {why}"
            messages += [{"role": "assistant", "content": text},
                         {"role": "user", "content": f"That failed a structural check: {why}. Fix and re-output ONLY the python."}]
            continue

        proc = subprocess.run(["bash", str(BUILD), str(py_out), "-o", str(wasm_out)],
                              capture_output=True, text=True, cwd=out_dir)
        if proc.returncode == 0 and wasm_out.exists():
            build_err = None
            break
        build_err = (proc.stderr or proc.stdout)[-1500:]
        messages += [{"role": "assistant", "content": text},
                     {"role": "user", "content": f"componentize-py build FAILED:\n{build_err}\nFix and re-output ONLY the python."}]

    build_pass = build_err is None and wasm_out.exists()
    result = {"model": model, "cell": cell["id"], "build_pass": build_pass,
              "iters_to_build": iters_used if build_pass else None,
              "tokens_in": tin, "tokens_out": tout, "wall_s": round(wall, 2),
              "build_err": (build_err or "")[:300] if not build_pass else None}

    pin, pout = PRICE[model]
    result["usd"] = round(tin / 1e6 * pin + tout / 1e6 * pout, 5)

    # deploy + invoke equivalence
    result["deploy_pass"] = False
    result["invoke_equiv"] = None
    if build_pass:
        program_cid = f"bakeoff_{cell['id'].lstrip(':')}_{model}"
        dep_ok, out, derr = deploy_and_invoke(wasm_out, program_cid, dict(cell["ref_input"]))
        result["deploy_pass"] = dep_ok
        if dep_ok:
            try:
                if cell["ref_strategy"] == ":host-python":
                    gold = host_reference(cell)
                    result["invoke_equiv"] = (out == gold)
                else:  # :gold-wasm — compared offline (see README); mark for follow-up
                    result["invoke_equiv"] = None
            except Exception as e:                       # relative-import / runtime ref failure
                result["ref_err"] = str(e)[:200]
        else:
            result["deploy_err"] = (derr or "")[:200]

    # LLM-judge code quality (only if we have a buildable port)
    result["judge_score"] = None
    if build_pass:
        jtext, _, _, _ = chat(JUDGE_MODEL, [
            {"role": "system", "content": "Score this WASM port of a LangGraph cell 1-5 on readability, "
             "faithfulness to original logic, and soundness of mocked imports. Output ONLY an integer 1-5."},
            {"role": "user", "content": f"ORIGINAL:\n```python\n{original}\n```\n\nPORT:\n```python\n{py_out.read_text()}\n```"}])
        m = re.search(r"[1-5]", jtext)
        result["judge_score"] = int(m.group()) if m else None

    tag = f"{GREEN}build✓{RST}" if build_pass else f"{RED}build✗{RST}"
    print(f"  {model:22s} {tag} iters={result['iters_to_build']} "
          f"deploy={result['deploy_pass']} equiv={result['invoke_equiv']} "
          f"judge={result['judge_score']} ${result['usd']} {DIM}{result['wall_s']}s{RST}")
    return result


# ── preflight ────────────────────────────────────────────────────────────────
def preflight():
    errs = []
    try:
        urllib.request.urlopen(f"{KOTOBA}/health", timeout=5)
    except Exception as e:
        errs.append(f"kotoba :8077 unreachable ({e}); start the kotoba server")
    try:
        req = urllib.request.Request(GATEWAY.replace("/chat/completions", "/models"),
                                     headers={"Authorization": f"Bearer {GATEWAY_KEY}"})
        urllib.request.urlopen(req, timeout=5)
    except Exception as e:
        errs.append(f"LiteLLM :4000 unreachable ({e}); bring up gateway w/ bakeoff-* routes")
    if not BUILD.exists():
        errs.append(f"build script missing: {BUILD}")
    if errs:
        print(f"{RED}PREFLIGHT FAILED:{RST}")
        for e in errs:
            print(f"  - {e}")
        sys.exit(2)


def main():
    preflight()
    cjson = HERE / "corpus.json"
    if not cjson.exists():
        print(f"{RED}corpus.json missing.{RST} Generate it from corpus.edn (README step 4) "
              "or hand-author the JSON mirror. corpus.edn stays the SoT.")
        sys.exit(2)
    corpus = json.loads(cjson.read_text())["corpus"]
    all_results = []
    for cell in corpus:
        print(f"{cell['id']}  ({cell['tier']}, {cell['loc']}L/{cell['nodes']}n)")
        for model in MODELS:
            try:
                all_results.append(migrate(model, cell))
            except Exception as e:
                print(f"  {model:22s} {RED}ERROR{RST} {e}")
                all_results.append({"model": model, "cell": cell["id"], "error": str(e)[:300]})

    # rollup per model
    rollup = {}
    for m in MODELS:
        rows = [r for r in all_results if r.get("model") == m and "error" not in r]
        n = len(rows) or 1
        rollup[m] = {
            "build_pass_rate": round(sum(bool(r.get("build_pass")) for r in rows) / n, 3),
            "deploy_pass_rate": round(sum(bool(r.get("deploy_pass")) for r in rows) / n, 3),
            "invoke_equiv_rate": round(sum(r.get("invoke_equiv") is True for r in rows) / n, 3),
            "avg_iters": round(sum(r.get("iters_to_build") or MAX_ITERS for r in rows) / n, 2),
            "avg_judge": round(sum(r.get("judge_score") or 0 for r in rows) / n, 2),
            "total_usd": round(sum(r.get("usd") or 0 for r in rows), 4),
            "total_wall_s": round(sum(r.get("wall_s") or 0 for r in rows), 1),
        }

    out = {"meta": {"models": MODELS, "max_iters": MAX_ITERS, "cells": len(corpus),
                    "judge_model": JUDGE_MODEL},
           "rollup": rollup, "results": all_results}
    (HERE / "results" / "results.edn").write_text(edn(out))
    (HERE / "results" / "results.json").write_text(json.dumps(out, indent=2))
    print(f"\n{GREEN}wrote results/results.edn + results.json{RST}")
    print("\nROLLUP:")
    for m, r in rollup.items():
        print(f"  {m:22s} build={r['build_pass_rate']} equiv={r['invoke_equiv_rate']} "
              f"iters={r['avg_iters']} judge={r['avg_judge']} ${r['total_usd']} {r['total_wall_s']}s")


if __name__ == "__main__":
    main()
