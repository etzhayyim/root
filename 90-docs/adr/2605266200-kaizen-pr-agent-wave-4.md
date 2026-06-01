---
id: adr-2605266200-kaizen-pr-agent-wave-4
title: "ADR-2605266200: Kaizen PR agent Wave 4 — PR draft generation"
status: proposed
doc_type: adr
topic: unispsc-organism-kaizen
authoritative: true
last_verified: 2026-05-26
priority: 7.0
axis: architecture
weight: 0.70
priority_note: "Introduces the Wave 4 PR agent component: a pure function mapping a KaizenProposal to a Markdown PR draft. This bridges the observer ecosystem output with human/agent PR review workflows."
authoritative_for:
  - KaizenProposal to PR draft markdown transformation
depends_on:
  - adr-2605240200-unispsc-organism-kaizen-self-reflection
related: []
supersedes: []
superseded_by: []
---

# ADR-2605266200: Kaizen PR agent Wave 4 — PR draft generation

**Status**: proposed
**Date**: 2026-05-26
**Deciders**: Jun Kawasaki

# Context

Following ADR-2605240200, the organism ecosystem has a `KaizenObserverCell` that observes the fleet and emits `KaizenProposal` records as NDJSON. The next step is to actually action these proposals.

Before introducing the full cron-driven PR-agent machinery (which requires GitHub API integration, branch management, etc.), we need to establish the deterministic core: converting a structured `KaizenProposal` into a human-readable Markdown Pull Request body.

# Decision

We are implementing a pure function: `kaizen_proposal_to_pr_draft(proposal_ndjson: str) -> str`.

1. **Input**: A single NDJSON string representing a `KaizenProposal`.
2. **Output**: A formatted Markdown string.
3. **Behavior**:
   - Parses the JSON.
   - Validates that `kind` is `"kaizen-proposal"`.
   - Extracts `summary`, `detail`, `ruleId`, `category`, `severity`.
   - Formats `suggestedAction` including `description`, `targetFiles`, `patchHint`, and `testPlan`.
   - Emits a final Markdown string suitable for use as a GitHub Pull Request body.

By isolating this as a pure function, we make it trivially unit-testable and independent of any specific Git or GitHub SDK. The surrounding PR agent can just call this function and pass the result to the GitHub API.

## Next Steps

In subsequent iterations, the PR agent cron job will be built to tail the proposal NDJSON queue, execute the patch (using LLM or deterministic sed/awk), and open the PR using this generated draft as the body.
