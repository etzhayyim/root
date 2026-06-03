---
id: doc-lexicon-deep-dive-260528
title: "Cycle 73 lexicon deep dive — Pattern F re-engagement test on AT Protocol Lexicon v1 violations"
status: active
doc_type: reference
topic: lexicon-deep-dive
authoritative: false
last_verified: 2026-05-28
authoritative_for:
  - cycle 73 lexicon violation breakdown by etzhayyim-legacy vs etzhayyim-native scope
  - 181 non-etzhayyim violation inventory with auto-fix safety analysis
  - escalation path for owner sign-off on schema migrations
related:
  - doc-axis-9-saturation-survey-260527
  - doc-registry-matrix-cycles-58-69-retrospective-260527
supersedes: []
superseded_by: []
---

# Cycle 73 — lexicon deep dive (Pattern F re-engagement test)

**Context**: cycle 72 documented Pattern F saturation across 3 axis-9
candidates. Cycle 73 tested whether the 3198 known lexicon violations
(documented-deferred per audit-health) contain auto-fixable subsets
that would re-engage Pattern F.

**Result**: Yes-and-no. **3017 violations** are in `com/etzhayyim/etzhayyim/`
subtree (pre-cutover, constitutional skip per CLAUDE.md root §"Do Not"
etzhayyim-rename invariant). **181 violations are in non-etzhayyim post-cutover
religious-corp-native lexicons** — a tractable scope. Of those 181,
173 (95.6%) are `type='number'` violations whose mechanical fix would
be a **breaking schema change** requiring owner + Council attestation
per ADR-2605181100. **Not safe to auto-fix without governance.**

## Violation breakdown (cycle 73 scope, 2026-05-28)

| Scope | Files | Violations | Disposition |
|---|---|---|---|
| `com/etzhayyim/etzhayyim/` (legacy) | many | **3017** | Constitutional skip — pre-cutover invariant |
| `com/etzhayyim/` non-etzhayyim (post-cutover) | 51 | **181** | Tractable but breaking |
| **Total** | | **3198** | Matches cycle 56 audit-health baseline |

## Non-etzhayyim 181-violation breakdown

| Class | Count | % |
|---|---|---|
| `type='number'` (use integer with implied units) | **173** | 95.6% |
| `inline type='object'` (use $ref to def) | 8 | 4.4% |
| Invalid format | 0 | 0% |
| Other | 0 | 0% |

## Auto-fix risk analysis

### `type='number'` violations (173)

**Per AT Protocol Lexicon v1 spec**: prefer integer types with implied
units (e.g., `cohortRatioPctIntegerHundredths`) over float types for
portability + no floating-point precision issues. The 173 violations
all use `type: number` for fields that semantically should be integer
with explicit unit suffix.

**Examples**:
- `silenCareReview.cohortRatio.under18Pct: number` → should be
  `under18PctIntegerHundredths: integer` (0-10000 representing 0.00-100.00%)
- `silenCareReview.cohortRatio.over65Pct: number` → same
- `generationRecord.kwhDelta: number` → likely `kwhDeltaIntegerMilli: integer`
  (multiply by 1000 → integer representing thousandths of kWh)

**Auto-fix is a BREAKING SCHEMA CHANGE** because it requires:
1. Property rename (adds units suffix) — wire format change
2. Type change (number → integer) — schema validation change
3. Value scaling (12.34 → 1234) — semantic value transformation
4. Cascade: any downstream consumer (TypeScript SDK / Python validators /
   PDS records already written) must adapt

**Per ADR-2605181100** (`com.etzhayyim.encrypted.*` wire format) +
Charter Rider §6 (lexicon SSoT), wire format changes require Council
Lv6+ attestation. Cycle 73 does NOT have authority to make these
changes without owner sign-off.

### `inline type='object'` violations (8)

**Per spec**: properties should `$ref` to a `$defs` declaration, not
inline an `object` schema. The 8 violations all have inline object
schemas under `properties.X.items` or similar.

**Fix is non-breaking**: extract the inline object into a sibling
`$defs` entry + replace inline with `$ref: "#/$defs/X"`. Schema
semantics unchanged; consumers that resolve `$ref` see same shape.

**However**: 8 violations across 8 different files in 4 different
actors (hikari / hodoki / etc.). Each needs the extracted `$defs`
naming chosen carefully. Tractable but per-file judgment work.

## Owners needing escalation

Counted from non-etzhayyim violations:

| Actor | Files | Violations |
|---|---|---|
| hagukumi | 1 | 4 |
| hikari | 4 | 9 |
| hodoki | many | ~80 |
| iyashi | several | ~30 |
| kokoro | 1 | ~5 |
| (others) | ~10 | ~50 |

Per ADR-2605271200 closure §"Documented-deferred": these are
documented-deferred state. Future cleanup requires per-actor owner +
Council attestation.

## Recommendation

**Cycle 73 outcome**: Pattern F does NOT re-engage on lexicon
violations. The 173 + 8 = 181 fixes are not auto-fix-safe; they
require:
- Owner action per-actor
- Council Lv6+ attestation per ADR-2605181100 + Charter Rider §6
- Cascade testing against TypeScript SDK + Python validators + PDS
  data migration

**Best next /loop direction**: still moving out of registry enforcement
arc (cycle 72's recommendation stands). Lexicon cleanup belongs to
substantive Tier-B actor work, not to /loop infrastructure cycles.

## Related findings

- Cycle 72 axis-9 saturation survey (sibling doc)
- Audit-health workflow baseline: 3198 lexicon-spec violations
  (documented-deferred per ADR-2605262130 closure)
- Validator: `70-tools/scripts/validate-lexicons.py` (pre-existing)
- Lefthook hook: `validate-religious-corp-lexicons` (staged-only
  mode per lefthook.yml; does NOT enforce full-tree audit)

## References

- ADR-2605271200 — closure documenting documented-deferred items
- ADR-2605181100 — wire format invariant (constitutional)
- ADR-2605262130 — kotoba storage substrate (lexicon SSoT carried)
- `70-tools/scripts/validate-lexicons.py` — canonical validator
- Cycle 72 sibling survey: `90-docs/baien/axis-9-saturation-survey-260527.md`
