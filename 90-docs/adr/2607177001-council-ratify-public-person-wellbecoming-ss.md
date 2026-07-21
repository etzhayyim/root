---
id: adr-2607177001-council-ratify-public-person-wellbecoming-ss
title: "Council ratification — ADR-2607177000 public-person as-of + wellbecoming/mago/ko priority"
status: accepted
doc_type: adr
topic: council-ratification
authoritative: true
last_verified: 2026-07-17
depends_on:
  - ADR-2607177000 (covenantal SS public-person + priority stack — superproject 90-docs)
  - ADR-2606052300 (fuchi)
  - ADR-2605302357 (§1.16)
  - ADR-2605192300 (Bootstrap Council)
  - ADR-2605192100 (§1.9 / §1.10)
---

# ADR-2607177001: Council ratification of public-person / wellbecoming priority SS surface

**Status**: accepted
**Date**: 2026-07-17
**Deciders**: Jun Kawasaki (Bootstrap Council Seat 1 / founder; owner standing authorization for agent-executed Council-level operational ratifications)

## Decision

**Ratify** the following as Council-approved operational doctrine and implementation surface:

1. **ADR-2607177000** (superproject `90-docs/adr/…`):
   - Priority stack: **wellbecoming > mago(孫) > ko(子) > present adherent**
   - `public-person?` as-of derivation for covenantal SS recipients
   - PUBLIC = facts; SCORE = unrepresentable; INTERNAL = rationing only
2. **fuchi implementation** on `etzhayyim/com-etzhayyim-fuchi` main @ `54c0b9ecc4b6`
   (`methods/public_person.cljc`, `data/public-person-dynamic.edn`, analyze public projection)
3. **Ontology v2** in the canonical fuchi repository:
   `orgs/etzhayyim/com-etzhayyim-fuchi/schema/maintainer-sustenance-ontology.edn`
   (`:ontology/priority-stack`, empty `:ontology/score-surface-keys`)

## Scope of this ratification

| In scope | Out of scope (still gated) |
|---|---|
| Doctrine + offline/dry-run code landing | Live disbursement / SBT mint / openmail notify |
| Public-surface fact projection | Live `FUCHI_ALLOW_LIVE_*` legs (existing live_gate) |
| Ontology closed vocabs for public/score | Full 5-seat Bootstrap Council multi-sig on-chain |

Live outward legs remain refuse-by-default until a future Council+operator+member gate flip (ADR-2606052300 G10). This ratification does **not** enable live cash or live provision.

## Bootstrap Council honesty

Bootstrap Council Seats 2–5 RFP (ADR-2605192300) may still be open. This ratification is recorded as **Seat 1 / founder attestation** under owner standing authorization (2026-07-10 / 2026-07-17) that agent-executed Council-level operational decisions may proceed with Seat 1 authority when full multisig is not yet populated. When Seats 2–5 are seated, they may co-attest this record without amending the doctrine.

## Attestation record

```edn
{:council.attestation/id "att.2607177001.public-person-ss"
 :council.attestation/adr "2607177000"
 :council.attestation/companion "2607177001"
 :council.attestation/level :lv6+
 :council.attestation/seats [{:seat 1 :did "did:web:etzhayyim.com:member:founder"
                              :role :founder :vote :for}]
 :council.attestation/quorum-note "bootstrap-seat-1-standing-authorization"
 :council.attestation/at "2026-07-17T00:00:00Z"
 :council.attestation/implements
 ["etzhayyim/com-etzhayyim-fuchi@f47ba29e228c"
  "00-contracts/schemas/maintainer-sustenance-ontology.kotoba.edn#v2"]
 :council.attestation/does-not-enable [:live-disbursement :live-sbt-mint :live-provision]}
```

## Consequences

- Operators and agents treat ADR-2607177000 as **Council-ratified** for offline implementation and pin.
- Live SS delivery still requires separate live-gate ratification.
- Multi-gen wellbecoming priority remains Tier-0 (Charter §1.9 / §1.10 / Rider); this ADR only operationalizes recipient publicity and score non-representation.
