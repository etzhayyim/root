---
id: doc-2605240600-bit-packed-xnor-popcount-kernels
title: "Bit-packed XNOR-popcount matmul kernels — 4-backend implementation + Mac verification"
status: active
doc_type: reference
topic: roso-distill
authoritative: true
authoritative_for:
  - bit-packed XNOR-popcount matmul algorithm reference + correctness oracle
  - per-backend kernel source (MLX Metal / CUDA-HIP / Triton / CPU SIMD AVX-512+NEON)
  - real measured TOPS on Apple Silicon M4 (2 backends end-to-end)
  - documented build blockers for the EVO Windows ComfyUI portable env
last_verified: 2026-05-24
related:
  - adr-2605242000-roso-pattern-frontier-distill
  - 90-docs/baien/quant-shootout-260524/
  - 70-tools/scripts/bench/quant-training-shootout/kernels/
---

# Bit-packed XNOR-popcount matmul — 4 backends

Companion to `90-docs/baien/quant-shootout-260524/` which showed that
PyTorch eager `sign(W) @ sign(X)` runs at the SAME or WORSE TOPS than
bf16 dense matmul on every backend tested (because the dense matmul
kernel still does the full bf16 multiply-accumulate ignoring the
"signed" structure). The escape: replace the dense matmul with a real
bit-packed XNOR-popcount kernel that does 32 effective MACs per
hardware popcount instruction.

This doc documents the algorithm + 4 backend implementations, with
measured numbers on the 2 that built cleanly in this session
(Mac M4: MLX Metal + ARM NEON CPU SIMD).

## Algorithm

Map ±1 values to bits: positive → 1, non-positive → 0. Pack 32 elements
into one uint32. The dot product of two K-length ±1 vectors becomes:

```
match    = popcount( ~(x_bits ^ w_bits) )    # XNOR + popcount
dot_real = 2 * match - K_padded - pad        # pad = K_padded - K
y[i, j]  = alpha * beta * dot_real
```

Padding convention: pad both x and w with +1 bits so padding always
XNOR-matches; subtract `pad` from the raw result to recover the
true K-length dot product.

## Backend matrix

| backend | source file | popcount primitive | host | status | sustained TOPS | speedup vs dense bf16 |
|---|---|---|---|---|---|---|
| **MLX Metal** | `kernels/xnor_metal_mlx.py` | MSL `popcount(uint)` | Mac M4 (Apple GPU) | **built + verified** | **6.31** @ 4096³ | **1.98×** |
| **CPU SIMD NEON** | `kernels/xnor_cpu_simd.cpp` (`#if __ARM_NEON`) | `vcntq_u8` + `vpaddlq_u8/u16` + `vaddvq_u32` | Mac M4 (ARM CPU) | **built + verified** | **1.87** @ 4096³ | **13.70×** |
| **CPU SIMD AVX-512** | same `xnor_cpu_simd.cpp` (`#if __AVX512VPOPCNTDQ__`) | `_mm512_popcnt_epi32` (1 cycle, 16 lanes) | Intel Ice Lake+ / AMD Zen 4+ (EVO Ryzen Zen 5) | source written, **build blocked on EVO** — Windows ComfyUI portable has no `cl.exe` | — | — |
| **CUDA/HIP** | `kernels/xnor_cuda_hip.cu` + `xnor_cuda_hip_setup.py` | `__popc(uint)` → 1 cycle on NVIDIA SM 7.0+ / `V_BCNT_U32_B32` on AMD RDNA/CDNA | NVIDIA Volta+ / AMD ROCm | source written, **build blocked on EVO** — Windows ComfyUI portable has neither MSVC nor `CUDA_HOME` set | — | — |
| **Triton** | `kernels/xnor_triton.py` | SWAR popcount (portable across triton versions; `tl.popcount` autodetected if present) | CUDA (Linux/Windows) / ROCm (Linux) | source written, **install blocked on EVO** — no Triton Windows wheel on PyPI; works on WSL2 / Linux | — | — |
| **PyTorch reference (SWAR)** | `kernels/bit_packed_xnor.py` (top-level, no custom kernel) | SWAR popcount via `>>`, `&`, `+` on int32 tensors | any backend torch supports | built + verified | 0.04 (MPS) / 0.02 (CPU) | < 1× (dispatch overhead) |

## Mac M4 measured results

### Correctness — all 4 sizes, all 2 built backends

`max_abs_diff = 0.000e+00` against `(sign(X) @ sign(W).T) * alpha * beta`
fp32 numpy reference. Sizes tested: (B,K,N) = (8,64,16) / (16,256,128) /
(32,**1023**,256) / (64,4096,512). The K=1023 case validates the
not-multiple-of-32 padding logic.

### Throughput

| shape (B,K,N) | MLX Metal dense bf16 | **MLX Metal XNOR** | ARM NEON dense bf16 | **ARM NEON XNOR** |
|---|---|---|---|---|
| 16,256,128 | 0.003 TFLOPS | 0.007 TOPS (1.88×) | 0.013 TFLOPS | **0.076 TOPS (5.96×)** |
| 64,1024,512 | 0.24 TFLOPS | 0.26 TOPS (1.04×) | 0.116 TFLOPS | **1.391 TOPS (11.95×)** |
| 128,2048,2048 | 1.40 TFLOPS | 2.07 TOPS (1.49×) | 0.131 TFLOPS | **1.586 TOPS (12.11×)** |
| **256,4096,4096** | **3.20 TFLOPS** | **6.31 TOPS (1.98×)** | **0.136 TFLOPS** | **1.867 TOPS (13.70×)** |

### EVO Radeon 8060S (gfx1151) ROCm comparison — 2026-05-24

To validate the Mac M4 results against another GPU class, the same
pure-PyTorch SWAR-popcount XNOR + dense fp/bf/int paths were run on
EVO-X2 (AMD Radeon 8060S Graphics, gfx1151 RDNA 3.5 APU, 60 GB unified,
ROCm 7.2.53 + torch 2.9.1+rocm7.2.1).

**Reliable 4096³ measurements** (small shapes' sub-microsecond timing
collapsed to torch.cuda.synchronize sampling noise on Windows ROCm):

| metric | Mac M4 GPU | **EVO Radeon 8060S** | ratio EVO/Mac |
|---|---|---|---|
| dense fp32 @ 4096³ | 2.60 TFLOPS | 0.89 TFLOPS | 0.34× (slow path) |
| dense bf16 @ 4096³ | 3.23 TFLOPS | **9.30 TFLOPS** | **2.88×** |
| dense fp16 @ 4096³ | 3.27 TFLOPS | **9.54 TFLOPS** | **2.92×** |
| XNOR-popcount pure-PyTorch SWAR | 0.036 TOPS | 0.088 TOPS | 2.44× |
| **XNOR-popcount custom Metal/HIP** | **6.31 TOPS** ✓ | source-only, build blocked | — |
| MLX int8/int4/int2 quant | 2.7 TOPS | quanto crashed (Win+ROCm incompat) | — |
| ANE (Core ML) | 4.13 TFLOPS | N/A (no NN accelerator on consumer Radeon) | — |

**Findings**:

1. **EVO Radeon 8060S has ~2.9× higher raw bf16/fp16 throughput** than
   Apple M4 GPU on this shape (9.3 vs 3.2 TFLOPS). The RDNA 3.5 APU's
   matrix accelerators win at sustained dense matmul.
2. **fp32 path is unusually slow on gfx1151** (0.89 TFLOPS) — torch.matmul
   on ROCm Windows hits an unoptimized fp32 dispatch; the fast paths are
   bf16/fp16 (the tensor-core-equivalent matrix units).
3. **Pure-PyTorch XNOR runs but stays slow** on both backends (Mac MPS 0.036,
   EVO ROCm 0.088 TOPS @ 4096³) — the broadcast XOR + SWAR popcount
   chain in PyTorch eager is dispatch-bound, not compute-bound. The 2.4×
   EVO advantage tracks the dense bf16 advantage (both backends pay the
   same eager overhead per call; EVO's raw matmul is just faster).
4. **Custom HIP kernel remains blocked on EVO** — Windows ComfyUI portable
   has neither MSVC `cl.exe` nor `CUDA_HOME` set, both required by
   `torch.utils.cpp_extension.load()` even for hipcc-only builds.
   Unblock path: install Visual Studio Build Tools (~1.5 GB) + set
   `CUDA_HOME` to any path, OR switch EVO to WSL2 + Linux torch+ROCm.
5. **Asymmetric comparison limitation**: we measured Mac M4's full
   XNOR-Metal speedup (6.31 vs 3.23 dense = 1.95×) but NOT EVO's
   equivalent HIP path. With a working HIP build, the EVO XNOR kernel
   would land at the same ~1.95-2.0× multiple of dense = **~18-19 TOPS
   sustained** (extrapolated). That's the prize waiting for the build
   environment to be fixed.
6. **EVO quanto int8/4/2 path crashed** — `optimum.quanto` on Windows
   ROCm 7.2 has a `linear() argument 'weight' must be Tensor, not
   NoneType` bug after `freeze()`. Same quanto API works on Mac CPU.
   Likely a Windows-specific quanto cache / monkey-patch issue;
   workaround = use quanto's bf16-fallback or upgrade quanto to a
   newer release.
7. **ANE comparison is asymmetric** — Apple Silicon ships a dedicated
   NN accelerator (4.13 TFLOPS dense fp16 measured); AMD consumer
   Radeon does NOT (no analog of ANE on RDNA 3.5). EVO's GPU matrix
   accelerators provide the equivalent throughput (9.30 TFLOPS bf16 =
   2.25× faster than ANE on dense), but no separate silicon block.

### Core ML + Apple Neural Engine (ANE) dense fp16 matmul

Implemented in `kernels/coreml_ane_bench.py`. Built via the dedicated
`/tmp/coreml-venv` (Python 3.12 + coremltools 9.0, since coremltools
has no Python 3.14 wheel as of 2026-05-24).

| shape (B,K,N) | CPU_ONLY | CPU_AND_GPU | **CPU_AND_NE** | ALL (compiler choice) |
|---|---|---|---|---|
| 16, 256, 128 | 0.030 | 0.030 | 0.033 | 0.023 |
| 64, 1024, 512 | 1.021 | 0.100 | 0.403 | 0.378 |
| 128, 2048, 2048 | 2.639 | 0.694 | **2.872** | 2.850 |
| **256, 4096, 4096** | 2.614 | 1.613 | **4.091** | **4.133** |

All values in TFLOPS (Core ML always casts to fp16 internally for ANE).

Findings:

- **ANE is the fastest dense fp16 path on M4** at 4.13 TFLOPS @ 4096³
  (~38 TOPS vendor-claimed peak; 11% utilization sustained on this
  arbitrary GEMM shape — the ANE prefers conv-shaped ops).
- **Core ML CPU_AND_GPU is SURPRISINGLY SLOW** (1.61 TFLOPS) — Core ML's
  Metal dispatch path has more overhead than MLX direct (3.23 TFLOPS).
  When VRAM-bound or for arbitrary GEMM, prefer direct MLX over Core ML
  GPU. The win-condition for Core ML GPU is when the model is a real
  trained network with multiple ops the Core ML compiler can fuse.
- **ANE is NOT user-programmable** — no XNOR-popcount kernel possible.
  The 4.13 TFLOPS represents the **upper bound on dense fp16 on this
  silicon**. The bit-packed AND/XNOR-popcount kernels at 6.31-6.82 TOPS
  **beat the ANE by ~50-60%** on this hardware.
- **ALL ≈ CPU_AND_NE** (4.13 vs 4.09 TFLOPS at 4096³) — the Core ML
  compiler chose to dispatch the matmul to the ANE for this shape.
  For smaller shapes (64,1024,512), it actually under-performs
  CPU_ONLY (0.378 vs 1.021 TFLOPS) because the small-matmul ANE
  prefers CPU dispatch.

### 5 additional low-bit techniques on Apple M4 Metal

Implemented in `kernels/xnor_techniques_metal.py` — same shapes, same MLX
runtime. AND-popcount kernel verified `max_abs_diff = 0.000e+00` against
the dense unsigned reference across all 4 sizes.

| shape (B,K,N) | AND-popcount | bit-slice W2×X1 | bit-slice W4×X1 | bit-serial 2×2 | LUT 8×8 |
|---|---|---|---|---|---|
| 16, 256, 128 | 0.006 | 0.002 | 0.002 | 0.002 | 0.001 |
| 64, 1024, 512 | 0.381 | 0.046 | 0.038 | 0.052 | 0.037 |
| 128, 2048, 2048 | 2.013 | 0.123 | 0.071 | 0.109 | 0.097 |
| **256, 4096, 4096** | **6.817** | 0.245 | 0.141 | 0.217 | 0.117 |

All values in TOPS. Key takeaways:

- **AND-popcount BEATS XNOR-popcount** at 4096³ (6.817 vs 6.31 TOPS,
  +8%) because the kernel has one fewer op (no `~` after `^`). Same
  algorithm-class hardware ceiling. Choice between XNOR (±1 mapping)
  and AND ({0,1} mapping) is a numerical / training-stability question,
  not a perf question.
- **Bit-slice (W=2bit, X=1bit)** at 0.245 TOPS = 26× slower than XNOR
  because the current Python-level implementation calls 2 separate
  Metal kernels per matmul + Python sum, paying kernel-launch overhead
  twice + tensor allocation. A fused kernel would close most of the gap.
- **Bit-serial 2×2** at 0.217 TOPS = same Python-loop issue, 4 kernel
  launches (2×2 bit planes).
- **LUT 8×8** at 0.117 TOPS = bottlenecked by 128 KB table fitting only
  in L2 (not L1) — each thread does K=4096 byte lookups, each L2 hit
  ~10× slower than register-resident popcount. The LUT path's strength
  is when K is small (sub-512) AND the table can be locked into L1.
- **The bit-slice / bit-serial / LUT paths are the "Phase 2" optimization
  target** — a single fused Metal kernel doing all bit-plane multiplies
  in one launch should hit ~3-5 TOPS, closing the gap with AND-popcount.

### Dense quant matmul on Apple M4 Metal (MLX, for comparison)

| shape (B,K,N) | fp32 | bf16 | fp16 | int8 (g=64) | int4 (g=64) | int2 (g=64) | **XNOR-popcount** |
|---|---|---|---|---|---|---|---|
| 16, 256, 128 | 0.003 | 0.004 | 0.003 | 0.003 | 0.005 | 0.005 | 0.007 |
| 64, 1024, 512 | 0.195 | 0.258 | 0.218 | 0.246 | 0.202 | 0.236 | **0.26** |
| 128, 2048, 2048 | 1.009 | 1.094 | 0.997 | 1.003 | 1.023 | 0.928 | **2.07** |
| **256, 4096, 4096** | 2.598 | 3.234 | 3.265 | 2.690 | 2.696 | 2.593 | **6.31** |

Units: TFLOPS for fp/bf rows, TOPS for int rows and XNOR-popcount.
All measured via MLX 0.31.1 on Apple M4 GPU. Quantized rows use
`mlx.quantize` + `mlx.quantized_matmul` with `group_size=64`.

**fp8 / fp4 status**: Apple M4 silicon has **no native fp8 / fp4 ALU**.
MLX 0.31 does not expose fp8 / fp4 dtypes. These formats require
NVIDIA H100/B200 (FP8 Tensor Cores, FP4 in B200) or AMD MI300X
(FP8 via matrix cores) — no Apple Silicon variant currently ships
them. Listed here as "—" / unsupported.

### Key observations

1. **MLX quantized_matmul int8/int4/int2 all hit the same ~2.7 TOPS** at
   4096³ — equal to bf16/fp16 dense throughput. This is because Apple
   M4 GPU has **no native int matmul accelerator**; the MLX kernel
   dequantizes int → fp16 on-the-fly and runs the matmul on the
   FP16 ALUs. Same TOPS, lower VRAM (real benefit is memory, not compute).
2. **Bit-packed XNOR-popcount Metal beats every dense path** at 4096³:
   6.31 TOPS = 1.93× MLX int8 = 1.95× bf16 dense = 2.43× fp32 dense.
   This is the real silicon-level speedup that the 1-bit family
   unlocks on Apple GPU: the popcount(uint) MSL builtin is 1 cycle
   per 32 bits = 32× theoretical density vs FP16 multiply.
3. **NEON CPU is the bigger relative winner (13.7×)** because dense bf16
   matmul on Apple Silicon CPU is *not* particularly fast (no native
   bf16 matmul unit on the M4 CPU — falls back to NEON fmla on f16).
   The XNOR kernel benefits from a dedicated 1-cycle byte popcount.
4. **Practical 1.93×-13.7× ≪ theoretical 16-32×**: PyTorch eager dispatch
   + tensor allocation overhead caps the practical speedup. To approach
   the theoretical multiplier, the kernel must fuse with surrounding
   operations (RMSNorm + activation binarization), eliminating
   round-trips to memory between layers. That's a Phase 2 follow-up.
5. **Bottom line for roso (FULL 16-row ranking on Apple M4 @ 4096³)**:

   | rank | kernel | TOPS / TFLOPS | vs bf16 dense (MLX) | dispatch |
   |---|---|---|---|---|
   | **1** | **AND-popcount Metal** (this work) | **6.817** | **2.11×** | MLX `popcount(uint)` |
   | **2** | **XNOR-popcount Metal** (this work) | **6.31** | **1.95×** | MLX `popcount(~(a^b))` |
   | **3** | **Core ML ALL (auto-chooses ANE)** | **4.133** | **1.28×** | ANE fp16 |
   | **4** | **Core ML CPU_AND_NE** (ANE-allowed) | **4.091** | **1.27×** | ANE fp16 |
   | 5 | fp16 dense matmul (MLX) | 3.27 | 1.01× | M4 GPU FP16 ALU |
   | 6 | bf16 dense matmul (MLX baseline) | 3.23 | 1.00× | M4 GPU BF16 ALU |
   | 7 | int4 quantized matmul (MLX, g=64) | 2.70 | 0.83× | dequant-on-fly → FP16 ALU |
   | 8 | int8 quantized matmul (MLX, g=64) | 2.69 | 0.83× | dequant-on-fly → FP16 ALU |
   | 9 | Core ML CPU_ONLY (fp16) | 2.61 | 0.81× | ARM CPU FP16 |
   | 10 | fp32 dense matmul (MLX) | 2.60 | 0.80× | M4 GPU FP32 ALU |
   | 11 | int2 quantized matmul (MLX, g=64) | 2.59 | 0.80× | dequant-on-fly → FP16 ALU |
   | 12 | XNOR-popcount NEON CPU (this work) | 1.87 | (13.7× vs bf16 CPU) | ARM NEON `vcntq_u8` |
   | 13 | Core ML CPU_AND_GPU | 1.61 | 0.50× | Core ML metal dispatch (overhead-heavy) |
   | 14 | bit-slice W=2bit×X=1bit Metal | 0.245 | 0.076× | un-fused (2 kernel launches) |
   | 15 | bit-serial 2×2 Metal | 0.217 | 0.067× | un-fused (4 kernel launches) |
   | 16 | bit-slice W=4bit×X=1bit Metal | 0.141 | 0.044× | un-fused (4 kernel launches) |
   | 17 | LUT 8×8 Metal | 0.117 | 0.036× | L2-cache-bound (128 KB table) |
   | — | **fp8** | unsupported | — | Apple M4 silicon に fp8 ALU 無し |
   | — | **fp4** | unsupported | — | Apple M4 silicon に fp4 ALU 無し |

   **Key takeaways**:
   - The 1-bit family (AND/XNOR-popcount) **beats the ANE by ~50-60%**.
     The ANE is the fastest dense fp16 path but cannot run custom 1-bit
     kernels (not user-programmable).
   - **ANE is the silver medal** at 4.09-4.13 TFLOPS @ 4096³ — useful
     for stock dense fp16 deployment via Core ML, but **not extensible**.
   - **The ONLY way to exceed ANE throughput on M4 is to write custom
     Metal kernels** with `popcount(uint)` — exactly what this work does.
   - Multi-bit / LUT paths currently lose due to un-fused kernel dispatch
     overhead — Phase 2 work fuses them into single Metal launches.

## EVO blocked items — what's needed to unblock

1. **CUDA/HIP** — install Visual Studio Build Tools (~1.5 GB) on EVO
   Windows so `cl.exe` is on PATH, AND set `CUDA_HOME` to a CUDA install
   (even a stub one) so PyTorch's `cpp_extension.load()` accepts the
   build. Then `xnor_cuda_hip.cu` will compile via hipify + hipcc.
2. **Triton** — switch to WSL2 + Linux Python wheel
   (`pip install triton`), then `xnor_triton.py` runs directly. There
   is no native Windows Triton wheel on PyPI as of 2026-05-24.
3. **CPU SIMD AVX-512** — same as #1, needs `cl.exe`. The kernel source
   has `#if defined(__AVX512F__) && defined(__AVX512VPOPCNTDQ__)`
   compile-time gates and will auto-select on AMD Ryzen Zen 4+ /
   Intel Ice Lake+.

All 3 sources are algorithmically identical to the Mac-verified versions
(same `2*popcount(~(x^w)) - K_padded - pad` formula), so passing
correctness on EVO is expected once the build environment is configured.

## Files

```
70-tools/scripts/bench/quant-training-shootout/
├── bit_packed_xnor.py            # pure-PyTorch SWAR-popcount reference (portable)
└── kernels/
    ├── xnor_metal_mlx.py         # ★ MLX Metal kernel (Mac, built + verified)
    ├── xnor_cpu_simd.cpp         # ★ AVX-512 + NEON (NEON built+verified on Mac)
    ├── xnor_cpu_simd_setup.py    # cpp_extension loader + bench
    ├── xnor_cuda_hip.cu          # CUDA/HIP kernel (source ready, EVO build blocked)
    ├── xnor_cuda_hip_setup.py    # cpp_extension loader + bench
    └── xnor_triton.py            # Triton kernel (source ready, no Win wheel)
```

Raw measurements:
- `xnor_metal_mlx_results.json` — MLX Metal XNOR-popcount full results
- `xnor_cpu_simd_results.json` — ARM NEON XNOR-popcount (`backend: arm_neon_vcntq`)
- `dense_quant_metal_results.json` — Mac M4 Metal dense matmul shootout (fp32/bf16/fp16/int8/int4/int2)
- `pytorch-mps-reference.json` — pure-PyTorch SWAR-popcount baseline on MPS
- `pytorch-cpu-reference.json` — pure-PyTorch SWAR-popcount baseline on CPU

## Reproducing on Mac

```bash
# MLX Metal (Apple GPU)
KMP_DUPLICATE_LIB_OK=TRUE python3 \
  70-tools/scripts/bench/quant-training-shootout/kernels/xnor_metal_mlx.py

# ARM NEON CPU SIMD (auto-builds via clang)
python3 \
  70-tools/scripts/bench/quant-training-shootout/kernels/xnor_cpu_simd_setup.py
```

Both complete in <30 seconds end-to-end (build + bench) on Mac M4.
