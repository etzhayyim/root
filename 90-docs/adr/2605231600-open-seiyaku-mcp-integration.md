---
id: adr-2605231600-open-seiyaku-mcp-integration
title: "Open Seiyaku Robotics MCP Integration"
status: accepted
doc_type: adr
topic: open-seiyaku
authoritative: true
last_verified: 2026-05-23
authoritative_for:
  - open-seiyaku-mcp
  - robotics-supply-chain-visualization
  - social-posting-integration
related:
  - adr-2604271830-patent-expired-pharma-seiyaku-handoff
  - 40-engine/kotoba/crates/kotoba-kotodama/mcp/open-seiyaku-mcp
supersedes: []
superseded_by: []
---

# Context

To bridge the gap between AI models (like Claude) and the autonomous pharmaceutical robotic manufacturing workflows managed under the `open-seiyaku` domain, there is a need to expose specific supply chain interactions via the Model Context Protocol (MCP). The interactions requested cover triggering generic manufacturing candidates, visualizing the end-to-end robotic supply chain, and posting activity to the AT Protocol social feed.

# Decision

We are introducing `@etzhayyim/open-seiyaku-mcp`, an MCP server module within the monorepo workspace at `40-engine/kotoba/crates/kotoba-kotodama/mcp/open-seiyaku-mcp/`.

It exposes three distinct tools:

1.  **`start_generic_manufacturing_candidate`**: A programmatic hook aligning with the `com.etzhayyim.apps.openPatent.startGenericManufacturingCandidate` lexicon. It triggers the pharmaceutical robotic workflow pipeline for patent-expired items.
2.  **`visualize_pharma_supply_chain`**: Generates Mermaid.js diagrams to visualize the supply chain logistics, spanning from the expired patent screening, procurement, robotics manufacturing (tending/handling), quality release, port logistics, and hospital/pharmacy delivery.
3.  **`post_to_etzhayyim_social`**: Bridges the manufacturing pipeline's events to the `yoro.etzhayyim.com` social feed, allowing for visible, verifiable automation milestones published by the `did:web:seiyaku.etzhayyim.com` actor.

The module is registered as a fully-fledged ecosystem actor through its `kotodama.jsonld` file and integrates directly with `.claude/mcp.json` using `tsx`. For production deployments, a `Dockerfile` and a Kubernetes Deployment manifest (`50-infra/k8s/open-seiyaku-mcp/deployment.yaml`) have been generated.

# Consequences

- **Accessibility**: Agents running within Claude or Cursor can now visually trace the pharmaceutical robotic supply chain and interact with the workflow directly without creating manual XRPC/ATProto requests.
- **Traceability**: All events can be logged seamlessly onto the social layer, satisfying organizational transparency mandates.
- **Ecosystem Integration**: The addition maps well into the existing MCP integrations established in ADR-2605180900 (unispsc-isic-mcp), expanding the standard for creating self-contained Agent-driven endpoints using `kotodama.jsonld`.
