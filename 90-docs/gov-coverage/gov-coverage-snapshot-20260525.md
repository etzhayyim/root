# Government Coverage Maturity Report

**Generated**: 2026/5/25 12:54:04

## Overall Score: 53.89/100

### Breakdown

| Layer | Coverage | Weight | Contribution |
|-------|----------|--------|--------------|
| L1 ISO-3 completeness | 90% | 20% | 18 |
| L2 COFOG×country density | 8% | 25% | 2 |
| L3 substrate-port coverage | 100% | 20% | 20 |
| L4 ingest records | 70% | 20% | 14 |
| L5 cell activation | 0% | 15% | 0 |

### Coverage Gaps

- L1: Missing ISO-3 country codes (target: 100%)
- L2: BPMN coverage incomplete (need 50+ more files)
- L4: Only 70% of target ingest records (need ~580 more)
- L5: 3 cells awaiting Council activation (ADR-2605250100/200/300)

### Reference

- **Status Row 35**: CLAUDE.md — Gov coverage 5-layer taxonomy
- **ADRs**: 2605212100 (migration), 2605214000 (mesh), 2605242330 (taxonomy), 2605250100/200/300 (L5 cells)
- **L1 Target**: 196 countries (100% ISO-3)
- **L2 Target**: 784 BPMN files (196 countries × 4 major COFOG categories)
- **L3 Target**: 3 substrate-ports (gov-mcp, lawfirm-admin, legal-entity)
- **L4 Target**: 1000 ingest demonstrator records
- **L5 Target**: 3 cells (member_registry, religious_marriage, religious_corp_taxation) — all Council-activation gated
