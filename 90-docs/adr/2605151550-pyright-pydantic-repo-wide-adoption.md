---
id: adr-2605151550
title: "Pyright and Pydantic Repo-Wide Adoption"
status: active
doc_type: adr
topic: toolchain
authoritative: true
last_verified: "2026-05-15"
---

# ADR 2605151550: Pyright and Pydantic Repo-Wide Adoption

**Date:** 2026-05-15
**Status:** Accepted
**Author:** AI Assistant

## Context

The repository contains a large and growing number of Python components (27+ sub-projects) distributed across different directories (`20-actors`, `40-engine`, `60-apps`, `70-tools`). While the ecosystem heavily relies on TypeScript for the frontend and Node.js components, the Python ecosystem suffered from inconsistent type-checking and runtime validation standards.

Previously, `pyright` and `pydantic` were used selectively, leading to:
1. Implicit `Any` propagation resulting in runtime `AttributeError`s and `TypeError`s (especially when dealing with `None` from dict `.get()` calls).
2. Unreliable dictionary shapes when processing JSON payloads from external systems or databases (e.g., Kotoba/Datomic `fetch_all` returning tuples vs dicts).
3. Weak developer experience and missed regressions during refactoring.

## Decision

We are adopting **Pyright (strict basic type-checking)** and **Pydantic (runtime validation)** globally across all Python sub-projects in the monorepo.

1. **Dependency Management**: Every `pyproject.toml` (27 in total) has been updated to include `pydantic>=2.7.0` in the main dependencies and `pyright>=1.1.300` in the `dev` dependencies.
2. **Global Pyright Configuration**: A root `pyrightconfig.json` has been introduced. It dynamically includes all valid Python source directories while aggressively ignoring non-Python assets (`node_modules`, `dist`, `.venv`, etc.) to prevent workspace enumeration timeouts.
3. **Pre-Push Hook**: A `pyright-check` step (`uvx pyright`) has been added to `lefthook.yml` under the `pre-push` stage. This prevents code with type violations from being pushed to the remote repository.
4. **Codebase Hardening**: Over 3,000 type errors were resolved across critical components, particularly in `20-actors/magatama/py/src/pymagatama`. This involved:
   - Replacing ambiguous `dict.get()` patterns with explicit `isinstance` checks or typed cast defaults.
   - Refactoring database layer types (e.g., `db_sync.py` and `db_alchemy.py`) to correctly type return rows and cursor arguments.
   - Implementing `# type: ignore` locally for dynamic or untypable external modules (like `alembic.context`).

## Consequences

### Positive
- **Early Bug Detection**: The vast majority of `NoneType has no attribute X` errors will now be caught statically before runtime.
- **Improved Code Quality**: Interfaces and function signatures are now unambiguous, improving readability and maintainability.
- **Standardization**: All Python code in the repository now adheres to the same baseline type safety standard.

### Negative
- **Friction in Prototyping**: Developers must now satisfy the Pyright type-checker before pushing. This adds overhead when quickly prototyping or dealing with deeply nested JSON where full typing is tedious.
- **External Library Issues**: We may encounter "false positives" from poorly typed external libraries, requiring developers to add explicit `# type: ignore` comments or type stubs.
