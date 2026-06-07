#!/usr/bin/env python3
"""Harvest the repo's REAL agentic tool surface → Gemma-chat tool-use SFT
(ADR-2605302359 §4 item 2 — the highest-value on-distribution signal).

Sources of the tool catalog (deterministic, from code):
  1. kotoba WIT `world.wit` — typed host functions kqe/kse/auth/llm/evm/chain
     (exact signatures + `///` doc comments → grounded tool schemas).
  2. kotodama `Invoke("", "method.name", params)` inter-cell RPC method names.

Output: JSONL rows in the SAME schema as seed/agentic-tooluse-r0-seed.jsonl
({tools:[...], messages:[...]}), grounded in tools this system actually
exposes — so the QLoRA teaches gemma-4-26B-A4B THIS stack's agentic API.

Modes:
  --mode template  (default): deterministic templated trace per tool. No LLM.
  --mode teacher --teacher-url http://192.168.1.17:11434  : enrich each tool
     into a richer dialogue via the Murakumo own-node Ollama gemma teacher
     (OpenAI-compat /v1/chat/completions). Murakumo-only (ADR-2605215000);
     NEVER a vendor API. Falls back to template on any failure.

Usage:
  harvest_traces.py --out seed/harvested-traces.jsonl
"""
from __future__ import annotations
import argparse, json, os, re, sys, glob

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
WIT = os.path.join(REPO, "40-engine/kotoba/crates/kotoba-runtime/wit/world.wit")

WIT_TYPE = {  # WIT → (json type, example value)
    "string": ("string", "example"),
    "list<u8>": ("string", "<bytes>"),
    "u32": ("integer", 8), "u64": ("integer", 1), "s32": ("integer", 1),
    "bool": ("boolean", True), "f32": ("number", 1.0), "f64": ("number", 1.0),
}


def _json_type(wit_t: str):
    wit_t = wit_t.strip()
    for k, v in WIT_TYPE.items():
        if wit_t.startswith(k):
            return v
    if wit_t.startswith("option<") or wit_t.startswith("list<"):
        return ("string", "")
    return ("string", "")


def parse_wit(path: str):
    """Yield {iface, name, params, desc} for each `name: func(...)`."""
    if not os.path.exists(path):
        return
    lines = open(path).read().splitlines()
    iface = None
    pending_doc = []
    i = 0
    while i < len(lines):
        s = lines[i].strip()
        i += 1
        m_if = re.match(r"interface\s+([a-z0-9_-]+)\s*\{", s)
        if m_if:
            iface = m_if.group(1); pending_doc = []; continue
        if s.startswith("///"):
            pending_doc.append(s.lstrip("/ ").strip()); continue
        # a func decl may span multiple lines — accumulate until parens balance
        if iface and re.match(r"[a-z0-9-]+\s*:\s*func\(", s):
            buf = s
            while buf.count("(") > buf.count(")") and i < len(lines):
                buf += " " + lines[i].strip(); i += 1
            s = buf
        m = re.match(r"([a-z0-9-]+)\s*:\s*func\((.*)\)\s*->", s) or \
            re.match(r"([a-z0-9-]+)\s*:\s*func\((.*)\)", s)
        if m and iface:
            name, raw = m.group(1), m.group(2)
            params = []
            if raw.strip():
                # split top-level commas (params have no nested commas in this wit except list<tuple>)
                depth = 0; cur = ""; parts = []
                for ch in raw:
                    if ch in "<(": depth += 1
                    elif ch in ">)": depth -= 1
                    if ch == "," and depth == 0:
                        parts.append(cur); cur = ""
                    else:
                        cur += ch
                if cur.strip():
                    parts.append(cur)
                for p in parts:
                    if ":" in p:
                        pn, pt = p.split(":", 1)
                        jt, ex = _json_type(pt)
                        params.append({"name": pn.strip().replace("-", "_"),
                                       "type": jt, "example": ex})
            yield {"iface": iface, "name": name,
                   "tool": f"{iface}.{name.replace('-', '_')}",
                   "params": params,
                   "desc": " ".join(pending_doc) or f"{iface} {name}"}
            pending_doc = []
        elif s and not s.startswith("//"):
            pending_doc = []


def parse_invoke_methods(roots):
    methods = set()
    pat = re.compile(r"""Invoke\(\s*["'][^"']*["']\s*,\s*["']([a-z_][a-z0-9_.]+)["']""")
    for root in roots:
        for f in glob.glob(os.path.join(root, "**", "*.py"), recursive=True) + \
                 glob.glob(os.path.join(root, "**", "*.md"), recursive=True):
            try:
                for mth in pat.findall(open(f, errors="replace").read()):
                    if "." in mth:
                        methods.add(mth)
            except Exception:
                pass
    return sorted(methods)


def tool_schema(t):
    props = {p["name"]: {"type": p["type"]} for p in t["params"]}
    return {"type": "function", "function": {
        "name": t["tool"], "description": t["desc"],
        "parameters": {"type": "object", "properties": props,
                       "required": [p["name"] for p in t["params"]]}}}


def gen_template_row(t, idx):
    args = {p["name"]: p["example"] for p in t["params"]}
    user = f"Use the {t['tool']} capability: {t['desc'][:160]}"
    result = "{\"ok\": true}"
    return {"id": f"harvest-{idx:03d}-{t['tool'].replace('.', '_')}",
            "tools": [tool_schema(t)],
            "messages": [
                {"role": "system", "content": "You are an agent for the etzhayyim/kotoba stack. Call the available tool with correctly-typed arguments when it fits; otherwise answer plainly."},
                {"role": "user", "content": user},
                {"role": "assistant", "content": "",
                 "tool_calls": [{"type": "function", "function": {"name": t["tool"], "arguments": args}}]},
                {"role": "tool", "name": t["tool"], "content": result},
                {"role": "assistant", "content": f"Done — invoked {t['tool']} and received the result."}]}


def gen_teacher_row(t, idx, url):
    import urllib.request
    schema = json.dumps(tool_schema(t)["function"], ensure_ascii=False)
    prompt = ("Given this tool schema, write ONE realistic user request that would "
              "trigger it and a JSON object of valid arguments. Reply as JSON "
              "{\"user\":..., \"arguments\":{...}}. Schema:\n" + schema)
    body = json.dumps({"model": "gemma4:e4b",
                       "messages": [{"role": "user", "content": prompt}],
                       "stream": False, "options": {"temperature": 0.4}}).encode()
    req = urllib.request.Request(url.rstrip("/") + "/v1/chat/completions",
                                 data=body, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            txt = json.load(r)["choices"][0]["message"]["content"]
        j = json.loads(re.search(r"\{.*\}", txt, re.S).group(0))
        user, args = j["user"], j["arguments"]
    except Exception:
        return gen_template_row(t, idx)  # fall back, never a vendor API
    row = gen_template_row(t, idx)
    row["messages"][1]["content"] = user
    row["messages"][2]["tool_calls"][0]["function"]["arguments"] = args
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="seed/harvested-traces.jsonl")
    ap.add_argument("--mode", choices=["template", "teacher"], default="template")
    ap.add_argument("--teacher-url", default="http://192.168.1.17:11434")
    args = ap.parse_args()

    wit_tools = list(parse_wit(WIT))
    invoke_methods = parse_invoke_methods([
        os.path.join(REPO, "40-engine/kotoba/crates/kotoba-kotodama")])
    # Invoke methods → generic param-less tools (the method dispatch surface)
    for m in invoke_methods:
        wit_tools.append({"iface": "invoke", "name": m, "tool": m,
                          "params": [{"name": "params", "type": "string", "example": "{}"}],
                          "desc": f"inter-cell RPC method {m} (kotodama Invoke dispatch)"})

    rows = []
    for i, t in enumerate(wit_tools):
        if args.mode == "teacher":
            rows.append(gen_teacher_row(t, i, args.teacher_url))
        else:
            rows.append(gen_template_row(t, i))

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"harvested {len(rows)} grounded tool-use traces "
          f"({len(list(parse_wit(WIT)))} WIT funcs + {len(invoke_methods)} Invoke methods) "
          f"-> {args.out}", flush=True)
    print("WIT tools:", ", ".join(sorted({t['tool'] for t in wit_tools if t['iface'] != 'invoke'})))
    if invoke_methods:
        print("Invoke methods:", ", ".join(invoke_methods[:12]))


if __name__ == "__main__":
    main()
