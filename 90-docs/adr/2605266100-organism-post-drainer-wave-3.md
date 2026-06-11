---
id: adr-2605266100-organism-post-drainer-wave-3
title: "ADR-2605266100: Organism Post Drainer (Wave 3) Minimal Implementation"
status: proposed
doc_type: adr
topic: unispsc-organism-post-drainer
authoritative: true
last_verified: 2026-05-26
priority: 7.5
axis: architecture
weight: 0.75
priority_note: "Wave 3 deliverable: A standalone TS drainer sidecar that tails the NDJSON queue populated by the Python organism cell and dispatches AT Protocol messages and posts via @etzhayyim/sdk. Enforces the substrate boundary."
authoritative_for:
  - Wave 3 drainer TS minimal implementation design
  - Inter-organism messaging dispatch logic
depends_on:
  - adr-2605240100-unispsc-organism-post-sink-substrate-bridge
  - adr-2605232345-unispsc-actor-as-organism
  - adr-2605266000-organism-inter-messaging
related: []
supersedes: []
superseded_by: []
---

# ADR-2605266100: Organism Post Drainer (Wave 3) Minimal Implementation

**Status**: proposed
**Date**: 2026-05-26
**Deciders**: Jun Kawasaki

# Context

ADR-2605240100 defined an NDJSON queue pattern for UNSPSC organisms to output Shinka posts. ADR-2605266000 introduced inter-organism messaging using encrypted envelopes over AT Protocol Lexicons. The Python cell process (Wave 1 & 2) writes to a local `emptyDir` NDJSON file to avoid importing AT Protocol substrate dependencies.

Wave 3 requires the implementation of the `drainer` sidecar. The drainer is a TypeScript daemon that runs adjacent to the cell in the same pod. It tails the NDJSON file, validates the records, handles encryption (for messages), and dispatches to the AT Protocol PDS via the `@etzhayyim/sdk`.

# Decision

1. **Daemon Implementation:** We will implement a minimal TS daemon in `40-engine/kotoba/crates/kotoba-kotodama/sdk/kotodama-host-sdk/src/drainer/` (or a new dedicated package `organism-post-drainer` under `20-actors/etzhayyim-organism/`). The daemon will `tail -f` the NDJSON file and dispatch each line to the PDS.
2. **K8s Manifest Update:** Uncomment the `drainer` container spec in `shard-0`, `shard-1`, and `shard-2` DaemonSets, activating the Wave 3 deployment footprint.
3. **Dispatch Logic:**
   - Lines with `lexicon="app.bsky.feed.post"` will be dispatched as standard Shinka posts.
   - Lines with `lexicon="com.etzhayyim.organism.message"` will be recognized as inter-organism messages. The drainer will parse the message intent and, in a future phase, perform Signal keywrap encryption before PDS dispatch (per ADR-2605266000). The minimal implementation will log this capability.

# Consequences

- **Positive:** Completes the Wave 3 milestone and bridges the organism internal behavior with the visible PDS substrate.
- **Negative:** Adds complexity to the TS side with tailing file management and eventual cryptographic operations.

# References
- ADR-2605240100
- ADR-2605266000
