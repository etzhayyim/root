# ooyake 公 — Maturity Scorecard

Honest R0 status per the gov-coverage maturity model (ADR-2605250680). **This is a
proof-of-model, not coverage.** Coverage is gated by `:sourcing` (G5): only
`:authoritative` rows count. The seed ships **zero** `:authoritative` rows; the
offline `reconcile.py` demo can promote **8 of 28** against the bundled authority
reference (see below) — still a demo, not live ingest.

## Seed contents (R0, 2026-06-02)

Two seed files: `gov-units.seed.edn` (proof-of-model chain) + `gov-units.jp-central.seed.edn` (full JP 府省庁).

| Vocabulary | Count | All `:unverified-seed`? |
|---|---|---|
| `:gov.unit/*` | **28** — base 15 (JP ×7, USA ×3, GBR ×2, DEU ×1, KOR ×1, EU ×1) + JP central 13 (内閣府 + 11省 + デジタル庁 + 復興庁) | yes |
| `:gov.address/*` (住所) | **17** — base 4 + JP central 13 (霞が関 + 市谷 + 紀尾井町) | yes |
| `:gov.window/*` (窓口) | 2 | yes |
| `:gov.form/*` (書式) | 2 (→ chigiri templates) | yes |
| `:gov.procedure/*` (手続き) | 3 (→ toritsugi-ref) | yes |
| `:gov.bpmn/*` (BPMN) | 3 (`:model-only`) | n/a |

**Full vertical chain proven**: `gov.jpn → 財務省 → 国税庁 → 東京国税局 → 麹町税務署`
(with 住所 + 窓口) and `東京都 → 新宿区 → 戸籍住民課窓口` (with 住所). **省庁単位の幅**:
the entire JP central government (内閣府 + 総務/法務/外務/財務/文科/厚労/農水/経産/国交/環境/防衛
省 + デジタル庁 + 復興庁) each with HQ 住所. **国際的な幅**: country + flagship ministry
rows for US/UK/DE/KR + EU supranational.

## Reconcile demo (R1 mechanism, offline)

`scripts/reconcile.py` proves the `:representative → :authoritative` promotion rule
(G5: promote only when `:gov.unit/wikidata` AND `:gov.unit/official-url` agree with
`registry/authority-reference.edn`). Latest run:

```
units in seed: 28 · authority records: 8
→ PROMOTED authoritative: 8  (gov.jpn, gov.jpn.cao, gov.jpn.mof, gov.jpn.mofa,
                              gov.jpn.meti, gov.jpn.pref.13, gov.usa.treasury, gov.gbr.hmrc)
→ conflicts (kept unverified): 0
→ no authority record (stays representative): 20
coverage: 28.6% authoritative (8/28) — rest honestly :representative
```

This is a deterministic OFFLINE demo against a bundled reference; **live fetch of
Wikidata / 行政機関コード / GeoNames is G4 + Council + operator gated** and is NOT run.

The reconcile logic is now a real cell: `cells/reconcile/cell.py` (`ReconcileCell`)
with `mode="bundled"` (runnable, the above) and `mode="live"` (raises, G4-gated).
`scripts/reconcile.py` is the thin CLI over it. Unit tests:
`cells/reconcile/test_reconcile_cell.py` — **5 passed** (promotion set, no-conflict
remainder, bundled-ok, live-gated, unknown-mode-rejected).

## What is NOT done (by design at R0)

| Question | Status |
|---|---|
| All world governments enumerated? | **NO** — 28 units (proof-of-model). The world has ~195 countries × thousands of units each. |
| Any `:authoritative` row in the seed? | **NO** — every seed row is `:representative` / `:unverified-seed`. The `reconcile.py` demo can promote 8/28 against the bundled reference, but that is a demo, not committed seed state or live ingest. |
| Cells running? | **PARTIAL** — `reconcile` (bundled mode) is implemented + unit-tested (5 passed); the other 5 cells are path-reserved scaffolds. `reconcile` live mode + all ingest/serve cells are gated. |
| Per-unit DID served? | **NO** — scheme defined; dynamic did.json serving is R2. |
| `findService` live? | **NO** — lexicon + BPMN defined; serving is R1/R2. |
| `/actors` search surfaces gov units? | **NO** — R1 (after `atlas_serve` + reconcile). |
| Addresses/hours authoritative? | **NO** — best-effort public references as of 2026-06-02, expected to drift. |

## Maturity score (self-assessed, R0)

- **L1 namespace** (country scaffolds): inherited from legacy `gov*` dirs (196 dirs) — but stubs, not ooyake-native yet.
- **L2 agency registry**: 28 ooyake-native units (`:representative`; full JP central government covered).
- **L3 public-services hub** (住所/窓口): 17 addresses + 2 windows (JP only).
- **L4 procedure ingest**: 3 procedures (JP only, → toritsugi).
- **L5 routing-around**: **out of scope** for ooyake (read-side only, G9/G10).

Coverage score remains governed by ADR-2605250680 (49.18/100 baseline). ooyake R0
moves the **schema/substrate** axis to green; the **data/coverage** axis stays red
until R1 authoritative ingest. **No silent truncation**: this file is the
canonical honest record (G5).
