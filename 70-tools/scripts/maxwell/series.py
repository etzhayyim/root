"""landscape-over-training: train maxwell-1 LoRA from base, snapshot weights at
checkpoints, then measure the REAL loss surface around each snapshot along the
SAME filter-normalized directions (Li et al.) → watch the basin deepen (grokking).
Murakumo-only (gad)."""
import json, pathlib, time, numpy as np, torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import LoraConfig, get_peft_model
BASE="google/gemma-4-E4B-it"; CORPUS=pathlib.Path.home()/"maxwell"/"corpus.jsonl"
CKPTS=[0,60,180,360,600]; G=11; SPAN=0.8; NB=4
torch.manual_seed(0)
tok=AutoTokenizer.from_pretrained(BASE)
model=AutoModelForCausalLM.from_pretrained(BASE,dtype=torch.bfloat16,device_map={"":0})
model=get_peft_model(model,LoraConfig(r=16,lora_alpha=32,lora_dropout=0.0,target_modules="all-linear",bias="none"))
model.train(); model.config.use_cache=False
lora={n:p for n,p in model.named_parameters() if p.requires_grad}
rows=[json.loads(l) for l in open(CORPUS) if l.strip()]
def enc(ex):
    text=tok.apply_chat_template(ex["messages"],tokenize=False)
    return tok(text,return_tensors="pt",truncation=True,max_length=768)["input_ids"].to("cuda")
evalset=[enc(r) for r in rows[:NB]]; pool=rows[NB:]
@torch.no_grad()
def meanloss():
    tot=0.0
    for ids in evalset: tot+=model(input_ids=ids,labels=ids).loss.item()
    return tot/len(evalset)
opt=torch.optim.AdamW([p for p in lora.values()],lr=2e-4)
snaps={}; tl={}
def snap(s):
    snaps[s]={n:p.detach().clone() for n,p in lora.items()}; tl[s]=meanloss()
    print(f"snapshot step {s} eval_loss {tl[s]:.4f}",flush=True)
snap(0)
t0=time.time(); i=0
for step in range(1,max(CKPTS)+1):
    ex=pool[i%len(pool)]; i+=1; ids=enc(ex)
    loss=model(input_ids=ids,labels=ids).loss
    opt.zero_grad(); loss.backward(); opt.step()
    if step in CKPTS: snap(step)
print(f"trained {max(CKPTS)} steps in {time.time()-t0:.0f}s",flush=True)
# fixed filter-normalized directions from the FINAL snapshot's per-tensor norms
final=snaps[max(CKPTS)]; g=torch.Generator(device="cuda").manual_seed(1)
def fdir():
    d={}
    for n,p in final.items():
        r=torch.randn(p.shape,generator=g,device="cuda",dtype=p.dtype)
        d[n]=r*(p.norm()/(r.norm()+1e-12))
    return d
d1,d2=fdir(),fdir()
def setw(base,a,b):
    with torch.no_grad():
        for n,p in lora.items(): p.copy_(base[n]+a*d1[n]+b*d2[n])
axis=np.linspace(-SPAN,SPAN,G); series=[]
for s in CKPTS:
    Z=np.zeros((G,G))
    for ia,a in enumerate(axis):
        for ib,b in enumerate(axis):
            setw(snaps[s],a,b); Z[ia,ib]=meanloss()
    series.append({"step":s,"train_loss":tl[s],"Z":Z.tolist()})
    print(f"grid step {s} done  Zmin {Z.min():.3f} Zmax {Z.max():.3f}",flush=True)
out=pathlib.Path.home()/"maxwell"/"landscape_series.json"
out.write_text(json.dumps({"axis":axis.tolist(),"span":SPAN,"G":G,"checkpoints":CKPTS,"series":series}))
print("WROTE",out,flush=True)
