# murakumo-8bit

Pure `int8` / fixed-point training sandbox for Murakumo.

This is not a production LLM trainer. It is an experiment bed to answer a narrower question:

- how far can we push `int8`-only payloads
- with integer-only scale metadata
- while logging saturation, dead gradients, and quantization loss

Current scope:

- toy linear regression trainer
- pure integer forward/backward/update path
- optimizer comparison: `adam`, `adam-v16`, `adam-v16-soft`, `momentum-sgd`, `nesterov-sgd`, `signsgd`, `qsgd`
- integer scale metadata (`numerator`, `shift`)
- Arrow IPC checkpoint export

Run:

```bash
cargo run -- train-toy --steps 200 --optimizer momentum-sgd --out /tmp/murakumo-8bit-toy.arrow
```

Recurrent toy:

```bash
cargo run -- train-recurrent --steps 64 --input-dim 6 --hidden-dim 4 --seq-len 6 --optimizer signsgd-ef --out /tmp/murakumo-8bit-recurrent.arrow
```

To force a different recurrent state gradient policy:

```bash
cargo run -- train-recurrent --steps 64 --input-dim 6 --hidden-dim 4 --seq-len 6 --scale-mode max --state-scale-mode p90 --optimizer adam --out /tmp/murakumo-8bit-recurrent.arrow
```

Inspect:

```bash
cargo run -- inspect --input /tmp/murakumo-8bit-toy.arrow
```

Sweep:

```bash
cargo run -- sweep --steps 64 --input-dim 8 --output-dim 4 --batch-size 32 --out /tmp/murakumo-8bit-sweep.json
```

Recurrent sweep:

```bash
cargo run -- sweep-recurrent --steps 32 --input-dim 6 --hidden-dim 4 --seq-len 6 --batch-size 16 --out /tmp/murakumo-8bit-recurrent-sweep.json
```

Benchmark:

```bash
cargo run -- bench --steps 64 --input-dim 8 --output-dim 4 --batch-size 32 --block-size 8 --warmup 1 --repeat 5
```

Recurrent benchmark:

```bash
cargo run -- bench-recurrent --steps 32 --input-dim 6 --hidden-dim 4 --seq-len 6 --batch-size 16 --block-size 8 --warmup 1 --repeat 5
```

Mamba2-style simplified full forward, CPU only:

```bash
cargo run -- bench-mamba2-full-forward --dim 16 --state-dim 4 --expand 2 --seq-len 16 --batch-size 8 --block-size 8 --warmup 1 --repeat 5
```

Mamba2-style simplified full forward, GPU only (`wgpu`/Metal):

```bash
cargo run -- bench-mamba2-full-forward-wgpu --dim 16 --state-dim 4 --expand 2 --seq-len 16 --batch-size 8 --block-size 8 --warmup 1 --repeat 5
```

Mamba2-style simplified full forward, `fp16` GPU-only attempt:

```bash
cargo run -- bench-mamba2-full-forward-fp16-wgpu --dim 16 --state-dim 4 --expand 2 --seq-len 16 --batch-size 8 --block-size 8 --warmup 1 --repeat 5
```

Current limitation:

- on the current `wgpu`/`Naga` stack, the WGSL `enable f16;` path is rejected before execution, so this command currently exits with an explicit capability error instead of a benchmark result

Mamba2-style simplified train step, GPU-only path:

```bash
cargo run -- bench-mamba2-outproj-train-wgpu --dim 16 --state-dim 4 --expand 2 --seq-len 16 --batch-size 8 --block-size 8 --lr-numerator 3 --warmup 1 --repeat 5
```

Path semantics:

- `mamba2-full-forward-cpu-only`: CPU reference only
- `mamba2-full-forward-gpu-only`: forward entirely on `wgpu`
- `mamba2-full-forward-fp16-gpu-only`: intended `fp16` GPU forward path, currently blocked by `wgpu`/`Naga` WGSL `f16` support
- `mamba2-outproj-train-gpu-only`: GPU forward + GPU residual + GPU core grad/update (`out_proj` + `in_proj`)

The sweep report now includes:

- full per-run rows across `optimizer x block_size x rounding x scale_mode x lr_numerator`
- `best_overall`
- `best_by_optimizer`
- short `findings` strings summarizing the current toy result

Current findings:

- pure `int8` `Adam` is bottlenecked by `v`; dedicated `grad_sq_scale`, `pow2` blockwise quantization, and `isqrt(v)` denominator help less than expected
- `adam-v16` keeps `v` alive, but the plain `isqrt(v)` denominator over-suppresses updates; `adam-v16-soft` shifts that denominator down and recovers meaningful update mass
- `Momentum SGD` is the next practical baseline because it keeps only one extra state tensor and preserves more update mass than `Adam` in this toy setup
- `SignSGD` is the lowest-information baseline; it is useful as a Shannon floor for direction-only updates, not as the expected quality winner
- `Nesterov SGD` and `QSGD` are implemented in the same toy harness for side-by-side comparison under the same fixed-point constraints
- `SignSGD-EF` is currently the strongest pure `int8` toy optimizer in the sweep because the error buffer preserves update mass that plain `SignSGD` loses
- after sweeping denominator softening, the best short linear `adam-v16-soft` setting is `denom_shift=3`, improving on `adam-v16` from `loss=111516, weight_ratio=0.012` to `loss=98927, weight_ratio=0.574` while keeping `v_ratio=0.945`
- after sweeping denominator softening, the best short recurrent `adam-v16-soft` setting is `denom_shift=2`, improving on `adam-v16` from `loss=6629, weight_ratio=0.346` to `loss=6228, weight_ratio=0.729` while preserving `v_ratio=0.342`
- the recurrent toy still ranks `SignSGD-EF` best overall in this tiny setup, but denominator softening makes the `AdamV16` line materially more viable than the earlier dead-update regime
- current recurrent sweeps also show that changing only the recurrent `state_scale_mode` (`max`, `p75`, `p90`) does not materially move the result in this tiny setup, so the main bottleneck is still optimizer/update quantization rather than state-gradient scaling alone
