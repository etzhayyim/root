---
id: "2606071300"
title: "Deprecate yata and lancedb-wasm in favor of kotoba, enable Dependabot auto-merge"
status: "accepted"
doc_type: "adr"
topic: "infrastructure-management"
authoritative: true
authoritative_for:
  - ".github/workflows/dependabot-auto-merge.yml"
related:
  - "2605262130"
---

# Deprecate yata and lancedb-wasm in favor of kotoba, enable Dependabot auto-merge

## Context and Problem Statement

The `50-infra/yata` and `50-infra/lancedb-wasm` directories contained legacy implementations and forks related to the prior execution layer architecture. With the consolidation to the `kotoba` substrate engine as the single source of truth for the religious-corp graph (as declared in ADR-2605262130), these legacy components are obsolete.

Simultaneously, Dependabot has been opening numerous PRs for these and other repositories. The overhead of manually checking CI status and merging these automated PRs is high.

## Decision Drivers

*   Consolidate all database/graph functionality into the `kotoba` engine.
*   Reduce technical debt by deleting obsolete code (`yata` and `lancedb-wasm`).
*   Reduce maintenance burden by automating the merging of Dependabot updates when they pass all required CI checks.

## Considered Options

*   **Option 1:** Keep the directories as cold backups indefinitely.
*   **Option 2:** Delete the directories and enable auto-merge. (Chosen)

## Decision

1.  **Deletion:** We will completely remove `50-infra/yata` and `50-infra/lancedb-wasm`. They are now deprecated in favor of `kotoba`.
2.  **Dependabot PRs Closed:** All pending Dependabot pull requests related to these deleted directories will be closed.
3.  **Auto-Merge Enabled:** We are enabling Dependabot auto-merge. This involves two steps:
    *   Enabling `Allow auto-merge` via the repository settings API.
    *   Adding a GitHub Actions workflow (`.github/workflows/dependabot-auto-merge.yml`) that explicitly calls `gh pr merge --auto --squash` when the actor is `app/dependabot` and CI passes.

## Consequences

*   **Positive:** A cleaner repository with fewer outdated infrastructure components. Less manual overhead for maintaining dependencies.
*   **Negative:** None. Any required components from the `lancedb-wasm` or `yata` era have been successfully migrated or entirely superseded by `kotoba`.
