---
id: adr-2605266300-organism-lifecycle-r0
title: "ADR-2605266300: organism lifecycle semantics R0 (birth, clone, retire, excommunication)"
status: proposed
doc_type: adr
topic: organism-lifecycle
authoritative: true
last_verified: 2026-05-26
priority: 6.5
axis: architecture
weight: 0.65
authoritative_for:
  - Organism lifecycle events (birth, clone, retire, excommunication)
  - Lexicon definitions for lifecycle events (`com.etzhayyim.organism.lifecycle`)
depends_on:
  - adr-2605232345-unispsc-actor-as-organism
  - adr-2605262700-chigiri-legal-procedure-tier-b-actor-r0
---

# ADR-2605266300: organism lifecycle semantics R0 (birth, clone, retire, excommunication)

**Status**: proposed
**Date**: 2026-05-26
**Deciders**: Jun Kawasaki

## Context

Following the establishment of the `artificial-organism` ecosystem and the transformation of UNSPSC actors into organisms (ADR-2605232345), we need formal semantics for the lifecycle events of these organisms. Until now, organisms existed in a somewhat amorphous state without well-defined genesis, replication, termination, or punitive mechanisms.

Furthermore, ADR-2605262700 defines the `chigiri` legal procedure, including the G12 excommunication process, which necessitates a corresponding lifecycle event at the organism level.

## Decision

We define four foundational lifecycle events for the organism ecosystem. These events will be represented as Lexicon schemas under `com.etzhayyim.organism.lifecycle` and will be persisted via on-chain attestation (either KotobaDatomic or Kotoba-KQE).

The 4 events are:

1.  **`birth`**:
    *   **Triggers**: Addition of a new UNSPSC code, propagation of a `chigiri.member_onboarding` actor, or manual attestation by Council Lv6+.
    *   **Semantics**: The genesis of a new organism entity.
2.  **`clone`**:
    *   **Triggers**: Shard rebalancing (e.g., during Wave 2 moving an organism from shard-0 to shard-1).
    *   **Semantics**: Duplication of an organism. It retains the same actor DID family but operates on a different shard/context.
3.  **`retire`**:
    *   **Triggers**: Deprecation of a UNSPSC code, completion of a designated role, or 30 days of inactivity.
    *   **Semantics**: Graceful termination of an organism. The organism goes dormant and ceases active processing.
4.  **`excommunication`**:
    *   **Triggers**: `chigiri` G12 procedure cross-actor invocation (ADR-2605262700). Requires Council Lv6+ ≥4/7 attestation.
    *   **Semantics**: Punitive and immediate termination/banishment of an organism from the ecosystem.

## Consequences

*   **Positive**: Provides a rigorous, structured lifecycle for the 18,000+ organisms, enabling automated garbage collection (`retire`), load balancing (`clone`), and governance enforcement (`excommunication`).
*   **Negative**: Adds complexity to the organism runtime, as every organism must now implement or be governed by these lifecycle state machines.
