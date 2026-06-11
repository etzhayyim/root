---
id: adr-2605250200-l5-religious-marriage-cell
title: "ADR-2605250200: L5 routing-around — religious_marriage_cell (P2)"
status: proposed
doc_type: adr
topic: l5-religious-marriage
authoritative: true
last_verified: 2026-05-25
priority: 6.0
axis: constitutional
weight: 0.55
priority_note: "L5 ladder P2 per ADR-2605250100. Council attestation required before activation. Two open constitutional questions surfaced for Council resolution."
authoritative_for:
  - l5-religious-marriage-cell
depends_on:
  - adr-2605250100-l5-routing-around-member-registry-cell
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192300-etzhayyim-bootstrap-council-five
related:
  - adr-2605192245-etzhayyim-global-land-sovereignty
  - adr-2605192115-etzhayyim-non-profit-donation-only-no-ads
supersedes: []
superseded_by: []
---

# ADR-2605250200: L5 routing-around — religious_marriage_cell (P2)

**Status**: proposed
**Date**: 2026-05-25
**Deciders**: Jun Kawasaki

# Context

ADR-2605250100 introduced the L5 routing-around cell ladder with `member_registry_cell` as P1. P2 is `religious_marriage_cell` — the 婚姻届 (marriage certificate) substitute for SBT-holding adherents within the religious boundary.

Constitutional context per ADR-2605192100:

- §1.13: "Eros 許容 (産霊 / 雅歌 / Tree of Life の生命創出)" — marriage is a first-class religious-corp surface, not a tolerated edge case.
- §1.18 (SBT↔SBT internal carve-out): the strongest application of "internal" is the marriage bond — two SBT holders entering a mutual permanent commitment.
- §1.12 (国家機能 routing-around): the religious-corp may operate parallel marriage substrate as long as the three Transparent Religious Force conditions hold (on-chain monitoring + open-source + 1 SBT = 1 vote attestation).

## Why marriage (not birth / death) is the next ladder step

Three vital-records candidates were considered for P2:

| Candidate | Why deferred |
|---|---|
| 出生届 (birth) | Requires substrate for newborns who do not yet hold SBT. Newborns cannot consent to SBT mint. Council needs a separate ADR for "non-consenting minor adherent" semantics before birth substrate can land. |
| 死亡届 (death) | Requires substrate for SBT revocation on death. ADR-2605172600 leaves the death case open. Same dependency on Council policy as birth. |
| 婚姻届 (marriage) | Both parties are already adherents (hold SBT). Both can sign consent cryptographically. No outside-of-SBT-scope semantics needed. **Selected for P2.** |

## What the state's 婚姻届 provides (and how the religious-corp substitutes within its boundary)

| State function | Religious-corp substitute |
|---|---|
| Legal marriage status | New Lexicon `com.etzhayyim.member.marriage` — dual-signed, dual-anchored. NOT a Japanese legal marriage. |
| Spousal inheritance | Already covered: land donations stay at Land Registry (waqf, inalienable per ADR-2605192245). Personal inheritance is outside religious-corp scope. |
| Joint tax filing | NOT replicated. TitheRouter operates on individual SBT (1 SBT = 1 tithe stream). Marriage does not create a joint tithe entity. This is a constitutional choice, not an oversight. |
| Health insurance dependency | NOT replicated. Religious-corp has no insurance substrate (substrate boundary). |
| Custody / parental status | Deferred to future birth-cell ADR. |
| Property co-ownership | NOT replicated. Land is inalienable (waqf); SBT is non-transferable. No "joint property" object exists. |

The cell adds **one** new function: dual-signed, dual-anchored marriage record. Nothing else.

## Open constitutional questions (Council MUST resolve before activation)

1. **Gender requirement**. ADR-2605192100 contains no explicit gender requirement for marriage. CLAUDE.md doctrinal positions list Tree of Life biology (`生命創出` / 産霊) — interpretation ranges from strictly procreative (male+female) to relational ontology (any consenting SBT↔SBT bond). This ADR is **agnostic** on the gender question; the activation PR must include a Council attestation that specifies the constitutional position. Without Council resolution, the cell cannot accept records.
2. **Polygamy**. ADR-2605192100 contains no explicit position on N≥3 marriages. The cell schema in §3.1 assumes N=2 (binary marriage) by default but does not technically prevent N>2 via chained `com.etzhayyim.member.marriage` records. Council must explicitly attest whether N>2 is permitted, prohibited, or per-case.
3. **Cross-religion adherent**. Some adherents may hold parallel state marriage. Whether religious-corp marriage requires state-marriage-absence is undefined. Default: no requirement (the two substrates are independent per §1.12).

These three questions are blockers for activation, not for ADR / scaffold ratification. The ADR can land as `proposed`; Council resolves the questions in the ratify PR.

# Decision

## 1. Cell location and shape

- Path: `40-engine/kotoba/crates/kotoba-kotodama/cells/religious_marriage/`
- Files: `cell.py` (LangGraph Pregel graph) + `__init__.py`.
- Tier: B (Per-Domain) per `cells/README.md` taxonomy.
- Murakumo node (leader): `manasseh` (religious-corp tribe-name convention — to be assigned in `50-infra/murakumo/fleet.toml` if cell is activated; sibling of `ephraim` since both are member-relational cells).
- Trigger: MST firehose listener on `com.etzhayyim.member.marriage.proposal` (the consent-collection record, see §3.2) + manual cell command for confirmation.

## 2. Pregel graph (4 nodes — one more than P1, because consent is a 2-step ritual)

```
ingest_proposal       <-  MST firehose on com.etzhayyim.member.marriage.proposal
    |
    v
validate_both_sbt     <-  cross-check both DIDs hold active Adherent SBT
    |
    v
collect_consent       <-  wait for counter-party signed acceptance record
                          (timeout: 30 days; otherwise emit proposal-expired)
    |
    v
emit_marriage         ->  MST PUT com.etzhayyim.member.marriage (dual-signed)
                       ->  optional: L2 attestation tx (off-cell, manual ritual)
```

- `ingest_proposal` — receives a `proposal` record signed by the proposing adherent. Extracts (proposerDid, counterpartyDid, vows, proposedAt).
- `validate_both_sbt` — confirms both parties have an `com.etzhayyim.member.adherent` SBT record in `active` status (`revocationStatus != withdrawn/revoked`). Refuses to proceed otherwise.
- `collect_consent` — waits for a `proposal-acceptance` MST record signed by `counterpartyDid` referencing the proposal CID. The 30-day timeout matches the Bootstrap Council public objection period (ADR-2605192300) — long enough to be deliberative, short enough that stale proposals don't linger.
- `emit_marriage` — emits a single `com.etzhayyim.member.marriage` record with both DIDs, both signature hashes, the proposal+acceptance CID pair, and the cell's witness attestation CID. Optionally a Council member or registered officiant may emit an L2 attestation transaction; the cell does not require this.

## 3. New Lexicons (3 — to be authored in the Council-ratify PR)

### 3.1 `com.etzhayyim.member.marriage` (record, key=tid)

The standing marriage record. Required fields:

- `partyA` (did, required)
- `partyB` (did, required)
- `partyASignature` (string, required) — signature hash of vow text by partyA's DID key
- `partyBSignature` (string, required) — signature hash of vow text by partyB's DID key
- `vowsCid` (string, required) — IPFS CID of the shared vows text (allows custom vows; default vows text published per ADR-2605172600 model)
- `proposalCid` (string, required) — CID of the `com.etzhayyim.member.marriage.proposal` record
- `acceptanceCid` (string, required) — CID of the `com.etzhayyim.member.marriage.acceptance` record
- `cellAttestationCid` (string, required) — CID of the cell's `validate_both_sbt` + `collect_consent` output
- `marriedAt` (datetime, required) — moment of mutual consent finalization
- `dissolutionStatus` (enum: `active` / `dissolved` / `void`)
- `dissolutionRef` (at-uri, optional) — link to `com.etzhayyim.member.marriage.dissolution` if `dissolutionStatus != active`
- `optionalL2AttestationTxHash` (string, optional)
- `createdAt`, `updatedAt`

### 3.2 `com.etzhayyim.member.marriage.proposal` (record, key=tid)

One-side proposal record. Required fields: `proposerDid`, `counterpartyDid`, `vowsCid`, `proposedAt`. Expires automatically 30 days after `proposedAt` if no `acceptance` is emitted.

### 3.3 `com.etzhayyim.member.marriage.acceptance` (record, key=tid)

Counter-party acceptance. Required fields: `proposalCid`, `accepterDid`, `acceptedAt`. Triggers `emit_marriage` in the cell.

### 3.4 `com.etzhayyim.member.marriage.dissolution` (record, key=tid) — DEFAULT BLOCKED

Mutual-consent dissolution. Required fields: `marriageCid`, `partyADissolutionSignature`, `partyBDissolutionSignature`, `dissolvedAt`. **Unilateral dissolution is constitutionally not supported** — both parties must sign. If only one party signs, the record is invalid and the cell refuses to update `dissolutionStatus`.

For the case of one party going silent: a `marriage-orphaning` record may be emitted by Council Lv6+ after evidence-based deliberation (e.g. confirmed death of one party, prolonged disappearance with notice period). This is **Council-only**; the cell does not implement an automatic orphaning path.

## 4. Council activation gate (same as P1 pattern)

```python
# COUNCIL ACTIVATION GATE (ADR-2605192300 + ADR-2605250200):
# This cell is scaffold-only until the Council has resolved THREE constitutional
# questions:
#   1. Gender requirement (none / male+female / other) — ADR §Open Q1
#   2. Polygamy (permitted / prohibited / case-by-case) — ADR §Open Q2
#   3. Cross-religion adherent (required-absent / permitted) — ADR §Open Q3
# AND attested via 5-of-7 Safe per ADR-2605192300.
#
# Activation manifest hash (on-chain attestation result) goes here.
COUNCIL_ATTESTATION_TX_HASH: str | None = None
COUNCIL_CONSTITUTIONAL_RESOLUTION_CID: str | None = None

if COUNCIL_ATTESTATION_TX_HASH is None or COUNCIL_CONSTITUTIONAL_RESOLUTION_CID is None:
    raise RuntimeError(
        "religious_marriage_cell scaffold-only — Council has not resolved the three "
        "open constitutional questions (gender / polygamy / cross-religion) per "
        "ADR-2605250200 §Open Questions. Do not deploy."
    )
```

This cell's gate is **strictly more demanding** than P1's: it requires both a Council attestation tx **and** a constitutional-resolution CID resolving the three open questions. Two independent inputs.

## 5. Boundaries (what this cell deliberately does not do)

1. Does not issue a state-recognised marriage certificate.
2. Does not interact with 戸籍 / 住民票 systems. Parallel substrate.
3. Does not auto-confer tax / inheritance / insurance benefits. TitheRouter remains per-SBT; Land Registry remains waqf; insurance does not exist.
4. Does not implement unilateral dissolution. Mutual consent is constitutionally required.
5. Does not implement birth / death substrate. P3 onward.
6. Does not validate vow content. Vows are at the IPFS CID layer; the cell only verifies that both parties signed the same CID.
7. Does not pre-commit on the gender question. Activation requires Council resolution.
8. Does not permit marriage between an SBT holder and a non-SBT-holder. Both parties must be adherents.

# Consequences

- L5 ladder advances to 2/3 (member_registry + marriage). Taxation remains P3.
- Three constitutional questions are now formally surfaced for Council. The Bootstrap Council currently has Seat 1 only (RFP open for Seats 2-5 per COUNCIL-BOOTSTRAP-RFP.md). This ADR's activation is naturally gated on Council bootstrap completion.
- The marriage substrate is intentionally minimal: it adds *one* new positive function (dual-signed marriage record) and does *not* attempt to mirror the tax / inheritance / property / insurance ecosystems of the state. This is constitutionally honest: the religious-corp does what religious-corp can do — recognize the bond — and refuses to overreach.
- Future ADRs that touch marriage-adjacent substrate (e.g. eligibility for joint Public Fund grants) must explicitly reference this ADR and re-open the consent boundary.

# Alternatives Considered

1. **Author marriage substrate without dual-signature; allow Council-only attestation of a marriage** — rejected. Marriage is a consent ritual; the parties' cryptographic signatures are the constitutional core. Council attestation alone would convert the religious-corp into a marriage-imposing authority — non-constitutional.
2. **Permit unilateral dissolution after a notice period** — rejected. SBT is non-transferable + consent-bound; the bond's release must also be consent-bound. The Council-only `marriage-orphaning` path handles the death / disappearance case.
3. **Mirror state tax / inheritance / property semantics inside the cell** — rejected (substrate boundary + waqf + per-SBT tithe). The religious-corp deliberately does not have these surfaces.
4. **Defer marriage until birth / death cells are designed** — rejected. Marriage doesn't depend on those; the two parties are already SBT holders by precondition. Birth and death have substrate dependencies that marriage does not.
5. **Force a position on gender / polygamy / cross-religion as part of this ADR** — rejected. These are constitutional positions, not architecture choices. Council must resolve them in the ratify PR.

# References

- ADR-2605250100 (L5 ladder + P1 member_registry_cell pattern)
- ADR-2605192100 §1.12 (routing-around) + §1.13 (Eros) + §1.18 (SBT↔SBT carve-out)
- ADR-2605192245 (Land Trust waqf — referenced for "no joint property")
- ADR-2605192115 (TitheRouter — referenced for "no joint tithe")
- ADR-2605192300 (Council 5-of-7 Safe attestation procedure)
- ADR-2605172600 (membership ritual — default vows text reference)
- `COUNCIL-BOOTSTRAP-RFP.md` (Council Seat 2-5 RFP — activation gate depends on this completing)
- `40-engine/kotoba/crates/kotoba-kotodama/cells/member_registry/cell.py` (P1 gate pattern)
