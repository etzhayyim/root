---
id: adr-2605072000
renumbered_from: "2605072000"
title: Saikin (細菌) — Bacteria Horizontal Transfer Layer
status: active
doc_type: adr
topic: saikin-bacteria-horizontal-transfer-layer
authoritative: true
last_verified: 2026-05-07
authoritative_for:
  - saikin ecosystem member design
  - horizontal signal transfer in myco-yeast artificial organism
related:
  - adr-2605071200-myco-yeast-artificial-organism-jp-naming
  - adr-2605071900
supersedes: []
superseded_by: []
---

# Saikin (細菌) — Bacteria Horizontal Transfer Layer

## Goal

Introduce saikin (細菌, bacteria) as the Horizontal Signal Transfer Layer of the myco-yeast
artificial organism — a layer that propagates knowledge laterally across otherwise disconnected
actor clusters via mechanisms analogous to bacterial horizontal gene transfer (HGT).

## Scope

- `saikin.etzhayyim.com` CF Worker (nanoid `s41k1n01`)
- `vertex_saikin_colony`, `vertex_saikin_signal`, `edge_saikin_transfer`, `edge_saikin_member` graph tables
- 4 Zeebe task types: `saikin.probe_environment`, `saikin.transfer_signal`,
  `saikin.form_colony`, `saikin.lyse`
- BPMN: `horizontal-transfer-cycle.bpmn` (R/PT20M timer)

## Executive Summary

In microbiology, bacteria share genetic material across species boundaries through horizontal
gene transfer — conjugation, transduction, and transformation. This bypasses vertical
inheritance and allows rapid spread of advantageous traits (e.g., antibiotic resistance)
through a population that would otherwise be genetically isolated.

Saikin mirrors this in the knowledge graph:

| Metaphor | Biology | Software |
|---|---|---|
| HGT | cross-species gene transfer | cross-cluster signal propagation |
| Probe | chemotaxis toward nutrients | scan external data sources for novel signals |
| Transfer | plasmid conjugation | copy signal to target actor's fixation space |
| Colony | biofilm cooperative | cooperative group of related signals |
| Lysis | cell rupture releasing contents | decompose processed signal, return to graph |

**Key invariant**: saikin transfers do not consume the source signal — they copy it.
This is the defining difference from hakkou's irreversible transformation.
Signal ownership remains in the originating actor's namespace; saikin creates
edge records (`edge_saikin_transfer`) linking source to target.

## Decision

1. **Horizontal layer** — saikin sits alongside (not above or below) kobo/kabi/kinoko.
   It operates on signals that have already been fixed by koke but not yet committed to
   hakkou, bridging disconnected actor clusters.
2. **Probe-then-transfer cycle** — timer-driven BPMN (R/PT20M) probes the environment
   for novel signals, evaluates transfer candidates, forms colonies where appropriate,
   and lyses fully-processed signals.
3. **Colony semantics** — a colony groups related signals under a shared `colonyId`.
   Members (`edge_saikin_member`) share processing context without merging identity.
   Colony formation triggers cooperative enrichment in kabi's mycelium network.
4. **Lysis** — when a signal has been transferred and enriched sufficiently, `lyse`
   decomposes it into the graph as released knowledge. Unlike hakkou's `ferment` (which
   produces a derived artifact), lysis releases the signal's component assertions directly.
5. **Nanoid** — `s41k1n01` (alpha-start rule, saikin phonetic mnemonic).
6. **Graph schema** — `vertex_saikin_signal` (tracked signal with transfer metadata) +
   `vertex_saikin_colony` (cooperative group) + `edge_saikin_transfer` (transfer event) +
   `edge_saikin_member` (colony membership edge).

## Rationale

| Option | Pro | Con |
|---|---|---|
| Extend kabi with cross-cluster routing | Reuse mycelium actor | kabi's concern is mycelium density/coverage, not lateral copy semantics |
| **Saikin as dedicated HGT layer** | Clean semantic boundary; colony/lysis metaphor distinct; probe cadence independent (PT20M vs kabi's PT45M) | New actor to deploy |
| Cross-actor invoke at L3 dispatcher | No new actor needed | Lacks colony formation, lysis lifecycle, and HGT audit trail |

Separate HGT layer wins: Shannon η is higher when lateral propagation is isolated from
mycelium density logic. Cross-cluster signal copies require transfer receipts
(`edge_saikin_transfer`) that cannot live in kabi without polluting the mycelium graph.

## References

- ADR-2605071200: Myco-Yeast Artificial Organism JP Naming
- ADR-2605071900: Koke Bryophyta Primary Fixation Layer
- `etzhayyim-root/00-contracts/bpmn/com/etzhayyim/saikin/horizontal-transfer-cycle.bpmn`
