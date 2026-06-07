---
id: adr-2606074500-kotoba-py-siblings-engine-core-vs-actor-placement
title: "ADR-2606074500: kotoba Python siblings — engine-core vs actor placement (iso20022 → engine, kawase → actor)"
status: proposed
doc_type: adr
topic: kotoba-py-sibling-placement-taxonomy
authoritative: true
last_verified: 2026-06-07
priority: 5.5
axis: architecture
weight: 0.40
priority_note: "Establishes the durable rule for WHERE a kotoba-prefixed Python sibling lives, now that the subrepo-era 'consumers live outside the mirror' rule (ADR-2605282300) is dissolved by submodule mechanics (ADR-2606074000). The question is no longer in-vs-out of the engine repo for git-hygiene reasons, but: is this generic engine-core capability (→ kotoba submodule), or actor-specific business logic (→ 20-actors/<actor>/)? Sorts the surviving siblings: kotoba_iso20022 → engine core; kotoba_kawase → its actor; kotoba_murakumo → engine core (already landed, founder-confirmed)."
authoritative_for:
  - placement taxonomy for kotoba-prefixed Python siblings (engine-core vs actor vs infra)
  - kotoba_iso20022 canonical location (kotoba submodule py/)
  - kotoba_kawase canonical location (20-actors/kawase-yui/)
depends_on:
  - "2606074000"  # kotoba_murakumo re-integration (submodule era; dissolves the relocation hazard)
  - "2605282300"  # subrepo-era relocation rule (superseded)
  - "2605282200"  # kawase-yui actor
  - "2605262130"  # kotoba canonical substrate
related: []
supersedes: []
superseded_by: []
---

# ADR-2606074500: kotoba Python siblings — engine-core vs actor placement

**Status**: proposed
**Date**: 2026-06-07
**Deciders**: Jun Kawasaki

## Context

After ADR-2606074000 re-integrated `kotoba_murakumo` into the kotoba submodule,
two more kotoba-prefixed Python packages remained parked at `40-engine/`
siblings of the submodule, both placed there under the now-superseded
subrepo-era rule (ADR-2605282300, "religious-corp downstream consumers live
OUTSIDE the upstream mirror"):

- `40-engine/kotoba_iso20022/` — a dependency-free, charter-clean ISO 20022
  payment-message codec (pain.001 / pacs.008 / pacs.002 / camt / pacs.004).
- `40-engine/kotoba_kawase/` — the adherent-facing client surface for the
  **kawase-yui** remittance actor (ADR-2605282200).

With submodule mechanics removing the git-hygiene reason to keep consumers out
of the engine repo, the placement question is no longer "in vs out of the engine
repo" but a cleaner architectural one:

> Is this **generic engine-core capability** that any kotoba user would want, or
> **actor-specific business logic** that belongs with one actor?

## Decision

Adopt a three-bucket placement taxonomy and sort the siblings accordingly.

### The buckets

1. **Engine core** → `40-engine/kotoba` submodule (Apache-2.0). Generic,
   charter-neutral, reusable substrate capability; depends only on the engine's
   public interfaces and open standards; not tied to a single actor;
   upstream-shippable. Monorepo-context test inputs (if any) must degrade to
   skips in a standalone checkout (per ADR-2606074000).
2. **Actor** → `20-actors/<actor>/`. Business logic specific to ONE actor;
   charter-bound; consumes the engine; co-located with the actor's
   manifest / cells / lex.
3. **Platform/infra** → `50-infra/` (or a shared SDK). Cross-cutting,
   operating-entity-specific capability used by many actors.

### The sort

| Package | Generic? | Charter-bound? | Tied to 1 actor? | Bucket |
|---|---|---|---|---|
| `kotoba_iso20022` | yes (zero-dep ISO 20022 codec) | no (format only) | no | **Engine core** → `40-engine/kotoba/py/kotoba_iso20022/` |
| `kotoba_kawase` | no (mirrors `KawaseYuiPool.sol`) | yes | yes (kawase-yui) | **Actor** → `20-actors/kawase-yui/kotoba_kawase/` |
| `kotoba_murakumo` | mostly (thin Modal-shim) | partly (Murakumo-only) | no (cross-actor) | **Engine core** (landed ADR-2606074000; founder-confirmed) |

- **`kotoba_iso20022` → engine core.** It carries `dependencies = []`, imports
  only stdlib, and has no runtime coupling to `etzhayyim_organism`, the Charter
  scanner, or monorepo paths. It is the traditional-finance analogue of the
  "AT-Protocol MST = ingress/interop wire" substrate rule: a generic codec
  translating the ISO 20022 banking wire ⇄ the kotoba EAVT Datom log. Its one
  monorepo-context test input (an etzhayyim Lexicon used to verify bridge record
  shape) degrades to a per-test skip when absent. The stray tracked `.coverage`
  artifact is dropped.
- **`kotoba_kawase` → actor.** Its exceptions mirror `KawaseYuiPool.sol`
  one-for-one (G3 `NotAdherent`, G4 `OutOfBandFx`, G9 `PerMonthCapBreached`,
  G14 `JurisdictionNotActivated`), it references `50-infra/etzhayyim-kawase-pool/`
  and the L4 `kawase_pool_match` cell, and it is gated on the Adherent SBT. This
  is single-actor, charter-bound business logic; it belongs with the kawase-yui
  actor, not as an orphan sibling of the engine.
- **`kotoba_murakumo` → engine core.** Already landed in the submodule
  (ADR-2606074000). Although it binds the religious-corp Murakumo-only invariant
  and the Charter scan, the binding is a thin shim with fallbacks and a
  configurable fleet path; the founder confirmed engine-core placement.

## Consequences

- **Positive**: each sibling now lives at the layer its nature dictates;
  `40-engine/` no longer holds orphan consumer packages; the engine's generic
  surface (iso20022) is reusable upstream; the actor's client surface (kawase)
  is discoverable next to its manifest/cells/lex.
- **Path adjustments**: `kotoba_iso20022` test_bridge resolves to the monorepo
  root (`parents[3]→parents[5]`) and skips when the Lexicon is absent;
  `kotoba_kawase` test_layer_composition resolves to the monorepo root
  (`parents[3]→parents[4]`). The kawase cross-layer test that probes the
  submodule's `kawase_pool_match` cell only passes when the submodule is
  populated (i.e. the real monorepo, not a bare worktree).
- **Submodule pointer**: the monorepo advances `40-engine/kotoba` to the commit
  adding `py/kotoba_iso20022/` (stacked on the local kotoba line per the minimal-
  change decision in ADR-2606074000; upstream contribution tracked via a separate
  clean PR).
- **Rule going forward**: a new kotoba-prefixed Python package is placed by the
  three-bucket test above, NOT by the retired subrepo-era "consumers live
  outside" heuristic.
