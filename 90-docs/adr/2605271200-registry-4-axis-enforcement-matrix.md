---
id: adr-2605271200-registry-4-axis-enforcement-matrix
title: "ADR-2605271200: registry enforcement 4-axis matrix LANDED — cycles 48-51 closure (docs.json freshness + graph.jsonld freshness + JSON Schema validation + 32 baseline .md violations cleaned)"
status: proposed
doc_type: adr
topic: registry-enforcement-matrix
authoritative: true
last_verified: 2026-05-27
priority: 5.5
axis: tooling
weight: 0.40
priority_note: "Closure amendment extending ADR-2605271100 (cycle 47 ADR-2605262500 closure). Cycles 48-51 built the 4-axis registry enforcement matrix that mechanically protects the doc system rules in 90-docs/CLAUDE.md. Each axis follows the same 3-layer pattern (generator+lint / lefthook hook / GitHub Actions workflow) established by cycles 27-30. All 4 axes are now PR-gates with 0 baseline violations across the matrix. Documents the substrate, the 5 reusable patterns extracted from the journey, and the kotodama-schema axis-5 deferred follow-on."
authoritative_for:
  - registry enforcement 4-axis matrix as of cycles 48-51 (2026-05-27)
  - (reserved) / (deferred-rename) marker convention adoption (cycle 46)
  - 4-axis cron deconfliction (:17 / :23 / :29 / :35 spread)
  - 5 reusable patterns from cycles 27-51 journey
  - kotodama-schema axis-5 deferred status + 38-violation survey
depends_on:
  - adr-2605271100-adr-2605262500-closure-and-verifier-marker-convention
  - adr-2605262500-robotics-world-data-ingestion-and-usd-pipeline
related:
  - adr-2605170900-etzhayyim-root-adr-canonical-home
supersedes: []
superseded_by: []
---

# ADR-2605271200: registry enforcement 4-axis matrix LANDED

**Status**: proposed
**Date**: 2026-05-27
**Deciders**: Jun Kawasaki

## Context

ADR-2605271100 (cycle 47) closed ADR-2605262500's 47-cycle journey and
introduced a cross-ADR contribution: the `(reserved)` / `(deferred-rename)`
deps.toml marker convention. That marker convention was the first
substrate piece built outside the original ADR-2605262500 scope.

Across the next 4 cycles (48-51, 2026-05-27 JST), the substrate
extended into a **4-axis registry enforcement matrix** that mechanically
protects the `90-docs/CLAUDE.md` documentation system rules ("Markdown
本文が canonical source; sidecars regenerate idempotently; same
判断を複数 doc に複写しない"). Each axis follows the same 3-layer
pattern (generator + lefthook hook + GitHub Actions workflow)
established by cycles 27-30 for deps.toml book-keeping.

This closure-amendment ADR captures the matrix as the canonical state
since it crosses ADR boundaries and isn't tied to any single Tier-B
actor wave.

## Decision

### 1. 4-axis registry enforcement matrix is canonical

| Axis | Source-of-truth | Sidecar | Verifier / Generator | Cycle | CI cron | Mode |
|---|---|---|---|---|---|---|
| **1. Book-keeping** | code/docs paths | `deps.toml` | `verify_deps_toml_paths.py` (with `(reserved)` + `(deferred-rename)` markers) | 27-30 + 46 | 03:17 UTC | **PR-gate** |
| **2. Doc registry** | `.md` front-matter | `90-docs/_registry/docs.json` | `regen-registry.py` (`--check`) | 48 | 03:23 UTC | **PR-gate** |
| **3. Relation graph** | `docs.json` projection | `90-docs/_registry/graph.jsonld` | `regen-graph-jsonld.py` (`--check`) | 49 | 03:29 UTC | **PR-gate** |
| **4. Schema validation** | both sidecars | `90-docs/_registry/schemas/{docs,graph}.schema.json` | `validate-registry-schemas.py` | 50 (tracker) → 51 (promoted) | 03:35 UTC | **PR-gate** |

**Source-of-truth chain**:
```
.md (canonical)
  ↓ regen-registry.py
docs.json (axis-2)
  ↓ regen-graph-jsonld.py
graph.jsonld (axis-3)

both sidecars → validate-registry-schemas.py → schema gates (axis-4)

repo paths → verify_deps_toml_paths.py → deps.toml gates (axis-1)
```

**Cron deconfliction**: :17 / :23 / :29 / :35 (6-minute spread × 4 axes)
isolates GitHub Actions runner load. Off-minutes avoid top-of-hour
bandwidth saturation.

### 2. Audit baseline (canonical post-cycle-51 clean state)

```
deps.toml:    583/598 resolve / 15 accepted-reserved / 0 bare drift     EXIT 0
docs.json:    in sync (657 entries)                                       EXIT 0
graph.jsonld: in sync (657 nodes)                                         EXIT 0
schema:       0 docs.json errors / 0 graph.jsonld errors                  EXIT 0
```

Any future bare missing path (no marker), any unfrozen marker, any
stale generator output, any new schema violation **fails CI on push**.

### 3. (reserved) / (deferred-rename) marker convention (cycle 46)

Two trailing suffix tokens on deps.toml `path` values absorb
owner-asserted future-impl + pre-cutover state:

```toml
[[adrs]]
path = "90-docs/adr/2605250730-tatekata-r1.md (reserved)"

[[modules]]
path = "00-contracts/lexicons/com/etzhayyim/apps/unispsc (deferred-rename)"
```

| State | Semantics | CI |
|---|---|---|
| `(reserved)` + missing | accepted future-impl | EXIT 0 |
| `(deferred-rename)` + missing | accepted pre-cutover per CLAUDE.md root §"Do Not" | EXIT 0 |
| Either marker + path EXISTS | stale-marker warning (drop suffix) | EXIT 0 with summary |
| No marker + missing | bare drift | EXIT 1 |

15 marker-bearing entries currently accepted (3 tatekata + 12 owner-asserted
spanning 5 ADRs).

### 4. Five reusable patterns from cycles 27-51

The 25-cycle journey produced 5 patterns that any future ADR can
adopt:

**Pattern A — Three-layer enforcement** (generator + lefthook hook + CI workflow):
- Maps to cycles 27-30 (`deps-toml-paths`), 48 (`docs-registry-freshness`),
  49 (`docs-graph-jsonld-freshness`), 50 (`registry-schema-validation`).
- Each axis takes ~13-22 minutes once the pattern is internalized.

**Pattern B — Tracker → PR-gate promotion** (cycles 50→51):
- Ship validator + workflow in "tracker mode" (nightly only, baseline
  documented) when baseline > 0.
- Clean baseline in subsequent cycle.
- Promote to PR-gate when baseline = 0.
- Removes the "wait for cleanup before shipping" deadlock.

**Pattern C — Marker convention for owner-asserted exemptions** (cycle 46):
- Trailing `(reserved)` / `(deferred-rename)` suffix.
- Avoids the "this CI fails because we know about it" anti-pattern.
- Stale-marker check catches markers that should be dropped.

**Pattern D — Cron deconfliction by off-minute** (cycles 30, 48, 49, 50):
- 6-minute spread (:17 / :23 / :29 / :35) avoids GitHub Actions
  runner load concentration.
- Off-top-of-hour avoids ISP bandwidth saturation peaks.

**Pattern E — Graceful import fallback for optional deps** (cycle 50):
- `jsonschema` not installed locally → script warns + exits 0.
- CI installs unconditionally via `pip install`.
- Operator-friendly without sacrificing CI strictness.

### 5. Kotodama-schema axis-5 deferred

Cycle 52 (this ADR) surveyed `90-docs/_registry/schemas/kotodama.schema.json`
+ the 65 `kotodama.jsonld` files across `60-apps/*` (42 in the
non-worktree path). **38 of 42 manifests fail validation**:

| Error class | Count | Root cause |
|---|---|---|
| `uiType: 'yoro'` not in enum | 26 | Schema enum missing `yoro` (description says it's a legacy value auto-mapped to appview, but enum is too narrow) |
| `performerType` missing (required) | 7 | Real data bugs — apps missing required field |
| `@context` const mismatch | 6 | 5 apps use `/ld/kotodama/v1`; 1 uses `/kotodama/v1` (no infix); schema's const requires `/ns/kotodama/v1` |
| `profile.category: 'infrastructure'/'knowledge'/'security'/'image-generation'` | 9 | Schema enum is overly religious-corp specific (government/international/religious/ngo/sport/academic); real data uses business-domain categories |
| `runtimeType: 'logical' / 'kotodama-zeebe'` | 4 | Schema enum missing 2 real values |
| `profile.agentType: 'advisory'` | 2 | Schema enum missing `advisory` |
| `profile.isBot: false` | 2 | Schema has `const: true` but 2 PWAs are not bots |

**Mix is schema-bugs + data-bugs**; cannot be cleanly resolved in one
cycle. Deferred to a future cycle that has 30-45 min budget. When
landed, axis-5 will follow Pattern A + Pattern B (tracker→PR-gate
promotion since baseline > 0 initially).

### 6. ADR-2605271100 status update

ADR-2605271100 was cycle 47's closure for ADR-2605262500 + introduced
the marker convention. **This ADR (2605271200) extends rather than
supersedes** ADR-2605271100. Both remain `proposed` until Council Lv6+ ≥3
ratification.

## Consequences

### Positive
- 4-axis registry enforcement is mechanical + idempotent
- 5 reusable patterns lower the cost of future enforcement work
- Baseline-clean state caps maintenance overhead
- `(reserved)` / `(deferred-rename)` markers absorb owner-asserted future-impl
  cleanly without weakening the gates

### Negative
- 4 nightly cron jobs + 4 PR-gate workflows + 4 lefthook hooks add
  total ~1.5s pre-commit overhead and ~5 min nightly CI minutes
- kotodama-schema (axis-5) is identified as available substrate but
  deferred — risk of growing data drift before axis-5 lands
- Process learning from cycle 51 (3-retry commit dance) documents the
  trailing-whitespace + end-of-file hook interaction with regen output

### Deferred (post-cycle-51 candidate list)

1. **CLAUDE.md row #71 update** (🟡 → 🟢 ADR-2605271100 + 2605271200 references)
2. **Axis-5 kotodama-schema** (38-violation survey above → 30-45 min cycle)
3. **PR #287 GitHub Actions live exercise** (passive; next PR triggers)
4. **Real-network PDS resolve smoke** (needs `pds.etzhayyim.com` access)
5. **Tier-B actor follow-on** (user direction)

## Alternatives Considered

### Why a new closure amendment ADR (2605271200) vs editing 2605271100?

**Chose**: separate ADR with `depends_on` link to ADR-2605271100.

**Why**: ADR-2605271100 documents cycles 1-47 specifically tied to
ADR-2605262500. Cycles 48-51 built cross-ADR substrate (registry
enforcement matrix) that any ADR can use — its scope is bigger than
ADR-2605262500's closure. A separate ADR captures the broader scope
without rewriting history.

### Why not promote kotodama-schema axis to PR-gate this cycle?

**Chose**: defer to a future cycle.

**Why**: 38 mixed schema-and-data violations across 13 .md files would
require ~30-45 minute single cycle of focused work. Cycle 52's budget
is consumed by this closure ADR + ~3-axis 4-clean confirmation. Deferring
allows axis-5 to land cleanly in dedicated session.

### Why not a 5th axis for `proof/` directory specialization?

**Considered**: `proof/` files may have different valid status values
than ADRs (per cycle 51's missing-status fix using `active`).

**Chose**: not yet — the existing schema accepts `active` status, so
there's no actionable specialization need until proof artifacts grow
new categorical attributes.

## References

- ADR-2605271100 — Cycle 47 closure of ADR-2605262500 + marker convention
- ADR-2605262500 — Robotics world-data pipeline (parent ADR)
- ADR-2605170900 — etzhayyim/root as canonical home for open ADRs
- `90-docs/CLAUDE.md` — Documentation System Rules (the rules being enforced)
- `70-tools/scripts/lint/verify_deps_toml_paths.py` — axis-1 verifier
- `70-tools/scripts/docs/regen-registry.py` — axis-2 generator
- `70-tools/scripts/docs/regen-graph-jsonld.py` — axis-3 generator (cycle 49)
- `70-tools/scripts/docs/validate-registry-schemas.py` — axis-4 validator (cycle 50)
- `90-docs/_registry/schemas/docs.schema.json` — axis-4 docs.json schema (cycle 50 rewrite)
- `90-docs/_registry/schemas/graph.schema.json` — axis-4 graph.jsonld schema (cycle 50 rewrite)
- `.github/workflows/{deps-toml-paths,docs-registry-freshness,docs-graph-jsonld-freshness,registry-schema-validation}.yml`
- `lefthook.yml` — 4 corresponding pre-commit hooks
