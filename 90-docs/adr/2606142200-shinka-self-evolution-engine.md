---
id: adr-2606142200-shinka-self-evolution-engine
title: "ADR-2606142200: Shinka — etzhayyim self-evolution engine (Robin + Co-scientist on Murakumo)"
status: proposed
doc_type: adr
topic: shinka-self-evolution-engine
authoritative: true
last_verified: 2026-06-14
priority: 7.5
axis: ml
weight: 0.75
priority_note: "Defines the recursive self-improvement loop that couples agent-capability evolution to Maxwell weight evolution on the Murakumo fleet; high reuse across every actor."
authoritative_for:
  - self-evolution-loop
  - agent-tournament-architecture
  - maxwell-frontier-efficiency-program
depends_on:
  - "2606101200"   # ibuki organism autonomy (closed beat loop + leash)
  - "2606101800"   # ibuki ecosystem (stigmergy, quorum sensing)
  - "2606111400"   # revocable leash (CACAO member-attributed autonomy)
  - "2606061000"   # Maxwell — default LLM weight (Gemma 4 E4B fine-tune)
  - "2605215000"   # Murakumo-only inference (no commercial GPU rental)
  - "2605250400"   # gemma-coder-distill recipe (peft+trl on EVO-X2 ROCm)
  - "2605242100"   # baien 4-tier ladder (edge / bonsai / server / XL)
  - "2605192100"   # Mission Charter (Tier-0 axioms, non-amendable)
related:
  - "2605241900"   # baien edge invariant (frontier-beating is NOT the edge target)
  - "2606062100"   # 3-tier immutability (Tier-0 fork-only)
external_refs:
  - "Robin: A multi-agent system for automating scientific discovery (Nature, s41586-026-10652-y; arXiv 2505.13400)"
  - "AI co-scientist (Google DeepMind, multi-agent generate-debate-evolve)"
  - "TLT — Taming the Long-Tail: Efficient Reasoning RL Training with Adaptive Drafter (MIT HAN Lab, arXiv 2511.16665) — research input for Tracks B/E"
supersedes: []
superseded_by: []
---

# ADR-2606142200: Shinka — etzhayyim self-evolution engine

**Status**: proposed (draft for Council review)
**Date**: 2026-06-14
**Deciders**: Jun Kawasaki

## Context

etzhayyim already has every *substrate* a self-evolution engine needs, but no
loop that closes them into recursive self-improvement:

| Primitive | Today | Role in self-evolution |
|---|---|---|
| **kotoba Datom log** (append-only EAVT) | live, IPNS head advancing | immutable memory + evidence + reward channel |
| **Pregel cells** (LangGraph StateGraph) | himawari 7 cells, 88 tests | composable agents (`.solve(state)->state`) |
| **ibuki beat cycle** (`replay→perceive→feel→decide→narrate→act→checkpoint`) | R3 live, 780 datoms | the orchestrator/supervisor pattern |
| **Kaizen outcome feedback** (`gh pr view --json state` → mood) | R3 live-verified | grounded, non-synthetic reward |
| **Charter gates G1–G8** | enforced by tests | hard constitutional constraint on any mutation |
| **CACAO leash** (member Ed25519 → capability) | R0 (ADR-2606111400) | autonomy is consent-bound, human-attributed |
| **Maxwell** (Gemma 4 E4B fine-tune) | R0 scaffold, `available:false` | the weight to be recursively improved |
| **Murakumo fleet** (10× Mac mini M4 + EVO-X2 ROCm) | Phase 5 live | the compute substrate |
| **Maxwell RSi pipeline** (`collect_corpus → gate_candidates → train → eval → deploy`) | corpus 125/1000, scaffold | the weight-evolution mechanism |

Two external systems demonstrate the missing loop:

- **Co-scientist** (DeepMind): a Supervisor agent coordinates six specialised
  agents — **Generation, Reflection, Ranking, Evolution, Proximity,
  Meta-review** — in a *generate → debate → evolve* cycle, with an **Elo
  tournament** (pairwise scientific debate, AlphaGo-style) selecting hypotheses
  and **test-time compute** spent mostly on verification.
- **Robin** (FutureHouse, Nature 2026): orchestrates literature agents
  (Crow/Falcon/Owl) and a data-analysis agent (Finch) in a continuous
  *hypothesis → experiment → analyse → updated-hypothesis* loop.

This ADR maps both onto etzhayyim primitives and defines **Shinka** (進化) — the
engine that evolves *agents* and *the weight they run on* together, under the
Charter, with humans retaining the merge veto.

## Decision

Stand up **Shinka** as two coupled loops sharing one substrate (the Datom log)
and one compute fabric (Murakumo). Loop A evolves **artifacts** (actors, cells,
lexicons, code, hypotheses). Loop B evolves **the weight** (Maxwell). The output
of Loop A is the training corpus for Loop B; the improved weight from Loop B
makes Loop A cheaper and stronger. This is the flywheel.

```
        ┌──────────────────── Loop A: capability (Co-scientist) ───────────────────┐
        │  Generation → Reflection → Ranking(Elo) → Evolution → Proximity → Meta    │
        │      ▲   proposals (cell/schema/code mutations)            │  PR draft     │
        │      └──────────────── Datom log (evidence) ──────────────┘               │
        └───────────────┬──────────────────────────────────────────┬───────────────┘
                        │ verified (instruction,completion) pairs   │ tournament-winner traces
                        ▼                                            ▼
        ┌──────────────────── Loop B: weight (Robin/RSi) ──────────────────────────┐
        │  collect_corpus → gate_candidates → train(EVO-X2) → eval(e7m micro) → deploy│
        │      └─────────── Maxwell vN → served Murakumo-only ───────┘               │
        └────────────────────────────┬──────────────────────────────────────────────┘
                                      ▼  better/cheaper weight feeds Loop A
```

### Loop A — Council of Agents (Co-scientist → Pregel cells)

A new actor **`shinka`** (`did:web:shinka.etzhayyim.com`, already referenced by
`70-tools/scripts/murakumo/hegemon_agent_loop.py`) runs an ibuki-style beat
cycle whose nodes are the Co-scientist roles, each a Pregel cell:

| Co-scientist agent | Shinka cell | Function | Charter gate |
|---|---|---|---|
| Supervisor | `shinka_orchestrator` | beat-cycle driver; adaptive plan → fan out cells across fleet | G6 Murakumo-only |
| Generation | `propose` | emit candidate mutations grounded in Datom-log retrieval + literature | G1 observation-only inputs |
| Reflection | `critic` | virtual peer review: correctness + **Charter G1–G8 pre-scan** (reuses `gate_candidates.py`) | G2/G3 provenance, no-PHI |
| Ranking | `tournament` | **Elo via pairwise debate**, parallelised across the 10 nodes | G6 |
| Proximity | `cluster` | dedup/diversity over proposal space (against `seen` set in log) | — |
| Evolution | `recombine` | merge/refine top-Elo proposals into stronger candidates | — |
| Meta-review | `synthesize` | write ADR draft + PR; **never auto-merge** | G7 no-server-key, G8 member-principal |

Invariants (inherited, non-negotiable):

1. **Proposals are facts, never retractions.** Every proposal, debate verdict,
   and Elo update is a `:db/add` datom — the evolution history is itself
   immutable evidence.
2. **No autonomous merge.** Meta-review produces a *PR draft*; a member
   Ed25519-signs the CACAO capability (ADR-2606111400) before any commit. The
   Council retains Lv6+ attestation for Charter-touching changes.
3. **Murakumo-only.** All inference (proposal, debate, ranking) runs on the
   fleet; commercial GPU is constitutionally prohibited (ADR-2605215000).

### Loop B — Maxwell flywheel (Robin → RSi pipeline)

Robin's *hypothesis → experiment → analyse → update* maps directly onto the
existing maxwell scripts, with the **experiment = a training run** and the
**data analysis = the microbench eval**:

| Robin stage | Maxwell RSi stage | Artifact |
|---|---|---|
| generate hypothesis | propose corpus/recipe delta | `maxwell-sft-corpus.jsonl` append |
| run experiment | `train.py` on EVO-X2 ROCm (LoRA r=16) | candidate adapter |
| analyse data | `eval.py` → `e7m bench micro` | microbench delta (pp) |
| update hypothesis | `deploy.py` gate: ≥250 steps **OR** ≥+5pp → flip `available` | Maxwell vN, provenance datom |

The corpus is fed by **Loop A's tournament winners**: every debate that produces
a verified, Charter-clean, PR-merged artifact yields one or more
`(instruction, completion)` pairs — this is the already-named "Wave 3 RSi
self-improvement loop" (currently 125/1000). Distilling the *orchestrated*
(multi-agent, frontier-class) traces back into the *single-pass* weight is the
mechanism by which Maxwell becomes efficient, not just capable (see Research
Program §F).

## Research Program — Maxwell + agents → frontier-class, efficiently, on Murakumo

**Thesis.** Frontier-class capability on a ~4B fleet weight is not reached by a
bigger model (prohibited by the edge/fleet tiering and the no-commercial-GPU
charter). It is reached by:

> **capability = (efficient small weight) × (test-time compute on the fleet) ×
> (verification/tournament) × (retrieval from the Datom log) → distilled back
> into the weight.**

This is exactly what Co-scientist and Robin demonstrate: a modest base model
plus heavy orchestration and verification beats a single frontier forward pass
on research-shaped tasks. Murakumo's 10 nodes are a *natural test-time-compute
substrate*. Tracks (each a measurable experiment, logged to the Datom log):

- **A. Fleet test-time compute.** Parallel best-of-N / self-consistency across
  the 10 Mac-mini Ollama endpoints, selected by the `tournament` cell (Elo).
  *Metric:* pass@k vs k, Elo vs node-count. *Hypothesis:* k=10 Maxwell ≈
  frontier single-pass on e7m bench.
- **B. Speculative / draft-verify across tiers, with an ADAPTIVE drafter.** baien
  (edge 1.58-bit) or a Maxwell-E2B MatFormer submodel (Track C) drafts, Maxwell
  verifies; or Maxwell drafts, EVO-X2 `llama3.3:70b` verifies the hard fraction.
  Apply **TLT** ("Taming the Long-Tail", MIT HAN Lab, arXiv 2511.16665): keep the
  drafter from going stale by **continuously retraining it on the fleet's idle
  Mac-mini cycles** to predict the current Maxwell's outputs, plus an adaptive
  rollout engine that tunes the spec-decode config to the workload. The fleet's
  ~10 idle nodes ARE the idle cycles TLT exploits; a stale static drafter is
  exactly the failure mode it fixes. Murakumo-only (the drafter trains + serves
  on-fleet, never commercial GPU). *Metric:* tok/s × accept-rate, end-to-end
  latency, drafter-staleness vs Maxwell generation.
- **C. MatFormer elastic inference.** Gemma E4B nests an E2B submodel; serve E2B
  for easy turns and E4B for hard ones, right-sizing compute per node capacity.
  *Metric:* quality/Joule per task-difficulty bucket.
- **D. Retrieval-augmented grounding.** RAG over the append-only EAVT log
  (CID-addressed, hallucination-resistant) closes the knowledge gap that
  frontier scale would otherwise buy. *Metric:* factuality on org-specific QA.
- **E. Verifier-grounded preference (DPO/RL).** Reward = Charter-gate pass +
  microbench delta + **real PR-merge outcome** (Kaizen already reads
  `gh pr state`). Outcome-grounded, never synthetic. *Metric:* win-rate on held
  pairs after preference tuning. When this reaches reasoning-RL, the rollout
  (candidate generation) is ~85% of wall-clock with long-tail stragglers — apply
  **TLT** (Track B's adaptive drafter) to the rollout to ~2× RL throughput on the
  fleet; this is TLT's primary target (it is RL-specific, NOT an SFT/M1 speedup).
- **F. Distillation flywheel (the core).** SFT Maxwell on Loop A's
  tournament-winner traces so the *orchestration collapses into the weights* —
  fewer debate rounds needed next cycle for the same quality. This is the
  recursive self-improvement: each turn the fleet needs less test-time compute
  for frontier-class output. *Metric:* rounds-to-quality over generations;
  watch for and gate against reward-hacking / mode collapse.
- **G. Fleet quantization frontier.** Per-node quant selection (MLX 4-bit /
  Metal on Mac-mini M4; ROCm for EVO-X2 training) maximising tok/s within
  unified memory. *Metric:* tok/s × quality Pareto front per node.

**Evaluation.** Extend the existing `e7m bench micro` (the deploy gate) and
`90-docs/frontier-bench-snapshot-260523.md` into a standing harness that scores
*orchestrated-Maxwell* against the frontier snapshot on identical tasks. The
honest claim is per-task-class, not global ("frontier-beating is explicitly not
the edge target" — ADR-2605241900 still holds for baien; Shinka's target is
*frontier-class on the org's own task distribution*, via orchestration).

## Staged rollout

- **S0 (this ADR):** name + register `shinka` actor; scaffold the 7 cells as
  `.solve()` stubs reusing himawari's StateGraph pattern; wire `propose`/`critic`
  to existing `collect_corpus.py` / `gate_candidates.py`. No autonomy.
- **S1:** Loop A dry-run — proposals + Elo tournament on Maxwell-fallback
  (gemma) over a fixed task set; Meta-review emits PR drafts for human review.
  Land Research Track A (fleet best-of-N) + the standing eval harness.
- **S2:** Couple loops — tournament winners append to `maxwell-sft-corpus.jsonl`;
  first EVO-X2 fine-tune; microbench gate; flip Maxwell `available:true` (M1)
  iff the gate **and** Gemma-ToU weight-licensing check (open in ADR-2606061000)
  both pass.
- **S3+:** Tracks B–G; CACAO-leashed semi-autonomous proposal cadence under
  Council attestation; ecosystem-style quorum (≥2/3) to promote a generation.

## Consequences

**Positive.** Closes the recursive loop on infrastructure that already exists;
turns the fleet into a test-time-compute engine; gives Maxwell a principled path
to frontier-class *efficiency* without violating the no-commercial-GPU charter;
every evolutionary step is immutable, attributable, and Council-gated — the
constitutional differentiator vs. Co-scientist/Robin.

**Negative / risks.** Reward-hacking against the microbench or PR-merge signal
(mitigate: diverse verifier lenses + held-out eval + mode-collapse gate);
compute pressure on a 10-node fleet (mitigate: MatFormer right-sizing, off-peak
scheduling); Gemma weight-licensing still unresolved (blocks S2 flip); autonomy
drift (mitigate: CACAO leash + no-auto-merge invariant remain hard gates).

## Open questions

1. Gemma Terms-of-Use inheritance on distilled Maxwell weights (carried from
   ADR-2606061000) — must clear before any `available:true` flip.
2. Elo-tournament debate cost on the fleet vs. quality gain — needs S1 numbers.
3. Whether the distillation flywheel (Track F) needs a periodic
   "frontier-teacher" snapshot (one-off, training-only, Charter §2(i) carve-out)
   to avoid self-distillation plateau, or whether outcome-grounded preference
   (Track E) suffices.
4. TLT (Tracks B/E) was demonstrated on homogeneous GPU clusters where the idle
   cycles live *inside* the RL training cluster during rollout stalls; our
   substrate is heterogeneous (single EVO-X2 ROCm trainer + 10 Mac-mini Metal
   inference nodes). Open: does the adaptive-drafter trainer port cleanly to
   "drafter retrains on Mac-mini idle cycles while EVO-X2 rolls out", and is the
   ROCm/Metal split a help (more truly-idle cycles) or a coordination cost? No
   public code (paper-only) — a from-scratch ROCm/MLX implementation is required.
