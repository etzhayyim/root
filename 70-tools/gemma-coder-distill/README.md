# gemma-coder-distill

LangGraph ReAct loop that distills **gemma4:e4b** into a LangGraph-coding
specialist, gated by the `70-tools/scripts/bench/langgraph-coding/` bench.

Authoritative ADR: [`90-docs/adr/2605250400-gemma-coder-distill-rocm.md`](../../90-docs/adr/2605250400-gemma-coder-distill-rocm.md).

## Trainer

**peft + trl direct** (per ADR §1.2 — Unsloth probed 2026-05-25 on EVO-X2
Windows ROCm 7.2.1 + Python 3.12, see
[`90-docs/baien/probe_unsloth_rocm.json`](../../90-docs/baien/probe_unsloth_rocm.json),
fail: CUDA-only dep tree).

## Layout

```
70-tools/gemma-coder-distill/
├── pyproject.toml
├── README.md (this file)
├── scripts/
│   └── probe_unsloth_rocm.py   # re-runnable when Unsloth ships Windows ROCm
└── src/gemma_coder_distill/
    ├── __init__.py
    ├── __main__.py             # CLI entrypoint
    ├── state.py                # DistillState TypedDict + TrainExample
    ├── graph.py                # LangGraph state machine
    └── nodes/
        ├── analyze.py          # (1) read bench, find weak categories
        ├── fetch_dataset.py    # (2) HF Apache/MIT corpora pull
        ├── validate.py         # (3) length + Charter Rider §2 scan
        ├── train.py            # (4) peft+trl LoRA on gemma-3-4b-it bf16
        ├── evaluate.py         # (5) re-run langgraph-coding bench, gate
        └── commit.py           # (6) append manifest on pass
```

## Quickstart

```bash
# install (on EVO-X2 ROCm venv)
ssh evo 'C:\Users\gad\ComfyUI\ComfyUI_windows_portable\python_embeded\python.exe ^
   -m pip install -e C:\path\to\repo\70-tools\gemma-coder-distill'

# dry-run plan only
ssh evo '...python.exe -m gemma_coder_distill ^
   --bench-dir 90-docs/baien --dry-run --max-iter 1'

# quick iter-00 smoke (1 epoch, n≤200, gate=0pp)
ssh evo '...python.exe -m gemma_coder_distill ^
   --bench-dir 90-docs/baien --quick --max-iter 1'

# full iter (2 epoch, gate=+3pp)
ssh evo '...python.exe -m gemma_coder_distill ^
   --bench-dir 90-docs/baien --max-iter 1'
```

## Distribution to Mac mini fleet (post-commit)

```bash
# 1) convert merged HF → GGUF Q4_K_M
ssh evo 'cd C:\llama.cpp && python convert.py ^
   C:\path\gemma-coder-distill-out\iter-00\merged ^
   --outfile gemma4-coder-e4b-iter00-Q4_K_M.gguf --outtype Q4_K_M'

# 2) push to each mini (Ansible — see ADR §3 Step 6)
ansible-playbook -i 60-apps/etzhayyim-project-murakumo/ansible/inventory/hosts.yml \
   60-apps/etzhayyim-project-murakumo/ansible/push-ollama-model.yml \
   -e model_file=gemma4-coder-e4b-iter00-Q4_K_M.gguf \
   -e model_tag=gemma4-coder:e4b-iter00

# 3) add LiteLLM route on judah
#    edit 50-infra/cluster/murakumo/litellm/config.yaml → add gemma4-coder entry
```

## License

Apache 2.0 + etzhayyim Charter Compliance Rider v2.0 (see
[`/CHARTER-RIDER.md`](../../CHARTER-RIDER.md)).

Per-iter license review required for **distill output** when training
dataset includes non-Apache sources (e.g. Gemma TOS for the base model
distribution path).

## Status

Scaffold + node logic landed 2026-05-25. Awaits:

- **Step 2**: `70-tools/scripts/bench/langgraph-coding/prompts.jsonl` + 50 graders (currently 1 seed)
- **Step 4**: coding-specific Apache/MIT HF corpora added to `DATASET_REGISTRY`
- **Step 5**: iter-00 quick run end-to-end on EVO-X2 (requires Step 2 done first)
- **Step 6**: Ansible push runbook (`60-apps/etzhayyim-project-murakumo/ansible/push-ollama-model.yml`)
- **Step 7**: LiteLLM route addition (`gemma4-coder:e4b` in `50-infra/cluster/murakumo/litellm/config.yaml`)
