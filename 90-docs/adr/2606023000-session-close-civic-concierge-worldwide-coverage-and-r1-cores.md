---
id: adr-2606023000
title: "ADR-2606023000: Session close — civic-concierge worldwide registry coverage + R1 pure compute cores/resolvers"
status: active
doc_type: adr
topic: session-close-civic-concierge-worldwide-coverage-and-r1-cores
authoritative: false
last_verified: 2026-06-02
priority: 4.0
axis: process
weight: 0.40
priority_note: "session-close record for the 6-iteration /loop civic-concierge maturation"
authoritative_for: []
related:
  - adr-2605312030-toritsugi-government-procedure-concierge-tier-b-actor-r0
  - adr-2605312500-kurashimori-consumer-protection-concierge-tier-b-actor-r0
  - adr-2605312400-moushibumi-democratic-participation-concierge-tier-b-actor-r0
  - adr-2605302130-himotoki-disclosure-request-tier-b-actor-r0
  - adr-2605262700-chigiri-legal-procedure-tier-b-actor-r0
  - adr-2605263400-musubi-covenant-ceremony-tier-b-actor-r0
  - adr-2606022600-session-close-r0-actor-coverage-sweep-and-organism-axis-convention
supersedes: []
superseded_by: []
depends_on:
  - ADR-2605312030 (toritsugi) · ADR-2605312500 (kurashimori) · ADR-2605312400 (moushibumi)
  - ADR-2605302130 (himotoki) · ADR-2605262700 (chigiri) · ADR-2605263400 (musubi)
---

# ADR-2606023000: Session close — civic-concierge worldwide registry coverage + R1 pure compute cores/resolvers

**Date**: 2026-06-02
**Status**: ACTIVE (documentation-only session closure)
**Deciders**: Jun Kawasaki

## Context

The operator drove a self-paced `/loop 30nin 全世界coverage, 成熟度を高めて`
across six iterations, maturing the six **citizen-facing civic-concierge Tier-B
actors** — toritsugi (取次, gov-procedure), kurashimori (暮らし守, consumer),
moushibumi (申文, democratic-participation), himotoki (繙き, DSAR/FOIA), chigiri
(契, legal-procedure substrate), musubi (結, covenant ceremony). Each actor was
R0 scaffold with a JP-centric (5–7-entry) seed registry. The work was executed
by adversarially-verified subagent workflows (~30 agents per coverage pass, ~12
per R1-core pass). A concurrent background `/loop` matured unrelated actors and
committed to the shared dev branch throughout; one coverage pass (iter-1/2) was
swept into that loop's omnibus commit `2ad240504` rather than landing as a
clean standalone commit — no work was lost (see Honest caveats).

The driving constraints, held every iteration: **R0 ceiling** (cell `cell.py`
wrappers stay import-time `RuntimeError`; no submission/dispatch/代行), **G14**
(every registry entry `verificationStatus = unverified-seed`; no live action),
**G8** (non-fabrication — cite real governing law, leave unknowns null, omit
obscure jurisdictions rather than invent them), and each actor's UPL /
political-neutrality / informational-only / zero-compensation boundary.

## Decision (what shipped)

1. **Worldwide registry coverage.** The six seed registries went from JP-centric
   (~25 entries total) to **363 entries across 47 distinct jurisdictions** (all
   G20 + representative jurisdictions on every continent). Two new registries
   were created (chigiri `legal-aid.seed.json` legal-aid referral; musubi
   `ceremony-recognition.seed.json` civil-recognition mapping). **100%
   `unverified-seed`**, every entry carrying a provenance URL + per-jurisdiction
   boundary caveat. (iter-1 worldwide + iter-3 long-tail deepening.)

2. **Lexicon reconciliation.** 4 lexicons extended additively (procedure /
   remedyTarget / participationTarget / disclosureTarget — new fields +
   knownValues, R0-permissive, no `additionalProperties:false`, no new required
   fields) + 2 created (`legalAidReferral`, `ceremonyRecognition`). Validators
   green (`lexicon-primary-types`, `nsid-lexicon-exists`,
   `no-legal-aid-consideration`).

3. **Fail-closed registry invariants tests.** 6 pytest suites (41 tests):
   unique ids, 100% `unverified-seed` (G14), provenance + lastVerified present,
   **≥12 distinct jurisdictions** (raised from ≥5 to lock worldwide coverage as
   a regression guard), boundary caveat present.

4. **R1 pure compute cores + routing resolvers — 9 modules across the 6 actors,
   ~300 tests, all behind closed activation gates.** Deadline/window family:
   kurashimori `cooloff.py` (cooling-off, JP-inclusive / EU-exclusive / US-FTC
   business-day conventions), himotoki `deadline.py` (DSAR/FOIA response windows
   — GDPR 1mo+2mo / CCPA 45+45 / LGPD 15 / PIPEDA 30 / FOIA 20 business days /
   APPI indeterminate→null), moushibumi `window.py` (participation window),
   toritsugi `deadline.py` (statutory filing window). Routing resolvers (pure
   registry queries, no eligibility/means determination): chigiri
   `referral_match.py`, musubi `recognition_resolver.py`, himotoki
   `target_resolver.py`, kurashimori `escalation_resolver.py`, moushibumi
   `opportunity_resolver.py`. The G-invariants (`is_legal_opinion` /
   `renders_advice` / `confers_civil_status` / `isEligibilityDetermination`) are
   hard-wired `False` with no code path to `True` and asserted in every record
   builder. **Adversarial verification caught two real defects, both fixed**: a
   moushibumi pre-open bug (`as_of < open_date` wrongly reported `is_open=True`
   → added `not_yet_open`, corrected `is_open` to `[open, close]`, + regression
   tests) and a toritsugi integration-test conflation of `statutoryProcessingDays`
   (authority processing time) with the member's filing window (+ bool-as-int
   rejection). Each gated `cell.py` was re-confirmed import-time `RuntimeError`.

5. **Verification-workflow docs.** 6 `registry/VERIFICATION.md` (5 new) — the
   G14 three-tier `unverified-seed → maintainer-verified → council-verified`
   human checklist, per-field over each registry's real schema, with a
   **worldwide per-jurisdiction provenance** check (official-domain table:
   `.go.jp` / `.gov` / `.gouv.fr` / `.gov.uk` / `europa.eu` / `.gob.*` /
   `.go.kr` …, fail-closed if not confirmable) and a citation to each actor's
   machine-enforced invariants test.

## Consequences

- The civic-concierge cluster has reached its **R0 + R1-pure maturity ceiling**:
  worldwide data, machine-verified fail-closed invariants, deterministic compute
  cores/resolvers for every actor, and a documented verification workflow — all
  with constitutional gates closed and zero live capability granted.
- Further maturation now requires an **operator/Council decision**, not more
  code: (a) Council R1 ratification (Bootstrap Council RFP closes 2026-06-19) to
  activate cells + drafting/dispatch; (b) explicit charter-scope approval to
  extend worldwide registries to charter-global actors (e.g. kanae fiscal-flow);
  or (c) over-implementation the per-actor MATURITY ledgers explicitly warn
  against.
- **Honest caveats**: cell `cell.py` Pregel wrappers remain import-smoke-gated
  (this env's langgraph is broken by a pydantic/pydantic-core version mismatch;
  tests run with `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` and exercise the gate-free
  pure cores, never `super_step`). iter-1/2 (initial worldwide + lexicon +
  kurashimori cooloff) landed inside the concurrent loop's omnibus commit
  `2ad240504`, not a dedicated commit; iter-3 is `f7c520bac`; iter-4/5/6 land in
  this session-close commit. No `[[modules]]` entries exist for these actors, so
  only the ADR registry is updated in deps.toml.

## Alternatives Considered

- **Deepen registries to 100+ obscure jurisdictions.** Rejected — beyond the
  major-economy + per-continent representatives already covered, the model's
  knowledge thins and fabrication risk (G8) rises sharply; padding entry counts
  for jurisdictions whose statutes/channels can't be grounded would violate the
  charter. Omission is the honest floor.
- **Activate the gated `cell.py` bodies to claim R1.** Rejected — that bypasses
  the per-actor Council R1 activation gates. Landing tested, gate-free pure cores
  is the charter-respecting way to pre-build R1 logic.
- **Stand up charter-global new actors (kanae, etc.) this session.** Deferred —
  expanding an actor's worldwide surface is a charter-scope call for the
  operator/Council, not an autonomous loop decision.

## References

- Per-actor master ADRs: 2605312030 / 2605312500 / 2605312400 / 2605302130 /
  2605262700 / 2605263400
- `20-actors/<actor>/registry/{*.seed.json,VERIFICATION.md}` + `MATURITY.md`
- `40-engine/kotoba/crates/kotoba-kotodama/cells/{kurashimori_cooloff_check,himotoki_deadline_check,moushibumi_status_track,toritsugi_status_track,chigiri_legal_aid_clinic,musubi_recognition_resolver,kurashimori_escalation,moushibumi_opportunity_match}/`
- `70-tools/scripts/audit/test_<actor>_registry_seed.py` (6 fail-closed suites)
- Commits: `2ad240504` (iter-1/2, via concurrent omnibus) · `f7c520bac` (iter-3 long-tail) · this session-close (iter-4/5/6 + ADR + deps.toml)
