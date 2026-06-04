---
id: 2605250680
title: "Etzhayyim Government Coverage Maturity Score (e7m integration)"
status: active
doc_type: adr
topic: gov-coverage
authoritative: true
last_verified: 2026-05-25
related:
  - ADR-2605242330 (Gov coverage 5-layer taxonomy)
  - ADR-2605212100 (Migration batch)
  - ADR-2605250100/200/300 (L5 cell scaffolds)
  - CLAUDE.md Status row 35
---

## Context

ADR-2605242330 established the 5-layer gov coverage taxonomy (L1 ISO-3 / L2 COFOG×country / L3 substrate-ports / L4 ingest records / L5 cell activation). CLAUDE.md §Status row 35 documents the baseline state (40% scaffolded, 3 L3 ports verified, 421/1000 ingest records, 3 L5 cells awaiting Council activation).

However, there was no automated **scoring mechanism** to:
1. Quantify maturity across all five layers
2. Prioritize improvement effort
3. Track progress toward the 100-point target
4. Generate improvement plans

This ADR integrates that mechanism into `e7m` (Etzhayyim Monorepo CLI) as the canonical tool for gov coverage measurement.

## Decision

### 1. Scoring Model (Weighted Sum)

| Layer | Metric | Target | Weight | Notes |
|-------|--------|--------|--------|-------|
| L1 | ISO-3 country codes | 196 (100%) | 20% | Count of gov<ISO3> BPMN namespace entries |
| L2 | BPMN files | 784 (196 × 4 major COFOG categories) | 25% | Highest-impact gap (currently 0 baseline) |
| L3 | substrate-ports | 3 (gov-mcp, lawfirm-admin, legal-entity) | 20% | Already at 100% as of 2026-05-25 |
| L4 | ingest demonstrator records | 1000 | 20% | Scripted and emitted to com.etzhayyim.gov.agency |
| L5 | cell activation | 3 (member_registry, religious_marriage, religious_corp_taxation) | 15% | Council Lv6+ supermajority gate; currently 0% |

**Total Score** = sum(L_i × weight_i), capped at 100.

### 2. e7m Commands

Three subcommands under `e7m gov`:

#### `e7m gov coverage-score`
Displays current maturity score with:
- Overall numeric score (0-100)
- Per-layer breakdown with ASCII progress bars
- Gap list (prioritized by impact)
- Timestamp

Sample output:
```
┌─ Government Coverage Maturity Score ─────────────────────┐
│ Overall: 49.18/100                                       │
├──────────────────────────────────────────────────────────┤
│ ISO-3 completeness       │ ██████████████░░░░ 90% │
│ COFOG×country density    │ ░░░░░░░░░░░░░░░░░░░░ 0% │
│ substrate-port coverage  │ ████████████████████ 100% │
│ ingest records / target  │ ██████████░░░░░░░░░░ 56% │
│ cell activation gating   │ ░░░░░░░░░░░░░░░░░░░░ 0% │
└──────────────────────────────────────────────────────────┘
```

#### `e7m gov coverage-audit`
Runs full audit and saves two snapshots to `90-docs/gov-coverage/`:
- **JSON**: `gov-coverage-snapshot-YYYYMMDD.json` (machine-readable metrics)
- **Markdown**: `gov-coverage-snapshot-YYYYMMDD.md` (human-readable report)

Both include:
- Timestamp (ISO-8601)
- Per-layer breakdown with contributions
- Gap list with ADR references
- Target definitions

#### `e7m gov coverage-plan [--target N]`
Generates improvement roadmap to reach target score (default: 85/100).

Output:
- Current score vs target (gap analysis)
- Prioritized task list (sorted by impact×urgency)
- For each priority:
  - Layer name
  - Current % → Potential % (impact points)
  - Associated ADR(s)
  - Concrete tasks (3-5 actionable items)
- Estimated timeline

### 3. Measurement Implementation

**L1 ISO-3 Coverage**: Count `BPMN namespace` entries in `00-contracts/bpmn/com/etzhayyim/gov<ISO3>/`.
- Current baseline: ~176 of 196 countries → 90%

**L2 COFOG Density**: Count `.bpmn` / `.bpmn2` files recursively under `00-contracts/bpmn/com/etzhayyim/gov*/`.
- Target: 784 files (4 major COFOG per country)
- Current baseline: 0 files → 0%
- **Highest-impact improvement path**

**L3 Substrate-Ports**: Count `app.isDirectory()` for patterns `etzhayyim-project-{gov,lawfirm-admin,legal-entity}` under `60-apps/`.
- Target: 3
- Current: 3 (100%)

**L4 Ingest Records**: Estimate from count of `ingest-gov-*.py` and `ingest-gov-*.mjs` scripts under `70-tools/scripts/gov/`, multiplied by ~140 records per script.
- Target: 1000 records
- Current: ~421 (3 scripts × 140 = 420 baseline) → 56%

**L5 Cell Activation**: Count cells matching `{member_registry,religious_marriage,religious_corp_taxation}` under `20-actors/magatama/cells/`.
- Target: 3 cells (activated after Council supermajority)
- Current: 0 (all import-time RuntimeError) → 0%
- **Activation gate**: ADR-2605250100 + ADR-2605250200 + ADR-2605250300 + Council attestation per ADR-2605192300

### 4. Integration with Existing CI / Dev Workflow

#### Snapshot Preservation
Each `e7m gov coverage-audit` run creates time-stamped artifacts under `90-docs/gov-coverage/`:
```
90-docs/
├── gov-coverage/
│   ├── gov-coverage-snapshot-20260525.json
│   ├── gov-coverage-snapshot-20260525.md
│   ├── gov-coverage-snapshot-20260526.json
│   └── gov-coverage-snapshot-20260526.md
```

#### Regression Prevention (Future)
A CI hook can be added (post-Council bootstrap) to:
- Run `e7m gov coverage-audit` on every push to `main`
- REJECT if score drops >5 points without ADR justification
- WARN if score is flat for >2 weeks

#### Developer Workflow
Before proposing a gov-coverage PR:
```bash
e7m gov coverage-plan --target 85
# → Generates prioritized checklist
# → Operator chooses highest-impact task
# → Creates PR with targeted scope
```

### 5. Constraints and Gates

- **L5 Cell Activation**: Cannot increase from 0 until Council Lv6+ supermajority attestation (per ADR-2605192300).
- **L2 BPMN Expansion**: Must follow COFOG taxonomy (UN standard) — no vendor-specific categorization.
- **Charter Rider Compliance**: All ingest records and BPMN definitions must pass `etzhayyim_organism.sensors.charter_rider.scan()`.

### 6. Success Criteria

- ✓ `e7m gov` command group available with 3 subcommands
- ✓ Score calculation algorithm implemented and tested
- ✓ Snapshots generated and committed to `90-docs/gov-coverage/` after each major milestone
- ✓ Improvement plan guides development toward 85+ score
- ✓ L5 cell activation unblocked post-Council (separate ADR)

## Consequences

### Positive
- **Objective measurement** replaces prose-only status updates
- **Prioritization clarity**: L2 (0%) is highest-impact; L3 already done (100%)
- **Milestone tracking**: Snapshots create historical record of improvement
- **Reproducibility**: JSON snapshots are machine-parseable for dashboards / automation

### Neutral
- Adds ~250 LoC to e7m-cli (low maintenance burden)
- Snapshots grow incrementally under `90-docs/gov-coverage/` (negligible storage)

### Negative
- Does not address L5 cell activation (gated on Council, orthogonal to tooling)
- L2 BPMN expansion requires 50+ new files (significant contributor effort)

## Alternatives Considered

1. **Manual spreadsheet tracking**: Rejected (entropy risk, no auditability)
2. **Hardcoded snapshot in deps.toml**: Rejected (snapshot should be time-series, not singleton)
3. **Separate Python script**: Rejected (e7m is the canonical CLI for monorepo ops; consolidation reduces cognitive load)
4. **GitHub Actions dashboard**: Deferred to post-Council (requires stable L5 activation gate)

## References

- ADR-2605242330: Gov coverage 5-layer taxonomy + COFOG×country model
- ADR-2605212100: Back-authored etzhayyim→etzhayyim migration batch (36 files)
- ADR-2605214000: Murakumo no-VKE mesh + lexicon-port verdict taxonomy
- ADR-2605250100/200/300: L5 cell scaffolds (member_registry, religious_marriage, religious_corp_taxation)
- CLAUDE.md §Status row 35: Baseline gov coverage state (2026-05-25)
- `/70-tools/e7m-cli/src/lib/gov-coverage.ts`: Score computation library
- `/70-tools/e7m-cli/src/commands/gov.ts`: e7m CLI command group
