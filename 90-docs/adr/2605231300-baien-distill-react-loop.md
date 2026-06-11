---
id: adr-2605231300-baien-distill-react-loop
title: "Baien score-improvement distill ReAct loop on EVO-X2"
status: proposed
doc_type: adr
topic: baien-training-loop
authoritative: true
last_verified: 2026-05-23
authoritative_for:
  - baien score-improvement closed-loop architecture
  - LangGraph state machine for distillation iterations
  - teacher model selection rule (OSS only, on-fleet)
  - LoRA-on-bf16-master training contract (per ADR-2605092350 §LoRA)
  - bench gate (micro → core3 promotion threshold)
  - license inheritance handling (Llama 3 community / Qwen Apache / etc.)
depends_on:
  - adr-2605092350-baien-1bit-multimodal-edge-browser-cpu-design
  - adr-2605101000-baien-mx-multimodal-expansion-from-rw
  - adr-2605070700-rw-native-model-training-weight-lineage
  - adr-2605202345-evo-x2-gpu-pod-fleet-integration
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
related:
  - 70-tools/baien-distill/
  - 70-tools/scripts/bench/baien-microbench/microbench.py
  - 70-tools/etzhayyim-cli/bench.go
  - doc-260523-frontier-bench-snapshot
supersedes: []
superseded_by: []
---

# Goal

Define a **closed-loop distillation pipeline** that uses an on-fleet
OSS teacher model to generate targeted SFT data for baien's weakest
bench categories, LoRA-fine-tunes the baien bf16 master, and gates
promotion through the same bench harness (`e7m bench micro` →
`e7m bench core3`) that produced the original weak signal.

The loop is a **LangGraph ReAct state machine**: each iteration
*reasons* over the latest bench delta and *acts* by generating
category-targeted training data, training a LoRA adapter, and
re-evaluating.

This ADR is **not** about pretraining baien (already done by
Microsoft) nor about the baien-MX modality grafts
(ADR-2605101000). It is about **post-train SFT/LoRA** to close
specific score gaps surfaced by `e7m bench`.

# Scope

In scope:

- LangGraph state machine spec (6 nodes + 3 conditional edges).
- Teacher selection rule (OSS only, on-fleet inference endpoints).
- Per-category SFT data generation strategy.
- LoRA training contract (target modules, rank, batch size, epochs).
- Eval gate (micro pass-rate Δ → optional core3 promotion).
- Storage in `vertex_training_checkpoint` (ADR-2605070700) under
  new training_kind `baien-distill-react`.
- License inheritance handling — derivative weights inherit teacher
  license; **publication requires per-iteration legal review**.

Out of scope:

- Modifying the baien BitNet pretraining (Microsoft 4T token run).
  Distillation operates on the bf16 master; ternary re-quant
  happens at promotion time, not in the loop.
- Multimodal modality grafts — those follow the Move 1/2/3 path
  in ADR-2605101000.
- Frontier-API teacher use (OpenAI / Anthropic / Gemini). All teachers
  must run on the etzhayyim fleet (Apache 2.0 + Charter Rider boundary
  per ADR-2605192200; commercial-API distillation breaks the
  donation-only payment substrate and the Charter Rider §2(h)
  prohibition on commercial coupling).
- Reinforcement-learning loops (PPO/DPO with reward model). Initial
  scope is SFT-only; DPO is a deferred extension.

# Decision

Implement a **7-node LangGraph state machine** at
`70-tools/baien-distill/src/baien_distill/graph.py`.

The data-source step branches at the conditional edge after `analyze`:
default (`source=hf`) goes to `fetch_dataset` directly; explicit
`--source teacher` goes through `select_teacher → generate`. Both
converge at `validate`.

```
                  ┌─────────────┐
   start ───▶     │ 1. analyze  │ ← reads 90-docs/baien/results-*.jsonl
                  └─────┬───────┘   + lm-eval-260523/<task>/*.json
                        │
                        ▼ (source switch)
              ┌──────────────────────┐
        hf   ─┤  source == "hf"?     ├─ teacher
       (default)                       (fallback)
              └─────┬────────────┬──┘
                    ▼            ▼
        ┌────────────────┐  ┌─────────────┐
        │ 3a. fetch_     │  │ 2. select   │
        │   dataset (HF) │  │   teacher   │
        │  Apache-2.0    │  └─────┬───────┘
        │  Opus distill  │        │
        │  default       │        ▼
        └─────┬──────────┘  ┌─────────────┐
              │             │ 3b. generate│
              │             │  (teacher   │
              │             │   inference)│
              │             └─────┬───────┘
              └──────────┬────────┘
                         ▼
                  ┌─────────────┐
                  │ 4. validate │   filter: length, json-parse, MC-letter,
                  │             │   no-PII, charter-rider §2 violations
                  └─────┬───────┘   → list[TrainExample] (filtered)
                        │
                        ▼
                  ┌─────────────┐
                  │ 4. validate │   filter: length, json-parse, MC-letter,
                  │             │   no-PII, charter-rider §2 violations
                  └─────┬───────┘   → list[TrainExample] (filtered)
                        │
                        ▼
                  ┌─────────────┐
                  │ 5. train    │   LoRA-on-bf16-master, peft+transformers
                  │  lora       │   save adapter + dataset hash to
                  └─────┬───────┘   vertex_training_checkpoint
                        │
                        ▼
                  ┌─────────────┐
                  │ 6. evaluate │   merge LoRA, run e7m bench micro,
                  │             │   if Δ ≥ +2.0%: also run e7m bench core3
                  └─────┬───────┘
                        │
                        ▼  (conditional)
                  ┌─────────────────────┐
                  │ decide              │   ┌── commit  ──▶ end (ok)
                  │ - improved & core3? ├──┤── retry   ──▶ back to (1) w/ different strategy
                  │ - max_iter reached? │   └── abort   ──▶ end (no-op)
                  └─────────────────────┘
```

Iteration cap: `max_iter = 3` by default (configurable).

# Node specifications

## 1. `analyze`

Input: most recent
- `90-docs/baien/results-<YYMMDD>.jsonl` (microbench, 15 rows)
- `90-docs/baien/lm-eval-<YYMMDD>/<task>/results_*.json` (lm-eval per-task)

Output (added to state):
- `weak_categories: list[CategorySpec]` ranked by gap-to-frontier and
  by absolute floor (random-chance gap)

Heuristic ranking:
```
gap_score(c) = (frontier_best[c] - baien[c])         # absolute gap
              + 0.5 * (50% - baien[c]).clip(min=0)   # below-random penalty
              + 1.0 * (c in {IFEval, multilingual})  # high-priority weight
```

The highest 1–3 categories are selected as targets for this
iteration. The reasoning is recorded in `state.notes`
(ReAct-style explicit rationale).

## 2. `select_teacher`

Constraints:

| Rule | Reason |
|---|---|
| OSS license only (Apache / MIT / Llama-Community) | ADR-2605192200 Charter Rider, no commercial-API distillation |
| Endpoint must be on etzhayyim fleet (LAN) | donation-only substrate; no external API |
| ≥ 8 tok/s effective throughput | data generation must complete in ≤ 24h |
| At least 7B params *and* significantly stronger than baien on target category | useful teacher signal |

Candidates (as of 2026-05-23):

| Model | Endpoint | Throughput (verified) | Notes |
|---|---|---|---|
| `llama3.3:70b` (Q4_K_M, 42GB) | `http://192.168.1.22:11434` (EVO-X2 ollama) | 1.18 tok/s | Strong teacher but very slow — only for ≤ 200 prompts |
| `llama3.2:3b` (Q4_K_M, 2GB) | EVO-X2 ollama | 83 tok/s | Same scale as baien, marginal teacher signal |
| `qwen3-32b-awq` (~18GB, future) | EVO-X2 (pull required) | ~5–10 tok/s (ROCm gfx1151) | **Default recommended teacher** once pulled |
| `gemma3:4b` | dan/issachar/joseph/zebulun/simeon/asher ollama (per fleet.toml) | unverified | Multi-node parallel possible via LiteLLM gateway (judah:4000) |

Selection rule:
```
if "qwen3-32b" available:        teacher = "qwen3-32b"  # default
elif target_category in {STEM,
                          coding}:    teacher = "llama3.3:70b"
elif target_category multilingual:    teacher = "qwen3-32b"  # JP capability
else:                                 teacher = "gemma3:4b-parallel"
```

## 3a. `fetch_dataset` (DEFAULT, ADR-2605231300 v0.2 pivot 2026-05-23)

For each weak category, sample from a curated **public Hugging Face SFT
dataset** rather than generating synthetic data from an on-fleet teacher.
This was the v0.1 design's biggest implicit cost (teacher inference time
+ teacher bias inheritance + license inheritance from teacher); replacing
it with a high-quality dataset that already exists removes all three.

Registry lives at
`70-tools/baien-distill/src/baien_distill/adapters/hf_dataset.py`
(`DATASET_REGISTRY`). Initial entries:

| Category | Dataset | Rows | License | Format |
|---|---|---|---|---|
| Reasoning | `lordx64/reasoning-distill-opus-4-7-max-sft` | 7,823 | **Apache-2.0** | Qwen3 chat-template `text` column, includes `<think>` blocks (Claude Opus 4.7 extended-thinking traces) |
| General | (reuses Reasoning set) | 7,823 | Apache-2.0 | same |
| IFEval | `aisingapore/Instruction-Following-IFEval` | 1–10k | CC-BY-4.0 | `prompt`+`response` (multilingual subsets) |
| Multilingual | *(deferred — Tulu mixture is ODC-BY with NC subsets; needs subset-by-subset review)* | — | — | — |
| MMLU | *(no SFT distill source — knowledge MC is not improved via SFT in general)* | — | — | — |

Adding a dataset = PR to `DATASET_REGISTRY` + per-row format adapter in
`adapters/hf_dataset.py`. No code changes to the LangGraph nodes.

The adapter normalizes every row to `TrainExample(prompt, response,
category, teacher_model="hf:<id>")` so downstream nodes (validate,
train) are dataset-agnostic.

**Default source = `hf`**; teacher generation remains available as a
fallback via `--source teacher` (see §3b).

## 3b. `generate_training_data` (FALLBACK, ADR §3b)

For each weak category, run a category-specific teacher generator:

| Category | Generator template |
|---|---|
| IFEval | Teacher receives "Generate an instruction with a precise verifiable constraint (format / count / case / keyword), followed by a compliant response. The constraint must be machine-checkable." → parsed into (instruction, response, scorer_spec) triple. |
| MMLU / multiple-choice | Teacher receives "Generate a 4-choice exam-style question on {subject}. Output JSON {q, A, B, C, D, correct, brief_explanation}." Subject pulled from MMLU subject list. |
| Reasoning (math / logic) | Teacher receives "Generate a one-paragraph reasoning problem and a step-by-step solution ending with 'Answer: <X>'. Difficulty: GSM8K-level." → CoT distillation. |
| Multilingual (JP↔EN) | Teacher receives "Translate the following English sentence into natural Japanese. Output JSON {en, ja}. Sentence: {seed_from_wmt_corpus}." Use existing WMT24++ source side as seeds. |
| General factual QA | Teacher receives "Generate a brief factual question and its 1-sentence answer in JSON." |

Each generator outputs:

```python
@dataclass
class TrainExample:
    prompt: str
    response: str
    category: str
    teacher_model: str
    seed: str | None
    scorer_spec: dict | None  # for IFEval-style verifiables
```

Default N per category: **200** (configurable). Total per iteration:
~400–600 examples (top 2–3 weak categories).

## 4. `validate_training_data`

Filter pipeline (each example must pass all):

| Check | Action on fail |
|---|---|
| `len(response) ≥ 8 chars and ≤ 1024 chars` | drop |
| `category == IFEval`: scorer self-check (teacher's response passes its own scorer_spec) | drop |
| `category == MMLU`: JSON parses, `correct` in {A,B,C,D} | drop |
| `category == Reasoning`: response contains "Answer:" or final numeric/letter | drop |
| `category == Multilingual`: JSON parses, both sides non-empty, language-id check (heuristic) | drop |
| **Charter Rider §2 content scan** (no advertising / no purchase prompt / no Gore / etc.) | **drop + log** |
| no PII heuristics (email / phone / SSN regex) | drop |

Pass rate target: **≥ 60%** after filtering. If lower, signal
`teacher_too_weak` and bounce back to node 2 with different teacher.

## 5. `train_lora`

Stack:

| Layer | Choice | Rationale |
|---|---|---|
| Lib | `peft` (Hugging Face) | Standard LoRA on transformers |
| Trainer | `trl.SFTTrainer` | Chat-template aware, easy SFT |
| Base | `microsoft/bitnet-b1.58-2B-4T-bf16` | bf16 master per ADR-2605092350 (direct ternary fine-tune unstable) |
| Target modules | `q_proj`, `k_proj`, `v_proj`, `o_proj` | standard attn LoRA |
| Rank | `r=16` (default), `alpha=32` | conservative |
| Dropout | `0.05` | |
| Batch | `1` (CPU) or `4` (ROCm if peft+rocm works) | EVO-X2 memory headroom |
| Optim | AdamW, lr=2e-4, cosine warmup 100 steps | standard |
| Epochs | 1–2 | overfit-resist on 400-600 examples |
| Precision | bf16 weights + fp32 master copy | |

Output:
- LoRA adapter dir: `~/baien-distill/iter-<N>/adapter/`
- `vertex_training_checkpoint` row with:
  - `kind = "baien-distill-react"`
  - `parent_kind = "bitnet-b1.58-2B-4T-bf16"`
  - `dataset_hash = sha256(jsonl(filtered_examples))`
  - `teacher_model_id`
  - `lora_config`
  - `final_loss`
  - `iter_index`

Runtime budget on EVO-X2 (Ryzen AI Max+ 395):

| Stack | Throughput est. | Status |
|---|---|---|
| Default system Python 3.10 + torch 2.12.0+cpu | 6–12 h / 500 examples | **verified usable** via `70-tools/baien-distill/scripts/probe_rocm.py` 2026-05-23 |
| ComfyUI bundled `python_embeded` (torch 2.9.1+rocm7.2.1, HIP 7.2, gfx1151) | ~1–2 h / 500 examples | **ROCm device detected** 2026-05-23 (`{"cuda": true, "hip": "7.2.53211-158bd99533", "device_count": 1}`); needs `pip install peft trl transformers datasets langgraph openai` into that env to be runnable. |

The eval subprocess in `evaluate.py` calls `sys.executable`, so
launching the loop from the ComfyUI python_embeded automatically
routes the re-eval through the ROCm-capable interpreter too.

## 6. `evaluate`

Always run `e7m bench micro` (~5 min) on the LoRA-merged model.

If `delta_micro_score ≥ +2.0 percentage points`:
- Optionally run `e7m bench core3` (~5h) for confirmation.
- If `delta_core3_score ≥ +1.0 pp` → `decision = "commit"`.
- Else (core3 regressed despite micro gain → overfit) → `decision = "retry"`.

If `delta_micro_score < +2.0 pp`:
- `decision = "retry"` (try different teacher or category mix), OR
  `"abort"` if `iter ≥ max_iter`.

## 7. decision routing (conditional edge)

```
decide() →
  if state.decision == "commit":  go to commit_node     → END (ok)
  if state.decision == "retry" and state.iter < max_iter: go to (1) analyze
  if state.decision == "abort":   go to abort_node       → END (no-op, weights discarded)
```

`commit_node` (implemented at `70-tools/baien-distill/src/baien_distill/nodes/commit.py`)
appends a JSONL line to `90-docs/baien/distilled-models.jsonl`. A separate
codegen `70-tools/scripts/llm-registry/gen-distilled-entries.mjs` reads
that manifest and emits
`40-engine/kotoba/crates/kotoba-kotodama/sdk/kotodama-host-sdk/src/llm-model-registry-distilled.ts`
(an auto-generated TS module imported and merged into `MODEL_REGISTRY`).

Rationale for two-phase ship (Python manifest → TS codegen) rather than
direct in-place edit of `llm-model-registry.ts`:

- The loop never edits TS files — no fragile AST manipulation.
- The reviewer sees a deterministic diff between manifest and TS module
  and explicitly flips `available: true` on a per-entry basis.
- Provenance (`DISTILLED_MODEL_PROVENANCE`) is emitted as a sibling
  export so audit / license tracking stays attached to the entry.

`abort_node` deletes the LoRA adapter dir (best-effort `shutil.rmtree`).

# State shape

```python
class DistillState(TypedDict):
    # input
    bench_dir: Path                    # 90-docs/baien/
    max_iter: int                      # default 3

    # mutated during loop
    iter: int                          # 0-indexed current iteration
    weak_categories: list[CategorySpec]
    teacher: TeacherSpec | None
    training_examples: list[TrainExample]
    lora_path: Path | None
    score_before: dict[str, float]     # category → pass rate before iter
    score_after: dict[str, float]      # category → pass rate after iter
    score_history: list[dict]          # one entry per iter (for telemetry)
    decision: Literal["commit", "retry", "abort", "pending"]

    # explainability
    notes: list[str]                   # ReAct-style reasoning trace, one per node
```

# Storage and registry

- `vertex_training_checkpoint` rows (per ADR-2605070700) record every
  successful iter, even non-committed ones — needed for lineage audit.
- LoRA adapter dirs live under
  `${runpod_handler.training_outputs_dir}/baien-distill-react/iter-<N>/`
  per ADR-2605070700.
- Generated training JSONL is stored alongside the adapter, hashed,
  and the hash is recorded on the checkpoint row.
- Telemetry (per-iter scores, teacher choice, decision) writes to
  `90-docs/baien/distill-loop-<YYMMDD>/history.jsonl`.

# License and Charter Rider implications

The distilled LoRA adapter is a **derivative work** of:
- baien base (Apache 2.0, MIT mix; Microsoft) — permissive
- the **data source** chosen in §3a / §3b — see tables below

### `--source hf` (DEFAULT) — public dataset path

| Dataset | License | Effect on distilled adapter |
|---|---|---|
| `lordx64/reasoning-distill-opus-4-7-max-sft` (Opus 4.7 traces) | **Apache-2.0** | Fully compatible. Charter Rider §2 applies to derived weights for first-party redistribution; no upstream naming clause |
| `aisingapore/Instruction-Following-IFEval` | **CC-BY-4.0** | Attribution required; record dataset id in `DISTILLED_MODEL_PROVENANCE` (commit_node already does this). Compatible with Apache-2.0 + Rider |
| `allenai/tulu-3-sft-mixture` (deferred) | **ODC-BY-1.0** (mixed; some NC subsets) | Subset-by-subset review required before use; **not auto-loaded** by registry. |

### `--source teacher` (FALLBACK) — on-fleet teacher path

| Teacher | Teacher license | Effect on distilled adapter |
|---|---|---|
| llama3.3 / llama3.2 | **Llama 3 Community License** | Distilled adapter MUST follow Llama naming convention ("Llama" in derivative name) + Acceptable Use Policy + 700M-MAU clause review |
| qwen3-* | **Apache 2.0 (Qwen license)** | Compatible with Apache 2.0; Charter Rider §2 still applies for first-party religious-corp distribution |
| gemma3 | **Gemma Terms of Use** | Restrictive — derivative must follow Gemma terms; consult before publishing |

Decisions for this ADR:

1. **Internal experimentation is unrestricted** — derived weights stay
   on-fleet, used only to measure the loop's effectiveness.
2. **Publication requires per-iter legal review.** No autopublish path.
3. **Charter Rider §2 content scan in node 4** ensures generated SFT
   data does not introduce advertising / commercial-purchase / Gore /
   etc. text into baien.
4. **Donation-only substrate compliance**: teachers must run on fleet
   (LAN), not via paid API. This is enforced in `select_teacher`
   constraint table above.

# Risks

| Risk | Mitigation |
|---|---|
| **Teacher bias propagation** — baien inherits teacher's failure modes (Llama hallucinations, Qwen JP idioms, etc.) | Diversify teachers across iters; track per-teacher bench delta |
| **Overfit to bench** — LoRA memorizes microbench patterns | Score gate uses BOTH micro (fast) AND core3 (broader); commit requires both ≥ threshold |
| **Catastrophic forgetting** — LoRA hurts other categories not in target list | Eval gate checks ALL categories; commit fails if any drops > 5 pp |
| **License pollution** — Llama-derived adapter accidentally redistributed | Naming convention enforced + git pre-commit hook check + ADR § license requires explicit review for any `state="committed"` row |
| **ROCm Windows instability** — peft+rocm doesn't work on EVO-X2 | Fallback to CPU training (slower but works); document actual configuration in ADR amendment when verified |
| **Wall-clock per iter too long** (8h+) | `--quick` mode reduces N to 100 + epochs to 1; full mode for overnight |

# Out of scope / future work

- **DPO / RLHF extension**: paired ranking from teacher → DPO. ADR
  amendment when SFT path is validated.
- **Multi-teacher ensemble**: ensemble of teachers per category
  (deferred — needs aggregation rule).
- **Cross-fleet parallel data gen**: distribute teacher inference
  across multiple gemma3:4b nodes via judah's LiteLLM gateway.
  Architecturally straightforward but not in initial design.
- **Continuous loop**: cron-triggered weekly bench + auto-distill +
  publish-with-review-gate. Requires Council Lv6+ approval per
  Religious-Corp Daemon Architecture (ADR-2605192415).
- **Cell catalog promotion**: if the loop becomes constitutional
  infra, add a `BaienDistillCell` to the Pregel cell catalog
  (ADR-2605192415 §4).

# Acceptance criteria (when this ADR transitions `proposed → accepted`)

1. `70-tools/baien-distill/` skeleton exists with the 6 node files,
   state.py, and graph.py (this ADR amendment can land them empty
   with TODOs).
2. End-to-end smoke: at `--quick --max-iter 1` with N=50 examples,
   the loop completes one iteration and writes a checkpoint row +
   telemetry row, even if score does not improve.
3. At least one teacher passes the `select_teacher` constraints from
   §2 with verified throughput.
4. `e7m bench distill` subcommand exists and dispatches the loop.

# References

- ADR-2605092350 baien design (LoRA-on-bf16 recipe)
- ADR-2605070700 vertex_training_checkpoint lineage table
- ADR-2605202345 EVO-X2 GPU pod integration (default execution host)
- ADR-2605192200 Charter Rider v2.0 (license + content prohibitions)
- 90-docs/baien/frontier-bench-snapshot-260523.md (target gaps)
- 70-tools/etzhayyim-cli/bench.go (`e7m bench` entrypoint)
