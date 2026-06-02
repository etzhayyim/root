---
id: adr-2605072100
title: Ki (木) — Vascular Synthesis Layer
status: active
doc_type: adr
topic: ki-vascular-synthesis-layer
authoritative: true
last_verified: 2026-05-07
authoritative_for:
  - ki ecosystem member design
  - vascular synthesis layer in myco-yeast artificial organism
related:
  - adr-2605071200-myco-yeast-artificial-organism-jp-naming
  - adr-2605071900
  - adr-2605072000
supersedes: []
superseded_by: []
---

# Ki (木) — Vascular Synthesis Layer

## Goal

Introduce ki (木, vascular plant / tree) as the Vascular Synthesis Layer of the myco-yeast
artificial organism — a layer that provides structured bidirectional knowledge flow analogous
to a tree's xylem (upward water transport) and phloem (downward sugar transport), with
growth rings representing versioned knowledge checkpoints.

## Scope

- `ki.etzhayyim.com` CF Worker (nanoid `k1k1b001`)
- `vertex_ki_absorb`, `vertex_ki_artifact`, `vertex_ki_ring`, `edge_ki_vascular` graph tables
- 4 Zeebe task types: `ki.absorb`, `ki.synthesize`, `ki.bloom`, `ki.ring`
- BPMN: `vascular-synthesis-cycle.bpmn` (R/PT60M timer)

## Executive Summary

A vascular plant is distinguished from mosses and fungi by its ability to transport water
and synthesized nutrients through dedicated internal channels over long distances. The xylem
carries raw water upward from roots; the phloem distributes photosynthate (sugar) downward
to all tissues. Growth rings record each year's conditions as a versioned checkpoint.

Ki mirrors this in the knowledge graph:

| Metaphor | Biology | Software |
|---|---|---|
| Xylem | upward raw water transport | absorb: raw signals from koke/hakkou into ki vascular input |
| Phloem | downward sugar/nutrient transport | bloom: synthesized knowledge artifact out to the graph |
| Photosynthesis synthesis | sugar production | synthesize: LLM-based structured synthesis of absorbed signals |
| Growth ring | annual dendrochronology layer | ring: versioned knowledge checkpoint (ISO8601 period) |
| Vascular bundle | xylem + phloem pair | edge_ki_vascular: links absorb source to artifact output |

**Key invariant**: ki produces **durable, versioned knowledge artifacts**. Unlike koke
(reversible) and hakkou (irreversible transformation), ki's synthesis is additive — each
bloom adds a new artifact without removing the absorbed inputs. Growth rings allow
point-in-time reconstruction of the knowledge graph state.

## Decision

1. **Synthesis layer** — ki sits above koke/hakkou in the knowledge maturation hierarchy.
   It consumes signals that have been fixed (koke) or fermented (hakkou) and synthesizes
   them into structured knowledge artifacts ready for downstream consumption.
2. **Absorb → Synthesize → Bloom pipeline** — signals enter via `absorb` (xylem),
   are synthesized by LLM via `synthesize`, and published via `bloom` (phloem).
   Each step writes to the graph immediately (Hyperdrive direct, ADR-0036).
3. **Growth ring checkpoints** — `ring` creates a versioned snapshot of all artifacts
   produced in a given period. The `ringId` is stamped on artifacts for provenance.
   This enables time-travel queries: "what did ki know at ring R?"
4. **PT60M cadence** — ki operates on a 60-minute vascular cycle, longer than koke (30m)
   and saikin (20m), reflecting that synthesis is a higher-cost operation than fixation
   or lateral transfer.
5. **Nanoid** — `k1k1b001` (alpha-start rule, ki phonetic mnemonic).
6. **Graph schema** — `vertex_ki_absorb` (absorbed input with sourceVertexId + inputKind) +
   `vertex_ki_artifact` (synthesized knowledge artifact with confidence) +
   `vertex_ki_ring` (growth ring checkpoint with snapshotCount) +
   `edge_ki_vascular` (absorb → artifact provenance edge).

## Rationale

| Option | Pro | Con |
|---|---|---|
| Extend hakkou with synthesis step | Reuse fermentation actor | Hakkou is irreversible transformation; synthesis is additive accumulation — wrong metaphor, wrong semantics |
| **Ki as dedicated vascular synthesis layer** | Clean absorb/bloom separation; growth ring versioning independent; LLM synthesis cadence distinct (PT60M) | New actor to deploy |
| Use kinoko consensus for synthesis | Reuse PoNF actor | kinoko's concern is multi-party consensus, not structured LLM synthesis with versioning |

Dedicated synthesis layer wins: the growth ring checkpoint pattern requires a first-class
`vertex_ki_ring` entity that has no natural home in hakkou (no versioning), kabi (no LLM),
or kinoko (no absorption). Shannon η is highest when xylem/phloem bidirectionality is
expressed as a single vascular layer.

## References

- ADR-2605071200: Myco-Yeast Artificial Organism JP Naming
- ADR-2605071900: Koke Bryophyta Primary Fixation Layer
- ADR-2605072000: Saikin Bacteria Horizontal Transfer Layer
- `etzhayyim-root/00-contracts/bpmn/com/etzhayyim/ki/vascular-synthesis-cycle.bpmn`
