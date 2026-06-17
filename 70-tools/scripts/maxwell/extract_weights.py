"""Extract REAL maxwell-1 tensors (Gemma4 E4B + M1-r2 LoRA) → JSON for plotting:
(1) per-layer base weight norms + LoRA ΔW norms, (2) LoRA ΔW singular values,
(3) real attention probabilities on a real prompt, (4) a real weight-matrix block."""
import json, re, pathlib, numpy as np, torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
BASE="google/gemma-4-E4B-it"; AD=str(pathlib.Path.home()/"maxwell"/"out"/"m1-r1")
tok=AutoTokenizer.from_pretrained(AD)
model=AutoModelForCausalLM.from_pretrained(BASE,dtype=torch.bfloat16,device_map={"":0},attn_implementation="eager")
model=PeftModel.from_pretrained(model,AD); model.eval()
PROJ=["q_proj","k_proj","v_proj","o_proj","gate_proj","up_proj","down_proj"]
layers={}; svals={}
for name,mod in model.named_modules():
    m=re.search(r"layers\.(\d+)\.",name)
    if not m or not hasattr(mod,"lora_A"): continue
    l=int(m.group(1)); proj=next((p for p in PROJ if name.endswith(p)),None)
    if proj is None: continue
    base=mod.base_layer.weight.detach().float()
    A=mod.lora_A["default"].weight.detach().float(); B=mod.lora_B["default"].weight.detach().float()
    sc=mod.scaling["default"]; dW=sc*(B@A)
    layers.setdefault(l,{})[proj]={"base":float(base.norm()),"dW":float(dW.norm())}
    if l==0 and proj=="q_proj": globals()["_W0"]=base.cpu().numpy()
    if proj=="q_proj":
        s=torch.linalg.svdvals(dW).cpu().numpy()[:16]; svals[l]=s.tolist()
# (3) real attention on a real prompt
msgs=[{"role":"user","content":"Convert to Clojure: def add(a,b): return a+b"}]
enc=tok.apply_chat_template(msgs,tokenize=True,add_generation_prompt=True,return_tensors="pt",return_dict=True).to("cuda")
with torch.no_grad(): out=model(input_ids=enc["input_ids"],attention_mask=enc["attention_mask"],output_attentions=True)
toks=[tok.decode([t]) for t in enc["input_ids"][0].tolist()]
La=20; att=out.attentions[La][0].float().mean(0).cpu().numpy()    # avg heads, seq×seq
# (4) real weight block: layer 0 q_proj base, block-mean downsample to 96x96
W0=globals()["_W0"]
def ds(M,n=96):
    r=np.array_split(M,min(n,M.shape[0]),0); r=[x.mean(0) for x in r]; M2=np.array(r)
    c=np.array_split(M2,min(n,M2.shape[1]),1); return np.array([x.mean(1) for x in c]).T
W0d=ds(W0)
out=pathlib.Path.home()/"maxwell"/"weights_viz.json"
out.write_text(json.dumps({"layers":layers,"svals":svals,"attn":att.tolist(),"tokens":toks,
    "attn_layer":La,"wq0":W0d.tolist(),"wq0_shape":list(W0.shape),"proj":PROJ,"n_layers":len(layers)}))
print("WROTE",out,"layers",len(layers),"attn",att.shape,"wq0",W0.shape,"->",W0d.shape)
