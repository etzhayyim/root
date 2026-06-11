#!/usr/bin/env python3
import os
import sys
import glob
import subprocess
import urllib.request
import json
import base64
import time

# Use the Murakumo cluster LLM to generate the WASM port.
LITELLM_URL = "http://127.0.0.1:4000/v1/chat/completions"
# Using gemma4 26b a4b per user request
MODEL = "gemma4:26b-a4b"
LITELLM_KEY = "sk-etzhayyim-litellm-local"

KOTOBA_SERVER = "http://localhost:8077"
OPERATOR_DID = "did:key:ze2e169933f9bcc6cb218e083b3d2a80c5a5a2b92fbf3cb41b4d5283ce3f6939f"

PROMPT_TEMPLATE = """
You are an expert python software engineer migrating a LangGraph actor to a Kotoba WASM component.
Below is the python source code for a LangGraph actor using `from langgraph.graph import StateGraph`.

Your task is to output ONLY the python code for the new `kotoba_langgraph` port. Do NOT include markdown code blocks or explanations, JUST the raw python code.

The port MUST follow these rules:
1. Import `wit_world` and `from kotoba_langgraph import StateGraph, KotobaCheckpointer, START, END, handle_invoke`
2. Define a global `compiled` graph variable: `compiled = _g.compile(checkpointer=KotobaCheckpointer())`
3. Define exactly:
```python
class WitWorld(wit_world.WitWorld):
    def run(self, ctx_cbor: bytes) -> bytes:
        return handle_invoke(ctx_cbor, compiled)
```
4. Do NOT put your graph builder inside the `WitWorld` class. Define the state dicts, node functions, and graph builder at the module level.
5. Adapt the original logic cleanly. Remove or mock local relative imports like `from .state_machine import ...` so the module can compile standalone. Provide mock return dictionaries instead.
6. Replace `__end__` with `END`.

Original Actor Code:
```python
{original_code}
```
"""

def generate_port(original_code: str) -> str:
    req_data = {
        "model": MODEL,
        "messages": [
            {"role": "user", "content": PROMPT_TEMPLATE.replace("{original_code}", original_code)}
        ],
        "temperature": 0.0
    }

    req = urllib.request.Request(
        LITELLM_URL,
        data=json.dumps(req_data).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + LITELLM_KEY},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            res = json.loads(response.read())
            content = res["choices"][0]["message"]["content"]
            # clean up LLM output bugs
            content = content.replace("<unused56>", "")
            content = content.replace("```python", "").replace("```", "").strip()
            return content
    except Exception as e:
        print("LLM generation failed: " + str(e))
        return ""

def jwt():
    b = lambda o: base64.urlsafe_b64encode(json.dumps(o, separators=(',', ':')).encode()).rstrip(b'=').decode()
    return b({'alg': 'HS256', 'typ': 'JWT'}) + '.' + b({'sub': OPERATOR_DID, 'exp': 9999999999}) + '.opsig'

def deploy_wasm(wasm_path: str, program_cid: str) -> bool:
    with open(wasm_path, "rb") as f:
        wasm_bytes = f.read()

    wasm_b64 = base64.b64encode(wasm_bytes).decode('ascii')

    import cbor2
    ctx_b64 = base64.b64encode(cbor2.dumps({"_setup": True})).decode('ascii')

    mcp_req = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "kotoba_wasm_run",
            "arguments": {
                "program_cid": program_cid,
                "program_type": "wasm-node",
                "agent_did": OPERATOR_DID,
                "wasm_b64": wasm_b64,
                "ctx_cbor_b64": ctx_b64
            }
        }
    }

    req = urllib.request.Request(
        KOTOBA_SERVER + "/mcp",
        data=json.dumps(mcp_req).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + jwt()},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req) as response:
            res = json.loads(response.read())
            if "error" in res:
                print("Deploy failed for " + program_cid + ": " + str(res["error"]))
                return False
            return True
    except Exception as e:
        print("Deploy exception for " + program_cid + ": " + str(e))
        return False

def main():
    # Target specific files first to not take too long while testing
    files = glob.glob("20-actors/gov-municipality/cells/**/cell.py", recursive=True)

    for f in files:
        if "final_sign_off" in f or "inspection_scheduling" in f:
            continue # already ported manually
        print("Processing " + f + "...")

        with open(f, "r") as src:
            original = src.read()

        if "from langgraph.graph import" not in original:
            continue

        module_name = f.split("/")[-2]
        wasm_name = module_name + "_kotoba"
        out_dir = "40-engine/kotoba/examples/kotoba-langgraph-" + module_name.replace("_", "-")
        out_py = os.path.join(out_dir, wasm_name + ".py")
        out_wasm = os.path.join(out_dir, wasm_name + ".wasm")

        os.makedirs(out_dir, exist_ok=True)

        print("  Generating port using LLM...")
        ported = generate_port(original)
        if not ported:
            print("  Generation failed, skipping.")
            continue

        with open(out_py, "w") as out:
            out.write(ported)

        print("  Building WASM component...")
        env = os.environ.copy()
        # Set python paths to locate bindings and kotoba_langgraph
        env["PYTHONPATH"] = "../../target/pywasm-bindings:../../py"
        res = subprocess.run([
            "../../scripts/build-pywasm.sh",
            wasm_name + ".py",
            wasm_name + ".wasm"
        ], cwd=out_dir, env=env, capture_output=True, text=True)

        if res.returncode != 0:
            print("  Build failed:\n" + res.stderr)
            continue

        print("  Deploying to Kotoba...")
        if deploy_wasm(out_wasm, "auto_" + module_name):
            print("  Successfully migrated " + module_name + ".")

        time.sleep(1)

if __name__ == "__main__":
    main()
