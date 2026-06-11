---
id: adr-2605263000-founder-lv7-emergency-authorization-runpod-5090-bench-interim
title: "Founder Lv7+ Emergency Authorization — RunPod RTX 5090 bench-eval interim use before §2(i)(2) ratification (2026-05-26)"
status: accepted-by-founder-pending-council-post-ratification
doc_type: adr
topic: founder-lv7-emergency-authorization-runpod-bench
authoritative: true
last_verified: 2026-05-26
priority: 9.0
axis: constitutional
weight: 0.9
priority_note: "Founder Lv7+ unilateral emergency authorization invoked. ADR-2605262200 §4 explicitly RESERVED this path; today (2026-05-26) Founder invokes it for limited bench-eval use. Council Lv6+ post-ratification recording required at P2 vote (2026-06-19+)."
authoritative_for:
  - "Interim use of RunPod RTX 5090 for baien-moemoekyun bench-eval (inference, NOT train) before P4 amendment effective date"
  - "Scope, time-bound, transparency requirements of this emergency authorization"
  - "Procedural commitment to Council post-ratification at next vote"
depends_on:
  - adr-2605262200-charter-rider-2i-baien-train-rental-carveout
  - adr-2605262300-baien-moemoekyun-r2-runpod-b200-train-architecture
  - adr-2605192300-etzhayyim-bootstrap-council-five
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
related:
  - moemoekyun-bench-plan-260526
  - 90-docs/baien/moemoekyun-bench-cycle{1,2,3}-260526.md
  - /tmp/runpod-5090-bench-bringup.sh (bringup script, NOT committed to repo)
supersedes: []
superseded_by: []
---

# ADR-2605263000: Founder Lv7+ Emergency Authorization — RunPod RTX 5090 bench-eval interim use (2026-05-26)

**Status**: accepted-by-founder-pending-council-post-ratification
**Date**: 2026-05-26 ~15:50 JST
**Authority invoked**: Founder Seat 1, Lv7+ (Jun Kawasaki) per ADR-2605192300 + Charter §0.1
**Constitutional weight**: invokes the emergency path that ADR-2605262200 §4 explicitly documented as "NOT taken"

# Context

ADR-2605262200 proposed the CHARTER-RIDER §2(i) train carve-out amendment for `baien-server-*` / `baien-XL-*`. The amendment is in `proposed-pending-council-ratification` status with earliest effective date P4 = 2026-07-19 (after Council Lv6+ vote at 2026-06-19+ + 30-day public objection).

ADR-2605262200 §4 documented:

> "Charter Rider §2(i) は明示的 amendment threshold (Lv6+ supermajority + 30-day) を持つ。Founder Lv7+ (Seat 1, Jun Kawasaki) は単独で expedited authorization を発出する権限を主張可能だが、本 ADR ではその経路を**取らない**。"

The reasoning given for NOT taking it included:
1. Founder unilateral override 緊張 Council-governed 自己定義
2. R1.4 可能 EVO-X2 で完遂可能、R&D 損失は 1.5 ヶ月程度
3. institutional integrity ledger 優先

**Today (2026-05-26 ~15:50 JST)**, /loop cycle 4 of moemoekyun bench-eval work reached an impasse:

- EVO-X2 still offline (operator power-on pending, blocker since 2026-05-26 morning)
- HumanEval+ smoke evaluator on Mac MPS produced 0/10 pass@1 across 2 retries
  (markdown fence + prompt engineering failed; root cause = need chat-template
  or proper harness like bigcode-evaluation-harness, NOT available in venv stack)
- MMLU-Redux 5-shot baseline on Mac MPS showed only +0.67pp lift (cycle 2 finding)
- Phase 1 canonical 5-shot lm-eval-harness baseline blocked on EVO

Founder provisioned RunPod RTX 5090 pod and directs `これで進めて` (proceed with this).
Strict reading of §2(i)(1) inference invariant prohibits this. Therefore Founder
invokes the §4-reserved emergency authorization to record the deviation transparently.

# Decision

## §1 Authorization scope

Founder Seat 1 Lv7+ HEREBY AUTHORIZES, subject to the limits below, **temporary
use of commercial GPU rental (RunPod RTX 5090, IP 157.157.221.30, port 51691)
for baien-moemoekyun bench-eval (inference) workloads** during the window
2026-05-26 ~15:50 JST → P4 amendment effective date (~2026-07-19).

### §1.1 Permitted

- Run lm-eval-harness Phase 1 (MMLU-Redux 2.0 / MMLU-Pro / GPQA-diamond / ARC / etc.) on `microsoft/bitnet-b1.58-2B-4T-bf16` and any moemoekyun checkpoints
- Run evalplus HumanEval+ / MBPP+ with proper chat template + extraction
- Run AIME26 / HMMT generative math eval (per cycle 4 plan)
- Run LiveCodeBench v6 exec-graded eval
- Run inference for **bench-quality data collection** (eval traces, error analysis)

### §1.2 NOT permitted (still prohibited)

- Production / external-facing inference serving (still Murakumo-only per §2(i)(1))
- Training / fine-tuning of any artifact (waits for §2(i)(2) ratification at P4)
- Use for any actor OTHER than baien-server-moemoekyun (other actors remain Murakumo-only)
- Continuous rental > 24 hours per session (§2(i)(2)(5) inherited cap)
- Single-session cost > $50 USD (tighter than ADR-2605262300 §6 $200, given inference-only and smaller scope)
- Cumulative pre-P4 cost > $200 USD (Founder self-imposed budget; if exceeded, halt and re-record)

### §1.3 Transparency requirements (MUST satisfy)

1. **Pre-flight log**: Pre-bench-run record at `90-docs/baien/runpod-5090-runlog-260526.jsonl`
   with (timestamp, planned tasks, expected wall, expected USD, dataset CIDs from substrate)
2. **Post-flight log**: Post-bench-run append to same JSONL with
   (actual wall, actual USD, output JSONLs path, results summary)
3. **No HF Hub publication** of moemoekyun bench outputs derived from this rental window — fleet-internal use only until P4 (matches G13 distribution boundary)
4. **Council post-ratification recording**: this ADR + each runlog entry MUST be submitted to Council at the next vote (2026-06-19+) for retroactive ratification or objection
5. **Cost log on kotoba-datomic (deferred to P4)**: full per-rental attestation Lexicon
   (`com.etzhayyim.train.rentalCostLog`, ADR-2605262300 §5) cannot fire yet
   (PDS emit dry-run only) — substitute = the `runpod-5090-runlog-260526.jsonl` file

### §1.4 Time bound

This authorization expires at **min(P4 amendment effective date, 2026-07-19, $200 cumulative cost)**.

If P4 is delayed (Council vote slip / objection sustained), this authorization
DOES NOT auto-extend — Founder must issue a new ADR with extension justification.

## §2 Constitutional reading

§2(i)(1) inference Murakumo-only is the **strict** rule. Bench-eval inference is
ARGUABLY part of the train workflow (per cycle 1-3 findings: bench result feeds
R1.4 corpus rebalance decision → bench-eval IS train-cycle infrastructure).
However, the §2(i)(2) proposed amendment text restricts the carve-out to
"gradient-bearing workloads", which by strict reading excludes bench-eval
inference.

Founder reads this as **textual ambiguity needing Council clarification**:
- Either §2(i)(2) text should be amended to include "bench-eval inference
  supporting train workflows on the carved-out tier"
- Or §2(i)(1) should be clarified to exclude self-training-loop bench-eval
- Or this Founder Emergency ADR stands as the documented gap-filler

At the 2026-06-19+ Council vote, the bundled package SHOULD include:
1. ADR-2605262200 ratification vote (the original train carve-out)
2. This ADR (2605263000) post-ratification recording
3. (optional) amendment to clarify §2(i)(1)/(2) boundary re: bench-eval

## §3 Procedural commitments

| Phase | Action |
|---|---|
| P0 (today, 2026-05-26) | This ADR commits to repo; runpod-5090-runlog-260526.jsonl scaffold (pre-flight) emitted |
| P1 (2026-05-26 → P4) | Each bench-eval run on 5090 logs to runpod-5090-runlog-260526.jsonl (post-flight) |
| P2 (2026-06-19) | Bootstrap Council bootstrap complete; submission package prepared |
| P3 (P2+ Lv6+ vote) | Council votes on ADR-2605262200 + ADR-2605263000 + (optional) clarification amendment |
| P4 (P3+30 days) | If ratified: ADR-2605262200 effective + this ADR recorded as accepted-by-council; if rejected: rotate API key, halt RunPod use, rotate to capex path (MI300X / EVO cluster expansion) |

## §4 Reversibility

- If Council REJECTS this emergency authorization at P3 vote:
  - All bench outputs from this rental window remain in religious-corp substrate (no external publication occurred per §1.3.3 G13 inheritance)
  - Founder accepts retroactive reprimand recorded on kotoba-datomic
  - Future emergency authorizations require pre-Council notification (new ADR + 7-day public notice)
- If Council RATIFIES: this ADR's status flips `accepted-by-council` and bench outputs become part of canonical moemoekyun baseline

## §5 Risk acknowledgment

Founder acknowledges:
1. **Institutional integrity cost**: Council-governed self-definition (per Charter §0) is structurally weakened by Founder unilateral action
2. **Slippery slope**: this sets precedent that "urgent R&D need" can override §2(i) outside formal amendment threshold
3. **Mitigation**: the ADR-2605262200 §4 path was specifically reserved AND this invocation is documented + bounded + retroactively-reviewable
4. **Counterfactual**: without this authorization, cycle 4-N of /loop runs would produce no canonical bench numbers until 2026-07-19+, with no actionable improvement signal feeding back into R1.4 corpus design

The Founder judges the institutional cost acceptable given:
- Explicit pre-documentation in ADR-2605262200 §4 ("path RESERVED")
- Tight scope (bench-eval only, NOT train; baien-server-moemoekyun only, NOT other actors)
- Hard budget cap ($200 USD cumulative)
- Hard time cap (~P4 ~2026-07-19)
- Transparent runlog requirement
- Council retroactive review committed

## §6 Pre-flight runlog scaffold

`90-docs/baien/runpod-5090-runlog-260526.jsonl` — append-only JSONL emit per
bench run. First entry (pre-flight, this ADR commit):

```json
{
  "schema": "etzhayyim.baien.runpod-emergency-runlog.v1",
  "adr": "ADR-2605263000",
  "ran_at": "2026-05-26T06:50:00Z",
  "phase": "pre-flight authorization",
  "vendor": "runpod-secure",
  "gpu_model": "nvidia-rtx-5090",
  "gpu_count": 1,
  "pod_endpoint": "ssh://root@157.157.221.30:51691",
  "planned_tasks": [
    "lm-eval-harness Phase 1 (MMLU-Redux 2.0 + MMLU-Pro + GPQA-diamond + ARC) 5-shot",
    "evalplus HumanEval+ (chat template + proper extraction)",
    "AIME26 + HMMT generative (per moemoekyun-bench-plan-260526.md Phase 2)",
    "LiveCodeBench v6 exec-graded smoke"
  ],
  "expected_wall_minutes": 120,
  "expected_usd_cost": 5,
  "cumulative_wall_minutes_pre_p4": 0,
  "cumulative_usd_cost_pre_p4": 0,
  "founder_did": "did:web:jun.etzhayyim.com",
  "founder_signature_method": "git commit signed by Jun Kawasaki <04.feasts_minded@icloud.com>",
  "council_post_ratification_target": "2026-06-19+"
}
```

# Consequences

## Positive

- Cycle 4-N of /loop unblocked, canonical bench numbers achievable today instead of waiting until 2026-07-19
- R1.4 corpus rebalance (math weakness, code generation) gets quantitative signal NOW from real lm-eval-harness 5-shot + evalplus runs
- Bench substrate (Phase 1-3 datasets pinned cycles 1-3) gets actual eval coverage
- Founder Lv7+ emergency path is now documented + invoked, creating precedent for future (rare) emergency situations

## Negative

- §2(i)(1) inference invariant has its first documented violation (bench-eval interpretation pending Council clarification)
- Institutional integrity: Council-governed posture weakened by precedent
- Slippery-slope risk: future bench needs may invoke same emergency path for non-essential reasons

## Open

- Council clarification at P3 of §2(i)(1)/(2) boundary re: bench-eval inference
- Whether to bundle a §2(i) amendment proposal extending the carve-out to bench-eval explicitly
- Whether to roll back any specific bench outputs if Council rejects post-ratification

# Alternatives Considered

| Option | Verdict |
|---|---|
| Wait until P4 (2026-07-19) for amendment ratification | Rejected — cycle 4-N /loop blocked for 1.5 months; R1.4 corpus design lacks bench signal |
| EVO-X2 power-on + retry | Rejected (provisional) — operator action pending all day, no ETA |
| Capex purchase (MI300X / additional EVO units) | Rejected for IMMEDIATE work — capex lead time multiple weeks; Founder will pursue as long-term per ADR-2605262200 §"Capex breakeven" |
| Use a different rented GPU vendor (Lambda / CoreWeave) | Equivalent — §2(i)(1) prohibits all commercial rental inference equally; same emergency authorization scope would apply |
| Continue Mac MPS smoke-only | Rejected — cycle 4 demonstrated this hits structural limits (HumanEval+ 0/10 due to harness missing, 5-shot loglikelihood near-flat) |
| Skip bench entirely until R1.4 train completes | Rejected — without baseline, R1.5 commit_gate (Δ ≥ +3pp) has nothing to compare against |

# References

- ADR-2605262200 §4 (Founder Lv7+ emergency authorization explicitly reserved, NOT taken at that time)
- ADR-2605262300 (R2+ RunPod B200 train architecture — informs cost cap + Lexicon spec)
- ADR-2605192300 (Bootstrap Council mechanics — sets P2 vote at 2026-06-19+)
- CHARTER-RIDER.md §2(i) (current text, amendment-pending notation per ADR-2605262200)
- 90-docs/baien/moemoekyun-bench-plan-260526.md (Phase 1-5 plan being executed)
- 90-docs/baien/moemoekyun-bench-cycle{1,2,3}-260526.md (cycle docs showing the impasse)
