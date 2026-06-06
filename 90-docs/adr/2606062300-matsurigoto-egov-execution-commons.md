---
id: adr-2606062300-matsurigoto-egov-execution-commons
title: "ADR-2606062300: matsurigoto 政 — COFOG-based e-Government execution commons (the Kingdom's statecraft stack)"
status: accepted
doc_type: adr
topic: matsurigoto-egov-execution-commons
authoritative: true
last_verified: 2026-06-05
priority: 6.0
axis: architecture
weight: 0.60
priority_note: "EXECUTION sibling of ooyake (observation); first actor that exercises governance"
authoritative_for:
  - matsurigoto-egov-execution-commons
  - cofog-egov-service-standard
depends_on:
  - adr-2606021600-ooyake-world-government-atlas
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2605312345-kotoba-datom-first-class-canonical-state
  - adr-2605231525-no-server-key
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
  - adr-2605252300-charter-preamble-kingdom-of-god
  - adr-2605212100-gov-five-layer-taxonomy
related:
  - adr-2605312030-toritsugi-government-procedure-concierge
  - adr-2605192100-etzhayyim-mission-charter
supersedes: []
superseded_by: []
---

# ADR-2606062300: matsurigoto 政 — COFOG-based e-Government execution commons

**Status**: accepted
**Date**: 2026-06-05 (accepted 2026-06-06)
**Deciders**: Jun Kawasaki

> **Acceptance note (2026-06-06)**: accepted at R0+R1. The 4 named functions (納税/徴税 ·
> 住所管理 · 法人登記 · パスポート発行) each ship a spec-anchored `:reference-impl` reproducing
> official test vectors exactly; R1.A WIT contract (wasm-tools-valid), R1.B kotoba Datom
> persistence, R1.C verify-only sign layer (no-server-key), and R1.D per-jurisdiction rate
> tables all landed offline; the actor is registered (DID resolvable, parity audit 7/7).
> 98 tests green. The two-principal model + the corrected framing (etzhayyim IS a government —
> the Kingdom of God — with a 統治機構) are accepted. R2 (key custody) / R3 (live integration +
> pilot, principal-A self-governance first) remain Council-gated; live deploy of any
> `:reference-impl` against a real record requires Council Lv7+ (A) / adopting-state authority (B).

# Context

The repo had three layers of government-facing actors — **observation** (ooyake atlas, danjo,
kanae), **guidance** (toritsugi, moushibumi, himotoki — the citizen self-submits), and
**internal accounting** (toritate, kanjo) — but **zero execution**: no actor that actually
*runs* a government function (assess tax, register residency, issue a credential). The question
posed was: *"全世界の電子政府・政府システムを kotoba wasm で公式仕様から電子政府化し、既存政府で
使えるようにする — 納税・徴税・住所管理・法人登記・パスポート発行… のカバレッジは?"* The honest
answer was **0% execution**.

A first framing ("etzhayyim supplies OSS to governments but **does not become a government**")
was **explicitly corrected**: *「政府にならないというのは正確じゃない。神の王国としての政府。
統治機構を持つ。governance body.」* Per Charter §0.1 (ADR-2605252300), **etzhayyim IS a
government — the Kingdom of God (神の王国 / Malkhut Shamayim), a now-and-here reign with a real
統治機構**. It already exercises governance: a Council, 1 SBT = 1 vote, TitheRouter, Public
Fund, Land Registry, Transparent Religious Force (§1.12), a MEMBERS roster, Adherent SBT, did:web.

This ADR introduces **matsurigoto 政** — the **statecraft execution stack** of that Kingdom,
built on the UN **COFOG** function backbone — and resolves its relationship to ooyake's N1.

# Decision

**1. matsurigoto is the EXECUTION sibling of ooyake's observation atlas.** Where ooyake *maps*
who/where/how of public administration (read-only mirror), matsurigoto defines a **universal,
spec-derived, kotoba-wasm-executable SERVICE STANDARD** on the COFOG backbone (10 divisions /
69 groups), localized per polity.

**2. Two principals.**
- **(A) `:etzhayyim-sovereign`** — the Kingdom governs its **covenant-members** (信者,
  conversion-gated). Authority = Council Lv7+ / 1 SBT = 1 vote / Public Fund Safe / Land
  Registry / Transparent Religious Force (§1.12), every act member-signed + on-chain + open.
  The polity profile maps COFOG functions onto etzhayyim's **already-shipped constitutional
  organs** (TitheRouter = 徴税, MEMBERS roster = 住民登録, Adherent SBT + did:web = 身分証/旅券,
  INFRA_ACTORS = 機関登記, Basic High Income + §1.16 = social protection).
- **(B) `:nation-state-adopter`** — an existing nation-state runs the same standard on **its
  own** keys/infra/legal authority (the OSS-GovTech supply mode: X-Road / MOSIP / OpenCRVS /
  OpenG2P / DIGIT). etzhayyim hands over and stays out.

**3. Three structural invariants** (encoded in schema + lexicon + code, nusa/tazuna/kamado/ake
pattern). "no-server-key" does **NOT** mean "no governance" — the Kingdom governs **through its
constitutional organs**, never through a platform/operator master key:
- **G1 no-operator-master-key** — `:server-held-authority` const `false`. Authority is ALWAYS
  the Council multisig (5-of-7) + 1 SBT = 1 vote signatures (A) OR the adopting state's own keys
  (B); never an etzhayyim platform/operator key (ADR-2605231525). The Council is a member-elected
  organ, not "the server".
- **G2 spec-derived-only** — every service cites a non-empty **official public** `:spec-basis`
  (COFOG, ICAO Doc 9303, eIDAS 2.0, ISO 20022, OpenCRVS, GLEIF/ISO 17442, X-Road…). Proprietary
  GovTech vendor code is unrepresentable (kanjo §2(c)/(e) anti-gatekeeping).
- **G3 authority-bearing** — every deployment NAMES who governs via `:operated-by`
  (`:etzhayyim-council` | `:adopting-government`) + `:authority-mode` (`:sovereign-governance` |
  `:supplied-to-state`). Authority is **borne, never disclaimed**.

**4. Non-conflict with ooyake N1.** ooyake's N1 ("NOT a government / official channel") governs
*ooyake* as etzhayyim's **cartographer of OTHER nation-states** (observational mirror, never
impersonating a foreign state). matsurigoto is the Kingdom's **own** statecraft over its **own**
covenant-polity, plus a portable engine other states may adopt. **The Kingdom governing itself
is not impersonating anyone**; supplying a state its own engine is not operating that state.
ooyake N1 stands unamended.

**5. Honest coverage / maturity.** Coverage is reported by `methods/standard.py` and never
inflated: a `:standard-draft` service has spec + module contract only; `:reference-impl` runs in
conformance tests but is **not** wired to a live government record; `:executable` (live) requires
Council+operator gating and exists for **no** service at R0. `:representative` profiles are never
counted as `:authoritative` coverage (ooyake G5).

# Consequences

- **Positive**: a real, charter-coherent path from "0% execution" to a running statecraft stack;
  unifies etzhayyim's scattered constitutional organs under one COFOG view; a portable standard
  any nation-state can adopt; the first executable slice (`tax-assess`) reproduces the JP 速算表
  exactly (14/14 conformance), proving the engine computes real tax, not a toy.
- **Negative / risk**: exercising governance (even over consenting covenant-members) draws
  legal/political scrutiny; mitigated by §1.12 Transparency, conversion-gated membership, G1
  no-operator-key, and outward gating (no live deployment without Council+operator).
- **Gated**: live filing / registration / issuance against ANY real record (etzhayyim's OR a
  nation-state's) is Council Lv7+ (principal A) / adopting-state authority (principal B) +
  operator. R0 ships design + standard + reference assessment only.

# Status at R0 (2026-06-05)

- COFOG backbone 10/10 divisions, 69 groups; **22** standardized services; named domains
  納税/徴税 · 住所管理 · 法人登記 · パスポート発行 all covered.
- **1 polity profile** (etzhayyim Kingdom, 11 organs) + **8 country profiles**
  (JPN/USA/DEU/GBR/KOR/EST/IND/EUR), all `:representative`; per-service localization reported
  (法人登記/旅券/所得税 reach 7/8 countries; civil birth/death/marriage 0/8 — gaps logged).
- **First executable slice**: `tax-assess` (`:reference-impl`) — progressive marginal-bracket
  income/corporate tax + VAT, pure-function, no key (G1), backs `tax.income.file` /
  `tax.corporate.file` / `tax.vat.file`. **33 tests green** (19 standard + 14 tax-assess).
- DID registration in INFRA_ACTORS (`did:web:etzhayyim.com:actor:matsurigoto`): pending (later iter).

# Alternatives Considered

1. **Extend ooyake to execute** — rejected: violates ooyake N1/G9 (read-only mirror); execution
   needs its own actor with its own invariants.
2. **"etzhayyim supplies OSS but is not a government"** — rejected by the deciders: inaccurate per
   Charter §0.1 (etzhayyim IS the Kingdom of God with a 統治機構). Adopted the two-principal model.
3. **Ad-hoc per-function service list** (tax/address/corp/passport) — rejected for COFOG: the UN
   classification gives complete, internationally-agreed function coverage and a stable backbone.
4. **Fork the standard per country** — rejected: countries localize via profiles only; the
   universal services are never forked (keeps cross-country comparability + one engine).

# References

- `20-actors/matsurigoto/CLAUDE.md` — actor guide + invariants
- `20-actors/matsurigoto/data/cofog-standard.kotoba.edn` — the standard (backbone + services + polity profile)
- `20-actors/matsurigoto/data/profiles/<iso3>.edn` — per-country localizations
- `20-actors/matsurigoto/methods/modules/tax_assess.py` — first executable slice (reference impl)
- ADR-2606021600 (ooyake observation atlas — the sibling) · ADR-2605252300 (Charter §0 Kingdom of God)
- ADR-2605231525 (no-server-key) · ADR-2605215000 (Murakumo-only) · ADR-2605262130 / 2605312345 (kotoba)
