---
id: adr-2605071900
title: Koke (苔) — Bryophyta Primary Fixation Layer
status: active
doc_type: adr
topic: koke-bryophyta-primary-fixation-layer
authoritative: true
last_verified: 2026-05-07
authoritative_for:
  - koke ecosystem member design
  - primary fixation layer in myco-yeast artificial organism
related:
  - adr-2605071200-myco-yeast-artificial-organism-jp-naming
supersedes: []
superseded_by: []
---

# Koke (苔) — Bryophyta Primary Fixation Layer

## Goal

Introduce koke (苔, Bryophyta) as Layer 0 of the myco-yeast artificial organism — a
pioneer organism that performs **reversible primary fixation** of raw external signals
before they enter the irreversible hakkou (発酵) fermentation pipeline.

## Scope

- `koke.etzhayyim.com` CF Worker (nanoid `k0k3m001`)
- `vertex_koke_fixation` + `edge_koke_flow` graph tables
- 4 Zeebe task types: `koke.scan_raw_signals`, `koke.fix_signal`,
  `koke.classify_fixation`, `koke.handoff_to_hakkou`
- BPMN: `photosynthesis-cycle.bpmn` (R/PT30M timer)

## Executive Summary

Moss is the pioneer plant — it colonises bare rock and creates soil for higher organisms.
Koke plays the same role in the myco-yeast ecosystem:

| Metaphor | Biology | Software |
|---|---|---|
| CO₂ | atmospheric carbon | raw external signal (text, URL, record) |
| Photosynthesis | CO₂ → glucose | primary fixation: signal → structured vertex |
| Glucose | stored energy | `vertex_koke_fixation` row |
| Carbon release | reversible exhalation | `releaseCarbon` XRPC — fixation deleted, signal returned raw |
| Handoff to fungi | moss → fungal substrate | `handoff_to_hakkou` → `vertex_hakkou_ferment` |

**Key invariant**: fixation is **REVERSIBLE** until handoff. This contrasts with hakkou's
irreversible transformation. Koke is the only layer that allows rolling back to raw state.

## Decision

1. **Layer 0** — koke sits below kobo (Layer 1), kabi (Layer 2), kinoko (Layer 3).
   It receives raw signals from external sources and prepares them for the ecosystem.
2. **Reversibility** — `releaseCarbon` deletes the fixation and restores the signal
   to unfixed state. Once `handoff_to_hakkou` fires, the signal is owned by hakkou
   and koke releases it (edge_koke_flow is the handoff record).
3. **Photosynthesis cycle** — timer-driven BPMN (R/PT30M) scans for unfixed signals,
   fixes them, classifies them, and optionally hands off high-confidence ones to hakkou.
4. **Nanoid** — `k0k3m001` (alpha-start rule, koke phonetic mnemonic).
5. **Graph schema** — `vertex_koke_fixation` (base vertex + promoted columns) +
   `edge_koke_flow` (handoff edge to hakkou).

## Rationale

| Option | Pro | Con |
|---|---|---|
| Extend hakkou with a "pending" state | Simpler schema | Violates hakkou's write-only irreversibility invariant |
| **Koke as separate Layer 0** | Clean separation; reversibility possible; pioneer metaphor accurate | New actor to deploy |
| Use kobo agent as signal buffer | Reuse existing actor | kobo is for individual agent lifecycle, not signal ingestion |

Separate layer wins: Shannon η is higher with clean boundary (no mixed-concern mutations
in hakkou, no prion-state contamination in kobo from raw signals).

## References

- ADR-2605071200: Myco-Yeast Artificial Organism JP Naming
- `etzhayyim-root/00-contracts/bpmn/com/etzhayyim/koke/photosynthesis-cycle.bpmn`
- `30-graph/graph-schema/migrations/20260507760000_vertex_koke_tables.ts`
