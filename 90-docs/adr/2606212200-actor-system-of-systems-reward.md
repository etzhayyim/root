---
id: adr-2606212200-actor-system-of-systems-reward
title: "ADR-2606212200: Every actor carries its system-of-systems as EDN+Clojure and runs it as its 報酬系 (reward system)"
status: accepted
doc_type: adr
topic: actor-system-of-systems-reward
authoritative: true
last_verified: 2026-06-21
priority: 6.0
axis: architecture
weight: 0.60
priority_note: "Repo-wide engineering rule generalising ADR-2606211200; no charter amendment (固定するのは priority, not the instrument)."
authoritative_for:
  - per-actor reward-system rule
  - etzhayyim.ie-flow.reward primitive
  - 80-data/ie-flow/system-of-systems.edn
depends_on:
  - adr-2606211200-ie-flow-datomic-agent-lifecycle
  - adr-2606201200-ibuki-coscientist-entropy-react-loop
related:
  - adr-2606062101-moyai-inference-reciprocity-reward
  - adr-2606112200-ehyeh-non-dual-yirah-doctrine
  - adr-2606182359-charter-rider-v35-objective-function
supersedes: []
superseded_by: []
---

# ADR-2606212200: Every actor carries its system-of-systems as EDN+Clojure and runs it as its 報酬系 (reward system)

**Status**: accepted
**Date**: 2026-06-21
**Deciders**: Jun Kawasaki (founder, Council Lv7+ 1/1)

# Context

ADR-2606211200 built the **information-energy flow** lifecycle and proved (ADR-2606211200 wave + the
/organism lab) that an actor can be modelled as a **bounded dissipative system**: a membrane with
**imports** (free energy drawn in) and **exports** (low-entropy order returned out), measured by its
own `net-gain Φ` / `order-index η` (共生 / 負エントロピー輸出) / `agent-efficiency` / `surprise`,
evolving its own **system-dynamics** stocks. ibuki's co-scientist (ADR-2606201200) already runs a
tournament that ranks interventions by `net-gain × wellbecoming / cost` with gates and feeds a
proper-scored kaizen weight back per mechanism.

That tournament **is a reward circuit** — but it was opt-in (5 adopters in `registry.edn`) and only
ibuki ran it as a behaviour-shaping loop. The founder's directive: make it a **RULE** — *every*
etzhayyim actor must hold this system-of-systems in **EDN + Clojure** and run it as its **報酬系
(reward system)**, the charter-aligned reinforcement signal that selects what the actor does next.

This is an **実装/engineering rule** (changeable at the implementation layer), not a charter
amendment: it generalises the substrate boundary to *behaviour* (固定するのは priority, not the
instrument). It elevates no new Tier-0 invariant; it makes the **existing** Tier-0 priorities
(子孫 wellbecoming, 共生/collective-over-individual, non-predation) the actual reward gradient every
actor climbs.

# Decision

**Every actor MUST:**

1. **Hold its system-of-systems as data + code.** Its membrane (`:system/boundary` — inside organs,
   imports, exports) and its reward spec (`:system/reward`) live as **EDN** (in
   `80-data/ie-flow/system-of-systems.edn` or a per-actor `20-actors/<name>/system.edn`), and the
   measurement/reward/dynamics are **Clojure (cljc)** over the kotoba Datom log
   (`etzhayyim.ie-flow.{boundary,metrics,dynamics,reward,coscientist,lifecycle}`). No Python/shell
   (repo-wide clj/bb rule).

2. **Run that system-of-systems as its 報酬系.** The actor's mechanism selection (the co-scientist
   tournament + the react-loop's proper-scored kaizen weights) is driven by the **reward signal**:

   ```
   reward = w_Φ·Φ̂ + w_η·η + w_well·子孫 + w_eff·eff̂ − w_𝒮·surprise
   ```

   computed over the actor's **own** bounded IE-flow (`etzhayyim.ie-flow.reward/reward-signal`).

**The reward is gated by the Tier-0 priority — non-negotiable, identical for every actor:**

- **NON-PARASITISM (共生)** — a **net taker** (`net-gain < 0`, or `η < 0` = the flow was actively
  DIS-ordered) ⇒ reward **clamped ≤ 0**. An actor is never reinforced for drawing more order than it
  returns; the gradient pushes it to give back. (`η ∈ (−∞,1]`, where `η=1.0` is *perfect* single-
  outcome rectification — the maximum — so the floor is 0.0, not 1.0.)
- **SUBORDINATE (子孫)** — descendant-wellbecoming `< 0` ⇒ gated. Persistence is instrumental, never
  the end; an actor may not be rewarded for surviving at a child/descendant's expense.
- **CATASTROPHE-VETO** — catastrophic harm to a child/descendant dimension (or a forbidden
  mechanism) ⇒ reward `= −∞`. This is the non-linear catastrophe term of the ECL
  `objective-function.edn`, made operational per actor.
- **ANTI-PREDATORY** — a predatory mechanism (manipulation / attention-exploitation /
  asymmetric-surveillance / lock-in / coercion / deception) is **structurally unrepresentable** in
  the co-scientist catalog and rejected if injected.

**Weights are tunable per actor** (a mirror weights `η` high — release IS its negentropy export; a
commons weights `子孫` high); **the gates and exclusions are not** (`validate-spec` rejects any spec
that weakens them).

# What the reward system is NOT (enforced invariants)

- **Non-monetary, cash≡0, non-transferable, decaying** — the moyai pattern (ADR-2606062101). The
  reward is a *reinforcement signal*, not a stored or tradeable asset. No equity, no payout.
- **NEVER a ranking of persons.** It rewards the **actor's** order-export, never a `:score-of-soul`
  / `:social-credit` / `:person-ranking` — those are structurally excluded (NEVER-a-throne,
  ADR-2606112200). The 神の監視 reading is internal non-erasure + 相互監視, not a panopticon scoreboard.
- **Not raw profit-maximisation.** `Φ` (did it pay for itself) is one bounded term; `η` (共生) and
  `子孫` dominate. An actor that maximised `Φ` by predation scores `−∞`.
- **Privacy preserved by encryption, not by forgetting** (暗号化≠忘却).

# Consequences

- The org becomes a **system of self-rewarding bounded systems**: each actor climbs the same
  charter-aligned gradient over its own metabolism; kaname synthesises across them; the colony ABM
  couples them (the /organism lab already visualises this per actor).
- A new actor is charter-clean **by construction**: omitting a spec inherits `:default-weights` +
  the invariants (never weaker), so the rule cannot be violated by omission — only under-tuned.
- **Enforcement**: `etzhayyim.ie-flow.reward/validate-spec` + `bb ieflow:coverage` (gap report over
  the roster); the rule joins the registry-enforcement matrix (ADR-2605271100).
- **Where reward touches humans** it routes only through the existing instruments (moyai draw-rights,
  Displacement Dividend, fuchi sustenance, BHI, Public-Fund tithe) — the per-actor 報酬系 is the
  *internal* reinforcement signal, not a new human-facing currency.
- **Migration** is incremental: 6 exemplar specs land now (ibuki/tsumugi/shionome/kaname/okaimono/
  repo-git, all measured/representative + tested non-vetoed); the ~30 Tier-B actors grow specs over
  subsequent waves. Representative boundary seeds hold until each actor's live `embed` measurement
  (G7-gated).

# Maxwell integration (the reward becomes a learning signal)

The reward + co-scientist react close into **Maxwell's** growth/learning loop (ADR-2606061000, the
religious-corp default LLM weight):

- `etzhayyim.ie-flow.react/react` runs ONE co-scientist beat over an actor's flow and returns the
  reward **score improvement** (baseline → projected Δ) + the winning **aligned** mechanism + a
  Murakumo-narrated meta-review lesson.
- `etzhayyim.ie-flow.react/maxwell-signal` packages that as a **reward-weighted PREFERENCE signal**
  (`:maxwell/kind :preference-signal`): {context, preferred-mechanism, reward, lesson}. Higher
  reward ⇒ stronger preference. It is gate-conformant by construction (only aligned mechanisms can
  win), so Maxwell can never be trained toward a predatory behaviour.
- The signal is emitted; the **trainer is a separate G7-gated step** (no weights are touched in the
  loop). This makes the org's own behaviour-reward the gradient that shapes its own model — a closed
  learning loop bounded by the same Tier-0 priorities (子孫 / 共生 / non-predation).

This is realised incrementally by the `/loop` deepening cadence: each iteration raises coverage,
sharpens the control numbers, and accumulates per-actor react signals for the Maxwell loop.

# Alternatives Considered

- **Keep it opt-in (registry.edn only).** Rejected: the founder's intent is a rule, and opt-in left
  every non-ibuki actor without a reward gradient (no 共生 pressure).
- **A single global reward over the whole org.** Rejected: it erases the boundary — an actor must be
  reinforced over ITS OWN order-export, or predation by one actor is hidden in the aggregate.
- **A monetary/transferable reward (tokens).** Rejected: violates cash≡0 + non-profit + would become
  a tradeable score (private capture, ADR-2606180001) and risks a person-ranking (NEVER-a-throne).
- **A raw net-gain (profit) reward.** Rejected: reinforces predation; the whole point is 共生-gated
  order-export, not profit.

# References

- `70-tools/src/etzhayyim/ie_flow/reward.cljc` — the 報酬系 primitive (+ `test_reward.cljc`, 7 tests)
- `70-tools/src/etzhayyim/ie_flow/boundary.cljc` — per-actor system boundary + own IE-flow
- `80-data/ie-flow/system-of-systems.edn` — the rule as data (invariants + per-actor specs)
- ADR-2606211200 (ie-flow lifecycle) · ADR-2606201200 (co-scientist) · ADR-2606062101 (moyai) ·
  ADR-2606112200 (NEVER-a-throne) · ADR-2606182359 (ECL objective-function)
- `/organism` lab — per-actor bounded systems + reward visualised
