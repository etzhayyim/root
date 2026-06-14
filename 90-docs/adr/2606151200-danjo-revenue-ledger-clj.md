---
id: adr-2606151200-danjo-revenue-ledger-clj
title: "ADR-2606151200: danjo revenue-ledger — clj tax-use tracer on the kotoba EAVT Datom log"
status: proposed
doc_type: adr
topic: danjo-revenue-ledger-clj
authoritative: true
last_verified: 2026-06-15
priority: 5.0
axis: architecture
weight: 0.50
priority_note: ""
authoritative_for:
  - danjo-revenue-ledger
depends_on:
  - adr-2605301600-danjo-public-accountability-oversight-tier-b-actor-r0
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2606042330-entity-as-actor-society-scale-social-mirror
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
related:
  - adr-2605302300-kanae-global-government-fiscal-flow-visualization
  - adr-2606062300-matsurigoto-egov-execution-commons
superseded_by: []
supersedes: []
---

# ADR-2606151200: danjo revenue-ledger — clj tax-use tracer on the kotoba EAVT Datom log

**Status**: proposed
**Date**: 2026-06-15
**Deciders**: Jun Kawasaki

# Context

The motivating question: 「日本政府の源泉所得税及び復興特別所得税が、どこにどのように使われているかを
1円単位で追えるか?」 danjo (弾正, ADR-2605301600) is the read-side oversight actor over the
state's published open-government books, but its existing cells (`budget_ledger`) only index the
EXPENDITURE side (appropriation/outlay). There was no actor that traced a specific REVENUE stream
through to expenditure, and no Clojure surface on the kotoba EAVT Datom log for it.

The honest fiscal reality is the crux:

- **源泉所得税** → 一般会計 (general account). Japanese public finance runs on the
  non-earmarking principle (ノン・アフェクタシオン): general-account revenue is fungible, so there
  is NO accounting fact linking a specific yen of this tax to a specific 歳出. Per-yen provenance
  is **not representable**.
- **復興特別所得税** → 一般会計 → 繰入 → 東日本大震災復興特別会計 (special account, 復興財源確保法).
  A special account is a CLOSED boundary, so within it 繰入額 → 歳出 reconciles **to the yen**.

A faithful tracer must encode this difference structurally, not as prose — and must not let an
honest-looking but false "this tax funded that outlay" claim be expressible.

# Decision

Build the **danjo revenue-ledger** as a Clojure capability under `20-actors/danjo/methods/*.clj`
on the kotoba EAVT Datom log (ADR-2605262130), inheriting danjo's constitutional discipline:

1. **Honest 3-way per-yen-traceability classification** (`taxes.clj`): every tax is
   `:general` (一般会計, fungible) | `:statutory-purpose` (目的税: 法定充当だが一般会計内, e.g.
   消費税→社会保障) | `:special-account` (特定財源). A tax is per-yen-traceable **IFF**
   `:special-account` — and that holds across the whole national + local registry (29 taxes, 国17
   + 地方12, ≈111兆 representative). Only ~1.3% of all tax is per-yen traceable — reported, never
   hidden (matsurigoto/danjo G5 coverage-honesty).
2. **Honesty gate** (the revenue-side analogue of danjo G4): `outlay-datoms` RAISES if anyone tries
   to attach `:gov.outlay/funded-by-tax` through a non-earmarked account. Per-yen provenance through
   a fungible boundary is **unrepresentable**, exactly as a legal verdict is for danjo.
3. **Per-yen flows** (`revenue_ledger.clj` `trace` + `transfers.clj`): 復興特別所得税 reconciles to
   residual 0; 国→地方 法定率繰入 (地方交付税, 地方交付税法6条) + 地方譲与税 are modeled as per-yen
   traceable inter-governmental transfers (≈19.3兆), **portion-honestly** (a tax fungible overall
   can have a legally-defined traceable portion without flipping its overall classification).
4. **Passive ingest** (`ingest.clj`, G3): projects the pre-published `gov.dataset.*` corpus
   (EDN + danjo's existing budgetRecord JSON via a dep-free `parse-json`) — never a live portal.
5. **Non-adjudicating observations** (`discrepancy.clj`): appropriation↔outlay reconciliation emits
   `:danjo.obs/*` in the SAME shape as danjo's `derived_datoms`; categories are factual relations
   with NO verdict token (G4); ≥2 source CIDs (G5); open versioned method-note (G6).
6. **Organizations as keyless mirror-actors** (`org_actor.clj`, entity-as-actor ADR-2606042330):
   real fiscal orgs (国税庁/税関/復興庁/資源エネルギー庁/財務省理財局・主計局/総務省 + 都道府県・市町村
   集約) as `did:web:etzhayyim.com:actor:jp-<handle>` with empty verificationMethod (no-server-key,
   ADR-2605231525). Observational mirror only — never represents or acts for the org.
7. **Persistence**: a local content-addressed commit-DAG log (`:tx/cid = "b"+sha256`, tamper-evident
   `verify-chain`) → a live kotoba `datomic.transact` bridge (`kotoba_bridge.clj`, ibuki R3 shape,
   host-allowlisted, dry-run default, no-server-key). An offline `autorun.clj` heartbeat composes the
   whole pipeline into one deterministic, resume-safe tx per cycle.
8. **Lexicons** (`com.etzhayyim.danjo.{taxClassification,fiscalOrg,reconciliationObservation}`) +
   a `revenueLedger` block in `manifest.jsonld` + an executable `maturity.clj` gate (9 honesty
   invariants verified across all data) + a coverage scorecard.

All figures are `:representative`; aggregate/program-level endpoints only (G10). Pure Clojure + JVM
stdlib; runs under `bb` and `clojure` (215 self-checks green).

# Consequences

- **R0 (this ADR)**: offline, `:representative`, self-verified. The honest answer to the motivating
  question is now structural code: 復興特別所得税 is 1円-traceable; 源泉所得税 is not, and the tracer
  cannot be made to claim otherwise.
- danjo's actor boundary is unchanged: still non-adjudicating, passive-only, no-server-key; the
  revenue-ledger is a capability OF danjo, not a new sovereign actor. Org mirrors do not impersonate.
- **R1 activation triggers (Council/operator-gated)**: (1) G7 live verification of the IPFS-pinned
  `jp_yosan`/`jp_fukko`/`jp_zeisei` corpus; (2) lexicon Council-attestation review; (3) live kotoba
  transact (`DANJO_KOTOBA_LIVE=1`) + fleet heartbeat registration.

# Alternatives Considered

- **Claim per-yen provenance for all taxes** — rejected: false for fungible general-account revenue
  (non-earmarking); would violate G4/G5 honesty.
- **A standalone new actor** — rejected: this is danjo's read-side mission (state's published books);
  a separate actor would duplicate the discipline and blur the boundary.
- **RisingWave/SQL store** — rejected by ADR-2605262130 (kotoba Datom log is canonical state).
- **Per-org full Tier-B actors** — rejected for R0: entity-as-actor keyless mirrors (ADR-2606042330)
  are the right weight; full actors are unwarranted for observational mirrors.

# References

- `20-actors/danjo/REVENUE-LEDGER.md` — capability overview + run commands
- `20-actors/danjo/data/REVENUE-COVERAGE.md` / `REVENUE-MATURITY.md` — generated scorecards
- ADR-2605301600 (danjo master) · ADR-2605262130 (kotoba substrate) · ADR-2606042330 (entity-as-actor)
- ADR-2605215000 (Murakumo-only inference) · ADR-2605231525 (no-server-key)
- `00-contracts/lexicons/com/etzhayyim/danjo/{taxClassification,fiscalOrg,reconciliationObservation}.json`
