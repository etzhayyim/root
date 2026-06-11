---
id: adr-2606061200-gov-legal-procedure-coverage-maturity-expansion
title: "ADR-2606061200: Worldwide Government/Legal Procedure Coverage + Maturity Expansion (toritsugi · chigiri · ooyake)"
status: accepted
doc_type: adr
topic: gov-legal-procedure-coverage-maturity-expansion
authoritative: true
last_verified: 2026-06-06
priority: 5.0
axis: architecture
weight: 0.50
priority_note: "R0 data + cross-actor integrity; live use stays Council/operator gated"
authoritative_for:
  - 20-actors/toritsugi/registry/procedures.seed.json
  - 20-actors/chigiri/registry/legal-aid.seed.json
  - 20-actors/ooyake/registry/gov-units.intl-procedures.seed.edn
  - 20-actors/ooyake/scripts/gen_intl_procedures.py
  - 70-tools/scripts/coverage/gen_gov_legal_coverage.py
depends_on:
  - 2605262700
  - 2605312030
  - 2606021600
related:
  - 2605302357
  - 2606052300
supersedes: []
superseded_by: []
---

# ADR-2606061200: Worldwide Government/Legal Procedure Coverage + Maturity Expansion (toritsugi · chigiri · ooyake)

**Status**: accepted
**Date**: 2026-06-06
**Deciders**: Jun Kawasaki

# Context

The founding question for this work was twofold: *「いまの lawfirm での法的手続きの全世界の行政処理のカバレッジは？また全世界政府の行政手続きの実装カバレッジは?」* — what is the worldwide coverage of (a) legal procedures / legal aid (the chigiri 契 "lawfirm" side, a referral substrate, NOT a law firm — UPL prohibited) and (b) government administrative procedures (the toritsugi 取次 concierge + the ooyake 公 government atlas).

At the start of a self-paced 16-iteration `/loop 30min 成熟度、カバレッジを向上` session the honest coverage was:

- **toritsugi**: 66 procedures / 41 jurisdictions, all `unverified-seed`.
- **chigiri**: 55 legal-aid referral bodies / 36 jurisdictions, all `unverified-seed`.
- **ooyake**: 7,106 government units (G20 the only `:authoritative` tier) but only **6 JP-only** `:gov.procedure` records; Denmark (a sovereign state) missing from the country tier.
- No cross-actor integrity tests, no committed coverage dashboards, and 17 failing tests in `70-tools/scripts/audit/` (mostly an `app`→`com` lexicon-path typo in the akashi suite + two baseline-drift counters).

# Decision

Expand coverage and **pin it with machine-checked cross-actor invariants**, under a strict no-fabrication discipline (every row a real cited authority, `unverified-seed`, never counted as authoritative coverage per G5; UPL / 行政書士法 boundaries preserved verbatim; ZERO constitutional-invariant amendments).

1. **Coverage (breadth + depth)**
   - toritsugi → **145+ procedures / 52 jurisdictions** across **9 procedure kinds** (passport, national-id/residence, **business/company registration**, **civil marriage registration**, driving licence, tax, social-security, civic, civil/vital). Every addition is an existing-jurisdiction deepening (parity preserved) using real official authorities; fee / statutory-days / per-country statute left to guide-time resolution rather than invented; `legalBasis` only where confident.
   - chigiri → **71 real public legal-aid bodies / 52 jurisdictions** (added IFDP/DPU/KLAC/法律援助/NLASO/legalaid.gov.ua/Adli Yardım/etc.), honest about jurisdictions where state civil legal aid is limited (e.g. SAU).
   - ooyake → added **`gov.dnk`** (Wikidata Q35) closing the lone sovereign gap (192 → 193 country units); generalized the atlas procedure projection from passport-only to the **full toritsugi registry** → **~157 `:gov.procedure` records / 50 jurisdictions** (incl. `eu-wide → gov.eu`).

2. **Owner-unit honesty (G5)** — atlas procedure `owner-unit` = the unambiguous country-level `gov.<iso>` (always resolvable), NOT a fabricated specific ministry; the precise issuing body is carried verbatim in `:gov.procedure/owner-authority`.

3. **Cross-actor integrity (machine-pinned, fail-closed, R0-safe)**
   - `70-tools/scripts/audit/test_gov_legal_coverage_parity.py` — ISO-3 code validity + coverage floor (≥47) + toritsugi↔chigiri shared-jurisdiction parity floor.
   - `70-tools/scripts/audit/test_ooyake_procedure_integrity.py` — every atlas `:gov.procedure/owner-unit` resolves to a real unit; every `:gov.procedure/toritsugi-ref` resolves to a live toritsugi `procedureId`; all `:unverified-seed`.
   - `70-tools/scripts/audit/test_ooyake_intl_projection_fresh.py` — the committed projection EXACTLY matches what the committed generator would emit (no missing / ghost / owner drift).

4. **Reproducibility + observability**
   - Committed generators: `20-actors/ooyake/scripts/gen_intl_procedures.py` (toritsugi → atlas projection) and `70-tools/scripts/coverage/gen_gov_legal_coverage.py` (toritsugi + chigiri COVERAGE.md).
   - Committed auto-generated dashboards: `20-actors/{toritsugi,chigiri,ooyake}/COVERAGE.md` — each states on its face that all rows are `unverified-seed` wayfinding scaffold, NOT authoritative coverage.

5. **Repo-wide maturity (audit 17 red → 0)** — fixed the akashi `app`→`com` lexicon-path typo (`test_akashi_invariants.py` + `adapters/dry_run_fixtures.py`), indexed `displacementTenureAttestation` in `give/README.md`, and re-baselined the subrepo upstream-health counters 7 → 8 after investigating (all 8 confirmed 404 defunct/unpublished upstreams of vendored app code — re-based, not blind-bumped, with the full list documented).

# Consequences

- The three-layer civic stack — **ooyake (structure) → toritsugi (delivery) → chigiri (legal aid)** — is now connected at worldwide scale (49–52 jurisdictions), every cross-reference machine-verified, the projection reproducible from a committed generator and guarded against drift, and the honest coverage visible in committed dashboards.
- `70-tools/scripts/audit/` is fully green (≈494 tests, 0 red).
- **Honest limits unchanged**: all procedure/referral rows remain `unverified-seed` / `:representative` — wayfinding scaffold, NOT verified live coverage (G5). Live submission, live ingest, live publish, and `:representative→:authoritative` promotion stay Council/operator gated (toritsugi G14, ooyake publish gate, chigiri VERIFICATION.md). hkg/twn atlas procedures are honestly skipped (no country unit, political-status sensitivity). No constitutional-invariant amendments.

# Alternatives Considered

- **Mark added rows `:authoritative`** — rejected; they are not verified through the reconcile pipeline (G5/G8 honesty). They stay `unverified-seed`.
- **Uniform ministry owner-unit (e.g. `gov.<iso>.foreign`)** — rejected; passport/registry-issuing authority differs by country, so a uniform ministry would fabricate the owner. Country-level owner + verbatim `owner-authority` is the honest choice.
- **Blind-bump the subrepo baseline 7→8** — rejected; investigated git history first, confirmed all 8 are defunct external upstreams, documented the list, then re-based.

# References

- ADR-2605262700 — chigiri legal-procedure Tier-B actor (R0)
- ADR-2605312030 — toritsugi citizen procedure concierge
- ADR-2606021600 — ooyake world government atlas
- ADR-2606052300 — matsurigoto e-gov execution commons (related)
- `20-actors/{toritsugi,chigiri,ooyake}/COVERAGE.md` — committed coverage dashboards
- `20-actors/{toritsugi,chigiri,ooyake}/MATURITY.md` — per-iteration loop log
