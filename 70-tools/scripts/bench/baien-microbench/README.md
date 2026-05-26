# baien-microbench

Minimal 15-prompt verifiable bench for **baien** (BitNet b1.58 2B-4T,
ADR-2605092350). Each prompt has a rule-based scorer so a single
numeric pass-rate per category is produced — no judge model required.

Not a substitute for full IFEval / MMLU / GPQA runs. Purpose is a
fast smoke + floor signal during baien iteration.

## Run

On the box where baien is loadable (today: EVO-X2 via gad@192.168.1.22
per ADR-2605202345):

```bash
python -m pip install --index-url https://download.pytorch.org/whl/cpu torch
python -m pip install transformers accelerate huggingface_hub

# greedy, do_sample=False
python microbench.py \
  --model microsoft/bitnet-b1.58-2B-4T-bf16 \
  --out results.jsonl
```

CPU bf16 takes ~5 min wall on Ryzen AI Max+ 395; pure llama-arch
models on the same host would be faster but lack the BitNet
architecture support in stock ollama (see snapshot doc for the i2_s
path discussion).

## Categories

| Category | n | scoring |
|---|---|---|
| IFEval-like | 5 | format predicate (5-line, 3-line haiku, all-upper, JSON keys, 10–20 word) |
| MMLU MC | 5 | exact single-letter pick (A/B/C/D) |
| Reasoning | 1 | regex on `0.05` / `5 cents` for the bat-and-ball CRT |
| Multilingual | 2 | substring match (`tokyo`/`東京`, `thank`/`thanks`) |
| General | 2 | substring match (`H2O`/`H₂O`, `7`) |

Scorers are intentionally strict on format. Compare the raw `response`
field in the JSONL to distinguish a real model miss from a
format-strictness false-negative.

## Output format

JSONL, one row per prompt:

```json
{
  "ts": "2026-05-23T03:14:30+00:00",
  "model": "microsoft/bitnet-b1.58-2B-4T-bf16",
  "id": "ifeval_5caps",
  "category": "IFEval",
  "ok": false,
  "reason": "want 5 lines, got 1",
  "elapsed_sec": 19.33,
  "response": "Berlin, Brussels, Copenhagen, Dublin, Edinburgh"
}
```

## Latest snapshot

See `90-docs/baien/frontier-bench-snapshot-260523.md` for the 2026-05-23
result (8/15 strict, 73.3% lenient) and the §A frontier-model
positioning table.
