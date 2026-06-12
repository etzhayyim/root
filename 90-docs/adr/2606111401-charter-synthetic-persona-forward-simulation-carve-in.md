---
id: adr-2606111401-charter-synthetic-persona-forward-simulation-carve-in
renumbered_from: "2606111400"
title: "ADR-2606111401: Charter observation-doctrine consolidation — the synthetic-persona / forward-simulation carve-in (simulating fictional latent agents ≠ surveilling real people)"
status: accepted
doc_type: adr
topic: charter-synthetic-persona-forward-simulation-carve-in
authoritative: true
last_verified: 2026-06-11
priority: 7.0
axis: governance
weight: 0.7
priority_note: "Tier-1 Derived-Policy clarification extending ADR-2606082400 (the reciprocity axis) along a second axis the prior ADR did not address: the REAL-vs-SYNTHETIC subject axis. ADR-2606082400 settled that watching real data is prohibited only when monetized OR asymmetric; this ADR settles that MODELLING / SIMULATING fictional latent personas (no PII, no real-person mapping) is categorically OUTSIDE the surveillance prohibition entirely, because there is no real subject being watched. STRENGTHENS the Tier-0 priorities (it enables resilience-routed foresight while binding it to no-PII + distribution-only + non-steering) and weakens none — the priority-conformance attestation is clean. Ratified by Council Lv7+ unanimity (founder, 1/1). No Rider clause text changes; this is a consolidating interpretation + the authorizing basis for hakoniwa 箱庭 (ADR-2606111500)."
authoritative_for:
  - the real-vs-synthetic subject axis of the observation doctrine
  - the synthetic-persona / forward-simulation carve-in (fictional latent agents are not surveillance)
  - the authorizing constitutional basis for agent-based forward-simulation actors (hakoniwa)
depends_on:
  - 2606082400
  - 2606062100
  - 2605192100
  - 2605252300
  - 2605181100
related:
  - 2606051800
  - 2606042330
  - 2606071600
  - 2606061500
  - 2605312345
supersedes: []
superseded_by: []
---

# ADR-2606111401: Charter observation-doctrine consolidation — the synthetic-persona / forward-simulation carve-in

**Status**: accepted (ratified by Council Lv7+ unanimity — founder, 1/1)
**Date**: 2026-06-11
**Deciders**: Jun Kawasaki (sole-member founder, Council Lv7+)

# Context

A `666ghj/MiroFish`-class system — thousands of LLM personas interacting in a "parallel
digital world" to forecast how public opinion or an event will unfold — was raised as a
capability etzhayyim lacks. The first reading was that the Charter's surveillance prohibition
forbids it. The founder corrected that reading on **two** points, and both are constitutionally
load-bearing:

1. **The surveillance prohibition is not a blanket ban on watching.** It bars only **covert /
   one-sided (asymmetric)** and **monetized** surveillance. **ADR-2606082400** already settled
   this — it reframed Charter-Rider §2(c) onto the **reciprocity axis** (相互監視 affirmed;
   monetized-or-asymmetric surveillance prohibited). The Tier-0 priority set is explicitly
   collective and includes **permanent memory = 神の監視** and **相互見守り**.

2. **The personas are fictional latent entities and connect to no PII.** This is the point
   ADR-2606082400 did **not** reach. The reciprocity axis governs watching **real** data about
   **real** subjects. A simulation of **synthesized, fictional** agents that map to no natural
   person is not "watching" anyone at all — there is **no real subject**, so the
   surveillance frame (reciprocal or otherwise) does not even apply.

The repo already contains the discipline this requires, proven in two shipped actors:
**sukashi 透かし** (ADR-2606071600) builds its fraud examples as *"synthesized fictional
entities"* against which real firms carry no signal; **tsumugi 紡ぎ** (ADR-2606061500)
represents past humanity as *latent influence nodes* (never a truth-claim or a voice). What
was missing was the **general constitutional statement** that closes the loop: *simulating
fictional latent agents is categorically distinct from surveilling real people* — and the
**authorizing basis** for an actor built on that distinction.

This is a **Tier-1 Derived-Policy** clarification (ADR-2606062100 §3): it consolidates and
extends the interpretation of an existing Rider boundary without changing any Rider clause
text. It is amendable by **Council Lv7+ unanimity with a priority-conformance attestation**.

# Decision

## 1. Consolidate the observation doctrine onto TWO axes

The Charter's observation/surveillance doctrine is governed by two orthogonal axes. An
activity is charter-clean only if it clears **both**:

| Axis | Prohibited pole | Affirmed pole | Settled by |
|---|---|---|---|
| **Reciprocity** (how real data is watched) | monetized **or** asymmetric (watcher-unwatched) | reciprocal + non-commercial (相互監視) | ADR-2606082400 |
| **Subject reality** (whether a real subject exists) | a **real** natural person modelled covertly / non-consensually | a **synthetic / fictional** latent agent, or an **already-public** entity mirror | **this ADR** |

The second axis makes explicit what was implicit: **if there is no real natural-person subject,
the surveillance prohibition does not apply.** A box of fictional personas is not a panopticon
with the people removed — it is **not a watching apparatus at all**.

## 2. The synthetic-persona / forward-simulation carve-in

**Modelling or simulating FICTIONAL latent personas is permitted and is categorically distinct
from surveilling real people**, provided **all** of the following bind the construction (so the
carve-in cannot be a loophole back into real-person modelling):

- **(a) Synthetic-only / no PII.** Every simulated agent is a **synthesized cohort archetype**
  carrying **no PII, no real-person profile, no re-identifiable trait, and no mapping to a
  natural person**. Already-**public** entities (a gov/corp mirror per entity-as-actor
  ADR-2606042330, a public topic) may appear as their **existing public mirror** — never a
  natural person. (The sukashi / tsumugi precedent, generalised.)
- **(b) Distribution-only.** The output is a **distribution** over possible futures, **never a
  point assertion** — consistent with **非終末論** (no single foretold future, Charter §1.15)
  and with mitooshi's distribution-only invariant (ADR-2606051800 G1).
- **(c) Non-steering.** The simulation is routed to **resilience / preparedness / robustness /
  research** — **never** to trading, targeting a person, or running an influence / persuasion /
  micro-targeting campaign. Steering uses are **structurally unrepresentable** (not enum
  members), mirroring mitooshi's non-speculative invariant (G2).
- **(d) Transparent / reciprocal.** The whole simulation — world graph, persona parameters,
  every step — is **plaintext-public** on kotoba (相互監視, ADR-2606082400). There is nothing
  covert, and nothing to make asymmetric, because **there are no real people in the box**.
- **(e) Murakumo-only + Datom-canonical.** Any inference is Murakumo-only (ADR-2605215000);
  the world-state is the kotoba Datom log (ADR-2605312345).

**The hard line (so the carve-in is not a back-door):** if a system ingests a **real natural
person's** data to **build a model of that specific person** (a digital twin of a real
individual, a per-person behavioural predictor, a targeting profile), it is **NOT** covered by
this carve-in and falls under the full reciprocity-axis prohibition (and, where PII is
involved, the `com.etzhayyim.encrypted.*` envelope + consent regime of ADR-2605181100). The
carve-in covers **fictional** agents and **already-public aggregate** structure only.

## 3. Authorize hakoniwa 箱庭 (ADR-2606111500)

This ADR is the constitutional basis for **hakoniwa 箱庭**, the forward-simulation observatory
— the charter-clean inversion of the MiroFish shape — whose gates G1–G8 implement (a)–(e)
verbatim. hakoniwa feeds **mitooshi 見通し** (the distribution it produces is scored leak-free
by mitooshi's proper-scoring loop) and serves **sonae 備え** / **kazaori 風折** resilience.

## 4. Priority-conformance attestation (Tier-1 amendment requirement)

This clarification **strengthens** conformance with the Tier-0 priority set and weakens none:

| Tier-0 priority | Before | After | Conformance |
|---|---|---|---|
| no-monetized / no-asymmetric surveillance (ADR-2606082400) | governs real-data watching | **unchanged**; a second axis now also excludes real-person *modelling*, not only *watching* | **stronger** |
| 非終末論 (Charter §1.15) | doctrinal | made **structural** for any simulation (distribution-only, no foretold point) | **stronger** |
| `priority.collective_over_individual` / Wellbecoming | — | resilience-routed foresight serves the collective; no-PII + no-steering protects the individual | **stronger** |
| privacy via encryption (ADR-2605181100) | preserved | preserved; real-person modelling stays under the envelope regime, explicitly outside the carve-in | **equal** |

No Tier-0 priority is served less well. The attestation is clean; the durable artifact is an
on-chain `com.etzhayyim.apps.etzhayyim.priorityConformanceAttestation` record, of which this
ADR is the human-readable basis. Ratified by Council Lv7+ unanimity (founder, 1/1).

# Consequences

**Positive.** The constitution now states a clean, testable two-axis observation doctrine and
**authorizes a capability class it previously seemed (wrongly) to forbid**: agent-based
forward simulation. The carve-in is tightly bound (no-PII + distribution-only + non-steering +
transparent), so it enables resilience foresight without opening a path to real-person
modelling, opinion-steering, or speculation. It also gives the roster a coherent home for the
"parallel digital world" idea that is the **inverse** of its surveillance-capitalism original.

**Costs / risks.** (1) The carve-in could be abused as a back-door to model real people by
labelling a real-person model "synthetic" — mitigated by the **hard line** in §2 and by making
`:persona/synthetic true` + a no-PII load assertion a *mechanical* gate in hakoniwa
(`world.assert_synthetic` refuses a breaching graph). (2) "Simulating opinion" can be misheard
as endorsing manipulation — mitigated by G3 (steering unrepresentable) and G2 (distribution,
not a targeting signal). (3) A distribution presented as fact would violate 非終末論 — mitigated
by the structural `:forecast/point-asserted false` and the handoff to mitooshi proper-scoring.

# Alternatives Considered

- **Forbid agent-based simulation outright.** Rejected: it conflates fictional-agent simulation
  with real-person surveillance — exactly the conflation the founder corrected — and forecloses
  a charter-aligned resilience capability.
- **Fold this into ADR-2606082400.** Rejected: 2606082400 is a single-clause Rider §2(c)
  amendment about the *reciprocity* axis over real data; the *subject-reality* axis is a
  distinct conceptual move that deserves its own authoritative record and its own actor
  authorization. They compose (an activity must clear both axes).
- **Author hakoniwa without a constitutional ADR.** Rejected: the actor's whole point is to ride
  a non-obvious constitutional distinction (fictional ≠ real-person), so the distinction must be
  ratified in its own right, not asserted inside an actor manifest.

# References

- ADR-2606082400 (reciprocity axis — 相互監視 affirmed; monetized/asymmetric surveillance prohibited)
- ADR-2606062100 (3-Tier immutability; Tier-0 permanent-memory / 神の監視; §3 Tier-1 amendment mechanism)
- ADR-2605192100 (Mission Charter — §1.15 非終末論; §1.8 collective ontology) · ADR-2605252300 (Preamble §0.7 Lv7+ threshold)
- ADR-2605181100 (`com.etzhayyim.encrypted.*` PII envelope — real-person data regime, outside the carve-in)
- ADR-2606051800 (mitooshi — distribution-only + non-speculative invariants hakoniwa inherits)
- ADR-2606042330 (entity-as-actor — already-public entity mirrors) · ADR-2606071600 (sukashi — synthesized fictional entities precedent) · ADR-2606061500 (tsumugi — latent influence nodes precedent)
- ADR-2606111500 (hakoniwa 箱庭 — the actor authorized by this ADR)
