---
id: doc-baien-upstream-issue-microsoft-bitnet-arm64-i2s
title: "Upstream issue draft — bitnet.cpp i2_s on Apple Silicon arm64 produces incoherent output"
status: active
doc_type: how-to
topic: edge-multimodal-model-1bit
authoritative: false
last_verified: 2026-05-10
related:
  - adr-2605092350-baien-1bit-multimodal-edge-browser-cpu-design
---

# What this is

Paste-ready GitHub issue body for `microsoft/BitNet`. We bisected an
Apple-Silicon-specific bug in the `i2_s` decode path and have a
minimal repro the upstream maintainers can run. File when ready at:

> https://github.com/microsoft/BitNet/issues/new

# Title

```
i2_s on Apple Silicon (arm64) generates fluent-but-incoherent output;
linux/amd64 same model is fine
```

# Body

```markdown
## Summary

`bitnet.cpp` builds and runs at ~30 tok/s on Apple M1 Max with the
prebuilt `microsoft/BitNet-b1.58-2B-4T-gguf/ggml-model-i2_s.gguf`,
but the **output is fluent English tokens with no semantic
coherence**. The same GGUF on linux/amd64 (Skylake) produces correct
text at ~23.56 tok/s. The bf16 master loaded through `transformers`
on the same Apple Silicon host produces correct text. Therefore the
defect is localized to the **arm64 `i2_s` decode kernel**, not the
model and not the tokenizer.

## Repro

### Apple M1 Max (broken)

Host: Apple M1 Max, 32 GiB, macOS 26.4, Apple clang 21.

```bash
git clone https://github.com/microsoft/BitNet.git
cd BitNet
git submodule update --init --depth 1 --recursive
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt huggingface_hub
huggingface-cli download microsoft/BitNet-b1.58-2B-4T-gguf \
    --include "ggml-model-i2_s.gguf" \
    --local-dir models/BitNet-b1.58-2B-4T
python setup_env.py -md models/BitNet-b1.58-2B-4T -q i2_s
python run_inference.py \
    -m models/BitNet-b1.58-2B-4T/ggml-model-i2_s.gguf \
    -p "The capital of France is" -n 32 -t 4 -temp 0.0
```

Observed completion (greedy, temp=0):

```
"The capital of France is Scotia delivered qualified expressed ding
realistic two-if boardmotheraction c bear coming runaul..."
```

`system_info` reports `NEON = 0`, `MATMUL_INT8 = 0` — these flags are
display fields in this fork's llama.cpp; the actual cmake arguments
(`-target-feature +neon`, `-D__ARM_FEATURE_DOTPROD`) are passed.
Speed is ~30 tok/s, so a kernel is running — it is just producing
wrong activations.

### linux/amd64 Skylake (works)

Same GGUF, Ubuntu 22.04 + clang 14, in a Kubernetes Job. The
`setup_env.py` flow needs three workarounds (also useful as
reproducers of separate upstream issues), all isolated to file
`src/ggml-bitnet-mad.cpp`:

1. The `(int8_t *)vy` and `(uint8_t *)vx` casts on the lines
   declaring `y` and `x` drop `const`. `clang>=14` and `gcc>=11`
   reject the subsequent `int8_t * y_col = y + col * by;`. Rewrite
   each as `int8_t * y = const_cast<int8_t*>(reinterpret_cast<const int8_t*>(vy));`.
2. `setup_env.py` invokes `utils/convert-hf-to-gguf-bitnet.py`, which
   crashes on `transformers >= 4.57` (`tokenizer_config` mismatch).
   Pull `ggml-model-i2_s.gguf` directly from
   `microsoft/BitNet-b1.58-2B-4T-gguf` instead.
3. Ubuntu 24.04 (`clang 18`) rejects `ggml-bitnet-mad.cpp` even after
   the const-cast fix; Ubuntu 22.04 (`clang 14`) accepts it.

After patching, the same `run_inference.py` invocation produces:

```
"The capital of France is Paris. Paris is a city that is known for
its rich history, culture, and architecture. It is also a major
center for art, fashion, and cuisine"
```

Speed: load 0.62 s, prompt eval 24.78 tok/s, generation 23.56 tok/s.

### bf16 reference on the same M1 Max (works)

Loading the unquantized bf16 master through HuggingFace `transformers`
on the same host (CPU fp32, `torch._dynamo.config.disable = True`,
`device_map={"": "cpu"}`):

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
torch._dynamo.config.disable = True
m = AutoModelForCausalLM.from_pretrained(
    "microsoft/BitNet-b1.58-2B-4T-bf16",
    dtype=torch.float32, device_map={"":"cpu"})
tok = AutoTokenizer.from_pretrained("microsoft/BitNet-b1.58-2B-4T-bf16")
ids = tok("The capital of France is", return_tensors="pt").input_ids
print(tok.decode(m.generate(ids, max_new_tokens=16, do_sample=False)[0]))
```

Output: `"The capital of France is Paris. Paris is a city in the
north of France, and it is the"`.

So on the same physical host, `bf16 → transformers fp32 CPU` is
correct, `i2_s → bitnet.cpp arm64 stock` is wrong. The model is fine.

## Bisect summary

| Host | Path | Output | Speed |
|---|---|---|---|
| Apple M1 Max | bitnet.cpp i2_s arm64 stock | incoherent | 30 tok/s |
| Apple M1 Max | bf16 via transformers fp32 CPU | coherent | 0.20 tok/s |
| linux/amd64 Skylake | bitnet.cpp i2_s tl2 (after const-cast patch) | coherent | 23.56 tok/s |

## Side note: TL1 build path

We also tried `cmake -DBITNET_ARM_TL1=ON`. The codegen step
(`utils/codegen_tl1.py --model bitnet_b1_58-3B`) emits a
`src/ggml-bitnet-lut.cpp` so large that Apple `clang 21` does not
finish compiling it within 30 minutes (no error, no progress; we
killed it). We did not exercise the TL1 runtime path because of this.

## Asks

- Confirm the arm64 i2_s path is expected to reproduce on Apple
  Silicon, or document the supported arm64 hosts.
- If TL1 is the only intended fast+correct arm64 path: ship a
  smaller / pre-baked LUT for the 2B-4T model, or document a clang
  configuration that finishes the LUT compile in reasonable time.
- Accept the const-cast and `clang 18+` patches in
  `src/ggml-bitnet-mad.cpp` regardless — these unblock all modern
  Linux toolchains and are independent of the arm64 correctness bug.

Happy to send a PR for the const-cast + Ubuntu 24.04 fixes.
```
