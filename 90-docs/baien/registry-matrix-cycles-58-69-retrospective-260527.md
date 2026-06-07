---
id: doc-registry-matrix-cycles-58-69-retrospective-260527
title: "Registry enforcement matrix Part 2 — cycles 58-69 retrospective (8-axis defense-in-depth)"
status: active
doc_type: reference
topic: registry-matrix-part2-retrospective
authoritative: false
last_verified: 2026-05-27
authoritative_for:
  - cycles 58-69 chronology — 8-axis matrix expansion from 5 to 8 axes
  - detection-first / categorize / auto-fix pattern productivity numbers
  - silent-bug-hunt discoveries (4 new bug classes found post-cycle-58)
  - tracker-mode + retrofit patterns
related:
  - doc-registry-matrix-cycles-46-57-retrospective-260527
  - adr-2605271200-registry-4-axis-enforcement-matrix
  - doc-registry-enforcement-matrix-runbook-260527
supersedes: []
superseded_by: []
---

# Registry enforcement matrix Part 2 — cycles 58-69 retrospective

**Period**: 2026-05-27 JST cycles 58-69 (12 cycles, ~~3 wall hours)
**Trigger**: Continuation of /loop after cycle 58 retrospective marked
end of "Part 1" (cycles 46-57; 5-axis matrix)
**Outcome**: 5-axis → 8-axis matrix; 1107 data fixes; 3-layer defense
on every axis.

## Chronology — 12 cycles

| # | ~Time | Headline | Net effect |
|---|---|---|---|
| 58 | ~14 min | Cycles 46-57 retrospective | (closes "Part 1" arc) |
| 59 | ~22 min | 37 stale dupes removed + duplicate detection (axis-1 augment) | +1 detection class |
| 60 | ~20 min | 6th axis: relation integrity tracker (1461 baseline) | +1 axis |
| 61 | ~22 min | 7th axis: id↔filename consistency tracker (88→57) | +1 axis, 6 auto-fixed |
| 62 | ~10 min | Cycle-61 chipping (57→53; off-by-45 typo found) | +4 data fixes |
| 63 | ~16 min | Relation path-as-related auto-fix (346 across 155 files) | -349 relation issues |
| 64 | ~16 min | +depends_on coverage + 435 auto-fixes | -435 relation issues; new field tracked |
| 65 | ~10 min | 5-field id-norm (223 auto-fixes) | -213 relation issues |
| 66 | ~13 min | md-link wrong-absolute-prefix (54 fixes) | New surface investigated |
| 67 | ~16 min | 8th axis: md-link validator | +1 axis |
| 68 | ~10 min | Axis-8 defense-in-depth (lefthook + GHA) | Pattern A applied to axis 8 |
| 69 | ~12 min | Retrofit axes 6+7 with lefthook + GHA | **3-layer complete on all 8 axes** |
| 70 | (this) | Test coverage gap closed + this retrospective | depends_on tests added |

Total: ~181 min build time. Average ~15 min/cycle.

## Silent-bug-hunt discoveries

Following cycle 59's insight ("adding detection mechanisms after
observation > predicting in advance"), 4 new bug classes were found:

| Cycle | Discovery | Baseline initial |
|---|---|---|
| 59 | deps.toml duplicate paths/ids | 37 (cleaned in same cycle) |
| 60 | Dangling relations | 1461 (5-field tracking) |
| 61 | id↔filename mismatches | 88 (auto-fix to 57) |
| 64 | depends_on coverage gap | +525 in new field tracking |
| 66 | Broken in-repo markdown links | 86 (auto-fix to 33) |

Per-cycle find-rate: **5 distinct bug classes in 8 cycles** (one cycle had follow-up cleanup vs new discovery).

## Pattern catalogue extended

Cycle 52's 5 patterns extended by 2 more in cycles 59-69:

| Pattern | Use cases | First appearance |
|---|---|---|
| A — 3-layer enforcement (validator + lefthook + CI) | 8 axes | Cycles 27-30 |
| B — Tracker → PR-gate promotion | Axes 4, 6, 7, 8 | Cycle 50 → 51 |
| C — `(reserved)` / `(deferred-rename)` markers | Cross-ADR | Cycle 46 |
| D — Cron off-minute deconfliction | 8 GHA workflows | Cycles 30, 48-69 |
| E — Graceful optional-dep import | jsonschema | Cycle 50 |
| **F — Detection-first / categorize / auto-fix** | **Cycles 59-66** | **Cycle 59** |
| **G — Defense-in-depth retrofit** | **Cycles 68-69 (axes 6/7/8)** | **Cycle 68** |

## Total deliverables (cycles 58-69)

- **3 new validators**: validate-relation-integrity.py / validate-id-filename-consistency.py / validate-md-links.py
- **1 validator augmented**: verify_deps_toml_paths.py (cycle 59 duplicate detection)
- **3 new GHA workflows**: relation-integrity-validation.yml / id-filename-consistency.yml / md-link-validation.yml
- **3 new lefthook hooks**: relation-integrity / id-filename-consistency / md-link-validation
- **1107 data fixes** across 6 bug classes:
  - 37 deps.toml dupes
  - 346 path-as-related rewrites
  - 435 depends_on normalizations
  - 223 5-field id-normalizations
  - 6 uppercase-ADR-prefix cleanups
  - 4 engineering policy + 1 off-by-45 typo
  - 56 broken markdown link rewrites (54+2)
- **Test count growth**: 38 (cycle 56) → 85 (cycle 70)
- **2 retrospective docs**: cycles 46-57 (Part 1, cycle 58) + this (cycles 58-69, cycle 70)

## 8-axis matrix final state (cycle 69)

```
PR-gate axes (5):
  1. deps.toml book-keeping        (cycle 27-30 + 46 markers + 59 dupes)
  2. docs.json freshness           (cycle 48)
  3. graph.jsonld freshness        (cycle 49)
  4. docs+graph schema validation  (cycle 50 → 51)
  5. kotodama manifest validation  (cycle 53)

Tracker axes (3):
  6. relation integrity (6-field)  (cycle 60 + 64 depends_on)  baseline 1011
  7. id↔filename consistency       (cycle 61)                    baseline 53
  8. markdown link integrity       (cycle 67)                    baseline 33

Defense layers per axis (all 8 complete):
  - Validator/generator (CLI)
  - Lefthook pre-commit hook
  - GHA workflow (PR + nightly)
```

Cron spread (8 nightly workflows, 6-min apart): `:17 / :23 / :29 / :35 / :41 / :47 / :53 / :59`.

## Audit baseline post-cycle-70 (canonical state)

```
deps.toml:    566/581 resolve / 15 accepted-reserved / 0 drift / 0 dupes  EXIT 0
docs.json:    in sync (660 entries)                                          EXIT 0
graph.jsonld: in sync (660 nodes)                                            EXIT 0
schema:       0 docs + 0 graph errors                                        EXIT 0
kotodama:     42/42 valid                                                    EXIT 0
relation:     1011 known (6-field)                                           EXIT 0 / strict: 1
id-filename:  53 known (rename-pending floor)                                EXIT 0 / strict: 1
md-links:     33 known                                                       EXIT 0 / strict: 1
85 unit tests pass (1 cond-skip)                                             ALL PASS
9 e7m verify constitutional invariants                                       9/9 ✓
```

## Lessons learned

### What worked
1. **Detection-first cadence**: cycles 59-66 averaged 1 new bug class every 2 cycles. Looking for what's INVISIBLE to existing enforcement was the highest-leverage activity.
2. **Pattern F (categorize-then-auto-fix)**: 1107 fixes across 6 classes via 6 batch scripts. Categorization step prevented over-eager fixes.
3. **Tracker mode (Pattern B)**: Cycles 60+61+67 all shipped validators with non-zero baselines as nightly trackers. Avoided the "wait for cleanup before shipping" deadlock.
4. **Cycle 64 coverage gap**: `depends_on` was a real frontmatter field invisible to cycle 60's validator because the indexer (regen-registry.py) didn't surface it. Fixed by adding SURFACED_KEYS entry + schema property + validator field — but the gap remained invisible until I happened to look. **Coverage gaps are intrinsically silent.**
5. **Defense-in-depth retrofits (cycles 68-69)**: Axes 6+7 were CLI-only for 7+8 cycles before getting lefthook+CI. Once Pattern G was established, retrofit each axis took ~10 min.

### Friction
1. **Cycle 51's commit-retry-dance** (3 retries due to trailing whitespace) — encoded into hygiene-sweep snippet that cycles 52-69 used preemptively. Single-attempt clean commits became the norm.
2. **Cycle 66's audit-logic bug**: initial markdown-link audit treated absolute paths as repo-relative, under-counting by 47 entries. Self-test on validator logic would have caught this.
3. **Cycle 64 cascade**: adding depends_on to SURFACED_KEYS broke schema validation (additionalProperties: false rejects new fields). Tight coupling between SURFACED_KEYS + schema requires both to change together — should be tested.

## Future work

Per cycle 69 candidate list:
- Continue chipping tracker baselines (1011 + 53 + 33)
  - id-filename's 53 is rename-pending-blocked (constitutional)
  - relation's 1011 includes 813 dangling-related-truly-orphan (recreate-original-docs needed)
  - md-links' 33 mixes truly-broken + manual-judgment
- Look for axis-9 candidates:
  - Lefthook hook glob coverage (dead hooks)
  - Schema $defs references vs declarations
  - Cargo workspace member integrity
  - pyproject.toml internal consistency
- Other directions:
  - CLAUDE.md row #79 catch-up (housekeeping)
  - Tier-B actor follow-on (substantive product work)

## References

- ADR-2605271100 — Cycle 47 closure introducing `(reserved)` marker convention
- ADR-2605271200 — Cycle 52 closure documenting 4-axis matrix (axes 1-4)
- `90-docs/baien/registry-matrix-cycles-46-57-retrospective-260527.md` — Part 1 retrospective
- `90-docs/baien/registry-enforcement-matrix-runbook-260527.md` — Cycle 55 operator runbook (still authoritative)
- This file — Part 2 retrospective (cycles 58-69)
