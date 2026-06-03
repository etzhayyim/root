---
id: adr-2605270200-assembler-operator-readability-arc-closure
title: "ADR-2605270200: ADR-2605262400 §4 cold-path assembler operator-readability arc — caps (rows + bytes) + description fields (Recipe / output_metadata / per-source) + --summary markdown verb + seed-block honesty + Recipe.warnings()"
status: proposed
doc_type: adr
topic: assembler-operator-readability
authoritative: true
last_verified: 2026-05-27
priority: 6.5
axis: architecture
weight: 0.20
priority_note: "Closure amendment to ADR-2605262400 §4 (cold-path corpus assembler at 70-tools/baien-moemoekyun-train/scripts/assemble-public-corpus.py). Records an 8-commit operator-readability arc landed 2026-05-27 JST across ~9 autonomous /loop cron windows that brought the assembler from 'works correctly but operator can't tell what just happened' to 'every gap visible at three independent surfaces (stderr / dry-run JSON / --summary markdown)'. No ADR-2605262400 invariant is changed — this is operator-visibility scaffolding on top of an unchanged core. Real-data verified on 4 in-tree recipes (tier-a-netreg-foundations / tier-a-routing / tier-c-dns-graph-nc / tier-a-geo-and-netreg-mixed); moemoekyun-r1.4-coding-math.toml uses a different schema (ipfs_dag_cid + note vs datasetPin_at + description) and was deliberately not migrated. 41/41 assembler unit tests pass. Also documents an infra-hygiene pass: chopped-suffix typo fixes (1 broken production import, 4 broken test imports from parallel-agent commit 023988900) + langsmith pytest plugin disable across all 5 in-tree Python packages with [tool.pytest.ini_options]."
authoritative_for:
  - ADR-2605262400 §4 cold-path assembler operator-readability state as of 2026-05-27
  - Recipe TOML schema additions: description (top-level + per-source) + max_rows + max_bytes
  - dry_run_summary() JSON shape additions: description / outputMetadata / sources[] / placeholderPins / warnings[] / seedBlock.exists
  - assemble() manifest shape additions: description / outputMetadata / bytesEmitted / effective*Cap / *CapHit / seedBlock.sourcePathExisted
  - assemble-public-corpus.py --summary CLI verb (markdown render)
  - 5 in-tree Python packages' pytest pyproject hardening against langsmith plugin pydantic-core crash
depends_on:
  - adr-2605262400-public-data-organism-ipfs-ingestion
  - adr-2605270100-public-data-organism-ipfs-ingestion-closure
related:
  - adr-2605262100-baien-moemoekyun-r1-phase0-coding-train
  - adr-2605262130-kotoba-storage-substrate-unification
supersedes: []
superseded_by: []
---

# ADR-2605270200: assembler operator-readability arc closure

**Status**: proposed
**Date**: 2026-05-27
**Deciders**: Jun Kawasaki

## Context

ADR-2605262400 (2026-05-26) landed the public-data ingestion substrate
including a cold-path corpus assembler at
`70-tools/baien-moemoekyun-train/scripts/assemble-public-corpus.py`.
The assembler was functionally complete (real-data verified per
ADR-2605270100 closure) but operator-readability was thin:

- Recipes lacked context fields — an operator opening a 6-month-old
  `manifest.json` from cold storage saw `targetArtifact: "baien-server-x-v1"`
  and a list of subdataset paths, but no explanation of what the
  corpus was meant to contribute.
- `[output_metadata] description = """..."""` blocks were loaded into
  `Recipe.output_metadata` and then silently dropped — a latent defect.
- A recipe declaring `[seed_block] weight = 0.5` whose `seed_path`
  didn't resolve on disk would silently emit ZERO seed rows, with no
  visible signal in any output. All 5 in-tree recipes hit this RIGHT
  NOW (no `seed-blocks/` directory exists anywhere in the tree).
- Operators had no way to bound a single-source's emission for huge
  sources (e.g. RIPE-RIS bview NDJSON with 5–10M rows) without
  iterating the full file.

Across ~9 autonomous `/loop 30min 進めて` cron windows on 2026-05-27 JST,
8 commits closed the operator-readability gap end-to-end without
changing any ADR-2605262400 invariant.

## Decision

The cold-path assembler now exposes three independent operator-visibility
surfaces for every recipe + every assembly run:

| Surface | Audience | Render |
|---|---|---|
| `--dry-run` (stdout) | Machine / CI / tooling | JSON with `description` / `outputMetadata` / `sources[]` per-source preview / `placeholderPins` / `warnings[]` / `seedBlock.exists` |
| stderr | Always-on terminal output | `WARN:` lines from `Recipe.warnings()` |
| `--summary` (stdout) | Human / browsing recipe docs | Markdown with description / metadata / `## ⚠ Issues (N non-fatal advisories)` / per-source sections / seed-block presence |

The assemble manifest (`manifest.json` persisted to disk) mirrors the
dry-run shape: `description` / `outputMetadata` / per-source `bytesEmitted`
+ `effectiveRowCap` + `capHit` + `effectiveByteCap` + `byteCapHit` +
`description` / `seedBlock.sourcePathExisted`.

### Schema additions (TOML)

```toml
# Top-level (new)
description = "..."

[output_metadata]   # was silently dropped; now propagated
license_summary = "..."
intended_use = "..."

[[source]]
description = "..."           # new
max_rows = 1000               # new (per-source)
max_bytes = 524288            # new (per-source)
```

### CLI additions

```bash
# Bounded row emission (head-biased, NDJSON-clean cap)
--max-rows-per-source N
# Bounded byte emission (head-biased, NDJSON-clean cap)
--max-bytes-per-source N
# Operator-facing markdown summary
--summary
```

### API additions

```python
recipe.description: str = ""
recipe.warnings() -> list[str]       # non-fatal, distinct from validate()
SourceSpec.description: str = ""
SourceSpec.max_rows: int = 0          # 0 = no cap
SourceSpec.max_bytes: int = 0         # 0 = no cap
```

### Two warning families today (R1)

1. **Missing seed-block file** — declared weight, file absent ⇒ honest
   warning + dry-run `seedBlock.exists = false` + manifest
   `seedBlock.sourcePathExisted = false` + markdown `## Seed block — ⚠ MISSING`.
2. **Placeholder datasetPin pins** — `PLACEHOLDER_X` in `datasetPin_at`
   detected at parse time (assembly will hard-fail later; the warning
   surfaces the gap at dry-run time).

## Consequences

**Positive (intended)**:

- 6-month-cold-storage manifest reading: an operator opening a
  `manifest.json` sees a one-paragraph context note for the recipe +
  one-line context for each source.
- `--dry-run` machine-readable consumers can gate on `warnings.length > 0`
  without parsing stderr.
- `--summary` markdown verb produces a single-file recipe browser —
  useful for code review, recipe-author hand-off, or sidecar `.md`
  per recipe.
- All 5 in-tree corpus recipes now surface their (currently-broken)
  state visibly: missing seed-block files (all 5) + placeholder pins
  (7 of 7 sources in `tier-a-netreg-foundations.toml`). Operator can
  see what needs authoring or pinning before attempting full assembly.

**Negative (accepted)**:

- Schema additions are purely additive — existing recipes without
  new fields default to `""` / `0` / `False` safely. No backward-compat
  shim needed.
- `--summary` is operator-facing only; it does NOT modify state and
  is not part of the assembly contract.

**Behavioral fix deferred**:

The assembler still silently skips missing seed-block files at
assembly time. The right fix (refuse-to-assemble vs auto-stub vs
warn-only) requires operator policy input — whether seed-block
content will be committed in-tree or operator-generated externally.
This ADR closes the *visibility* gap; the *behavioral* call is
deferred to whoever authors the seed-block content.

**Out of scope (not addressed by this arc)**:

- `seed-blocks/` directory is still empty. Authoring canonical
  synthetic Q/A for the 5 in-tree recipes is operator-policy work
  (the content gets used to train baien-moemoekyun-* and propagates).
- `moemoekyun-r1.4-coding-math.toml` uses a different schema
  (`ipfs_dag_cid` + `note` instead of `datasetPin_at` + `description`)
  and is consumed by a different code path. Not migrated.

## Implementation map (8 commits landed 2026-05-27 JST)

| # | Commit | Change | Tests |
|---|---|---|---|
| 1 | `a28db5b48` | `--max-rows-per-source` CLI flag + per-source `max_rows` override | smoke-only |
| 2 | `ac211fdda` | Unit tests for `--max-rows-per-source` (8 cases) | 8/8 PASS |
| 3 | `f66fbdd9b` | `--max-bytes-per-source` CLI flag + per-source `max_bytes` override + byte accounting via refactored `_emit_corpus_row()` returning bytes | 22/22 (8 new) |
| 4 | `2fbe6b4ad` | Top-level `Recipe.description` field plumbed into dry-run + manifest | 24/24 (+2) |
| 5 | `3d90961b5` | Surface latent `Recipe.output_metadata` dict in dry-run + manifest (was loaded then discarded) | 26/26 (+2) |
| 6 | `503856f7b` | Per-source `SourceSpec.description` + dry-run `sources[]` preview array | 29/29 (+3) |
| 7 | `aa229d16b` | Backfill description content (top-level + per-source) on 4 in-tree corpus recipes | n/a (content) |
| 8 | `89d489cf7` | `--summary` markdown verb consuming all the above operator-readability fields | 32/32 (+3) |
| 9 | `532e2e331` | Fix 1-char-chopped-suffix typos from parallel-agent commit 023988900 (1 broken production import `pr_agent.py`, 4 broken test imports) | n/a (bugfix) |
| 10 | `24788a73f` | Disable langsmith pytest plugin in 2 pyproject.toml (e7m-dataset + magatama-py) — defeats pydantic-core mismatch on system Python | n/a (infra) |
| 11 | `0de43b5a6` | Extend langsmith pytest plugin disable to 3 more pyproject.toml (baien-moemoekyun-train + etzhayyim-py + graph-schema) | n/a (infra) |
| 12 | `e333b097a` | Surface missing seed-block files honestly (`seedBlock.exists` / `seedBlock.sourcePathExisted` / markdown `⚠ MISSING` header) | 34/34 (+2) |
| 13 | `265262e48` | `Recipe.warnings()` API + CLI stderr `WARN:` lines (seed-block missing + placeholder pins) | 37/37 (+3) |
| 14 | `1af62f427` | Warnings surfaced in dry-run JSON `warnings[]` + markdown `## ⚠ Issues` section | 41/41 (+4) |

13 of 14 commits are code; 1 is content backfill on existing recipes;
2 are infra (typo fixes + pytest config). All landed clean through the
full lefthook gate.

### Why 14 commits, not 1 ADR-up-front?

Each cron window picked a single concrete bounded task. The arc was
not planned end-to-end — it emerged from "now that I just shipped X,
the natural complement is Y." Documented here retroactively as a
single arc so a future reader can see the operator-readability story
as one thing rather than chasing 14 mostly-unconnected commits.

## Alternatives Considered

**Refuse-to-assemble on missing seed-block file** (behavioral fix
deferred): Considered for commit `e333b097a` but rejected — the
visibility fix is sufficient operator information; rejecting the
recipe outright forces the operator to either author content or
mutate the recipe, neither of which is a decision the assembler
should make unilaterally.

**Add the new fields to a separate `[recipe_meta]` table**: Considered
for top-level `description` — rejected because `description` is also
used inside `[seed_block]` and `[[source]]` blocks; flat top-level
matches the existing TOML idiom.

**Unify `note` (in `moemoekyun-r1.4-coding-math.toml`) with new
`description`**: Considered as part of commit `aa229d16b` — rejected.
`note` is an unrelated field consumed by a different code path
(the recipe uses `ipfs_dag_cid` instead of `datasetPin_at`). Migrating
that recipe would require resolving the schema split first, which is
out of scope for this arc.

## References

- ADR-2605262400 — the substrate this arc decorates
- ADR-2605270100 — the §4.3 perception-path closure that landed the same week
- `70-tools/baien-moemoekyun-train/scripts/assemble-public-corpus.py` (assembler)
- `70-tools/e7m-dataset/tests/test_corpus_assembler.py` (21 tests)
- `70-tools/e7m-dataset/tests/test_corpus_assembler_caps.py` (16 tests)
- `70-tools/baien-moemoekyun-train/recipes/{tier-a-netreg-foundations,tier-a-routing,tier-c-dns-graph-nc,tier-a-geo-and-netreg-mixed}.toml` (4 backfilled recipes)
