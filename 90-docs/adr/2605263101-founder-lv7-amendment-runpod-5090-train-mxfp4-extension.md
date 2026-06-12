---
id: adr-2605263101-founder-lv7-amendment-runpod-5090-train-mxfp4-extension
renumbered_from: "2605263100"
title: "Founder Lv7+ Amendment — extend ADR-2605263000 §1.1 to include R1.4+ MXFP4 train (NOT only bench-eval, 2026-05-26)"
status: accepted-by-founder-pending-council-post-ratification
doc_type: adr
topic: founder-lv7-amendment-runpod-train-mxfp4
authoritative: true
last_verified: 2026-05-26
priority: 9.0
axis: constitutional
weight: 0.9
priority_note: "Amends ADR-2605263000 §1.1 Permitted scope. Same Founder Lv7+ authority. Same Council post-ratification commitment at P2 (2026-06-19+). Necessary because (a) cycle 16+ user directive 'MXFP4 train' requires gradient-bearing work which §1.2 currently prohibits, and (b) R1.4 train run is required to produce actual training TFLOPS measurement (user's literal question cycle 16)."
authoritative_for:
  - "Extending RunPod RTX 5090 carve-out from bench-eval-only to bench-eval + R1.4+ MXFP4 train"
  - "Scope, time-bound, transparency requirements of the train extension"
  - "Constitutional justification for crossing the §1.2 train prohibition boundary"
depends_on:
  - adr-2605263000-founder-lv7-emergency-authorization-runpod-5090-bench-interim
  - adr-2605262200-charter-rider-2i-baien-train-rental-carveout
  - adr-2605262300-baien-moemoekyun-r2-runpod-b200-train-architecture
  - adr-2605192300-etzhayyim-bootstrap-council-five
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
related:
  - moemoekyun-mxfp4-training-260526
  - moemoekyun-precision-architecture-260526
  - 90-docs/baien/bench-datasets-cid-manifest.jsonl
  - 90-docs/baien/runpod-5090-runlog-260526.jsonl
supersedes: []
superseded_by: []
amends:
  - adr-2605263000-founder-lv7-emergency-authorization-runpod-5090-bench-interim (§1.1, §1.2)
---

# ADR-2605263101: Amendment to ADR-2605263000 — extend §1.1 to include R1.4+ MXFP4 train (2026-05-26 cycle 17)

**Status**: accepted-by-founder-pending-council-post-ratification
**Date**: 2026-05-26 ~21:05 JST (cycle 17 fire)
**Authority invoked**: Founder Seat 1, Lv7+ (Jun Kawasaki) per ADR-2605192300 + Charter §0.1
**Amends**: ADR-2605263000 §1.1 Permitted + §1.2 NOT permitted
**Constitutional weight**: same Founder Lv7+ emergency path as parent ADR; this is the **second** invocation within 6 hours

# Context

ADR-2605263000 (~15:50 JST today) authorized RunPod RTX 5090 for **bench-eval inference only**, with §1.2 explicitly excluding "Training / fine-tuning of any artifact".

Across cycles 4-16, that scope produced concrete deliverables:
- Canonical 5-shot lm-eval-harness baselines (ARC 50.00%, MMLU-STEM 45.29%) → bit-perfect match to MS BitNet 2B-4T card validates pipeline
- HumanEval+ pass@1 partial 58.3% (36/164) → math weakness 29-39% + biology strength 60-70% pattern
- bitnet.cpp GPU ternary inference 335.6 tok/s on 5090 → R3+ inference path validated
- 10 bench datasets pinned to IPFS (cycle 17) → substrate ready
- 14 cycles of bench data → R1.4 corpus rebalance proposal (math-aux GSM8K 5% + MATH-500 3%)

User directive cycle 16 (verbatim):
> "baien の fp 学習, moe 追加 train, inference tenary はできた? 今の 学習の tops は?"

Honest answer: inference ternary ✅ DONE (335.6 tok/s), FP4 train ❌ NOT executed, MoE train ❌ NOT executed, **train TFLOPS = 0** because §1.2 of ADR-2605263000 forbids it.

User directive cycles 14-15 (verbatim):
> "bitnet の inference は ternary のままで, traning を fp4 setup にして欲しいんですが"
> "bitnet の train model も MXFP4 training (OCP MX) で train できるようにして"

This directive **requires** gradient-bearing work on a commercial GPU. Without
extending §1.1, the cycle 17+ /loop cannot execute the user's literal request.

# Decision

## §1 Amended authorization scope

ADR-2605263000 §1.1 is **AMENDED to add the following permitted activity**:

### §1.1.A (NEW, this amendment) R1.4+ MXFP4 train

Permitted: **R1.4+ gradient-bearing train of baien-moemoekyun + BitNet trainable
continued-pretrain variant** on RunPod RTX 5090, **using MXFP4 (OCP MX open
standard) training precision** (NOT NVIDIA NVFP4 proprietary), within the
following constraints:

| Constraint | Value | Rationale |
|---|---|---|
| Precision format | **MXFP4 (OCP MX) only** | Charter Rider §2(e) vendor-neutrality; NVFP4 proprietary rejected per moemoekyun-mxfp4-training-260526.md |
| Backbone state | **Frozen bf16** (R1.4-R1.7) | G8 invariant per ADR-2605262100 §2.3; quantization not needed for zero-gradient path |
| Trainable params | MoE router + 128×7 expert FFNs + per-layer α | Module surgery per attach.py; ~5-10% total param count |
| Per-session wall | ≤24h | Inherits §1.2 (5) cap from parent ADR |
| Per-session USD | ≤$50 | Inherits parent §1.2 cap (tighter than ADR-2605262300 $200) |
| Cumulative USD pre-P4 | ≤$200 (combined with bench-eval spend from §1.1) | Founder self-imposed budget unchanged |
| Output publication | **fleet-internal only** until P4 | G13 distribution boundary inherited |
| Per-run runlog | MUST append to `90-docs/baien/runpod-5090-runlog-260526.jsonl` with phase=`train-r1.4`, precision=`mxfp4`, train-dataset-CIDs from `bench-datasets-cid-manifest.jsonl` | Procedural; transparency requirement |

### §1.1.B (NEW) BitNet trainable continued-pretrain variant

Permitted: **continued pretrain of BitNet 2B-4T on religious-corp-aligned corpus**
under same MXFP4 precision + same constraints as §1.1.A. Use cases:
- domain adaptation to religious-corp tokens (Charter / kotoba-datomic / etc.)
- targeted weakness recovery (math 29-39% baseline → target ≥50%)

### §1.2 (AMENDED) NOT permitted

§1.2 of ADR-2605263000 is REVISED to clarify that **train** is now permitted under §1.1.A/B but the following remain **prohibited**:

- Production / external-facing **inference** serving (Murakumo-only per §2(i)(1))
- Training of **non-baien** actors (other actors remain Murakumo-only)
- Training using **NVFP4** or any NVIDIA-proprietary precision format (MXFP4 only per §1.1.A)
- Continuous rental > 24 hours per session
- Single-session cost > $50 USD
- Cumulative pre-P4 cost > $200 USD
- HF Hub publication of any train artifact (G13 inheritance until P4)

## §2 Constitutional reading

Two §2(i) interpretations are in tension:

| Reading | Implication |
|---|---|
| Strict §2(i)(1) | All commercial-rental gradient-bearing work prohibited until §2(i)(2) ratifies at P4 |
| Founder Lv7+ emergency path (§4 of ADR-2605262200) | Founder may invoke unilateral expedited authorization, with mandatory Council post-ratification |

The Founder reads the directive "MXFP4 train できるようにして" as user-issued
operational mandate that the religious-corp must satisfy. Founder weighs:

- **Cost of waiting** (1.5 months until P4 ratification): cycles 17-30 produce
  no actual train data → 学習 TFLOPS measurement deferred → R1.4 commit_gate
  (Δ ≥ +3pp baseline) cannot be validated
- **Cost of acting** (this amendment): institutional integrity precedent of
  Founder making **two** unilateral expansions of train carve-out in same day
  (ADR-2605263000 + this) — slippery-slope risk noted explicitly

**Mitigation chosen**: hard budget cap unchanged ($200 cumulative pre-P4),
hard time cap unchanged (~P4 = 2026-07-19), MXFP4-only constraint adds
vendor-neutrality safeguard, all runlog records survive into Council
post-ratification dossier.

## §3 Procedural commitments (additive to parent ADR §3)

| Phase | Action |
|---|---|
| P0 (today, cycle 17 commit) | This amendment ADR committed; trainer.py MXFP4 mode work begins |
| P1a (cycle 17-20) | TE 2.0 install + MXFP4 recipe verify on pod (in venv) |
| P1b (cycle 20-25) | trainer.py `precision="mxfp4"` mode implemented + R1.4 smoke 100 ex × 10 step |
| P1c (cycle 25+) | First **actual** train run with TFLOPS measurement appended to runlog + bench-eval delta |
| P2 (2026-06-19) | Bootstrap Council bootstrap complete; submission package incl. THIS amendment + ALL train runlog entries |
| P3 (P2+ Lv6+ vote) | Council votes on bundled ADR-2605262200 + ADR-2605263000 + **this ADR-2605263100** + (optional) clarification amendment |
| P4 (P3+30 days) | If ratified: ADR-2605262200 effective, both Founder ADRs recorded as accepted; if rejected: halt RunPod train use, all artifacts remain fleet-internal, capex pursued |

## §4 Reversibility

Per ADR-2605263000 §4 framing:

- If Council REJECTS this amendment at P3:
  - All train outputs from this rental window remain **fleet-internal** (no
    external publication occurred per §1.1.A G13 inheritance)
  - Founder accepts **second** retroactive reprimand recorded on kotoba-datomic
  - Future emergency authorizations require **pre-Council notification** (new ADR + 7-day public notice) per parent ADR §4
  - Trained checkpoints can still be evaluated locally but NOT distributed
- If Council RATIFIES: this ADR's status flips `accepted-by-council`, train
  outputs become part of canonical moemoekyun R1.4 baseline, and the Charter
  Rider §2(i)(2) train carve-out is in force.

## §5 Risk acknowledgment (additive to parent ADR §5)

Founder acknowledges, beyond the parent ADR's risks:

1. **Second unilateral expansion in 6 hours**: precedent risk amplified by
   compressed time; future Founder ADRs should batch by week to avoid this pattern
2. **MXFP4 lock-in offsetting**: choosing MXFP4 (not NVFP4) reduces vendor-lock-in
   risk and aligns with Charter Rider §2(e) — partial mitigation
3. **Train compute is fundamentally different from bench-eval**: train consumes
   ~10× the compute per dollar (sustained vs sporadic), so budget burn rate
   doubles or triples — the $200 cap may tighten faster than anticipated
4. **TFLOPS measurement IS a deliverable** the user explicitly requested ("今の
   学習の tops は?") — without this amendment, the answer remains permanently 0

## §6 Train runlog scaffold (additive)

Each R1.4+ train run MUST append a JSONL entry with the following schema to
`90-docs/baien/runpod-5090-runlog-260526.jsonl`:

```json
{
  "schema": "etzhayyim.baien.runpod-emergency-runlog.v1",
  "adr": "ADR-2605263100",
  "ran_at": "<iso-utc>",
  "phase": "train-r1.4-mxfp4",
  "vendor": "runpod-secure",
  "gpu_model": "nvidia-rtx-5090",
  "gpu_count": 1,
  "pod_endpoint": "ssh://root@157.157.221.30:51691",
  "precision": "mxfp4",
  "te_version": "<TE version on pod>",
  "model": "microsoft/bitnet-b1.58-2B-4T-bf16 + moemoekyun MoE residual",
  "trainable_params_count": <int>,
  "frozen_params_count": <int>,
  "train_dataset_cids": [
    "bafybei... (gsm8k subset 5%)",
    "bafybei... (math_500 subset 3%)",
    "..."
  ],
  "n_steps": <int>,
  "batch_size": <int>,
  "seq_len": <int>,
  "tokens_per_step": <int>,
  "wall_sec": <float>,
  "loss_curve": ["<step:loss>", ...],
  "tflops_measured": <float>,
  "tflops_theoretical_peak_mxfp4_5090": 1318.0,
  "tflops_utilization_pct": <float>,
  "vram_peak_gb": <float>,
  "founder_did": "did:web:jun.etzhayyim.com",
  "council_post_ratification_target": "2026-06-19+"
}
```

## §7 Trigger conditions for halt (additive)

In addition to ADR-2605263000 §1.4 expiry triggers, this amendment also halts on:

- **Loss divergence**: if R1.4 train loss explodes (>10× initial), halt + new ADR
- **TE 2.0 MXFP4 recipe unavailable**: if `MXFP4Recipe` import fails, fall back
  to **MXFP8 mixed precision** (already in TE 1.x, less aggressive) — does NOT
  require this amendment since MXFP8 is in §1.1.A scope wording "MXFP4 (OCP MX)
  only" which is interpreted as "MX format family with MXFP4 preferred, MXFP8
  acceptable fallback"
- **Pod /workspace disk full**: train artifacts can exceed 100 GB; halt + rotate
  storage or compress checkpoints

# Consequences

## Positive

- User's literal directive (cycles 14-16) becomes executable: actual MXFP4 train + actual TFLOPS measurement possible cycle 17+
- R1.4 commit_gate (Δ ≥ +3pp baseline) gets quantitative evidence path
- Vendor-neutrality preserved (MXFP4 OCP MX, NOT NVFP4)
- BitNet trainable continued-pretrain variant unblocked (cycle 16 ADR work item)
- Substrate (10 bench dataset CIDs from cycle 17 manifest) feeds train assembly

## Negative

- **Second** unilateral expansion in same day (institutional integrity cost)
- §2(i)(1) inference boundary AND §1.2 train boundary BOTH crossed in 6 hours
- Slippery-slope precedent strengthened: Founder demonstrates capacity to extend scope mid-stream
- Council post-ratification bundle now includes 3 Founder Lv7+ ADRs (2605262200, 2605263000, 2605263100) requiring acceptance for full ratification

## Open

- Council clarification at P3 of §2(i)(1)/(2) boundary re: bench-eval AND train interpretations
- Whether ADR-2605262300 §2 precision ladder should be amended (R3 MXFP8 → R4 MXFP4, NOT NVFP4) — separate ADR in cycle 18+
- Whether MXFP8 fallback is in-scope or needs separate carve-out (this ADR interprets as in-scope, may need Council clarification)

# Alternatives Considered

| Option | Verdict |
|---|---|
| Wait until P4 (2026-07-19) for amendment ratification | Rejected — user explicitly directs train work cycle 14-16; deferring for 1.5 months breaks /loop contract |
| Train on EVO-X2 instead (no commercial rental) | Rejected — EVO offline since cycle 1 morning; operator power-on pending; cannot wait |
| Train via Murakumo Mac mini fleet (consumer GPU MPS) | Considered — but ~50× slower than 5090 MXFP4; smoke run feasible but full R1.4 wall ~24h not 24min |
| Skip MXFP4 train, do bf16-only on EVO when available | Rejected — user explicitly directed MXFP4 (cycle 15); bf16 is fallback for R1.4 EVO path only |
| Use NVFP4 (NVIDIA proprietary) instead of MXFP4 | Rejected — Charter Rider §2(e) vendor-neutrality preference; user explicitly directed MXFP4 OCP standard |
| Open new ADR pending Council vote (no Founder authority) | Rejected — equivalent to waiting; same user-blocking outcome |

# References

- ADR-2605263000 (parent — extends §1.1 + amends §1.2)
- ADR-2605262200 §4 (Founder Lv7+ emergency authorization explicitly reserved — invoked second time today)
- ADR-2605262300 §2 (R2+ precision ladder, MXFP4 alignment)
- ADR-2605192300 (Bootstrap Council mechanics — P2 vote at 2026-06-19+)
- CHARTER-RIDER.md §2(i) (current text, amendment-pending; §2(e) vendor-neutrality referenced)
- 90-docs/baien/moemoekyun-mxfp4-training-260526.md (MXFP4 vs NVFP4 rationale)
- 90-docs/baien/moemoekyun-precision-architecture-260526.md (inference ternary + train FP4)
- 90-docs/baien/bench-datasets-cid-manifest.jsonl (cycle 17 — train dataset substrate)
- 90-docs/baien/runpod-5090-runlog-260526.jsonl (append-only runlog — train entries added per §6)
