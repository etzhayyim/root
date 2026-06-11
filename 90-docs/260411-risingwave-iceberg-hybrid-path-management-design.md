# Kotoba/Datomic Iceberg Hybrid Path Management Design

**Date**: 2026-04-11
**Status**: Proposed
**Scope**: `50-infra/linode/kotoba-iceberg`

## Decision

Adopt a hybrid 3-layer management model for `path`, `blocker`, and `kosei`.

1. `deps.toml` is the machine-readable source for current selection, active blockers, and authoritative links.
2. `paths/ACTIVE.md` is the short operational summary that an LLM or human should read first inside the component.
3. `90-docs` holds the long-form Shannon comparison, rationale, and evidence trail.

## Why Hybrid

`deps.toml` alone is strong for tooling but becomes noisy when architecture reasoning grows.
`90-docs` alone is readable but too far from the component during editing.
The hybrid split keeps current-state answers local while preserving full design history in a canonical document.

## Layout

```text
50-infra/linode/kotoba-iceberg/
  deps.toml                  # selected_path, blockers, authoritative links
  paths/
    ACTIVE.md                # current path, blockers, rollback, next actions
    BACKLOG.md               # candidate/fallback overview
    path-a-built-in-env.md
    path-b-lakekeeper-rest.md
    path-c-lakekeeper-rest-rust.md
    path-d-nessie-sinks.md
    path-e-hummock-only.md

90-docs/
  260411-kotoba-iceberg-hybrid-path-management-design.md
```

## Shannon Comparison

| Method | Strength | Weakness | Shannon eta |
|---|---|---|---:|
| `deps.toml` only | strongest machine readability | becomes too verbose for design tradeoffs | 0.84 |
| `90-docs` only | strongest narrative clarity | far from the edited component | 0.60 |
| `paths/` only | good locality and readability | weaker structured discovery | 0.74 |
| central registry only | great global indexing | high drift risk from the component | 0.65 |
| hybrid | balances locality, structure, and long-form evidence | slightly more files | 0.89 |

## Rules

- `deps.toml.invariants.selected_path` and `paths/ACTIVE.md` must always match.
- A path change must update `rollback_path` and `active_blockers`.
- Long-form benchmark data, vendor links, and Shannon tables belong in `90-docs`, not in `deps.toml`.
- `paths/path-*.md` files stay short and stable: summary, strength, weakness, use-when.

## Initial Selection

Current recommendation is `Path C: Lakekeeper + rest_rust`.

- It removes Java `S3FileIO` from the data path.
- It preserves standard Iceberg REST catalog interoperability.
- It keeps `Path E: Hummock only` as the clean rollback target.
