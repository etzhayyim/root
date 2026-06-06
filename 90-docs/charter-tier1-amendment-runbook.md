---
id: charter-tier1-amendment-runbook
title: "Charter Tier-1 Amendment Runbook — how to amend a Derived Policy (Rider §2) without touching a Tier-0 Priority"
status: active
doc_type: how-to
topic: charter-tier1-amendment
authoritative: true
last_verified: 2026-06-06
authoritative_for:
  - the operational procedure for amending a Charter-Rider §2 Tier-1 Derived Policy
  - how a priorityConformanceAttestation is produced and what gates it
related:
  - adr-2606062100-charter-priority-over-specifics-reconciliation
  - CHARTER-RIDER.md
  - 00-contracts/lexicons/com/etzhayyim/apps/etzhayyim/priorityConformanceAttestation.json
depends_on:
  - adr-2606062100-charter-priority-over-specifics-reconciliation
---

# Charter Tier-1 Amendment Runbook

This closes the procedure gap flagged in ADR-2606062100 (Negative/Risks): the
`priorityConformanceAttestation` lexicon exists, but the **steps** to actually run a
Tier-1 amendment were not written down. This is that procedure.

## What this does and does NOT cover

- **Covers**: amending a **Tier-1 Derived Policy** — a Charter-Rider §2 prohibited-use
  category (`§2(a)`..`§2(k)`). Example: tightening §2(d) or adding a new derived clause.
- **Does NOT cover**: a **Tier-0 Priority** (wellbecoming / multigen / collective /
  permanent-memory / tithe-redistribution-exists). Those are **fork-only** — changing one
  is founding a different association (`Constitution.sol` constant ⇒ chain fork). No runbook;
  no vote can do it. The `priorityConformanceAttestation.tier0Immutable` const `true` field
  encodes this: the artifact structurally cannot target a Tier-0 key.
- **Does NOT cover**: a **Tier-2 Parameter** (κ, quorum, tithe rate, …). Those move by the
  ordinary governance path (`setMutable` from the bound Governance contract, 1 SBT = 1 vote +
  timelock) — no priority-conformance attestation needed.

## Preconditions

1. The proposed change is to Rider §2 text only (a Derived Policy), not to a Tier-0 priority.
2. You can show the change **serves a named Tier-0 priority at least as well** as the text it
   replaces (`conformanceFinding ∈ {serves-better, serves-equally}`; `serves-worse` is
   unrepresentable in the lexicon).
3. **Council Lv7+ unanimity** is achievable. With the current one-member roster, unanimity =
   the founder's assent (1/1). Once the Bootstrap Council is seated, it is all Lv7+ seats.

## Steps

1. **Draft the new Rider text.** Edit `/CHARTER-RIDER.md` §2 (and bump the version line if the
   change is substantive). Keep the `0. NATURE OF THIS RIDER` framing intact — every §2 clause
   must remain a derivation from a Tier-0 priority.

2. **Compute the new Rider hash.** From `50-infra/etzhayyim-chain-contracts/`:
   ```
   cast keccak "0x$(xxd -p ../../CHARTER-RIDER.md | tr -d '\n')"
   ```
   This is the value the genesis anchor and the attestation must carry. (It is the same hash
   `ConstitutionInvariants.t.sol::test_rider_text_hash_matches_file` recomputes from the file.)

3. **Fill the attestation.** Create a record against
   `com.etzhayyim.apps.etzhayyim.priorityConformanceAttestation` with:
   - `amendsTier`: `tier-1` (const — the only legal value)
   - `tier0Immutable`: `true` (const — affirms no Tier-0 key is touched)
   - `riderSection`: e.g. `2(d)`
   - `servesPriority`: the Tier-0 priority key the change serves. The enum values are the
     **exact** `Constitution.sol` Tier-0 constant keys (e.g. `priority.multigen_over_current`,
     `memory.right_to_erasure_denied`) — `keccak256(value)` is a registered constant, and
     `ConstitutionInvariants.t.sol::test_lexicon_servesPriority_matches_tier0_constants`
     drift-locks the enum against the genesis (CI fails if they diverge)
   - `conformanceFinding`: `serves-better` or `serves-equally`
   - `priorTextHash`: hash of the Rider text **before** this change (the current on-chain
     `license.charter_rider_text_hash`)
   - `proposedTextHash`: the hash from step 2
   - `councilUnanimous`: `true` (const), `councilApprovals`: the count of Lv7+ assents
   - `serverHeldKey`: `false` (const — member/Council-signed, never platform-signed)
   - `proposedBy`: proposer DID; `rationale`: why it serves the priority; `attestedAt`: time
   Validate it: `python3 70-tools/scripts/validate-lexicons.py --files <record-or-lexicon> --exit-on-error`.

4. **Obtain Lv7+ unanimity.** Every Lv7+ seat signs (member-key, not server). Record the
   attestation on the kotoba Datom log (append-only, permanent — it is never deleted; a later
   amendment links via `supersededAttestation`, it does not erase).

5. **Update the on-chain anchor.** Set `license.charter_rider_text_hash` to `proposedTextHash`:
   - Pre-mainnet: edit the genesis literal in `script/Deploy.s.sol` `_mutables()` (the
     `LICENSE_CHARTER_RIDER_TEXT_HASH` slot) **and** the mirror in
     `test/ConstitutionReligiousCorpWave.t.sol`.
   - Post-mainnet: `setMutable(license.charter_rider_text_hash, proposedTextHash)` from the
     bound Governance contract (the hash is a Tier-2 mutable, so governance can update it —
     but only do so against a ratified Lv7+ priority-conformance attestation).

6. **Re-run the drift-lock.** `forge test --match-path test/ConstitutionInvariants.t.sol`.
   `test_rider_text_hash_matches_file` must pass — it proves the on-chain anchor equals
   `keccak256(/CHARTER-RIDER.md)`. If it fails, the Rider text and the anchor disagree: fix
   before merging.

7. **Record + publish.** Commit the Rider + genesis + attestation together; update
   ADR-2606062100 (or a successor ADR) with the amendment. The append-only attestation is the
   permanent audit trail (お天道様は見ており、人は忘れない — the record is never erased).

## Invariants the procedure cannot violate

- A Tier-0 priority is never touched (lexicon `tier0Immutable` const + the priorities being
  `Constitution.sol` constants ⇒ `setMutable` reverts `ImmutableKey`).
- The amendment can only be attested as serving the priority equally or better.
- The attestation is member/Council-signed (`serverHeldKey` const `false`).
- The Rider text and its on-chain hash stay in lock-step (CI drift-lock).
