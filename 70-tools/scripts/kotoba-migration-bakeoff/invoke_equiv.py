#!/usr/bin/env python3
"""invoke-equivalence gate for the kotoba migration bake-off.

The REAL quality gate (ADR-2605312100 open item): build-pass != runtime-correct.
For each (cell, model) with a built agent.wasm, this:
  1. runs the ORIGINAL cell's solve(ref_input) in host CPython           -> GOLD
  2. deploys+invokes agent.wasm on kotoba :8077 with the same input      -> WASM
  3. compares the two output state dicts                                  -> equiv?

Contract (verified from kotoba source):
  POST :8077/mcp  JSON-RPC tools/call name=kotoba_wasm_run
    args: {wasm_b64, agent_did, ctx_cbor_b64, max_supersteps}
    auth: Authorization: Bearer <JWT> — check_auth only validates exp (no sig)
  ctx CBOR = {graph, session_cid, args:{input, thread_id}}
  resp.result.output_cbor_b64 -> CBOR {"ok": json_str} | {"err": msg}

Usage: invoke_equiv.py [cell-id ...]   (default: the 2 no-relative-import cells)
"""
from __future__ import annotations
import base64, json, sys, importlib.util, urllib.request
from pathlib import Path
import cbor2

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
KOTOBA = "http://localhost:8077"
DID = "did:key:ze2e169933f9bcc6cb218e083b3d2a80c5a5a2b92fbf3cb41b4d5283ce3f6939f"
GREEN, RED, YEL, RST = "\033[32m", "\033[31m", "\033[33m", "\033[0m"


def jwt_for(did):
    b = lambda o: base64.urlsafe_b64encode(json.dumps(o).encode()).rstrip(b"=").decode()
    return f"{b({'alg':'HS256','typ':'JWT'})}.{b({'sub':did,'exp':9999999999})}.opsig"


def _find_solve_cls(mod):
    return next(v for v in vars(mod).values()
                if isinstance(v, type) and hasattr(v, "solve") and v.__module__ == mod.__name__)


def host_reference(cell):
    """Run the ORIGINAL cell's solve(ref_input) in host CPython (gold output).

    Handles both no-relative-import cells (direct file load) and relative-import
    cells (`from .state_machine import ...`) by importing the cell as a package
    member so the relative import resolves.
    """
    src = ROOT / cell["src"]
    celldir = src.parent              # .../<cell_name>
    has_rel = "from ." in src.read_text()
    if has_rel and (celldir / "__init__.py").exists():
        parent = celldir.parent       # .../cells  (cell_name becomes a top-level package)
        pkg = celldir.name
        sys.path.insert(0, str(parent))
        try:
            mod = importlib.import_module(f"{pkg}.cell")
            return _find_solve_cls(mod)().solve(dict(cell["ref_input"]))
        finally:
            sys.path.pop(0)
            for k in [k for k in sys.modules if k == pkg or k.startswith(pkg + ".")]:
                del sys.modules[k]    # avoid cross-cell contamination
    # no-relative-import: load the file directly
    sys.path.insert(0, str(celldir))
    try:
        spec = importlib.util.spec_from_file_location(f"_ref_{cell['id']}", src)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return _find_solve_cls(mod)().solve(dict(cell["ref_input"]))
    finally:
        sys.path.pop(0)


def invoke_wasm(wasm_path, ref_input):
    """Deploy+invoke agent.wasm on :8077, return (output_state | None, err | None)."""
    import hashlib
    wasm_bytes = Path(wasm_path).read_bytes()
    wasm_b64 = base64.b64encode(wasm_bytes).decode()
    h = hashlib.sha256(wasm_bytes).hexdigest()[:32]
    program_cid = "bake-" + h
    # NOTE: the running :8077 binary caches the compiled program by AGENT_DID (the
    # ADR-2605310200 program_cid-cache fix is in source but not in the deployed
    # binary). So use a UNIQUE agent_did per wasm to defeat the stale cache.
    did = f"did:key:zBake{h}"
    ctx = {"graph": "equiv", "session_cid": program_cid,
           "args": {"input": dict(ref_input), "thread_id": program_cid}}
    ctx_b64 = base64.b64encode(cbor2.dumps(ctx)).decode()
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                       "params": {"name": "kotoba_wasm_run",
                                  "arguments": {"wasm_b64": wasm_b64, "agent_did": did,
                                                "program_cid": program_cid,
                                                "ctx_cbor_b64": ctx_b64, "max_supersteps": 32}}}).encode()
    req = urllib.request.Request(f"{KOTOBA}/mcp", data=body, method="POST",
                                 headers={"Content-Type": "application/json",
                                          "Authorization": f"Bearer {jwt_for(did)}"})
    with urllib.request.urlopen(req, timeout=120) as r:
        resp = json.loads(r.read())
    if "error" in resp:
        return None, f"rpc: {resp['error']}"
    result = resp.get("result", {})
    # MCP wraps the tool output as result.content[0].text = JSON string
    try:
        inner = json.loads(result["content"][0]["text"])
    except Exception as e:
        return None, f"unexpected result shape: {e} / {str(result)[:200]}"
    out_b64 = inner.get("output_cbor_b64")
    if not out_b64:
        return None, f"no output_cbor_b64 (status={inner.get('status')}, gas={inner.get('total_gas_used')})"
    out = cbor2.loads(base64.b64decode(out_b64))
    if "err" in out:
        return None, f"wasm-err: {out['err'][:300]}"
    return json.loads(out["ok"]), None


def norm(x):
    """Order-insensitive comparison key (dicts compare by content)."""
    return json.dumps(x, sort_keys=True, default=str)


def main():
    corpus = json.loads((HERE / "corpus.json").read_text())["corpus"]
    want = set(sys.argv[1:]) or {"service-request", "final-sign-off"}  # no-rel-import cells
    corpus = [c for c in corpus if c["id"].lstrip(":") in want]
    models = ["claude", "gemini", "gemma"]

    rows = []
    for cell in corpus:
        cid = cell["id"].lstrip(":")
        print(f"\n{cell['id']}  (ref_input={cell['ref_input']})")
        try:
            gold = host_reference(cell)
            print(f"  {YEL}host-ref{RST}: {norm(gold)[:140]}")
        except Exception as e:
            print(f"  {RED}host-ref FAILED{RST}: {e}")
            continue
        for m in models:
            wasm = HERE / "runs" / cid / m / "agent.wasm"
            if not wasm.exists():
                continue
            try:
                out, err = invoke_wasm(wasm, cell["ref_input"])
            except Exception as e:
                out, err = None, str(e)[:200]
            if err:
                print(f"  {m:8s} {RED}invoke-fail{RST}: {err}")
                rows.append({"cell": cell["id"], "model": m, "equiv": None, "err": err})
                continue
            strict = norm(out) == norm(gold)
            # equivalence modulo input-passthrough: kotoba_langgraph (graph.py:175)
            # merges the FULL input dict into state and never drops unwritten channels,
            # unlike real langgraph. So a port is "equivalent" if every gold key matches
            # and the ONLY extra keys are input keys that passed through.
            extra = set(out) - set(gold)
            input_keys = set(cell["ref_input"])
            gold_matches = all(k in out and norm(out[k]) == norm(gold[k]) for k in gold)
            modulo = strict or (gold_matches and extra <= input_keys)
            if strict:
                tag, verdict = f"{GREEN}EQUIV ✓{RST}", "strict"
            elif modulo:
                tag, verdict = f"{YEL}EQUIV~ (modulo input-passthrough: {extra}){RST}", "modulo-input"
            else:
                tag, verdict = f"{RED}MISMATCH{RST}", "mismatch"
            print(f"  {m:8s} {tag}")
            rows.append({"cell": cell["id"], "model": m, "equiv": strict,
                         "equiv_modulo_input": modulo, "verdict": verdict,
                         "extra_keys": sorted(extra), "wasm_out": out, "gold": gold})

    (HERE / "results" / "invoke-equiv.json").write_text(json.dumps(rows, indent=2, default=str))
    n_strict = sum(r.get("equiv") is True for r in rows)
    n_modulo = sum(r.get("equiv_modulo_input") is True for r in rows)
    print(f"\n{GREEN}{n_strict}/{len(rows)} strict-equivalent{RST}, "
          f"{n_modulo}/{len(rows)} equivalent-modulo-input-passthrough → results/invoke-equiv.json")


if __name__ == "__main__":
    main()
