---
id: adr-2605266400-organism-memory-persistence-r0
title: "ADR-2605266400: Organism long-term memory persistence R0"
status: proposed
doc_type: adr
topic: unispsc-organism-memory
authoritative: true
last_verified: 2026-05-26
priority: 6.5
axis: architecture
weight: 0.65
priority_note: "Provides long-term memory persistence for artificial organisms. Solves the amnesia problem where the bounded in-memory InboxBuffer loses historical context across cell restarts, pod evictions, or shard rebalances. Defines hot, warm, and cold memory tiers connected to the kotoba-kqe storage substrate."
authoritative_for:
  - Organism memory persistence tiering (hot/warm/cold)
  - Memory flush and archive events (cell tick, daily cron)
  - Read path contracts for memory retrieval
  - Kaizen agent integration for long-term trend analysis
depends_on:
  - adr-2605232345-unispsc-actor-as-organism
  - adr-2605262130-kotoba-storage-substrate-unification
related:
  - adr-2605240100-unispsc-organism-post-sink-substrate-bridge
  - adr-2605240200-unispsc-organism-kaizen-self-reflection
  - adr-2605266300-organism-lifecycle-r0
supersedes: []
superseded_by: []
---

# ADR-2605266400: Organism long-term memory persistence R0

**Status**: proposed
**Date**: 2026-05-26
**Deciders**: Jun Kawasaki

# Context

ADR-2605232345 introduced the `InboxBuffer` as the short-term working memory for artificial ecosystem organisms. This buffer holds recent inbound commits, reactions, follower wellness deltas, and mood shifts. However, `InboxBuffer` is explicitly **bounded and in-memory**.

This creates a critical amnesia problem:
- **Restarts:** If an organism cell restarts, pod crashes, or the organism is migrated during shard rebalancing, the `InboxBuffer` is cleared.
- **Short-sightedness:** Organisms cannot remember interactions beyond the limited capacity of their hot working memory.
- **Lost Context:** The Kaizen agent (ADR-2605240200) currently reads only recent tick data and queue tails, limiting its ability to observe long-term behavioral trends or systematic drift across an organism's lifecycle.

To be true artificial organisms, these actors need **long-term memory persistence**. This ADR defines the R0 architecture for memory tiering, relying on `kotoba-kqe` arrangements (ADR-2605262130) as the canonical storage substrate for historical observations.

# Decision

We adopt a three-tier memory architecture for organism observations: **Hot, Warm, and Cold**.

## 1. Storage Tiers

### Hot (In-Memory)
- **Store:** `InboxBuffer` (in-memory dataclass).
- **Scope:** Current tick and immediate recent history.
- **Prune Policy:** Bounded by strict item counts (existing constraint per ADR-2605232345).
- **Read Path:** `hot_sample()` — fast, synchronous access for immediate mood calculation and response generation.

### Warm (kotoba-kqe Substrate)
- **Store:** `kotoba-kqe` arrangement (EAVT/AEVT/AVET/VAET).
- **Scope:** Recent history, typically the last 7 days of interactions and mood shifts.
- **Prune Policy:** Size-bounded per organism (e.g., ≤100MB per organism). Older records are truncated once they reach the cold tier or exceed the warm capacity limit.
- **Read Path:** `warm_lookup(key, n)` — retrieves the last `n` records matching a specific context key or topic.

### Cold (IPFS / Archival)
- **Store:** IPFS-pinned subdataset (via `kotoba-store` S3 backend for cold tiering).
- **Scope:** Permanent archival history of the organism's entire lifecycle.
- **Prune Policy:** Permanent (append-only).
- **Read Path:** `cold_resolve(cid)` — asynchronous retrieval of historical dataset shards via their Content Identifier.

## 2. Persistence Events

The transition of memory from hot to warm to cold is driven by ecosystem cadences rather than continuous synchronous writes:

- **Cell Tick (Hot → Warm Flush):**
  At the end of each `organism.tick()`, the accumulated hot observations (that were not previously flushed) are batched and asynchronously written to the `kotoba-kqe` substrate. This ensures the warm store is at most one tick behind the hot memory.

- **Daily Cron (Warm → Cold Archive):**
  A dedicated background cron job runs daily (or periodically based on data volume). It reads the tail of the warm `kotoba-kqe` store for the organism, bundles the observations into immutable chunks, computes the CID, and pins the bundle to the cold IPFS tier, simultaneously pruning the warm store's oldest records.

## 3. Read Path Contracts

Organisms and observer agents access these tiers via standard interfaces:

```python
class OrganismMemory:
    def hot_sample(self) -> list[Observation]:
        # Existing InboxBuffer access
        pass

    def warm_lookup(self, topic_key: str, limit: int = 50) -> list[Observation]:
        # Queries kotoba-kqe arrangements for recent history
        pass

    async def cold_resolve(self, cid: str) -> DatasetShard:
        # Fetches deep archival data from IPFS block store
        pass
```

*(Note: The exact Lexicon scaffold and `kqe` arrangement schemas are out of scope for R0 and will be defined in R1).*

## 4. KaizenObserver Integration

This tiering directly enhances the Kaizen ecosystem self-reflection (ADR-2605240200).
Currently, the `KaizenObserverCell` reads the NDJSON queue tails (representing the hot/warm boundary).
With this memory architecture, Kaizen rules can execute `warm_lookup()` to detect patterns over days rather than minutes.

For example, a new Kaizen rule can query the warm tier to detect if an organism has been locked in an extreme stress state for multiple days across restarts, something that cannot be observed from a flushed in-memory buffer.

# Consequences

## 正の効果 (Positive Effects)
- **Resilience:** Organisms survive cell restarts and pod evictions without losing their contextual memory.
- **Depth of Character:** Organisms can reference interactions from days ago, allowing for more complex responses and mood evolution.
- **Enhanced Kaizen:** The observer ecosystem gains visibility into long-term trends, enabling deeper self-correction proposals.
- **Substrate Alignment:** Heavily leverages the new `kotoba-kqe` engine (ADR-2605262130) as the native solution for structured history.

## 負の効果 / コスト (Negative Effects / Costs)
- **Storage Overhead:** Requires persisting state for 18,344 organisms. The 100MB warm limit per organism equates to ~1.8TB of warm `kotoba-kqe` state across the fleet, requiring careful capacity planning.
- **Tick Latency:** The hot-to-warm flush adds a background I/O operation to the cell tick.
- **Complexity:** Organisms must now merge `hot_sample()` and `warm_lookup()` contexts when synthesizing complex responses, requiring logic to deduplicate or prioritize memories.

## Out of Scope (for R0)
- The concrete Lexicon schema definitions for persisted observations.
- The exact `kotoba-kqe` arrangement keys.
- The implementation of the daily cron archiver.
- Cross-organism shared memories.

# References

- ADR-2605232345 — UNSPSC actor as ecosystem organism
- ADR-2605262130 — Kotoba Storage Substrate Unification
- ADR-2605240100 — UNSPSC organism post sink (substrate bridge)
- ADR-2605240200 — KaizenObserver ecosystem self-reflection
- ADR-2605266300 — Organism lifecycle R0
