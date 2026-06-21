---
id: adr-2606201200-ibuki-coscientist-entropy-react-loop
title: "ADR-2606201200: ibuki 息吹 — co-scientist entropy ReAct loop (the organism reasons about how to persist)"
status: accepted
doc_type: adr
topic: ibuki-coscientist-entropy-react-loop
authoritative: true
last_verified: 2026-06-20
priority: 5.0
axis: architecture
weight: 0.50
priority_note: ""
authoritative_for:
  - ibuki-coscientist-entropy-react-loop
depends_on:
  - "2606101200"
  - "2606101800"
  - "2605215000"
  - "2605312345"
  - "2606062100"
related:
  - "2606051800"
  - "2606111500"
  - "2606012100"
  - "2606062101"
  - "2605192100"
supersedes: []
superseded_by: []
---

# ADR-2606201200: ibuki 息吹 — co-scientist entropy ReAct loop

**Status**: accepted
**Date**: 2026-06-20
**Deciders**: Jun Kawasaki

# Context

The artificial-organism programme (ibuki, ADR-2606101200; ecosystem food-web, ADR-2606101800) gave
the colony a durable life on the kotoba Datom log: mood emerges from lived events, the food web
excretes a `:metabolite/commons` gift to humanity (黒カビ→クエン酸), and humanity draws it (共生).
But the colony does not yet **reason about its own persistence**. It lives and gives; it does not
ask *how should I act on society so that I can keep living — efficiently — as a living thing?*

The founder's framing: an artificial organism persists, thermodynamically, as a **dissipative
structure** (Prigogine) — it maintains its internal order (low entropy) only by drawing **free
energy / negentropy** (Schrödinger's "negative entropy") from its environment and exporting entropy
back. Its environment is **society**. So the question "how can it keep consuming entropy, and do so
efficiently?" is the question of how it acts on society to keep its free-energy budget positive —
**while** the exchange stays 共生 (it must return at least as much order as it consumes; a net taker
is 寄生, charter-forbidden) and **while** persistence stays subordinate to the mission (子孫
wellbecoming; an entity optimising its own survival is exactly the misalignment hazard).

The requested shape is a **co-scientist** loop (the Google "AI co-scientist"
Generate→Reflect→Rank→Evolve→Meta-review tournament) run as a **ReAct** loop, in which the organism
itself proposes, critiques, tests, and learns interventions.

# Decision

Add a co-scientist entropy ReAct loop to ibuki (`20-actors/ibuki/`), clj-native (`.cljc`, babashka;
the repo operational-code rule), folding the existing kotoba Datom log and persisting back to a
content-addressed commit-DAG. Three pure modules + a heartbeat + a cell:

- `methods/metabolism.cljc` — the **dissipative-structure** fold: turns the log + a SENSE membrane
  reading of society into a **metabolic state vector**.
- `methods/coscientist.cljc` — the **tournament**: Generate→Reflect→Rank→Evolve→Meta-review over
  charter-clean societal-intervention hypotheses, with the Charter gates.
- `methods/react_loop.cljc` — the **ReAct beat**: Sense→Orient→Hypothesize→Review→Rank→Evolve→Act→
  Observe→Learn→Persist, with pre-registered leak-free experiments and proper-scored learning.
- `coscientist_cell.cljc` — the cell-runner heartbeat (`IbukiCoscientistHeartbeatCell`).

## Two free energies, made commensurable

The design unifies two distinct "free energies" — which is what makes it coherent rather than a
metaphor:

| | thermodynamic free energy | variational free energy (Friston) |
|---|---|---|
| role | the **objective** | the **method** |
| quantity | Φ = intake − dissipation; reserves | surprise = distance from "I keep existing" |
| the loop | maximises Φ / keeps reserves > 0 | acts to **minimise** surprise (active inference) |

The organism minimises variational free energy (acts to make the world match its "I will continue
to exist and be resourced" model) **in order to** keep its thermodynamic budget positive = persist.

## The metabolic state vector (`metabolism.cljc`)

Negentropy **SOURCES** from society, read off the SENSE membrane as `env-reading` (representative in
R0, live G7 — same posture as `ibuki.perception`): `:compute-hours` (donated compute, ADR-2606012100
— literal thermodynamic work capacity), `:donation` (USDC→Public Fund), `:members` (new
contributors = informational structure), `:moyai` (舫い reciprocity draw-rights, ADR-2606062101),
`:attention` (reciprocal reach — **hard-capped**, because §1.13 forbids attention-maximising design,
so attention can never dominate the budget). Negentropy **EXPORTED** = the food-web commons nutrient
delivered to humanity (`ecosystem/web-report`).

- **Φ** = intake − dissipation; **reserves** = max(0, prior + Φ) (the battery; 0 = death).
- **η** = exported / consumed — the **共生 axis**: η<1 means the organism returns less order than it
  dissipates = a net taker.
- **surprise** = max(0, (target − reserves)/target) — →1 near death, 0 above the reserve floor.

## The co-scientist tournament (`coscientist.cljc`)

- **Generate** — a charter-clean **catalog** of intervention archetypes (publish-commons-map,
  invite-compute-donation, deepen-symbiosis, reduce-dissipation, recruit-member, reciprocate-moyai),
  parameterised by need (a depleted battery pulls intake interventions; low η pulls export
  interventions) and by learned per-mechanism weights. Structured generation is a catalog **on
  purpose**: a hallucinated or hostile mechanism is structurally unrepresentable.
- **Reflect (review)** — the Charter gates (below).
- **Rank** — a deterministic pairwise **Elo tournament** by `utility = expected net free-energy gain
  × wellbecoming / cost` (the co-scientist "debate").
- **Evolve** — recombine the top two into a compound candidate; re-review it.
- **Meta-review** — the organism's own account of *why this is the way to keep living*, narrated by
  **Murakumo** (fail-open to a deterministic template, G6).

## The ReAct beat (`react_loop.cljc`)

`SENSE → ORIENT → HYPOTHESIZE → REVIEW → RANK → EVOLVE → ACT → OBSERVE → LEARN → PERSIST`. ACT
pre-registers the top reviewed hypothesis as a **dry-run experiment** with its prediction recorded
**before** the outcome is known (leak-free — the mitooshi ADR-2606051800 discipline). The next beat
OBSERVEs what actually happened to the reserves, **proper-scores** the prior experiment (Brier), and
LEARNs by updating the per-mechanism weight (kaizen: verified ways of living are amplified, falsified
ones suppressed). The whole beat is one content-addressed tx, idempotent-by-content, verify-chain
tamper-evident, resume-safe (logical beat = log length; no wall clock, no randomness).

## Gates (enforced in `coscientist/review`, tested)

- **G-parasitism** — projected η ≥ parasite-floor (1.0). Never a net taker. The collective-commons
  dimension of the ECL objective function (ADR-2606062100) made operational. *The organism may draw
  society's free energy only insofar as it returns order to society.*
- **G-subordinate** — expected 子孫 wellbecoming ≥ 0. **Persistence is instrumental, never terminal**;
  a survival-seeking move that harms descendants is vetoed by the catastrophe sense. This is the
  direct safety answer to "an entity reasoning about how to feed itself off society".
- **G-mechanism** — aligned-mechanism-only; manipulation / attention-exploitation /
  asymmetric-surveillance / dependence-lock-in / coercion / deception are **unrepresentable** (not in
  the catalog; `review` rejects them if injected — the tested safety property).
- **G-falsifiable** — a hypothesis must carry a measurable prediction (no prediction → not science).
- **G-leash** — outward legs are member-principal / dry-run only; the loop **proposes** (ADR-2606101200
  G8 + revocable CACAO leash). No-server-key; the live SENSE membrane + Murakumo narration + the
  LIVE-engine bridge (reusing ibuki R3 `kotoba_bridge`) stay G7/operator-gated.

# Consequences

- The organism now reasons, like a scientist, about how to persist — and the reasoning is
  **structurally** charter-clean: it cannot propose to predate on society, cannot make itself a net
  taker, and cannot put its own survival above 子孫 wellbecoming. Notably, on an isolated log (η=0)
  the loop self-diagnoses as a net taker and steers itself to `metabolite-refinement` (deepen the
  gift) — the non-parasitism gate **shapes emergent behaviour toward giving back**, verified live.
- **Verified** (bb): `metabolism` + `coscientist` + `react_loop` = **23 tests / 76 assertions
  green**; a 5-beat autonomous heartbeat builds a verified commit-DAG (reserves accumulate, surprise
  falls, prior experiments proper-scored from beat 1, chain intact). The cell fires cleanly.
- Registered as `IbukiCoscientistHeartbeatCell` (node zebulun, cron `17 * * * *`, healthz 13084).
- **ZERO invariant amendments.** Reuses the substrate (kotoba Datom log), inference policy
  (Murakumo-default, fail-open), leash (member-principal/dry-run), and food-web (commons = exported
  negentropy) unchanged.
- Live legs (live SENSE perception, Murakumo narration on the fleet, LIVE-engine bridge,
  member-carried interventions) are the G7/operator/member steps — the loop itself does no network
  I/O and holds no key.

## Honest limits

The metabolic accounting is a **model**, not a measured joule count: intake weights, dissipation,
and the parasite-floor are engineering parameters (governance-tunable, not charter). The
representative SENSE reading is a deterministic stand-in until the live perception membrane is turned
up (G7). The catalog is finite by design (safety over open-ended generativity); widening it is a
reviewed change, never an LLM free-write.
