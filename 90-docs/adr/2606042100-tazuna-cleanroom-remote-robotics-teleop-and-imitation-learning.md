---
id: adr-2606042100
title: "tazuna 手綱 — clean-room remote-robotics fleet operation + teleoperation + learning-from-demonstration (the Orbit-shaped gap)"
status: proposed
doc_type: adr
topic: remote-robotics-teleop-and-imitation-learning
authoritative: true
last_verified: 2026-07-12
priority: 5.0
axis: architecture
weight: 0.80
authoritative_for:
  - tazuna (手綱) remote-robotics fleet-operation + teleoperation actor charter (R0)
  - clean-room remote-robotics-ops / fleet-management interop surface (Orbit / Open-RMF / ROS 2 / MCAP / LeRobot published-API-shapes-only)
  - learning-from-demonstration (imitation / behavior-cloning) loop on the baien edge substrate
  - Transparent-Force binding for remote actuation (every teleop command = an on-chain-anchored Datom)
related:
  - adr-2606032100
  - adr-2606032130
  - adr-2606010600
  - adr-2605242600
  - adr-2605242630
  - adr-2605261800
  - adr-2606033600
  - adr-2605242000
  - adr-2605231525
  - adr-2605215000
  - adr-2605241900
  - adr-2606031600
supersedes: []
superseded_by: []
depends_on:
  - ADR-2605192100 (Mission Charter — §1.12 Transparent Force three-condition invariant)
  - ADR-2605231525 (no-server-key — member signs the actuation command, server never does)
  - ADR-2606032100 (Labor-Liberation Robotics Wave — the robot bodies tazuna operates: sanae/hataori/kiyome)
  - ADR-2606032130 (Displacement Dividend — the G2 coupling gate)
  - ADR-2605242600 (Baien federated R0 — the learning substrate the demonstration loop trains on)
  - ADR-2605215000 (Murakumo-only inference)
  - ADR-2605241900 (Baien edge-target invariant — the policy envelope)
---

# ADR-2606042100: tazuna 手綱 — clean-room remote-robotics fleet operation + teleoperation + learning-from-demonstration

**Date**: 2026-06-04
**Status**: PROPOSED
**Deciders**: Jun Kawasaki (author), Council Lv6+ (ratify R0→R1), Council Lv7+ (ratify any live-actuation force class)
**ADR Hierarchy**: Parent = ADR-2605192100 (Mission Charter, §1.12 Transparent Force + 構造的労働解放). Control-plane sibling above the robotics-body actors of ADR-2606032100 (sanae/hataori/kiyome). Coupled to ADR-2606032130 (Displacement Dividend, G2). Learning loop builds on ADR-2605242600/2605242630 (Baien federated) within the ADR-2605241900 edge envelope. Clean-room interop pattern reuses ADR-2606033600 (sumitsubo) G1 + ADR-2605261800 (nv-compat).

## Context

The question posed: *does any existing actor design the Boston-Dynamics-Orbit shape — **remote operation of a robot fleet**, and **learning/training from that operation** — and is it clean-room?*

A thorough sweep of the roster (ADRs + `20-actors/` + code) returns a precise three-part verdict:

| Orbit capability | etzhayyim status before this ADR |
|---|---|
| **Remote operation / teleoperation / fleet control plane** | **ABSENT.** All robotics is *autonomous-only*. teleop is an explicit non-goal in wadachi (轍, ADR-2605242000), funadaiku (船大工, ADR-2606013400), and the labor-liberation wave. `fleet.toml` is Murakumo *compute*-node placement, not physical-robot fleet management. |
| **Learning from teleoperation** (imitation / LfD / behavior cloning) | **ABSENT entirely.** Zero occurrences of imitation-learning / learning-from-demonstration / behavior-cloning anywhere. baien federated (ADR-2605242600) trains LLM LoRA adapters on *pre-collected datasets*, not robot demonstration trajectories. No demonstration-capture pipeline exists. |
| **Clean-room interop pattern** | **EXISTS and is reusable.** sumitsubo (ADR-2606033600) interops with proprietary CAD using *published API shapes only* (no SDK/decompile/trademark, G1). nv-compat (ADR-2605261800) mirrors the NVIDIA Isaac/Omniverse API surface the same way. The pattern is proven; nothing applies it to robot ops. |

So the etzhayyim roster has **robot bodies** (sanae 早苗 field-ag, kiyome 清め cleaning, hataori 機織 garment — ADR-2606032100; giemon arms; kami-autodrive GNC — ADR-2606010600) and a **physics/sim spine** (kami-engine / kami-genesis / kami-autodrive, nv-compat Isaac), but **no head that remotely operates the fleet and no loop that learns from the operating**.

This is not a small gap for the labor-liberation mission. The honest meta-finding of ADR-2606035000 was that *"robotics ~0% real"* — the bodies raise `RuntimeError` on `.solve()` and have no skills. The reason real robot skills are missing is the same everywhere in the field: **autonomous manipulation of the unstructured world (open-field weeding, limp-fabric seam handling, a stranger's kitchen) is unsolved, and the only known bootstrap is human demonstration.** Boston Dynamics Orbit, NVIDIA Isaac/GR00T, Tesla Optimus, and the entire LeRobot ecosystem all share one architecture: *a human teleoperates the robot → trajectories are recorded → a policy is learned → the robot earns autonomy → the human takes the reins back only on exception.*

etzhayyim needs that architecture, but it needs it **charter-clean**: remote actuation of a physical machine is exactly the capability the Mission Charter's force-separation invariant (§1.12) was written to constrain, and the demonstration data is a member's **labour** (Wellbecoming trajectory + 要配慮 PII), not a scrapeable corpus. This ADR designs that head.

### Why "手綱" (tazuna — the reins)

The reins are the perfect metaphor and the perfect constraint. You **hold the reins** to guide a horse that does not yet know the path (teleoperation). As it learns, you **release the reins** (autonomy hand-off). The whole actor is the disciplined holding-and-releasing of the reins under transparent, member-signed, on-chain-logged control — and the slow earning of autonomy through demonstration. The 手綱-release *is* the imitation-learning loop closing. (Sibling glyph resonance with watatsuna 綿津綱, whose 綱 is the submarine *cable*; tazuna's 綱 is the teleoperation *tether*.)

## Decision

Create **`tazuna` 手綱** — a Tier-B **horizontal control-plane actor** with two coupled faces, R0 design-only:

1. **Operation face (the Orbit-shaped half)** — a transparent, member-signed, on-chain-logged **fleet-management + teleoperation control plane** over the robotics-body actors (sanae/kiyome/hataori/giemon/wadachi). Fleet registry + health, mission dispatch, and time-boxed teleoperation sessions with deadman / e-stop / latency-budget / autonomy-fallback.

2. **Learning face (the train-from-it half)** — a **learning-from-demonstration loop**: teleop trajectories are recorded as consent-bound Datoms → shaped into an open-format (LeRobot-shaped) demonstration dataset on the kotoba/IPFS/DataLad substrate → an imitation / behavior-cloning **policy** is trained via **baien federated** (ADR-2605242600) inside the **edge envelope** (ADR-2605241900), Murakumo-only → the policy is sim-evaluated and only ever **handed the reins under supervision** (instant member takeback). The 手綱-release.

Both faces are **clean-room** in the sumitsubo/nv-compat sense (§ below). DID `did:web:etzhayyim.com:actor:tazuna`; namespace `com.etzhayyim.tazuna.*`. Follows the funadaiku/karakuri R0 contract (dual manifest, cells with `.solve()` → `RuntimeError`, lexicons, `:representative` kotoba seed, one empirically-tested pure-Python method — here the safety-critical `teleop_safety` reasoner).

### Clean-room interop surface (G1 — published API shapes only)

tazuna speaks the *vocabulary* of the robot-ops ecosystem so the bodies are portable and operators are not re-trained, but it ships **zero vendor code**. Exactly the sumitsubo rule: published call shapes, open specifications, and open standards only — **no vendor SDK headers, no decompilation, no trademarked code, no forks.**

| Surface | What tazuna reuses | What it never touches |
|---|---|---|
| **Fleet ops** | The *published REST/gRPC call shapes* of Boston Dynamics **Orbit** (site/robot/mission/run resources) as a neutral vocabulary; **Open-RMF** (open-source, Apache-2.0) task-allocation + fleet-adapter concepts | The Orbit/Spot SDK, any Boston Dynamics binary, the "Spot"/"Orbit" trademarks in code (names appear only in adapter docstrings, like nv-compat) |
| **Robot transport** | **ROS 2** action/topic/service *shapes* + **DDS** concepts (open standard); **MCAP** + **rosbag2** open log container formats | Any proprietary robot firmware/SDK |
| **Demonstration data** | **LeRobot dataset** open schema (episodes / frames / state-action) + **Foxglove**/MCAP open viz formats | Proprietary teleop suites |
| **Sim / policy** | kami-engine / kami-genesis / kami-autodrive (first-party, Apache/MIT) + **nv-compat** Isaac Sim/Lab facade (ADR-2605261800, published-shape only) | NVIDIA SDK headers, Isaac binaries, GR00T weights |

The neutral op vocabulary is a normalized **`teleopCommand`** and **`robotDescriptor`** — one schema across the TS host and the py cell (the sumitsubo `ModelOp` / karakuri `ServiceOp` pattern). A vendor robot is reached only through a **clean-room adapter** that emits the open transport shape (ROS 2 / Open-RMF), never a vendor binding.

### Operation face — the teleoperation control plane

Four cells (`fleet_registry`, `mission_dispatch`, `teleop_session` [coded reference cell], `telemetry_ingest`). The defining, safety-critical cell is **`teleop_session`**, and its invariants are the heart of this ADR because *remote actuation of a physical machine is the single most charter-sensitive capability tazuna introduces.* Every teleoperation session is bound by:

- **Transparent Force (Mission Charter §1.12.B) — the hard gate.** Remote actuation can produce force in the world, so it is treated as *force* and admitted only under the constitutional three conditions: **(1) fully on-chain monitored** — every `teleopCommand` is a Datom, batched and anchored to the commit-DAG root on Base L2 (ADR-2605312345), so the complete actuation history is public and replayable (`as-of`); **(2) open-source** — all control + skill code is Apache-2.0 WASM/Rust, no proprietary trait; **(3) 1 SBT = 1 vote** — a robot's *force class* (see below) and its activation are governed by the existing `etzhayyim-force-authorization` contract. A `teleopGrant` references its force-authorization decision or it cannot be built.
- **no-server-key (ADR-2605231525) — non-negotiable.** The platform **never holds the key that commands a physical robot.** A `teleopGrant` carries `serverHeldKey=false` and an encrypted-envelope reference only; every actuation command is **signed by the member operator**, and a server signature is *refused by construction* (same enforcement as karakuri's session_broker). The control plane relays and logs; it never authors actuation.
- **Force class (N1 / kotoba-os precedent).** Each `robotDescriptor` carries a `forceClass`: `:observational` (sensors only, no actuation) · `:soft-actuation` (low-energy manipulation: seeding, wiping, fabric handling) · `:powered-actuation` (mobile platforms, heavier arms). `:weaponizable` is **unrepresentable** — the enum cannot express it, mirroring nusa's `:thc-class` and kotoba-os `liveActuation=false`. N1 (no weapons / no force-as-harm) holds structurally.
- **NOT a certified safety system (kotoba-os N2 precedent).** tazuna provides *soft-real-time teleop supervision* (deadman, e-stop, latency budget, autonomy-fallback) — it is **not** an IEC 61508 / ISO 13849 safety-rated controller. Hard-real-time and safety-rated live actuation of `:powered-actuation` near humans is **R5 / Council Lv7+ gated.**
- **Deadman + e-stop + latency budget + autonomy-fallback.** A session has a continuous member-presence deadman; loss of presence or a breach of the latency budget triggers an immediate **safe-stop → autonomy-fallback** (hand control to the body's own on-board safe behaviour), never an unsupervised continuation. This logic is the `teleop_safety` method, empirically tested.

### Learning face — the learning-from-demonstration loop (the 手綱-release)

Three cells (`demonstration_record`, `policy_train`, `autonomy_handoff`):

- **`demonstration_record`** — a teleoperation session's state-action trajectory is captured as a `demonstrationEpisode` (LeRobot-shaped: frames of observation + the member's commanded action) written to the kotoba Datom log and pinned to IPFS/DataLad (`80-data/tazuna`, no-git-lfs, per ADR-2605241500). **The demonstration is the member's labour**, so it is consent-bound, encrypted (`com.etzhayyim.encrypted.*`), `cash≡0` (a contribution, never paid work — ADR-2605301020 N1), and forms part of that member's Wellbecoming trajectory (`as-of`, 非終末論 — no terminal "trained" state).
- **`policy_train`** — imitation / behavior-cloning training runs on **baien federated** (ADR-2605242600/2605242630: WebGPU/edge LoRA over a frozen-encoder trunk), **Murakumo-only** (ADR-2605215000), and the resulting `policyArtifact` must fit the **baien edge envelope** (ADR-2605241900: WASM-32 + iPhone-12 + Android-4GB, frozen modality encoders). Sim-augmentation and domain-randomization come from kami-engine/kami-genesis + nv-compat Isaac (clean-room). A larger sim-trained policy is a separate `baien-server-*` carve-out, never the default edge artifact.
- **`autonomy_handoff`** — a trained policy is **never auto-promoted to live actuation.** It is sim-evaluated (kami-autodrive eval-gate pattern), then may run only under **supervised hand-off**: the policy drives while the member holds instant takeback (the SAE-L4-ceiling discipline of wadachi, ADR-2605242000). The `autonomyHandoff` record logs supervision level, takeback latency, and the Council/operator gate. This closes the loop: teleop → demonstration → policy → supervised autonomy → (exception) → teleop.

### Constitutional gates (IMMUTABLE R0→R5)

- **G1 — clean-room interop.** Published API shapes + open standards only (Orbit REST shape / Open-RMF / ROS 2 / DDS / MCAP / rosbag2 / LeRobot / Foxglove); **no vendor SDK, no decompilation, no trademarked code, no fork.** Vendor names only in adapter docstrings (sumitsubo G1 + nv-compat).
- **G2 — Displacement-dividend coupling (DEFINING, inherited from the wave).** tazuna may not operate a fleet that displaces human labour *live* unless the displaced cohort is registered for the tenure-weighted Displacement Dividend (ADR-2606032130). Remote-operation-and-learning that frees a worker must fund that worker.
- **G3 — Transparent Force.** Every `teleopCommand` is an on-chain-anchored Datom; control code open-source; force class + activation governed by 1 SBT = 1 vote via `etzhayyim-force-authorization` (Mission Charter §1.12.B). A `teleopGrant` without a force-authorization reference cannot be built.
- **G4 — no-server-key.** Actuation commands are member-signed; `serverHeldKey=false`; server signature refused (ADR-2605231525). The platform never authors a physical-robot command.
- **G5 — Murakumo-only inference.** All policy training/eval and any perception assist via LiteLLM 127.0.0.1:4000 / edge Murakumo only (ADR-2605215000); no commercial GPU rental in the religious-corp path.
- **G6 — edge-envelope policy.** A shipped `policyArtifact` fits the baien edge envelope (ADR-2605241900); larger policies are explicit `baien-server-*` carve-outs.
- **G7 — outward-gated.** ANY live actuation, live fleet enrollment, or live demonstration capture is Council Lv6+ + operator gated (Lv7+ for `:powered-actuation` near humans). R0–R2 = design + simulation + replay only.
- **G8 — consent-bound demonstration / PII.** Demonstration episodes are the member's own labour data, encrypted, consent-scoped, `cash≡0`; part of the member's Wellbecoming trajectory (`as-of`), never a third-party dataset.
- **G9 — privacy-by-construction (inherited from kiyome G9).** Teleoperation into homes/private spaces is on-device only — **no cloud video to third parties, no surveillance feed, no biometric capture**; the teleop link is encrypted end-to-end and operator-scoped. A remotely-operated robot is the opposite of a spy.
- **G10 — soft-RT only / not a certified safety system.** Deadman/e-stop/latency-fallback are best-effort supervision; IEC 61508 / ISO 13849 safety-rated and hard-RT live actuation are R5/Lv7+ (kotoba-os N2 precedent).
- **G11 — kotoba-EAVT audit.** Fleet, mission, every command, every demonstration, every hand-off = Datoms (`as-of`, replayable). The member and the public can audit exactly what was commanded and what was learned.
- **G12 — sourcing-honesty.** `:representative` fleet/registry; honest capability staging (manipulation is unsolved — R-stages must not imply otherwise).

### Non-Goals

- **N1** Weapons / fire-control / force-as-harm / dual-use-for-harm; `:weaponizable` force class is structurally unrepresentable (Mission Charter §1.12 force-separation).
- **N2** Surveillance / covert teleop / third-party data harvesting; the robot is not a sensor platform for anyone but its consenting principal (G9).
- **N3** Remote operation of a *non-member's* robot or account; tazuna operates only fleets the operator is authorized for (karakuri G1 / himotoki own-only precedent).
- **N4** A commercial teleoperation-labor marketplace / gig-teleop substrate (anti-§1.13; the loop exists to *retire* the toil, not to relocate it to a remote gig worker).
- **N5** Certified safety controller / hard-RT live actuation near humans (R5/Lv7+; not this design).
- **N6** Autonomy that exceeds the wadachi SAE-L4 ceiling, or any auto-promotion of a policy to live actuation without supervised hand-off + gate.
- **N7** Bundling or shipping any vendor SDK / firmware / weights, or evading a vendor ToS/anti-automation control (clean-room; karakuri N2 no-detection-evasion precedent).
- **N8** Cash payment for demonstrations or operation (no-payroll, cash≡0; contribution → vocation → donation only).

## Design — shared R0 contract

| Concern | R0 rule |
|---|---|
| Manifest | `manifest.edn` (canonical) + `manifest.jsonld` (DID + roadmap + non-goals). |
| Cells | langgraph Pregel, `:runtime :wasm`; `cell.py.solve()` raises `RuntimeError("tazuna R0 scaffold: activate via Council ADR …")`; only `state_machine.py` + the safety method are unit-tested. |
| Inference | Murakumo-only (ADR-2605215000); policy training on baien federated (ADR-2605242600). |
| Lexicons | `com.etzhayyim.tazuna.<RecordType>` EDN, integer-with-implied-units. |
| Data | kotoba EAVT EDN, `:representative` seed; demonstration blobs IPFS/DataLad, no git-lfs. |
| Witness | actuation records require the member operator's Ed25519 signature (G4) + on-chain anchor (G3). |

**Cells (7)** — operation: `fleet_registry` (reuben) · `mission_dispatch` (simeon) · **`teleop_session`** (levi, coded reference cell — deadman/e-stop/latency/force-auth/no-server-key) · `telemetry_ingest` (judah); learning: `demonstration_record` (zebulun) · `policy_train` (issachar) · `autonomy_handoff` (dan).

**Lexicons (6)** — `robotDescriptor` (fleet member + `forceClass` + edge envelope) · `teleopGrant` (member-signed, force-authorized, time-boxed; `serverHeldKey const false`) · `teleopCommand` (one on-chain-anchorable transparent-force Datom; `dryRun const true` at R0) · `demonstrationEpisode` (LeRobot-shaped trajectory; consent-bound; `cash const 0`) · `policyArtifact` (baien edge-envelope policy; CID + eval scorecard + promotion gate) · `autonomyHandoff` (supervised teleop→autonomy; takeback latency + gate).

**Method** — `methods/teleop_safety.py` (stdlib): the safety-critical reasoner — deadman timeout, e-stop, latency-budget breach → safe-stop/autonomy-fallback decision, and the force-class authorization gate. Empirically unit-tested.

## Roadmap

| Phase | Scope | Gate |
|---|---|---|
| **R0** (this ADR) | Charter + manifests + 7 cells (`RuntimeError`) + 6 lexicons + `:representative` kotoba seed + `teleop_safety` method (tested) + `teleop_session` state-machine (tested). No hardware, no live link. | This ADR (proposed) |
| R1 | Sim teleop in kami-engine/kami-autodrive (operate a simulated sanae/kiyome body); `demonstrationEpisode` capture in sim → LeRobot-shaped dataset; clean-room Open-RMF/ROS 2 adapter shapes. | Per-actor ADR + Council Lv6+ |
| R2 | baien federated behavior-cloning on sim demonstrations → first `policyArtifact` in the edge envelope; `autonomy_handoff` supervised in sim; force-authorization integration (no live actuation). | Future ADR + 30-day comment |
| R3 | Benchtop **single robot, `:soft-actuation`, member-signed teleop**, on-chain command log; demonstration capture on real hardware; displacement-cohort registry dry-run (G2). | Future ADR + Council Lv6+ + operator |
| R5 | `:powered-actuation` near humans / safety-rated / hard-RT live actuation; community-scale fleet; live displacement *only with* dividend active. | Council **Lv7+** + 60-day review + safety dossier |

## Consequences

**Positive** — closes the Orbit-shaped gap with the missing *head* (control plane) and *loop* (learning) over the existing robot bodies; gives the labor-liberation mission its only known bootstrap from `RuntimeError`-stub skills to real autonomy (teleop → demonstration → policy); establishes a reusable **Transparent-Force-binding-for-actuation** pattern (every command a Datom, member-signed, force-authorized) that any future actuating actor inherits; keeps the whole capability inside the constitution (no-server-key, edge envelope, Murakumo-only, privacy-by-construction, displacement coupling).

**Negative / risks** — (a) remote actuation is the most charter-sensitive capability yet introduced; the G3/G4/G9/G10 gates are load-bearing and the R5/Lv7+ ceiling on powered actuation must hold. (b) Real-world manipulation is unsolved; R-staging must be brutally honest (G12). (c) The learning loop depends on baien federated maturing (currently R0/R1). (d) Demonstration data is sensitive labour/PII; the consent + encryption envelope (G8) is essential. (e) One more horizontal actor adds surface; mitigated by the shared R0 contract and clean-room reuse.

## Alternatives Considered

1. **Extend each robotics actor with its own teleop/learning** — rejected; the control plane + learning loop are domain-orthogonal (the deadman, force-auth, no-server-key, demonstration-capture, and federated-training machinery is identical for sanae and kiyome). One horizontal actor; mirrors Orbit sitting above a heterogeneous Spot/Stretch fleet, and the existing find/render split (danjo→kanae) and observe/operate split (watatsuna→watatsumi).
2. **Bundle a vendor SDK (Orbit/Isaac) for speed** — rejected; violates Apache/Charter-Rider + the clean-room invariant. The sumitsubo/nv-compat published-shape pattern gives interop without the vendor code.
3. **Train policies on a commercial GPU cloud / collect demonstrations as paid gig work** — rejected; violates Murakumo-only (G5) and cash≡0/no-payroll (N8). Federated edge training + vocation-contribution only.
4. **Allow server-side actuation signing for convenience** — rejected outright; no-server-key (G4/ADR-2605231525) is non-negotiable for a key that commands a physical machine.
5. **Skip teleop, pursue pure sim-to-real autonomy** — rejected as insufficient alone; demonstration is the field-proven bootstrap for unstructured manipulation. Sim-to-real (kami-engine + nv-compat Isaac) augments, not replaces, the demonstration loop.

## Honest (R0 limitations)

- No hardware, no live robot link, no real fleet; all cells raise `RuntimeError`; fleet/registry are `:representative`.
- Real-world manipulation skills do not exist in the roster (ADR-2606035000 meta-finding); tazuna is the *architecture* to acquire them, not the skills themselves.
- baien federated is itself R0/R1 (ADR-2605242600); the policy_train cell targets it but cannot yet train a real robot policy.
- The clean-room adapters are *shapes* at R0 (no live ROS 2 / Open-RMF / Orbit endpoint is contacted; G7).
- Force-authorization, on-chain anchoring, and the displacement-dividend pool are referenced contracts, wired at R2/R3, not exercised live at R0.

## References

- ADR-2605192100 (Mission Charter — §1.12 Transparent Force three-condition invariant + 構造的労働解放)
- ADR-2606032100 (Labor-Liberation Robotics Wave — sanae/hataori/kiyome bodies)
- ADR-2606032130 (Displacement Dividend — G2 coupling)
- ADR-2606010600 (kami-autodrive — GNC autonomy + eval-gate + SAE ceiling)
- ADR-2605242000 (wadachi — SAE-L4 ceiling, supervised-autonomy discipline)
- ADR-2605242600 / 2605242630 (Baien federated R0/R1 — the learning substrate)
- ADR-2605241900 (Baien edge-target invariant — the policy envelope)
- ADR-2605261800 (nv-compat — clean-room Isaac/Omniverse API mirror)
- ADR-2606033600 (sumitsubo — clean-room CAD interop, G1 published-shape pattern)
- ADR-2605231525 (no-server-key — member-signed actuation)
- ADR-2605215000 (Murakumo-only inference)
- ADR-2606031600 (kotoba-os — soft-RT / not-a-safety-system + liveActuation=false precedent)

## Addendum (2026-07-12): satellite/high-jitter-link recovery hysteresis (G10 extension)

**Still R0.** No hardware, no live link, no live actuation, no gate change — this hardens the
existing `teleop_safety` reasoner + `teleop_session` state-machine (both already tested at R0)
without touching G3/G4/G7/G9/N5/N6.

**Motivation.** tazuna is the charter-clean substrate for remotely operating the labor-liberation
robot bodies; a plausible relay for a genuinely remote fleet is a LEO satellite link
(Starlink-class), which is jitter-prone (periodic beam-handoff spikes) rather than uniformly
degraded. The R0 `safe-state` verdict was a single-sample threshold: any one command with
`observed_latency_ms > latency_budget_ms` dropped the session to `autonomy-fallback`, and any one
subsequent in-budget sample let it resume `nominal` actuation on the very next tick. Over a
jitter-prone link this flaps — a single lucky sample mid-handoff would re-arm actuation while the
link is still effectively degraded, which is the opposite of what G10 soft-RT supervision is for.

**Change.** Latency-budget recovery is now link-quality-hysteresis-gated: a breach still trips
`autonomy-fallback` **instantly** (fail-fast, unchanged), but resuming `nominal` actuation requires
`recovery_samples` (default 3) **consecutive** in-budget samples (fail-safe against flapping). A
single blip during the recovery window resets the counter. Deadman lapse and e-stop remain
**instant and unaffected** by this window — a lapsed presence heartbeat is a different concern
(operator absence, not link jitter) and is left requiring an explicit operator re-arm, not a lucky
sample. This makes the existing safety gate strictly more conservative (slower to re-arm actuation
after a breach); it never actuates in a case the R0 design would have refused, and it can only
refuse actuation in cases the R0 design would have (over-eagerly) allowed.

**Where.** `methods/teleop_safety.cljc` gains `evaluate-session` (folds the unchanged `evaluate`
priority — e-stop > deadman > latency > nominal — over a sequence of relayed commands) and
`satellite-leo-grant-defaults` (an explicitly-labeled, explicitly-uncalibrated illustrative preset —
G12 sourcing-honesty: no real Starlink RTT/jitter figures are asserted). `evaluate` itself, and
every existing test against it, is untouched. `cells/teleop_session/state_machine.cljc`'s
`safe-state` now returns `[verdict cs']`, threading the hysteresis bookkeeping
(`link_fallback_active`, `latency_recovery_count`) across ticks via the state machine's existing
cell_state-forwarding convention (the outer loop already threads `cell_state` tick-to-tick; no new
persistence mechanism was introduced). 14 new tests (23+14+6 = 43 total, up from 29), all green.

**Honest (still true, unchanged from the R0 "Honest" section above):** this is a pure, offline,
advisory reasoner — no real satellite link has ever been contacted, no real latency/jitter
distribution has been measured, and `satellite-leo-grant-defaults` is not a calibrated operating
point for any real relay. Reaching a live link (even in sim) is still gated at R1+ per the Roadmap
table; this addendum only makes the R0 reasoner's behavior correct in the presence of jitter,
before there is anything real to plug it into.

References: `orgs/etzhayyim/com-etzhayyim-tazuna` PR #3 (`satellite-link-hysteresis`, merged
2026-07-12).
- ADR-2605312345 (kotoba Datom = first-class canonical state — the on-chain command log)
