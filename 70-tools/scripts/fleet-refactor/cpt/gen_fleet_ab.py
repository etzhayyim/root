#!/usr/bin/env python3
"""Fleet A/B: gemma4:e4b-it-qat vs gemma4:12b-it-qat over the held-out 54,
20-stream (10 nodes x 2). Native /api/chat, think:false. Same UNIT_SYSTEM prompt.
Emits heldout-gen-fleet.jsonl {actor,name,e4b_out,12b_out}."""
import json, sys, urllib.request, concurrent.futures as cf
sys.path.insert(0, ".")
from fleet_refactor import NODES, NodePool
from unit_refactor import UNIT_SYSTEM

POOL = NodePool(NODES, 2)  # 20 streams

def chat(ip, model, code):
    body = json.dumps({"model": model,
        "messages": [{"role":"system","content":UNIT_SYSTEM},
                     {"role":"user","content":"```python\n"+code+"\n```"}],
        "stream": False, "think": False,
        "options": {"temperature": 0.1, "num_ctx": 16384}}).encode()
    req = urllib.request.Request(f"http://{ip}:11434/api/chat", data=body,
                                headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req, timeout=420) as r:
        d = json.load(r)
    if "error" in d: raise OSError(d["error"])
    return d["message"]["content"]

def one(model, u):
    name, ip = POOL.acquire()
    try:
        return chat(ip, model, u["code"])
    finally:
        POOL.release(name)

def arm(model, units):
    outs = [None]*len(units)
    with cf.ThreadPoolExecutor(max_workers=20) as ex:
        futs = {ex.submit(one, model, u): i for i,u in enumerate(units)}
        done = 0
        for f in cf.as_completed(futs):
            i = futs[f]
            try: outs[i] = f.result()
            except Exception as e: outs[i] = f"ERROR: {e}"
            done += 1; print(f"{model} {done}/{len(units)}", flush=True)
    return outs

def main():
    units = [json.loads(l) for l in open("heldout-units.jsonl")]
    print(f"{len(units)} units, 20-stream fleet", flush=True)
    e4b = arm("gemma4:e4b-it-qat", units)
    twelve = arm("gemma4:12b-it-qat", units)
    with open("heldout-gen-fleet.jsonl","w") as f:
        for u,e,t in zip(units,e4b,twelve):
            f.write(json.dumps({"actor":u["actor"],"name":u["name"],
                                "e4b_out":e,"12b_out":t})+"\n")
    print("WROTE heldout-gen-fleet.jsonl", flush=True)

if __name__=="__main__": sys.exit(main())
