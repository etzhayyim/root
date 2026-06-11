---
id: adr-2605242630-baien-federated-r1-webgpu-backward-poc
title: "Baien federated R1 — single-device WebGPU LoRA backward-pass PoC"
status: accepted
doc_type: adr
topic: baien-federated-r1
authoritative: true
last_verified: 2026-05-24
status_note: "R1 ADR + R1a framework both landed (PRs #274 + #276). R1a delivers OPFS Adam-state + device-class detection + shard load/CID verify + Charter Rider on-device scanner + WGSL kernel sources (forward / backward / Adam) — every piece except the WebGPU autograd dispatch itself. R1b (WebGPU dispatch via transformers.js layer-replacement OR tfjs-webgpu autograd bridge + per-device run-log capture for the 3-consecutive-runs success criterion) is the remaining work item, scoped for a dedicated agent + real-device validation."
authoritative_for:
  - R1 device matrix (which devices count as "passing" before moving to R2)
  - WebGPU numerics fallback rules (fp32 grad accumulation gate)
  - OPFS Adam-state on-disk format (so a backgrounded PWA can resume)
  - R1 eval microbench prompt set (the 16 examples)
  - R1 success criteria (three consecutive lossAfter < lossBefore on same shard)
  - R1 out-of-scope (no aggregator, no lexicon publish, no multi-device)
depends_on:
  - adr-2605242600-baien-federated-train-via-ameno-webgpu
  - adr-2605241900-baien-edge-target-invariant
  - adr-2605231300-baien-distill-react-loop
  - adr-2605231525-no-server-key-religious-corp-architecture
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
related:
  - 20-actors/ameno/src/train.ts
  - 70-tools/baien-distill/src/baien_distill/nodes/federated_aggregate.py
supersedes: []
superseded_by: []
---

# Context

R0 (ADR-2605242600) landed the scaffold for federated baien post-train
— 5-layer architecture, lexicon, ameno stubs, Murakumo cell, dry-run
aggregator planner. Every R0 artifact is **throw-on-use or
RuntimeError-on-import**; no real training happens yet.

R1 turns the L1 WebGPU LoRA-only autograd kernel + L2 ameno PWA loop
into a real implementation that can run on **one device**, on a
**16-example shard**, and produce a Δ that empirically improves the
on-device microbench loss. No aggregator. No lexicon publish. No
multi-device coordination.

The reason R1 needs its own ADR (rather than being a routine
implementation task under R0) is that **WebGPU backward-pass numerics
on iOS Safari and Adreno-class Android is not a well-trod path**.
Most published WebGPU training demos use desktop M-series or RTX
hardware where fp16 reductions behave well. baien's constitutional
edge-target invariant (ADR-2605241900) requires iPhone 12 and Android
4 GB to be first-class — we have to characterise the numerics
fallback before we let real contributors run rounds.

# Scope

In scope:

- Device matrix (what counts as an R1 pass).
- Numerics fallback rules (when to drop to fp32 grad accumulation, what
  per-block activation-checkpointing schedule).
- OPFS Adam-state on-disk format (resumable across a PWA kill).
- The 16-example microbench shard (committed to git for reproducibility).
- R1 success criteria (three consecutive `lossAfter < lossBefore` on the
  same shard, on each device class).
- R1 implementation tasks (replacing the throw-on-use stubs in
  `ameno/src/train.ts`).
- Failure modes + abort conditions (thermal, OOM, fp16 overflow).

Out of scope (lands in R2..R4 under their own ADRs):

- Murakumo aggregator wiring into `baien-distill/graph.py`.
- Lexicon publish (`com.etzhayyim.baien.distributedTrainDelta` real
  emission with ES256 passkey signing).
- Multi-device swarm coordination.
- DP clip + Gaussian noise calibration (R2 — once real Δ distributions
  are observed across multiple devices).
- Byzantine aggregation (R3 — needs N ≥ 5 contributors).
- Modality-projector federated training (R4).
- Reward / payout mechanics (constitutionally fixed as out-of-scope by
  ADR-2605192100 §non-profit).

# Decision

## 1. Device matrix (R1 pass = all three rows green)

| Device class | Reference hardware | Min OS / browser | Memory ceiling | Step budget per round |
|---|---|---|---|---|
| iOS  | iPhone 12 (A14, 6 GB unified) | iOS 17.5 + Safari 17.5 (WebGPU enabled) | trunk fp16 ≤ 1.6 GB; total peak ≤ 2.5 GB | 50 |
| Android | Pixel 6 (Tensor G1, 8 GB) or any Adreno-650+ Android 14+ device with ≥ 4 GB | Chrome 121+ with `chrome://flags/#enable-unsafe-webgpu` | same | 30 |
| WASM desktop | M-series Mac (M1+) or RTX-class | Chrome 121+ or Safari 17.5+ | 4 GB headroom | 500 |

R1 is **passed** only when all three rows independently meet the
success criteria below. Failing any row means R1 is not done — R2
remains blocked.

## 2. WebGPU numerics fallback rules

R1 implements three numerics paths; the device profile selects at
runtime based on a 3-prompt warm-up benchmark (relative error vs. an
fp64 reference computed CPU-side):

| Path | Forward | LoRA grad accumulation | Adam moments (m, v) | Trigger |
|---|---|---|---|---|
| **A — fp16 throughout** | fp16 | fp16 | fp16 | Desktop M-series + RTX only, AND warm-up relative error < 1e-3 |
| **B — fp32 grad accum (DEFAULT for mobile)** | fp16 | fp32 | fp32 | iOS Safari, Adreno Android, AND fallback when path A warm-up fails |
| **C — full fp32** | fp32 | fp32 | fp32 | Last-resort safety; activates if path B overflows during warm-up |

The warm-up runs three deterministic forward+backward+update steps
on a fixed 3-example sub-shard and checks that the LoRA delta norm
ratio against the fp64 reference is within [0.99, 1.01]. If not,
fall down the table.

Activation checkpointing is fixed at **every other transformer
block** on mobile paths (B, C) — halves peak activation memory at
the cost of ~30% extra forward FLOPs. Desktop path A runs without
checkpointing.

## 3. OPFS Adam-state format

Adam optimizer state (m, v moments per LoRA parameter) is offloaded
between micro-batch steps so the PWA can survive a background kill.
Format:

```
/baien-train/<actorDid-sanitised>/<roundId>/
  meta.json         { rank, alpha, baseModelCid, prevAdapterCid,
                       iter, stepsCompleted, deviceClass, path }
  adam-m.f32        Float32Array of all m moments, layout = lexicographic
                    (layer-name, param-name) tuple sorted, A-then-B
  adam-v.f32        Float32Array of all v moments, same layout
  delta-A.f32       Current Δ for A matrices (rolling, updated each step)
  delta-B.f32       Current Δ for B matrices (rolling, updated each step)
  rng-state.json    Deterministic RNG seed + step count (for resumable
                    dropout)
```

`roundId` = `sha256(baseModelCid || prevAdapterCid || datasetShardCid || iter)`
truncated to 16 hex chars. Files are append-only within a round;
on round commit the directory is moved to `committed/<roundId>/`
and the rolling files become the final delta.

OPFS lifecycle:

- On resume, R1 reads `meta.json`, re-locates the trunk + shard via
  the IPFS cache (CID lookup), reconstructs the Adam state by
  loading the `.f32` files, then continues from `stepsCompleted`.
- On round commit, the rolling `delta-A.f32` + `delta-B.f32` are
  packed into a safetensors blob and pinned to IPFS (R1 stops at
  the local pin — publication to the lexicon firehose is R2).
- On round abort, the directory is moved to `aborted/<roundId>/`
  with a tombstone file describing the abort reason (thermal /
  OOM / fp16-overflow / scanner-fail).

## 4. R1 eval microbench shard (committed to git)

A 16-example shard at `90-docs/baien/r1-microbench-shard.jsonl`
(landed with the R1 implementation commit, not this ADR). The
shard is:

- 4 multiple-choice arithmetic prompts (deterministic graders)
- 4 short-form factual prompts (exact-match graders against
  reference)
- 4 instruction-following prompts (regex graders)
- 4 short multilingual prompts (en / ja / es / hi, exact-match
  on a token-set basis)

Why 16 and not the full microbench: 16 fits in iPhone 12 memory
budget for an eval pass under 30 seconds at q4f16 trunk weights;
the full bench would take 6+ minutes per device per round, which
breaks the "three consecutive runs" timing budget.

`prompts.jsonl` is content-addressed (CID committed to git as a
sidecar `.cid` file), so R2's aggregator can verify the contributor
used the canonical shard.

## 5. R1 success criteria

R1 is **passed** for a given device class when:

1. Three consecutive runs on the same `datasetShardCid` (and the
   same `prevAdapterCid` = empty-adapter CID for iter=0) each
   record `lossAfter < lossBefore × 0.98` — the same Wellbecoming
   ratio the R2 aggregator will enforce.
2. The numerics path selected (A / B / C) is stable across the three
   runs (no path-flip mid-run).
3. Peak observed memory stays ≤ 2.5 GB on iPhone 12 / Android 4 GB
   class and ≤ 4 GB on desktop.
4. Round completes within 5 minutes on mobile and 90 seconds on
   desktop.
5. OPFS Adam-state round-trip works: kill the PWA mid-round,
   relaunch, resume to completion — and the final `lossAfter`
   matches the no-kill run to within ±1e-4 (Wellbecoming reproducible).

The pass evidence is captured in a manual run-log file at
`90-docs/baien/r1-runlog-<deviceClass>.md`, signed by the operator
witness with the same passkey ES256 path R2+ will use.

## 6. Failure modes and abort conditions

R1 device-side aborts (the round produces no Δ; OPFS dir → aborted/):

- **thermal** — device-thermal-state ∈ {serious, critical} for > 5 s.
- **OOM** — any WebGPU buffer allocation > device GPU memory budget.
- **fp16-overflow** — any forward pass produces a NaN or ±Inf
  activation (caught by reduce-max on each block output).
- **scanner-fail** — `charter_rider.scan()` rejects > 5% of the
  shard rows on the device side.
- **timeout** — round exceeds 10 minutes wall-clock.

R1 does NOT abort on `lossAfter ≥ lossBefore` — that case is recorded
but the round still completes (it's a Wellbecoming reject for the
R2 aggregator, not a device-level abort). The operator decides
whether to retry.

## 7. R1 implementation task list (drives the R1 code commit)

The R1 code commit, which lands after this ADR is reviewed, replaces
the throw-on-use stubs in `20-actors/ameno/src/train.ts` with:

1. `detectDeviceClass()` — ua-string + WebGPU adapter info + memory
   budget probe.
2. WebGPU compute-shader implementations of:
   - LoRA forward (q/k/v/o_proj, fp16 with optional fp32 accumulator
     bind group).
   - LoRA backward (dA, dB chain-rule via vjp; no backward through
     trunk).
   - Adam step (m, v update + parameter step with bias correction).
3. OPFS layer (`@etzhayyim/ameno/train/opfs.ts`, new sibling).
4. `runFederatedRound()` orchestration.
5. Local-only safetensors pack + IPFS pin via `@etzhayyim/sdk`
   (no DID publish — that's R2).
6. Device run-log writer: appends to
   `90-docs/baien/r1-runlog-<deviceClass>.md` from the device, then
   the operator commits.

`signDeltaManifest()` and `publishDeltaRecord()` stay throws in R1
— they're the L3 publish path and belong to R2.

## 8. R2 prerequisites unblocked by R1

When R1 passes for all three device classes:

- The eval microbench shard CID is fixed (no further changes without
  a new ADR — round-replay parity).
- The Adam-state OPFS format is fixed (R2 aggregator may assume
  contributors use this exact layout).
- The numerics path selection logic is fixed (R2 aggregator can
  weight contributor trust priors by path).
- The R2 ADR can then specify aggregator wiring with concrete
  expectations.

# Consequences

## Positive

- Decouples real-device validation from aggregation logic. R2's
  aggregator design can rest on empirical R1 data (delta norms,
  numerics-path mix, runtime distributions) rather than guesses.
- The Adam-state OPFS format becomes a stable contract early —
  contributors who join in R3 will use the same on-disk format that
  R1 establishes.
- Forces the team to commit a small, content-addressed microbench
  shard up front. Subsequent rounds (R2..R4) cite the same shard,
  so cross-round comparisons are valid.

## Negative

- Requires three real devices to test (iPhone 12, an Adreno
  Android, an M-series Mac). For etzhayyim this is fine (operator
  already has all three); for an outside reviewer this is a non-trivial
  ask.
- iOS Safari WebGPU compute-shader backward graph is not a
  well-trod path. Expect surprises in fp16 precision; the path-A→B→C
  fallback is meant to absorb them but may need extension if path C
  also overflows.
- The 16-example shard is small. R2 + R3 will need a larger eval
  set to detect overfitting; this ADR explicitly does not pretend
  16 examples is enough for any quality claim — only for
  "Δ-direction-of-improvement" smoke.

## Constraint side-effects

- `ameno/src/train.ts` grows from a throw-on-use file (~200 LoC)
  to ~600–900 LoC after R1 implementation (kernels + OPFS +
  orchestration).
- A new `20-actors/ameno/src/train/opfs.ts` sibling lands.
- `90-docs/baien/r1-microbench-shard.jsonl` + `.cid` sidecar
  land in the R1 implementation commit (not this ADR commit) —
  small file (< 16 KiB).

# Alternatives Considered

## A1 — Skip R1 ADR, just implement and commit

Faster, but the numerics fallback rules + OPFS format end up as
implicit conventions in the code rather than as a documented
contract. R2's aggregator would then have to reverse-engineer
contributor expectations. Rejected for the same reason ADR-2605231300
exists for the server-side distill loop — pipeline contracts are
worth writing down before code lands.

## A2 — Test on M-series desktop only first, mobile later

Easier first step, but the constitutional edge-target invariant
(ADR-2605241900) makes iPhone 12 + Android 4 GB first-class. If we
defer mobile to R2 we'd discover mobile-specific numerics issues at
aggregation time, with N contributors already producing Δ that the
aggregator may not be able to merge. Rejected.

## A3 — Synchronous aggregator-in-the-loop from the start

Have R1 publish each Δ as it's produced, with the aggregator
running on Murakumo. Couples device-side numerics with aggregator
trust gates, which is exactly the entanglement R0 + R1 are meant to
break. Rejected; R2 owns the aggregator wiring.

## A4 — Run R1 on transformers.js's existing fp32 path only

The simplest implementation, but path A (fp16) is exactly the path
that meets the edge-target memory ceiling (ADR-2605241900). If we
ship fp32-only we'd blow the 2.5 GB budget on iPhone 12 and break the
constitutional invariant. Rejected.

# References

- ADR-2605242600 (R0 scaffold) — parent design this builds on.
- ADR-2605241900 (Edge-target invariant) — the memory / trunk-size
  ceiling R1 must respect.
- ADR-2605231300 (Baien distill ReAct loop) — server-side
  precedent for "pipeline contract before code".
- ADR-2605231525 (No server-side signing) — explains why R1
  produces a local Δ but does NOT sign or publish yet.
- ADR-2605192200 (Charter Rider v2.0) — `charter_rider.scan()`
  invocation at L2 step 2.
- ADR-2605242000 (wadachi R0 scaffold) — same phased-ADR-per-phase
  pattern this PR follows.
