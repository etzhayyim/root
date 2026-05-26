# langgraph-coding bench

ADR-2605250400 §1.5 で要求された **LangGraph 専用 exec-graded bench**。
gemma-coder-distill loop の `evaluate.py` が iter 前後で delta を読み、改善が
ない iter は `commit_node` で reject されるための gating 信号。

## Design

- **50 prompts** (`prompts.jsonl`) — LangGraph API surface 全体を網羅:
  - StateGraph 定義 (TypedDict / Pydantic state)
  - Annotated reducer (operator.add / custom)
  - node 関数 (sync / async)
  - conditional edges / `add_conditional_edges`
  - `interrupt()` + checkpointer
  - `Send` fan-out
  - subgraph composition
  - tool node (LangChain tool 互換)
  - error handling / retry policy
  - streaming (astream_events v2)

- **Exec-graded** — モデル生成コードを subprocess で実行し、固定入力に対する
  固定出力 assertion で pass/fail。LLM-as-judge は使わない (determinism)。

- **JSON 出力** — lm-eval-harness 互換形式で `90-docs/baien/results-langgraph-NN.jsonl`
  に append。`baien_distill.adapters.bench_reader` がそのまま読める。

## Run

```bash
# pre-distill baseline
python 70-tools/scripts/bench/langgraph-coding/run.py \
  --model http://192.168.1.17:4000 \
  --model-id gemma4:e4b \
  --out 90-docs/baien/results-langgraph-baseline.jsonl

# post-distill check
python 70-tools/scripts/bench/langgraph-coding/run.py \
  --model file:///path/to/merged \
  --model-id gemma4-coder:e4b-iter01 \
  --out 90-docs/baien/results-langgraph-iter01.jsonl

# delta
python 70-tools/scripts/bench/langgraph-coding/diff.py \
  --baseline 90-docs/baien/results-langgraph-baseline.jsonl \
  --new      90-docs/baien/results-langgraph-iter01.jsonl
```

## Acceptance for distill commit (ADR-2605250400 §1.5)

- iter-00 (smoke): delta ≥ 0 pp (no regression)
- iter-01+ (real): delta ≥ +3 pp on overall pass-rate

## Layout

```
70-tools/scripts/bench/langgraph-coding/
├── README.md       (this file)
├── prompts.jsonl   (50-prompt SoT, to populate)
├── graders/        (per-prompt exec graders, indexed by prompt id)
├── run.py          (entrypoint: serial generate + grade)
└── diff.py         (delta calculator)
```

## Status

Scaffold only. `prompts.jsonl` + `graders/` are the next concrete work
(ADR §3 Step 2). Until populated, distill loop cannot reliably gate on
LangGraph improvement.
