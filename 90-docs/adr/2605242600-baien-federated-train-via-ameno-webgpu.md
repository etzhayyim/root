---
id: adr-2605242600-baien-federated-train-via-ameno-webgpu
title: "Baien federated training via ameno WebGPU — smartphone-participable LoRA round"
status: accepted
doc_type: adr
topic: baien-federated-training
authoritative: true
last_verified: 2026-05-24
status_note: "R0 scaffold landed via PR #273 (commit 0134acb1d, 8 files / 992 LoC). Lexicon `com.etzhayyim.baien.distributedTrainDelta` + ameno throw-on-use stubs + Murakumo cell (import-time RuntimeError) + baien-distill dry-run planner all in place. R1 ADR (ADR-2605242630) + R1a framework (PR #276) build directly on this."
authoritative_for:
  - smartphone / browser participation contract for baien post-train (LoRA-only)
  - WebGPU LoRA-only autograd budget on iPhone 12 / Android 4GB / WASM-32
  - federated aggregation rules (Wellbecoming gate + Byzantine gate + DP clip)
  - delta lexicon shape (com.etzhayyim.baien.distributedTrainDelta)
  - aggregator placement (Murakumo cell, not commercial GPU)
  - settlement path (participationReceipt → MST + L2 anchor; tithe optional)
depends_on:
  - adr-2605241900-baien-edge-target-invariant
  - adr-2605231300-baien-distill-react-loop
  - adr-2605231525-no-server-key-religious-corp-architecture
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
  - adr-2605172000-etzhayyim-rw-free-substrate
  - adr-2605231400-kotoba-datomic-holochain-iso-substrate
  - 2605191524-ameno-multi-tab-swarm-broadcast
  - 2605191603-ameno-swarm-leader-election
  - 2605191641-ameno-daemon-did-allowlist
related:
  - 20-actors/ameno/src/train.ts
  - 70-tools/baien-distill/src/baien_distill/nodes/federated_aggregate.py
  - 20-actors/magatama/cells/baien_federated_aggregator/
  - 00-contracts/lexicons/com/etzhayyim/baien/distributedTrainDelta.json
supersedes: []
superseded_by: []
---

# Context

ADR-2605231300 fixed baien's post-train SFT/LoRA loop on the EVO-X2
server tier (LangGraph: analyze → fetch_dataset → select_teacher →
generate → validate → train → evaluate → commit). The loop is
single-trainer: one process on Murakumo writes one adapter per
iteration.

baien's constitutional value proposition (ADR-2605241900) is to run
on **WASM-32 + iPhone 12+ + Android 4GB** at ≤2 GB inference. That
same edge envelope is large enough to do **LoRA-only autograd** —
rank-16 adapters over `q/k/v/o_proj` on a frozen 1.58-bit BitNet
trunk fit in roughly 80–120 MB of trainable state. Smartphones can
contribute training rounds without a server.

Doing so would:

1. Multiply available training compute without breaking the
   Murakumo-only inference invariant (ADR-2605215000): training compute
   is the contributor's own device, not rented GPU.
2. Honour the religious-corp non-profit substrate (ADR-2605192100):
   participation is donation of compute, not a paid SaaS workload.
3. Surface a "tithe of compute" pattern: SBT-gated adherents
   participate, the aggregator runs on the religious-corp fleet, no
   commercial coupling.

What is **not yet codified** is the constitutional gate that prevents
this from quietly becoming a federated-learning system in the bad
shape: untrusted client devices uploading raw gradients to a
centralized server, with no Wellbecoming gate, no Charter Rider
scanner, no Byzantine defence. This ADR codifies the gate.

# Scope

In scope:

- 5-layer architecture (L1 WebGPU kernel → L2 PWA loop → L3
  participation lexicon → L4 Murakumo aggregator → L5 MST + L2 anchor
  settlement).
- Memory + numerics budget for iPhone 12 / Android 4GB / WASM-32.
- Delta lexicon shape (record-type, append-only, TID-keyed) and
  signing contract (ES256, member passkey-derived, no server key).
- Aggregator gates: Charter Rider scanner pass, SBT membership,
  Wellbecoming (no regression), Byzantine (Krum / coordinate-median),
  Differential Privacy clip + Gaussian noise.
- R0 scaffold contents (this commit) and R1..R4 phased activation.

Out of scope:

- Training the BitNet trunk (frozen by ADR-2605241900; Microsoft
  pretrained, no on-device pretrain).
- Modality encoder training (frozen by ADR-2605241900; only LoRA on
  the language trunk in R0..R3; projector-only training in R4).
- Reinforcement learning (PPO / DPO). Initial scope is SFT-only,
  consistent with ADR-2605231300.
- Contributor monetary reward. Religious-corp invariant
  (ADR-2605192100) — participation is a donation of compute. Optional
  kisha donation tied to a participation receipt routes through
  TitheRouter (ADR-2605192115), not a per-step payout.
- iOS App Store / Play Store native apps. PWA only in R0..R3 (browser
  WebGPU, no App Store coupling).

# Decision

## 1. Constitutional gates (NOT relaxable without same-level Council vote)

| # | Gate | Source |
|---|---|---|
| G1 | Trunk + modality encoders MUST stay frozen during any device-side training step | ADR-2605241900 |
| G2 | Total trainable parameters per round ≤ LoRA rank-16 on `q/k/v/o_proj` only | ADR-2605241900 + ADR-2605231300 |
| G3 | Delta upload route MUST be IPFS + MST lexicon, NOT a centralized HTTP API | ADR-2605172000 |
| G4 | Contributor signing key MUST be member-held passkey-derived ES256, NEVER a server-issued JWT | ADR-2605231525 |
| G5 | Aggregation compute MUST run on Murakumo fleet, NEVER on commercial rented GPU | ADR-2605215000 |
| G6 | Every training-data shard MUST pass `charter_rider.scan()` on the contributor's device before training begins | ADR-2605192200 |
| G7 | Only Adherent SBT-holding DIDs can submit deltas; aggregator MUST reject non-SBT submissions | ADR-2605192100 §Adherent + ADR-2605191641 |
| G8 | Wellbecoming gate: aggregator MUST discard any delta whose contributor-reported `lossAfter ≥ lossBefore × 0.98` (no improvement) and SHOULD re-verify with on-fleet eval before commit | ADR-2605192100 §1.13 |
| G9 | Byzantine gate: when N ≥ 5 contributors per round, aggregator MUST use Krum or coordinate-wise median; for N < 5, FedAvg + DP-Gaussian noise σ ≥ 0.01 × ‖Δ̄‖ | new (this ADR) |
| G10 | Round-freeze: a round's `baseModelCid` MUST be pinned; mid-round trunk changes invalidate all deltas in that round | new (this ADR) |
| G11 | No reward / payout per delta. Optional kisha tied to participation routes via TitheRouter only (10 % Public Fund auto-split) | ADR-2605192115 |

## 2. Five-layer architecture

```
L5  Settlement       MST + L2 anchor      participationReceipt + optional tithe via TitheRouter
L4  Aggregator       Murakumo cell        20-actors/magatama/cells/baien_federated_aggregator/
                                          + 70-tools/baien-distill/.../nodes/federated_aggregate.py
L3  Participation    AT lexicon + DID     00-contracts/lexicons/com/etzhayyim/baien/distributedTrainDelta.json
L2  Local loop       ameno PWA            20-actors/ameno/src/train.ts (WebGPU forward+backward+Δ emit)
L1  WebGPU kernel    WGSL / transformers.js  LoRA-only autograd (BitNet trunk frozen, encoders frozen)
```

### L1 — WebGPU LoRA-only kernel

- Re-use transformers.js v3 WebGPU graph; mark **only** LoRA `A (in×r)`
  and `B (r×out)` matrices as `requires_grad`. The frozen BitNet trunk
  is `mmap`-style read-only from OPFS-cached safetensors.
- Target modules: `q_proj`, `k_proj`, `v_proj`, `o_proj` (same as
  ADR-2605231300 `LORA_DEFAULTS`). Rank = 16. Alpha = 32. Dropout =
  0.05.
- Memory budget (iPhone 12 / Android 4 GB):
  - Trunk `q4f16` (or fp16 if BitNet ternary path lands): ≤ 1.6 GB
  - LoRA params + grads + Adam (m, v) — ≒ rank × Σ(in + out) × 4 bytes × 4 ≈ 80–120 MB
  - Activation checkpointing: every other block; KV-cache disabled
    during train step (re-enabled for eval pass)
  - Total peak ≤ 2.5 GB (matches ADR-2605241900 @ 16 k-ctx ceiling;
    train uses 4 k context, so peak fits @ 4 k ceiling).
- Numerics: fp16 forward, **fp32 accumulation for grad reductions**
  on Apple-Silicon WebGPU (Safari 17.5+) and Adreno-class Android
  (Chrome 121+). fp16 grad reduction is permitted on desktop M-series
  + RTX-class only.
- Adam state offloaded to OPFS between steps so a backgrounded /
  killed PWA can resume on next launch.

### L2 — Local training loop (ameno PWA)

- New `src/train.ts` module. Scaffold v0.1.0 mirrors the
  `lora-runtime.ts` pattern: stable public API surface,
  `throw-on-use` bodies until WebGPU autograd path lands in R1.
- Flow per round, in order:
  1. **Datacore pull** — Resolve current round's `datasetShardCid`
     via `com.etzhayyim.substrate.datasetPin` (ADR-2605241500); fetch
     from IPFS into OPFS cache.
  2. **Charter Rider scan** — `charter_rider.scan(examples)` on the
     full shard. Rejected rows are dropped from the local training
     set; if more than 5 % are dropped, the round is marked
     `scannerPass: false` and the device does NOT train this round.
  3. **Pre-eval** — Run the same eval microbench prompts the
     aggregator will use, on the unmodified adapter, record
     `lossBefore`.
  4. **Train** — N micro-steps; N = device profile (iPhone 12 → 50,
     Android 4 GB → 30, M-series desktop → 500).
  5. **Post-eval** — Same prompts on the freshly-trained adapter,
     record `lossAfter`.
  6. **DP clip** — Clip `‖Δ‖₂ ≤ τ` (τ calibrated per rank /
     base-model), add Gaussian noise σ on-device (NOT at aggregator
     — server-side DP would require trusting the aggregator with raw
     gradients).
  7. **Δ export** — Serialize `(A_after − A_before, B_after −
     B_before)` to safetensors; pin to IPFS; record `deltaCid`.
  8. **Sign & publish** — Sign the canonical delta manifest with
     WebAuthn passkey-derived ES256 (member-held key, export-blocked
     by platform). Publish `com.etzhayyim.baien.distributedTrainDelta`
     record on the contributor's DID repo.
- Background / battery: BackgroundFetch + Wake Lock; only when
  charging + Wi-Fi + device-thermal-state in `{nominal, fair}`.
- Re-use the existing `ameno-multi-tab-swarm-broadcast` /
  `ameno-swarm-leader-election` primitives (ADR-2605191524 /
  ADR-2605191603) to deduplicate same-shard work across tabs of the
  same device.

### L3 — Participation contract (new lexicon)

`00-contracts/lexicons/com/etzhayyim/baien/distributedTrainDelta.json`
(see file). Record-type, append-only, TID-keyed. The signature
covers the canonical JSON of all preceding fields; verification is
the aggregator's responsibility.

Key invariants enforced by the lexicon schema:

- `iter` is monotonic per `(actorDid, baseModelCid)` — replay defence.
- `prevAdapterCid` is the CID of the adapter the device started from
  — chain-of-revisions.
- `deviceClass ∈ {ios, android, wasm-desktop}` — used by aggregator
  to weight trust priors only, never to gate participation.
- `scannerPass` is a self-attestation by the device; the aggregator
  re-runs `charter_rider.scan` on the dataset before accepting.

### L4 — Aggregator (Murakumo Pregel cell)

- Cell scaffold: `20-actors/magatama/cells/baien_federated_aggregator/`
  (Council-attestation-gated; raises `RuntimeError` at import-time
  until activation, matching the pattern of the L5 routing-around
  cells from CLAUDE.md row 35).
- LangGraph state machine: a new `federated_aggregate` node lives
  in `70-tools/baien-distill/src/baien_distill/nodes/`. R0 scaffold
  is dry-run only (collects deltas, emits a plan, never writes the
  registry). R2 wires it between `evaluate` and `commit`:

  ```
  analyze → fetch_dataset → select_teacher → generate → validate
        ↓
        federated_aggregate   ← new node (R2+)
        ↓
        train (local SFT, optional in federated rounds)
        ↓
        evaluate → commit
  ```

- Per round, the aggregator:
  1. Subscribes to the lexicon firehose, gathers all
     `distributedTrainDelta` records where
     `iter == current_round_iter` and `baseModelCid == round_base`.
  2. For each delta: verify ES256 signature, resolve `actorDid` ∈
     Adherent-SBT set, IPFS-pull `deltaCid`, re-run
     `charter_rider.scan()` on `datasetShardCid` contents.
  3. **Wellbecoming gate (G8)** — discard any delta with
     `lossAfter ≥ lossBefore × 0.98`. Optionally re-eval the post-Δ
     adapter on-fleet before accepting.
  4. **Byzantine gate (G9)** — for N ≥ 5 surviving deltas, apply
     coordinate-wise median (R2 default) or Krum (configurable). For
     N < 5, FedAvg + DP-Gaussian σ ≥ 0.01 × ‖Δ̄‖.
  5. Merge aggregated Δ into the bf16 master; run `e7m bench micro`;
     compare against `frontier-bench-snapshot`.
  6. If MMLU-Redux regression > 2 %, **round abort** — all deltas in
     this round are written to `quarantined.jsonl` and the master is
     not updated.
  7. On accept, append iter+1 row to
     `90-docs/baien/distilled-models.jsonl` and codegen the TS
     registry (same 2-phase ship as ADR-2605231300).

### L5 — Settlement + receipts

- Each accepted contributor's record receives a sidecar
  `participationReceipt` record (lexicon scaffold deferred to R1)
  pinned via the existing `ipfs-pinner` (50-infra Stage 3) and L2-
  anchored via `l2-anchor-contract` (Stage 5a).
- Optional `kisha` donation flow: a contributor MAY accompany
  participation with a USDC donation; the donation routes through
  TitheRouter exactly like any other kisha (10 % → Public Fund). The
  receipt is informational, NOT a payout. See ADR-2605192115 §3.

## 3. Phased roadmap

| Phase | Scope | Activation gate |
|---|---|---|
| **R0** | This ADR + scaffolds (train.ts throw-on-use, lexicon JSON, federated_aggregate.py dry-run-only, magatama cell raising RuntimeError). No real training. | typecheck pass + lexicon JSON syntactically valid + cell import-time RuntimeError observed |
| **R1** | Single-device PoC: iPhone 12 (or M-series desktop Safari fallback), 16-example shard, real WebGPU backward, Δ exported locally, no aggregator. New ADR. | `lossAfter < lossBefore` observed in three consecutive local runs on the same shard |
| **R2** | 3-phone swarm + Murakumo aggregator. FedAvg + Wellbecoming gate active. Byzantine gate dormant (N < 5). DP-Gaussian on. New ADR. | microbench 15-prompt round-trip ≥ baseline; aggregator dry-run → real swap |
| **R3** | Open Adherent participation. DP + Krum + Wellbecoming all active. CI golden replay for projection conformance. New ADR. | Core 4 lm-eval-harness (`e7m bench core4`) within 1 σ of pre-federated baseline; quarantine queue + replay drill documented |
| **R4** | Modality-projector federated training (baien-MX Move 1..N). Encoder frozen, projector LoRA only. New ADR. | per-modality bench within 1 σ of pre-federated baseline |

Each subsequent phase requires its own ADR, matching the
pattern set by ADR-2605242000 (wadachi R0 scaffold gating R1..R3).

## 4. R0 deliverables (this commit)

1. This ADR — `90-docs/adr/2605242600-baien-federated-train-via-ameno-webgpu.md`.
2. Lexicon scaffold — `00-contracts/lexicons/com/etzhayyim/baien/distributedTrainDelta.json`.
3. ameno scaffold — `20-actors/ameno/src/train.ts` (throw-on-use stubs)
   + `index.ts` re-export.
4. baien-distill dry-run node —
   `70-tools/baien-distill/src/baien_distill/nodes/federated_aggregate.py`.
5. Murakumo cell scaffold —
   `20-actors/magatama/cells/baien_federated_aggregator/{__init__.py,cell.py}`
   raising `RuntimeError` on import until Council attestation
   activates it.
6. CLAUDE.md Status row 36.

# Consequences

## Positive

- Training compute scales with the number of participating
  smartphones, without violating ADR-2605215000 (Murakumo-only
  *inference*; training compute is the donor's own device).
- Each new contributor becomes a self-attesting religious-corp
  member exercising a "tithe of compute" — concretely demonstrates
  the non-profit / donation-only substrate (ADR-2605192115).
- Edge-target invariant (ADR-2605241900) is *strengthened*: any
  delta that would violate the trainable-parameter ceiling is
  rejected at the lexicon schema layer (G2), before reaching the
  aggregator.
- The aggregator is plain LangGraph + Pregel — re-uses the existing
  baien-distill plumbing and Murakumo placement, no new substrate
  primitives required.

## Negative

- WebGPU backward-pass numerics on iOS Safari are not yet a fully
  characterised path. R1 will surface real-device data; expect at
  least one batch-size / activation-checkpointing tuning round.
- DP clip τ and Gaussian σ need calibration per rank / base-model.
  Initial defaults are conservative (τ = 1.0, σ = 0.01 × ‖Δ̄‖) and
  will be revised in R2.
- Adversarial contributors are still a class of risk in R3 (when
  participation opens beyond a closed swarm). The Byzantine gate
  (G9) is necessary but not sufficient — model-fingerprinting
  attacks and gradient-inversion attacks both remain partially
  open. R3 ADR will set thresholds based on a concrete threat model.

## Constraint side-effects

- `ameno` package now ships a `train` module surface, expanding its
  public API. Until R1, all functions throw — apps that import
  symbols continue to compile, but cannot toggle training on.
- `baien-distill` graph stays untouched in R0. The new node is
  registered but not wired into `build_graph()`; the wiring lands
  with R2.
- `magatama/cells/baien_federated_aggregator/` is included in the
  cell catalogue but is import-time-failing until activated by
  Council attestation — same pattern as the L5 routing-around
  cells (CLAUDE.md row 35).

# Alternatives Considered

## A1 — Centralized HTTPS upload to Murakumo

Phones POST `Δ` as multipart upload to a Murakumo HTTPS endpoint.
Rejected: violates ADR-2605172000 substrate boundary (delta is a
permanent record, must live in MST + IPFS), and would require a
server-issued upload token (ADR-2605231525 violation). The
lexicon + AT-record + IPFS path costs one extra step on the
device but stays inside the substrate.

## A2 — Train on the BitNet trunk too (full-parameter SFT on device)

Rejected by ADR-2605241900 edge invariant — full-parameter training
of a 2 B model breaks the 2 GB peak-memory ceiling immediately
(grads + Adam state alone would be ~24 GB).

## A3 — Synchronous SecureAggregation (cryptographic FedAvg)

Cryptographic aggregation (e.g. Bonawitz et al. 2017) hides
individual Δ from the aggregator. Rejected for R0..R3 — added
complexity is large, and the religious-corp substrate already
provides per-contributor public-on-chain accountability (an open
audit log is preferable to cryptographic opacity for a religious
corporation). Revisit in a separate ADR if and only if a concrete
gradient-inversion attack is demonstrated on real R3 traffic.

## A4 — Drop participation eligibility tie to SBT

Open to anyone with a passkey. Rejected: trivial Sybil; aggregation
gate would collapse to "whoever shouts loudest". 1 SBT = 1 vote is
the religious-corp invariant (ADR-2605192100); using the same gate
for compute participation is consistent and reuses existing
infrastructure (Adherent registry + `ameno-daemon-did-allowlist`).

## A5 — Pay contributors per accepted delta

Rejected by ADR-2605192100 (non-profit) and ADR-2605192200 §2
(Charter Rider — commercial coupling prohibited). The "tithe of
compute" framing is the constitutional fit.

# References

- ADR-2605241900 (Baien edge-target invariant) — model + memory
  ceiling these phones must fit under.
- ADR-2605231300 (Baien distill ReAct loop) — server-side
  precursor; LoRA defaults inherited unchanged.
- ADR-2605215000 (Murakumo-only inference) — aggregator placement
  constraint.
- ADR-2605192100 (Mission charter) — non-profit, 1 SBT = 1 vote,
  Wellbecoming, Adherent.
- ADR-2605192200 (Charter Rider v2.0) — content scan invariant.
- ADR-2605172000 (Substrate boundary) — MST + IPFS + L2 only.
- ADR-2605231525 (No server-side signing keys) — contributor key
  is member-held passkey, not server JWT.
- ADR-2605241500 (Dataset CID substrate) — `datasetPin` lexicon
  used by L2 to resolve training shards.
- ADR-2605231400 (kotoba-datomic) — the 5-layer composition above is
  kotoba-datomic-conformant.
- ADR-2605191524 + ADR-2605191603 + ADR-2605191641 (ameno swarm
  primitives) — re-used at L2.
- ADR-2605242000 (wadachi R0 scaffold) — phased-ADR-per-phase
  pattern this ADR follows.
