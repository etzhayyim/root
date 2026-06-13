#!/usr/bin/env python3
"""A/B coverage eval: base gemma4-e4b-it-qat vs base+CPT-LoRA on held-out units.
Deterministic greedy decode; emits heldout-gen.jsonl {name, base_out, cpt_out}.
Gating (clj-kondo + bb-load) runs downstream on the orchestrator host."""
import json, sys, torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

BASE = "google/gemma-4-E4B-it-qat-q4_0-unquantized"
ADAPTER = "/home/gad/cpt-eval/cpt-clj-lora-v2"
SYSTEM = open("/home/gad/cpt-eval/UNIT_SYSTEM.txt").read()

def load_units(p):
    return [json.loads(l) for l in open(p)]

def build_prompt(tok, code):
    msg = [{"role":"user","content": SYSTEM + "\n\nTranslate this unit:\n\n```python\n" + code + "\n```"}]
    return tok.apply_chat_template(msg, tokenize=False, add_generation_prompt=True)

def gen(model, tok, prompt):
    ids = tok(prompt, return_tensors="pt").to(model.device)
    with torch.no_grad():
        out = model.generate(**ids, max_new_tokens=640, do_sample=False,
                             temperature=None, top_p=None, top_k=None,
                             pad_token_id=tok.eos_token_id)
    return tok.decode(out[0][ids.input_ids.shape[1]:], skip_special_tokens=True)

def main():
    units = load_units("/home/gad/cpt-eval/heldout-units.jsonl")
    print(f"{len(units)} units", flush=True)
    tok = AutoTokenizer.from_pretrained(BASE)
    print("loading base…", flush=True)
    base = AutoModelForCausalLM.from_pretrained(BASE, torch_dtype=torch.bfloat16, device_map="cuda")
    base.eval()
    prompts = [build_prompt(tok, u["code"]) for u in units]

    print("=== BASE generation ===", flush=True)
    base_outs = []
    for i,p in enumerate(prompts):
        base_outs.append(gen(base, tok, p)); print(f"base {i+1}/{len(units)}", flush=True)

    print("=== load adapter (CPT) ===", flush=True)
    cpt = PeftModel.from_pretrained(base, ADAPTER)
    cpt.eval()
    cpt_outs = []
    for i,p in enumerate(prompts):
        cpt_outs.append(gen(cpt, tok, p)); print(f"cpt {i+1}/{len(units)}", flush=True)

    with open("/home/gad/cpt-eval/heldout-gen.jsonl","w") as f:
        for u,b,c in zip(units, base_outs, cpt_outs):
            f.write(json.dumps({"actor":u["actor"],"module":u["module"],"name":u["name"],
                                "kind":u["kind"],"code":u["code"],
                                "base_out":b,"cpt_out":c})+"\n")
    print("WROTE heldout-gen.jsonl", flush=True)

if __name__=="__main__":
    sys.exit(main())
