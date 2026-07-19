# `com.etzhayyim.apqc.*` — APQC Process Classification Framework

Open spec for the APQC PCF (Process Classification Framework) catalog and the
Kyber BPMN projector that maps PCF process IDs to BPMN process definitions.

## Status

Tranche F scaffolding (Phase 2). Per ADR-2605172400, the user has confirmed
APQC + Kyber as full etzhayyim move (not SPLIT). Catalog reference data and
the BPMN projector spec live here; vendor-specific customer mapping stays
in `etzhayyim/etzhayyim-root` (60-apps/etzhayyim-project-kyber-*).

## NSIDs (planned)

- `com.etzhayyim.apqc.getProcess` — fetch one PCF process by ID
- `com.etzhayyim.apqc.listProcesses` — list PCF processes (paginated)
- `com.etzhayyim.apqc.projectToBpmn` — map a PCF process ID to its BPMN process_def
- `com.etzhayyim.apqc.listProjections` — list available PCF → BPMN mappings

## See also

- `orgs/etzhayyim/com-etzhayyim-app-open-apqc/` (west-managed app repository)
- `60-apps/etzhayyim-project-open-kyber/` (this repo, Tranche E)
- `00-contracts/lexicons/com/etzhayyim/kyber/` (this repo, Tranche A)
- ADR-2605172400 (vendor: 3-axis split rule + Tranche F)
- [ADR-0025 Kyber APQC/BPMN Projector Consolidation](https://github.com/etzhayyim/etzhayyim-root/blob/main/90-docs/adr/0025-kyber-apqc-bpmn-projector-consolidation.md) (foundational, vendor monorepo)

## Lexicon contract rules (per CLAUDE.md)

- camelCase identifiers everywhere
- integer-only (no float) — encode decimals as `*_milli` integers
- `items: { type: "ref", ref: "#typeName" }` for array-of-object (never plain nested object literals)
- `$type` must be set on every record payload
