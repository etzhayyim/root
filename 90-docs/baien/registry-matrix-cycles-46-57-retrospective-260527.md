---
id: doc-registry-matrix-cycles-46-57-retrospective-260527
title: "Registry enforcement matrix — cycles 46-57 retrospective (2026-05-27)"
status: active
doc_type: reference
topic: registry-matrix-retrospective
authoritative: false
last_verified: 2026-05-27
authoritative_for:
  - cycle-by-cycle chronology of the registry enforcement matrix build
  - pattern reuse maturity timeline (cycles 27-57)
  - technical decision log + lessons learned
  - final substrate state snapshot
related:
  - adr-2605271100-adr-2605262500-closure-and-verifier-marker-convention
  - adr-2605271200-registry-4-axis-enforcement-matrix
  - doc-adr-2605262500-implementation-retrospective-260527
  - doc-registry-enforcement-matrix-runbook-260527
supersedes: []
superseded_by: []
---

# Registry enforcement matrix — cycles 46-57 retrospective

**Period**: 2026-05-27 JST cycles 46-57 (12 cycles, ~~3.5 wall hours of
focused build time)
**Trigger**: Post-PR-287 (`feat/yakushi-wave-1c-r1-commissioning` merged
2026-05-27T01:29Z); user invoked `/loop 進めて` to continue
**Outcome**: 5-axis registry enforcement matrix landed; 48 unit tests;
5 GHA workflows; 5 lefthook hooks; 5-doc dossier.

## Chronology — 12 cycles

| # | ~Time | Headline | Branch | Deliverable |
|---|---|---|---|---|
| 46 | ~22 min | `(reserved)`/`(deferred-rename)` marker convention | main | 12 path markers absorbed; verifier expanded with 7 tests (10 → 17) |
| 47 | ~12 min | ADR-2605271100 closure for cycles 1-47 | main | 5-section closure doc + marker semantics canonical |
| 48 | ~13 min | docs.json freshness 3-layer | main | `regen-registry.py` CI wired; cron 03:23 UTC; 657 entries |
| 49 | ~14 min | graph.jsonld 3-layer + 8.6× expansion | main | NEW generator (171 lines); cron 03:29 UTC; 76 → 657 nodes |
| 50 | ~22 min | Schema validation 4th axis (tracker) | main | NEW validator (190 lines); 32 baseline violations documented |
| 51 | ~21 min | 32 baseline cleaned + axis 4 promoted | main | 18 .md files fixed; 3-retry commit dance |
| 52 | ~17 min | Closure ADR-2605271200 + 5 patterns named | main | Pattern A-E canonical names |
| 53 | ~22 min | 5th axis magatama (38 → 0 in single cycle) | main | NEW validator (160 lines); 5 schema enums + 13 data fixes |
| 54 | ~9 min | CLAUDE.md row #71 🟢 + new row #79 | main | Cycle 47 promise fulfilled |
| 55 | ~14 min | 5-axis matrix operator runbook (340 lines) | main | Operator daily checklist + failure mode recipes |
| 56 | ~18 min | 21 unit tests for cycle 49/50/53 generators | main | Test coverage gap closed for new scripts |
| 57 | ~14 min | regen-registry tests + pytest CI gates × 4 | main | Final test gap closed; defense-in-depth |

Total: ~198 min build time across 12 cycles. Average ~16.5 min/cycle.

## Pattern reuse maturity timeline (cycles 27-57)

Pattern A (3-layer enforcement: generator + lefthook + CI workflow):

| Cycle | Axis | Time | Notes |
|---|---|---|---|
| 27-30 | 1 — deps.toml book-keeping | ~75 min | **First implementation; full pattern invention** |
| 48 | 2 — docs.json freshness | ~13 min | Pattern reused; pre-existing generator |
| 49 | 3 — graph.jsonld freshness | ~14 min | Pattern reused; full new generator |
| 50→51 | 4 — Schema validation | ~22+21 min | Pattern reused; tracker→PR-gate (Pattern B introduced) |
| 53 | 5 — magatama manifest validation | ~22 min | **Pattern fully internalized**; single-cycle tracker→PR-gate compression |

**5.4× speedup** from cycle 27-30's 75 min → cycle 48's 13 min. The
pattern is now a ~15-minute template.

## Key technical decisions

### 1. `(reserved)` / `(deferred-rename)` marker convention (cycle 46)

**Problem**: deps.toml entries referencing future-impl paths failed the
verifier. 15 paths spanning 5 ADRs all had this issue.

**Solution**: Trailing suffix tokens on `path` values:
- `path = "90-docs/adr/foo.md (reserved)"` — owner-asserted future-impl
- `path = "00-contracts/lexicons/com/etzhayyim/apps/unispsc (deferred-rename)"` — pre-cutover per CLAUDE.md root §"Do Not"

Verifier strips marker before resolving; reports as `accepted-reserved`
distinct from `drift`. Stale-marker check catches markers that should
be dropped.

**Why two markers**: `(reserved)` is generic future-impl;
`(deferred-rename)` is specific to the etzhayyim→etzhayyim rename invariant.
Two markers > arbitrary token because operators can't bypass the audit
by writing `(skip)` or `(later)` — only specific intent-encoded tokens
are accepted.

### 2. Tracker → PR-gate promotion (Pattern B, cycle 50→51)

**Problem**: Cycle 50 shipped schema validator but found 32 baseline
violations. Strict PR-gate would have blocked all PRs. Tracker mode
defers the gate.

**Solution**: Ship validator + workflow in "tracker mode" (nightly
only, baseline documented), then clean baseline in next cycle, then
promote to PR-gate.

**Cycle 53 compressed this to a single cycle** by doing schema fixes +
data fixes + validator + CI all together because the cleanup was
script-driven.

### 3. Cron off-minute deconfliction (Pattern D, cycles 30/48/49/50/53)

| Workflow | UTC | Spacing |
|---|---|---|
| `deps-toml-paths` | 03:17 | base |
| `docs-registry-freshness` | 03:23 | +6 min |
| `docs-graph-jsonld-freshness` | 03:29 | +6 min |
| `registry-schema-validation` | 03:35 | +6 min |
| `magatama-manifest-validation` | 03:41 | +6 min |

Why off-minute (not on-the-hour): avoids ISP bandwidth saturation
peaks AND distributes GHA runner load.

### 4. Graceful optional-dep import (Pattern E, cycle 50)

**Problem**: `jsonschema` package requires `pip install` but PEP 668
blocks system-Python installs on macOS.

**Solution**: Validator imports jsonschema in try/except. If unavailable:
- `--strict` mode: exit 2 (CI uses this; installs via pip)
- Default mode: warn + exit 0 (operator gets non-blocking notice locally)

Operator-friendly without sacrificing CI strictness.

### 5. Pre-commit hygiene preemption (lesson from cycle 51)

**Problem (cycle 51)**: 3-retry commit dance from pre-existing
trailing-whitespace + missing final newlines in .md files. `🥊` in
lefthook output = hook FAILED (boxing emoji), not "auto-fix applied".

**Solution (from cycle 52 onward)**: Operator runs sed + tail-check
locally BEFORE commit:
```bash
for f in $(git diff --cached --name-only); do
  [ -f "$f" ] && sed -i '' 's/ *$//' "$f"
  if [ -s "$f" ] && [ "$(tail -c1 "$f" | xxd -p)" != "0a" ]; then
    printf '\n' >> "$f"
  fi
done
git add -u
```

Cycles 52-57 all clean single-attempt commits.

### 6. Defense-in-depth ordering (cycle 57 CI integration)

Per-axis enforcement layers in order:

```
1. Generator/validator logic     → unit tests (cycle 56-57)
2. Sidecar freshness             → --check / --strict (cycle 48-53)
3. Schema conformance            → live validation
4. Operator local gate           → lefthook pre-commit
5. CI gate                       → GHA PR-trigger
6. Nightly tracker               → cron schedule
```

CI workflow ordering: pytest → live --check. Script-logic regressions
fail BEFORE live-data drift, cleaner reviewer signal.

## Test coverage final state

| Cycle | Script | Tests | CI gate |
|---|---|---|---|
| 27-46 | `verify_deps_toml_paths.py` | 17 | `deps-toml-paths.yml` |
| 48-hookup | `regen-registry.py` | 10 (cycle 57) | `docs-registry-freshness.yml` (cycle 57) |
| 49 | `regen-graph-jsonld.py` | 8 (cycle 56) | `docs-graph-jsonld-freshness.yml` (cycle 57) |
| 50 | `validate-registry-schemas.py` | 6 (cycle 56) | `registry-schema-validation.yml` (cycle 57) |
| 53 | `validate-magatama-manifests.py` | 7 (cycle 56) | `magatama-manifest-validation.yml` (cycle 57) |
| **Total** | **5 scripts** | **48 tests (1 cond-skip)** | **5/5 CI-gated** |

## 5-axis matrix final state

| Axis | Source-of-truth | Sidecar | Verifier | Cycle | Cron |
|---|---|---|---|---|---|
| 1 | code/docs paths | `deps.toml` | `verify_deps_toml_paths.py` | 27-30 + 46 | 03:17 |
| 2 | `.md` front-matter | `docs.json` | `regen-registry.py --check` | 48 | 03:23 |
| 3 | `docs.json` | `graph.jsonld` | `regen-graph-jsonld.py --check` | 49 | 03:29 |
| 4 | both sidecars | `schemas/{docs,graph}.schema.json` | `validate-registry-schemas.py` | 50→51 | 03:35 |
| 5 | `magatama.jsonld` | `magatama.schema.json` | `validate-magatama-manifests.py` | 53 | 03:41 |

All 5 PR-gates. Baseline = 0 violations across the matrix.

## Audit baseline post-cycle-57

```
deps.toml:    592/607 resolve / 15 accepted-reserved / 0 bare drift     EXIT 0
docs.json:    in sync (659 entries)                                       EXIT 0
graph.jsonld: in sync (659 nodes / 565 with relations)                    EXIT 0
schema:       0 docs.json + 0 graph.jsonld errors                         EXIT 0
magatama:     42/42 valid                                                 EXIT 0
48 unit tests across 5 scripts                                            ALL PASS
9 e7m verify constitutional invariants                                    9/9 ✓
```

## Lessons learned

### What worked

1. **Pattern A reuse**: 75 min → 13 min compression (5.4×) shows the
   3-layer template was a real reusable pattern, not a one-off.
2. **Marker convention as cross-ADR contribution**: 15 paths absorbed
   without weakening the gate. The bias-toward-action vs
   bias-toward-strictness tension resolved by encoding owner intent.
3. **Tracker → PR-gate promotion**: shipping enforcement before
   baseline=0 avoided the "wait for cleanup before shipping" deadlock.
4. **Pre-commit hygiene preemption**: after cycle 51's 3-retry dance,
   cycles 52-57 all single-attempt clean commits.
5. **Closure ADR cadence**: ADR-2605271100 (cycle 47) and ADR-2605271200
   (cycle 52) provided checkpoints. Made the matrix visible to future
   readers without requiring archaeology through cycle commits.

### What didn't work / friction

1. **Cycle 51 commit dance**: 3 retries to commit 18 .md file edits.
   Lesson encoded in matrix runbook (cycle 55).
2. **Cycle 50 tracker-mode**: Shipping a validator that knows about
   32 known errors felt awkward. Worked, but Pattern B language
   (cycle 52) made the shape explicit.
3. **JSON schema rename latent bug** (cycle 46→48): renamed
   `missing_count` → `drift_count` in cycle 46 but the GHA workflow
   still referenced old key. Caught + fixed in cycle 48 — but it
   could have silently broken nightly runs for days.
4. **Voxelforge structural outlier** (cycle 53): one magatama.jsonld
   used non-canonical structure (string routes, missing nanoid).
   Required ad-hoc Python fix outside the batch script.

## Future axis-6 candidates

| Candidate | State |
|---|---|
| `hayate-model-artifact.schema.json` | NO current `*.hayate.manifest.json` artifacts exist; deferred until first artifact lands |
| `proof/` directory specialization | Only 2 files; status enum may want `verified` / `pending-replication` / `failed` |
| `pyproject.toml` schema | 48 pyproject.toml files; out-of-scope (PEP 621 + tool sub-schemas vary; not religious-corp canonical) |
| Lexicon schema validation | `00-contracts/lexicons/` has schemas; existing `validate-religious-corp-lexicons` lefthook hook covers subset |

## Total deliverables (cycles 46-57)

- **2 closure ADRs** (2605271100 + 2605271200)
- **1 operator runbook** (registry-matrix-cycles-55)
- **1 retrospective doc** (this file, cycle 58)
- **2 new generators**: regen-graph-jsonld.py (171 lines), validate-registry-schemas.py (190 lines), validate-magatama-manifests.py (160 lines)
- **48 unit tests** across 5 test files
- **5 GHA workflows** added or updated
- **5 lefthook hooks** added
- **3 schemas rewritten** (docs / graph / magatama)
- **38 baseline data violations cleaned** (32 docs cycle 51 + 13 magatama cycle 53; some overlap)
- **15 path markers** ((reserved) × 11 + (deferred-rename) × 4)
- **2 new CLAUDE.md rows** (#71 update + #79 new)

## References

- ADR-2605271100 — Cycle 47 closure
- ADR-2605271200 — Cycle 52 closure (4-axis matrix)
- `90-docs/baien/registry-enforcement-matrix-runbook-260527.md` — Cycle 55 operator runbook
- `90-docs/baien/adr-2605262500-implementation-retrospective-260527.md` — Cycle 40 sibling retrospective (cycles 1-39 of original ADR-2605262500)
- This file — Cycle 58 retrospective (cycles 46-57 of registry matrix)
