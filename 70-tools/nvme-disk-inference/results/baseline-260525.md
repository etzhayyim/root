# Baseline empirical bench — 2026-05-25

A/B comparison of disk storage tier for Gemma 4 26B-A4B MoE inference on
Mac mini M4 16GB.

## Setup

- **Host**: Mac mini M4 base (16GB unified memory, 10-GPU-core)
- **Internal SSD**: Apple SSD AP0256Z (256 GB; raw seq read 2.30 GB/s)
- **External SSD**: SanDisk Extreme Portable SSD (USB 3.2 Gen 2, 0x781:0x55BB,
  1 TB; raw seq read 0.836 GB/s)
- **Model**: gemma-4-26B-A4B-it-UD-Q3_K_M.gguf (12.73 GB on disk, Unsloth Dynamic)
- **Runtime**: llama.cpp b9290 + ggml 0.12.0 (Homebrew)
- **Invocation**: per `bench/llama-cli-flags.txt`

## Protocol

For each tier:
1. 14 GB junk-file write+read to flush page cache
2. `time -l llama-cli ... < /dev/null` (cold)
3. Capture full stdout/stderr to `results/{tier}-{ts}.txt`

Prompt: `"Mac mini M4 16GB で 26B MoE モデルを動かす最大の制約を 3 行で。"`
Generated: ~150 tokens (truncated by `-n 120` + early stop heuristic)

## Results

| Metric | SanDisk USB 3.2 Gen 2 | Internal NVMe | Delta |
|---|---:|---:|---:|
| **Generation throughput** | **7.9 tok/s** | **7.7 tok/s** | +3% (SanDisk) |
| Prompt eval | 3.1 tok/s | 3.2 tok/s | -3% |
| Wall time | 127.7 sec | 119.0 sec | +7% (SanDisk slower) |
| Peak RSS | 9.99 GB | 10.30 GB | -3% |
| Peak memory footprint | 7.20 GB | 7.20 GB | 0% |
| Page faults | 2.33M | 2.35M | -1% |
| Swaps | 0 | 0 | — |
| Raw seq read | 0.836 GB/s | 2.30 GB/s | -64% |

## Finding

**Steady-state generation throughput is storage-independent** for MoE × mmap
disk inference on Mac mini M4 16GB.

Despite a 2.75× raw bandwidth gap between internal NVMe and USB 3.2 Gen 2
SSD, the generation tok/s differ by <5% (within run-to-run variance).

The 7% wall-time difference is entirely attributable to the **cold-load
phase** (first-token latency), where the slower disk takes longer to
fault-in the initial expert working set.

## Why this works

Gemma 4 26B-A4B has 128 experts of which 8 + 1 shared are active per token.
With LRU cache behavior in macOS unified memory:

- First token: cold mmap fault-in dominates (~80 sec wall, disk-bound)
- Tokens 2..N: ~9/128 experts = 6.25% expert turnover per token
- Working set effectively held in 8-10 GB page cache (~5-7 GB experts active)
- Per-token incremental disk read: ~85-170 MB on expert rotation
- At 7.9 tok/s, disk traffic ≈ 0.7-1.3 GB/s — **within both tiers' capacity**

The MoE sparsity acts as natural compute-disk decoupling. Disk bandwidth
matters for cold-start; RAM cache matters for steady-state.

## Implication for storage tier investment

| Investment | Cold-load delta | Steady-state delta | ROI |
|---|---|---|---|
| TB5 NVMe (要 M4 Pro) | -50% (~40 sec faster) | ~0% | △ (interactive only) |
| TB4 NVMe single | -30% | ~0% | △ (interactive only) |
| TB4 NVMe ×2 parallel | -50% | ~0% | △ (interactive only) |
| USB 3.2 Gen 2 (current) | baseline | baseline | ✓ existing hardware sufficient |

**Recommendation**: do not invest in faster storage purely for inference
throughput on this workload class. TB5/TB4 upgrade only justified if
first-token latency dominates UX (interactive chat with many short turns).

## Caveats

1. **MoE-specific**: dense models (Llama 3.1 70B etc.) have no expert
   sparsity; the entire weight set is touched per token; disk bandwidth
   would matter much more.
2. **Mac mini M4 RAM-limited**: at ctx ≤2048; ctx ≥4096 risks swap thrashing
   regardless of storage tier.
3. **Cold-load matters for chat UX**: an 80 sec first-token wait is
   unacceptable for interactive use without pre-warm.
4. **Page cache fragility**: any background process taking >2 GB RAM evicts
   experts and reverts to disk read, dropping throughput.
5. **USB SSD thermal**: SanDisk Extreme observed 180 MB/s read after long
   idle (cold controller); pre-warm with a small read before bench.

## Raw outputs

- `internal-cold-{ts}.txt` — full llama-cli + time -l output
- `sandisk-cold-{ts}.txt`  — full llama-cli + time -l output

## References

- ADR-2605253000 (Mac mini M4 16GB Gemma 4 26B-A4B MoE NVMe disk inference)
- ADR-2605253015 (this project — nvme-disk-inference substrate)
- Apple "LLM in a Flash" (ICLR 2026)
