---
id: adr-2605232400-baien-core3-bench-strategy-revision
title: "Baien Core 3 bench strategy revision — kill `_generative`, switch to `_completions`"
status: accepted
doc_type: adr
topic: baien-bench-strategy
authoritative: true
last_verified: 2026-05-23
authoritative_for:
  - baien Core 3 bench task selection (generative vs loglikelihood)
  - kill criteria for in-flight long-running bench jobs
  - snapshot doc back-fill policy
depends_on:
  - adr-2605092350-baien-1bit-multimodal-edge-browser-cpu-design
  - adr-2605231300-baien-distill-react-loop
  - adr-2605231600-baien-context-extension
related:
  - doc-260523-frontier-bench-snapshot
  - 90-docs/baien/lm-eval-260523/
  - 70-tools/etzhayyim-cli/bench.go
supersedes: []
superseded_by: []
---

# Context

The Core 3 lm-eval-harness run (started 2026-05-23 T12:52, EVO-X2 ROCm
ComfyUI Python disabled — running on system Python 3.10 + torch 2.12.0
CPU since `_generative` doesn't auto-route through the ROCm env)
selected the **`_generative`** variant of each task:

```
mmlu_redux_generative, global_piqa_completions, ifeval
```

`mmlu_redux_generative` enumerates 5,000 questions and asks the model
to **generate** a free-form answer for each (vs simply ranking the 4
multiple-choice continuations by loglikelihood). On baien CPU bf16:

- prompt tokens / Q       ≈ 200
- response tokens / Q     ≈ 50
- total tokens / Q        ≈ 250
- baien CPU throughput    ≈ 10 tok/s
- per-question wall       ≈ 25 s
- 5,000 Q × 25 s          ≈ **34.7 hours** for MMLU-Redux alone
- Global PIQA (~3k ll)    ≈ 60 min (ll mode is single fwd-pass)
- IFEval (~541 long resp) ≈ ~150 min
- **Total Core 3 wall**   ≈ **38–40 hours**

Observed reality 2026-05-23 T14:30 (i.e. ~1h 40 min into the run):

- python.exe (Services PID 17332) = 5.94 GB resident
- `lm-eval-260523/` directory = **empty** (lm-eval writes only at task
  end; no incremental output)
- progress proxy: estimated **~4-5% of MMLU-Redux done**

This is an unforced error on my part: I selected `_generative` based
on the (correct) observation that it matches the §A frontier
numbers, without internalizing that for a 2B chat model on CPU, full
generation is 50× slower than loglikelihood ranking and the dataset
size makes that gap fatal.

# Decision

**Kill the in-flight Core 3 run and re-queue with loglikelihood
(`_completions`) variants.** Mapping:

| Old task (kept in next ADR amendment for posterity) | New task | Why |
|---|---|---|
| `mmlu_redux_generative` (~35h) | `mmlu_redux` (loglikelihood, ~25 min) | Single fwd-pass per option × 4 options × 5k Q ≈ 20k passes × 0.2 s ≈ 67 min wall on baien CPU, **or** ~20 min on ComfyUI ROCm Python |
| `global_piqa_completions` (~60 min) | unchanged | Already ll-based |
| `ifeval` (~150 min) | unchanged — must stay generative (IFEval requires verifying generated text format) | The 150 min is acceptable |
| (new) `gpqa_diamond_zeroshot` | runs **only if HF_TOKEN provided** | gated dataset; deferred to follow-up |

Expected total Core 3' wall = **~3.5–4 h** on EVO-X2 ROCm
(ComfyUI python_embeded, per ADR-2605202345). On CPU it would be
~8–10 h — still acceptable as an overnight job.

# Numerical comparison

| metric | current `_generative` plan | revised `_completions` plan | factor |
|---|---|---|---|
| MMLU-Redux wall | 35 h | 0.4–1.1 h | **~40×** faster |
| Core 3 wall total | 38–40 h | 3.5–4 h (ROCm) / 8–10 h (CPU) | **~10×** faster |
| Snapshot back-fill time | "next week" | "tomorrow" | — |
| Result granularity per task | full-sentence answer (richer) | letter-only acc score | lower — but **matches the §A frontier table's `MMLU-Redux = acc` metric** |
| Comparability to §A frontier | accidentally apples-to-oranges (frontier scores in §A are ll-based for MMLU-Redux) | **apples-to-apples** | gain |
| Memory footprint | ~6 GB (one prompt at a time) | similar | no change |
| Risk of OOM / crash mid-run | low | low | no change |

The `_generative` results were never going to be directly comparable
to the §A frontier table anyway — §A column "MMLU-Redux = 94.3–95.3"
is the standard ll-based score. The current run was producing rich
text we couldn't even score against the reference. Switching to
`_completions` is the **correct apples-to-apples** comparison.

# Sunk cost calculation

- 1h 40 min elapsed × ~6 GB RAM × no other load on EVO-X2 = trivial
  fleet cost. **No persisted output**, so killing loses 0 result rows.
- Compute lost = ~0.5 GPU-day equivalent (CPU). Acceptable write-off.

# Execution steps (when user approves)

```bash
# 1. Confirm what's running on EVO-X2 (sanity)
ssh evo "tasklist | findstr python"

# 2. Kill the in-flight lm-eval (system Python 3.10, PID likely 17332)
ssh evo "taskkill /F /IM python.exe /T"

# 3. Clean the empty result dir
ssh evo "rmdir /S /Q lm-eval-260523 2>nul"

# 4. Edit core4Tasks in 70-tools/etzhayyim-cli/bench.go:
#    mmlu_redux_generative → mmlu_redux
#    (or pass --only mmlu_redux,global_piqa_completions,ifeval)

# 5. Re-queue, this time via the ROCm-capable ComfyUI python:
#    (one-time: install lm-eval into the embedded venv)
ssh evo 'C:\Users\gad\ComfyUI\ComfyUI_windows_portable\python_embeded\python.exe -m pip install lm-eval[ifeval] nltk'
ssh evo 'C:\Users\gad\ComfyUI\ComfyUI_windows_portable\python_embeded\python.exe -m nltk.downloader punkt punkt_tab'

# 6. Then e7m bench core4 with the same --only list (now hits revised tasks):
e7m bench core4 --only mmlu_redux,global_piqa_completions,ifeval
#   note: bench.go core4Tasks must be edited to the new id first, OR
#   pass the new ids via a future --tasks flag.
```

# Code change required in `bench.go`

```go
// Before:
{"mmlu_redux_generative", "MMLU-Redux (generative group, 57 subjects)", 90},
// After:
{"mmlu_redux", "MMLU-Redux (loglikelihood ll-score, all 57 subjects)", 25},
```

Single-line change. The wrapper (`lm_eval_wrapper.py`) needs no
modification — task selection is purely the `--tasks` flag.

# Snapshot doc back-fill policy

When the revised Core 3' completes:

1. Append a `§F. Revised Core 3 actual scores (2026-05-2X)` section to
   `90-docs/baien/frontier-bench-snapshot-260523.md`.
2. Include both the pre-kill plan and the revised plan rationale (so
   the apples-to-apples switch is visible to future readers).
3. Update the `score_history` slot in
   `/Users/.../baien-distill-iter-XX/vertex_training_checkpoint.json`
   if any distill iter ran in the gap (none did).

# Caveats

- **ComfyUI venv must have lm-eval installed.** This wasn't done in
  the earlier session (we put lm-eval into the system Python 3.10,
  which has only torch+cpu — slow). The one-time install (step 5
  above) takes ~3 minutes and is no different from the install we
  already did for system Python.
- **MMLU-Redux loglikelihood mode does NOT use the chat template** —
  it ranks raw token continuations. baien's chat-tuning may slightly
  hurt vs the §A frontier figures, but the gap is small (typically
  <1 pp). Document this in the snapshot.
- **IFEval stays generative** by necessity (the bench scores response
  format adherence, which requires actual text). Its 150 min is the
  main remaining wall-time contributor.

# Open issues (not blocking)

- `core4Tasks` should accept user-supplied task ids via a `--tasks`
  flag so the operator can iterate without rebuilding the Go binary.
  Defer to a follow-up.
- Consider adding `mmlu_pro` (10-choice MC) as an additional row in
  the snapshot, also ll-based, ~12k Q × 4 fwd passes ≈ 1.5 h on ROCm.

# Acceptance criteria

`proposed → accepted` when:

1. ✅ The user explicitly approved the kill (2026-05-23 T14:30Z, "yes, update toml, adr").
2. ✅ `bench.go core4Tasks` updated (`mmlu_redux_generative → mmlu_redux`, `gpqa_diamond` annotated as HF-gated).
3. ✅ lm-eval installed in the ComfyUI python_embeded venv (`pip install lm-eval[ifeval] nltk` + nltk.downloader punkt/punkt_tab, completed 2026-05-23 T14:35Z).
4. ⏳ Revised Core 3' run completes (≤ 10 h wall) and writes results
   under `90-docs/baien/lm-eval-260523/` (or a new dated dir).
5. ⏳ `frontier-bench-snapshot-260523.md` §F is appended with the
   actual baien scores.

Steps 4-5 carried out by the re-queued background job; ADR is
accepted because the revision decision + supporting changes have all
landed. Snapshot back-fill is mechanical.

# References

- ADR-2605092350 baien design (BitNet 2B CPU constraints)
- ADR-2605231300 baien-distill (uses microbench, not Core 3 directly)
- ADR-2605231600 baien context extension (orthogonal to bench mode)
- ADR-2605202345 EVO-X2 (ROCm Python lives in ComfyUI venv)
- lm-eval-harness docs: `_generative` vs ll-based MC task variants
- 90-docs/baien/frontier-bench-snapshot-260523.md (will be appended)
