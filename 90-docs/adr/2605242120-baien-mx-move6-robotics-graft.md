---
id: adr-2605242120-baien-mx-move6-robotics-graft
title: "Baien Move 6 — robotics graft (edge = scene description only / server = action head post-Council)"
status: accepted
doc_type: adr
topic: baien-multimodal
authoritative: true
last_verified: 2026-05-24
authoritative_for:
  - baien Move 6 robotics architecture (edge / server tier split)
  - safety rationale for forbidding actuation at edge tier
  - Move 6 data source review per Charter Rider §2 scan
  - relation to wadachi (mobility sibling) — Move 6 is manipulation only
depends_on:
  - adr-2605092350-baien-1bit-multimodal-edge-browser-cpu-design
  - adr-2605101000-baien-mx-multimodal-expansion-from-rw
  - adr-2605231300-baien-distill-react-loop
  - adr-2605232500-baien-mx-move1-image-graft-self-training
  - adr-2605241900-baien-edge-target-invariant
  - adr-2605242000-roso-pattern-frontier-distill
  - adr-2605242100-baien-server-xl-carve-out
  - adr-2605242110-baien-mx-move5-video-graft
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
related:
  - 70-tools/baien-mx-train/src/baien_mx_train/moves/robotics.py
supersedes: []
superseded_by: []
---

# Context

baien Moves 1 / 4 / 5 / 7 all attach **perceptual** modalities (image,
audio, video, 3D). Move 6 — robotics — is qualitatively different
because it sits at the actuation boundary: the model can in principle
emit tokens that decode to actuator commands.

This is the first Move that touches the **physical-world risk surface**,
which intersects Charter Rider §2(h) (Wellbecoming) and §2(a) (no
weapons design). It also borders ADR-2605242000 (wadachi autonomous
mobility R&D), which has its own G1-G12 constitutional gates and SAE
J3016 Level 4 ceiling. Move 6 must be carved cleanly so that:

- baien at the edge tier **cannot** be coaxed into issuing actuator
  commands (no action head, period).
- A server-tier action head can be developed for research, but only
  ships **after Council Lv6+ ratification of an action-policy safety
  review**.
- The line with wadachi is clear: wadachi is **mobility / navigation**;
  Move 6 is **manipulation** (pick / place / interact with a
  manipulator). Different actor; different ADR ladder.

# Decision

## Split — edge is observation-only, server is actuation

| Tier | Capability | Encoders | Head | Output |
|---|---|---|---|---|
| **edge** | scene description only | Move 1 image encoder + Move 5 video encoder (on-demand per ADR-2605242110) | text head only | natural-language scene description, object lists, action observation |
| **server** | OpenVLA-style action policy | full multi-modal observation bundle | action chunking decoder (ACT-style, 7-DoF) | actuator command tokens decoded via `RoboticsActionDecoder` |

The edge tier reuses existing Move 1 / 5 encoders — **no new
encoder weights** at edge. The server tier wraps a `baien-server-*`
trunk under the ADR-2605242100 carve-out, with an action head added.

## Data row dataclasses

```python
@dataclass(frozen=True)
class RoboticsSceneRow:
    """Edge-tier training row: scene description only."""
    image: bytes            # SigLIP-compatible (224x224 RGB)
    scene_desc: str         # human-readable target (training label)
    env_meta: dict          # {"surface": "table", "objects": [...],
                            #  "lighting": "indoor"}
                            # training-time only, never used at inference
```

```python
@dataclass(frozen=True)
class RoboticsActionRow:
    """Server-tier training row: full action chunk (stub — ships post-Council)."""
    observation: dict       # multi-modal observation bundle
    action_chunk: list[list[float]]  # K timesteps x 7 DoF
    success_label: float    # 0.0..1.0
```

The server row is **declared but stub-only** in this ADR — its
trainer body lands only after the Council ratification described in
§Safety rationale.

## Safety rationale (constitutional alignment)

This is the load-bearing portion of the ADR.

1. **Charter Rider §2(h) Wellbecoming**: actuation from an
   under-specified edge LLM is a physical-world safety risk. The
   model can misinterpret a benign prompt as an actuator command in
   ways that would not matter at the text tier (worst case: bad
   text) but could matter at the actuator tier (worst case: physical
   harm). Edge tier MUST NOT issue actuator commands. The Python
   guard (`assert_edge_no_actuation`) makes this an exception-raising
   path, not a runtime fallback.
2. **Charter Rider §2(a) Weapons design**: any weaponizable action
   policy requires explicit ADR amendment **plus** Council Lv6+
   supermajority **plus** open-source release per ADR-2605192100
   §1.12.B (Transparent Force). Move 6 server tier is *not*
   weapons-adjacent by default (manipulation in domestic / research
   contexts), but the registry MUST be sanity-checked against
   Charter Rider §2 every commit_node.
3. **ADR-2605242000 sibling boundary**: wadachi handles autonomous
   mobility (vehicles / navigation) and has its own G1-G12 gates.
   Move 6 handles manipulation (arms / grippers) and does NOT inherit
   wadachi's mobility-specific gates. Cross-actor coordination on
   shared safety primitives (object detection, scene grounding) is
   fine; cross-actor capability sharing (mobility-as-manipulation
   tokens) is forbidden without an explicit ADR.

## Modality registry entries

- `robotics_scene` — edge-capable (image-in + text-out). Reuses Move 1
  SigLIP encoder; no new weights at runtime.
- `robotics_action` — **server-only**. Gated at adapter registration
  by `target_tier == "server"`. Loading from `edge` tier raises
  `RuntimeError` via `assert_edge_no_actuation`.

## Training data

| Tier | Dataset | Review |
|---|---|---|
| edge | Open-X-Embodiment scene captions subset | filter via `etzhayyim_organism.sensors.charter_rider.scan()`; many entries include industrial / warehouse contexts — verify no weapons / surveillance / fossil-fuel optimization tasks |
| server | OpenVLA fine-tune dataset | **post-Council ratification only** |

The edge tier subset selection is itself a Charter Rider §2 review
artifact — capture the filter manifest in `90-docs/baien/move6-edge-data-filter.jsonl`
with the per-row pass/fail rationale.

# Consequences

- **Edge ships first.** Move 6 edge-tier (scene description) ships
  alongside Moves 1 / 4 / 5 / 7 once data + projector training pass
  the standard 60 % microbench gate.
- **Server action head is gated.** No `baien-server-robotics-*` model
  publishes until the Council records a Transparent Force-style
  attestation for the action policy class.
- **No autonomous mobility leak.** The Python guard plus the explicit
  ADR-2605242000 sibling boundary prevent Move 6 from accidentally
  becoming a navigation policy.
- **Eval will mirror Move 1** (5 verifiable rule-based prompts on
  held-out scenes), gated at 60 % pass + Δ ≥ -3 pp on existing modes.

# Alternatives Considered

1. **Single-tier with policy-time guards.** Rejected — a single tier
   that "tries to" refuse actuator commands at runtime is weaker than
   structurally not having an action head. Defense in depth is cheap
   here (one guard function + tier split in the registry).
2. **Skip edge tier entirely.** Rejected — scene description is
   useful (accessibility, monitoring, robot-assisted documentation)
   and carries no actuation risk. Including it serves the mission
   without cost.
3. **Merge into wadachi.** Rejected — wadachi is mobility-only by
   design (kuni-umi S4 carve-out, ADR-2605201800 → ADR-2605242000).
   Manipulation has different physics, different datasets, different
   safety profile; deserves its own Move under baien.
4. **Defer Move 6 entirely until Council ratifies action head.**
   Rejected — needlessly couples the unrelated scene-description
   capability to a far heavier governance gate.

# Non-goals

- **Autonomous mobility** — see `20-actors/wadachi/` (kuni-umi S4
  carve-out, ADR-2605242000). Move 6 is **manipulation**, not
  navigation.
- **Real-time control loop** — Move 6 is **offline scene-understanding
  training** (and, post-Council, offline action-policy SFT). Closed-loop
  runtime is a separate runtime ADR.
- **Edge actuation under any condition** — no flag, no environment
  variable, no "advanced user" mode. The guard is unconditional.

# References

- ADR-2605241900 — baien edge-target invariant
- ADR-2605242100 — baien-server / baien-XL carve-out (where the
  server action head lives once ratified)
- ADR-2605192100 §1.12.B — Transparent Force (open-source + on-chain
  monitoring + 1 SBT = 1 vote)
- ADR-2605192200 — Charter Rider v2.0 (§2(a) weapons / §2(h)
  Wellbecoming)
- ADR-2605242000 — wadachi autonomous mobility R&D (sibling actor;
  mobility-only carve-out)
- ADR-2605242110 — Move 5 video graft (on-demand encoder reused)
- ADR-2605232500 — Move 1 image graft (architectural pattern)
- Open-X-Embodiment: https://robotics-transformer-x.github.io/
- OpenVLA: https://openvla.github.io/
- ACT (Action Chunking Transformer): https://github.com/tonyzhaozh/act
