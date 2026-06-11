---
id: doc-axis-9-saturation-survey-260527
title: "Cycle 72 axis-9 survey — matrix coverage saturation signal"
status: active
doc_type: reference
topic: axis-9-saturation-survey
authoritative: false
last_verified: 2026-05-27
authoritative_for:
  - cycle 72 axis-9 candidate investigation findings
  - matrix coverage saturation signal (Pattern F diminishing returns)
  - 1 known-deferred Cargo workspace orphan (hrse api/)
related:
  - doc-registry-matrix-cycles-58-69-retrospective-260527
  - doc-registry-enforcement-matrix-runbook-260527
supersedes: []
superseded_by: []
---

# Cycle 72 — axis-9 saturation survey

**Context**: cycles 59-66 found 4 new bug classes (axis-1 dupes,
relation, id-filename, md-links). Cycle 72 investigated 3 more
candidate surfaces to test whether Pattern F (detection-first) still
produces value.

**Result**: 3 candidates examined; 2 entirely clean; 1 found a single
isolated orphan. **Pattern F has reached diminishing returns.** The
8-axis matrix has substantively covered the repo's systematic drift
surfaces. Future axis-9+ work would primarily catch isolated single
findings rather than systematic bug classes.

## Candidates investigated

### Candidate A — JSON Schema `$defs` cross-references

**Question**: Do `$ref: "#/$defs/X"` entries point to declared `$defs`?

**Result**: 0 drift across 13 schema files.

**Verdict**: Clean surface. No axis warranted.

### Candidate B — `pyproject.toml` internal consistency

**Question**: Are there parse errors, missing project.name, or stale
etzhayyim-* dep refs (pre-cutover invariant)?

**Result**: 0 issues across 49 `pyproject.toml` files.

**Verdict**: Clean surface. No axis warranted.

### Candidate C — Cargo workspace member integrity

**Question**: Do declared `[workspace] members = [...]` resolve to
directories with their own `Cargo.toml`?

**Result**: 1 orphan across 16 Cargo workspaces:
- `60-apps/etzhayyim-project-hrse/Cargo.toml` declares member `api/`
  but the directory contains `appview/` + `main/` + no `api/` subdir.
  Sibling `MIGRATION-TODO.md` suggests this is documented-deferred
  pre-cutover state (matches the etzhayyimcojp/amanomibashira rename
  invariant pattern).

**Verdict**: Isolated drift, not systematic. Auto-fix not safe without
owner judgment (could be a rename-pending state). Document as
known-deferred; do not build a 9th axis for 1 finding.

## Cumulative Pattern F productivity

| Cycle | Candidate | Findings | Outcome |
|---|---|---|---|
| 59 | deps.toml dupes | 37 | Axis-1 augment (Pattern F first use) |
| 60 | Relation integrity | 1461 | Axis 6 (tracker) |
| 61 | id↔filename | 88 | Axis 7 (tracker) |
| 64 | depends_on coverage | 525 | Axis 6 extension |
| 66 | md-links | 86 | Axis 8 |
| **72** | **Schema $defs / pyproject / Cargo** | **0 / 0 / 1** | **No axis warranted** |

Pattern F find-rate: 5 productive cycles (avg ~480 findings/cycle in
the productive range) → cycle 72's 1 isolated finding (-99% efficiency).

## Matrix coverage saturation signal

The 8-axis matrix's actual coverage map:

| Surface | Axis | Coverage |
|---|---|---|
| Repo path book-keeping | 1 | ✓ |
| Doc frontmatter shape | 4 | ✓ |
| Doc registry sync | 2 | ✓ |
| Doc relation graph | 3 | ✓ |
| Doc relation semantics | 6 | ✓ (6 fields) |
| Doc id↔filename | 7 | ✓ |
| Doc body markdown links | 8 | ✓ |
| App manifest shape | 5 | ✓ |
| JSON Schema $defs refs | — | (clean, no axis) |
| pyproject.toml consistency | — | (clean, no axis) |
| Cargo workspace integrity | — | (1 known, no axis) |

The remaining drift surfaces are either:
- Already covered by an axis (5+3 = 8 axes operational)
- Clean enough not to need enforcement (3 candidates above)
- Documented-deferred (lexicon 3198 / kotoba symlinks / hrse api orphan)
- Constitutional (cycle 47's `(reserved)` / `(deferred-rename)` markers)

## Recommendation for `/loop` continuation

Pattern F has saturated. Future cycles in this arc are diminishing
returns. Productive next directions:

1. **Move out of registry enforcement** — pivot to substantive product
   work (Tier-B actors, Council Bootstrap, real-network smoke).
2. **Chip tracker baselines manually** — 1011 + 53 + 33 mostly need
   per-entry judgment, not auto-fix.
3. **CLAUDE.md row #79 catch-up** — long-deferred housekeeping.
4. **Lexicon validation deep dive** — 3198 known violations under
   `validate-religious-corp-lexicons`; might find an axis-9 if
   investigated for systematic class.

Option 4 is the only one that might re-engage Pattern F.

## Known-deferred items captured

- **hrse Cargo workspace orphan** (`60-apps/etzhayyim-project-hrse/`):
  member `api/` declared but no `api/Cargo.toml` exists. Files
  `appview/` + `main/` + sibling `MIGRATION-TODO.md` suggest
  pre-cutover rename state. Owner action needed.

## References

- ADR-2605271100 / ADR-2605271200 — closure ADRs
- Cycle 58 retrospective (cycles 46-57)
- Cycle 70 retrospective (cycles 58-69)
- Cycle 71 operator runbook refresh
