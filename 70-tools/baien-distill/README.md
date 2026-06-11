# baien-distill

LangGraph ReAct loop that distills baien (BitNet b1.58 2B-4T) from an
on-fleet OSS teacher, gated by `e7m bench` scores.

Authoritative ADR: [`90-docs/adr/2605231300-baien-distill-react-loop.md`](../../90-docs/adr/2605231300-baien-distill-react-loop.md).

## Layout

```
70-tools/baien-distill/
├── pyproject.toml
├── README.md  (this file)
└── src/baien_distill/
    ├── __init__.py
    ├── state.py            # TypedDict DistillState (source: "hf" | "teacher")
    ├── graph.py            # LangGraph state machine wiring (source-conditional branch)
    ├── nodes/
    │   ├── analyze.py            # (1) read bench results, rank weak categories
    │   ├── fetch_dataset.py      # (3a, DEFAULT) sample TrainExample from HF public datasets
    │   ├── select_teacher.py     # (2, fallback) pick on-fleet OSS teacher
    │   ├── generate.py           # (3b, fallback) teacher.cot() → list[TrainExample]
    │   ├── validate.py           # (4) filter (length / parse / Charter Rider §2)
    │   ├── train.py              # (5) peft+trl LoRA on bf16 master + merge_adapter()
    │   ├── evaluate.py           # (6) merge, microbench.py re-eval
    │   └── commit.py             # commit_node — append distilled-models.jsonl
    └── adapters/
        ├── hf_dataset.py         # HF Datasets loader + Qwen-chat-text parser + DATASET_REGISTRY
        ├── ollama_teacher.py     # OpenAI-compat client → EVO-X2 / judah LiteLLM
        ├── baien_student.py      # transformers loader for the bf16 master
        └── bench_reader.py       # parses 90-docs/baien/results-*.jsonl and lm-eval JSON
```

## Runtime modes

This loop assumes **train and eval run on the same host** so that
`merged/` adapter dir paths agree. Two deployment modes:

| Mode | Python | Where to launch from | Throughput | Notes |
|---|---|---|---|---|
| **CPU (EVO-X2 default Python 3.10)** | `C:\Program Files\Python310\python.exe` | `ssh evo "python -m baien_distill ..."` | 6–12h / iter | works today; verified via `probe_rocm.py` |
| **ROCm (EVO-X2 ComfyUI bundled)** | `C:\Users\gad\ComfyUI\ComfyUI_windows_portable\python_embeded\python.exe` | `ssh evo "...\python_embeded\python.exe -m baien_distill ..."` | ~1–2h / iter (est.) | torch 2.9.1+rocm7.2.1 / HIP 7.2 / gfx1151 — verified 2026-05-23. Need to `pip install peft trl transformers datasets langgraph openai` into that embedded venv first |
| **Mac (Apple MPS)** | local | `python -m baien_distill ...` | similar to CPU | uses MPS where transformers supports it (BitNet mostly CPU) |

`evaluate.py` uses `sys.executable` for the microbench subprocess, so
whichever Python launches the loop is what re-evals the merged model.

## Quickstart (after at least one bench run exists)

```bash
cd 70-tools/baien-distill
uv venv --python 3.10 .venv
. .venv/bin/activate
pip install -e .[dev]

# dry-run: print plan without fetching dataset or training
python -m baien_distill --bench-dir ../../90-docs/baien --dry-run --max-iter 1

# DEFAULT — pull Opus-distilled reasoning SFT from Hugging Face (Apache-2.0)
python -m baien_distill --bench-dir ../../90-docs/baien --quick --max-iter 1
# equivalent: --source hf  (this is the default)

# FALLBACK — generate via on-fleet OSS teacher (Qwen3-32B / llama3.3 / ...)
python -m baien_distill --bench-dir ../../90-docs/baien --quick --max-iter 1 --source teacher

# via the etzhayyim CLI
e7m bench distill --max-iter 1 --quick
e7m bench distill --max-iter 1 --quick --source teacher
```

## Data source registry

Curated public datasets per weak category live in
`src/baien_distill/adapters/hf_dataset.py` (`DATASET_REGISTRY`). To add
one, append a `DatasetSpec(...)` row and (if needed) a format adapter in
`_row_to_example()`.

Initial entries (2026-05-23, ADR-2605231300 §3a):

| Category | Dataset | Rows | License |
|---|---|---|---|
| Reasoning | `lordx64/reasoning-distill-opus-4-7-max-sft` | 7,823 | Apache-2.0 |
| General | (reuses Reasoning) | 7,823 | Apache-2.0 |
| IFEval | `aisingapore/Instruction-Following-IFEval` | 1–10k | CC-BY-4.0 |
| Multilingual | *(deferred — Tulu has NC subsets)* | — | — |
| MMLU | *(no SFT distill source — knowledge MC is not improved via SFT)* | — | — |

## Status

Skeleton ships node stubs and the LangGraph wiring. The non-trivial
work (actual teacher prompts, peft training loop, score-delta logic)
is left as TODOs and is per-node tracked in the ADR §"Acceptance
criteria".

## License

Apache 2.0 + etzhayyim Charter Compliance Rider v2.0 (see
[`/CHARTER-RIDER.md`](../../CHARTER-RIDER.md)).

When the loop produces LoRA adapter artifacts derived from a teacher
that has a non-Apache license (e.g. Llama 3 Community License), the
**published** adapter inherits the teacher license terms in addition
to Apache 2.0 + Rider. See ADR-2605231300 §"License and Charter
Rider implications" for the per-iter review gate.
