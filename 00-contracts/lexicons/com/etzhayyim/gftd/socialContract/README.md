# `com.etzhayyim.socialContract.*` — Social contract — open community-rule record

Tranche F Phase 2 wave 2 scaffolding placeholder (group B).

## Status

Lexicon catalog placeholder. Per [ADR-2605172400](https://github.com/etzhayyim/etzhayyim-root/blob/main/90-docs/adr/2605172400-etzhayyim-vendor-three-axis-split-rule.md) (3-axis split rule), this scope is etzhayyim — passes Liability (no fiduciary), Custody (public / self-custodied), Settlement (free or on-chain).

Phase 3 will populate this directory with actual lexicon JSON files. Stub created so the catalog has a slot.

## NSIDs (planned)

To be defined. Naming convention: `com.etzhayyim.socialContract.<methodOrRecord>` (camelCase per CLAUDE.md Identifier rule).

## Lexicon contract rules

- camelCase identifiers
- integer-only (no `type: "number"`)
- `items: { "type": "ref", "ref": "#typeName" }` for array-of-object
- `$type` set on every record payload
