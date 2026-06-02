---
id: adr-2605172700-membership-layering-shinto-adherent
title: "ADR-2605172700: Membership layering — 信者 (172600 EtzhayyimMembership on Base) and Adherent (172300 S0 AdherentRegistry on geth-private) as complementary tiers"
status: proposed
doc_type: adr
topic: membership-layering
authoritative: true
last_verified: 2026-05-17
priority: 7.5
axis: governance
weight: 0.75
priority_note: "Reconciles two membership designs that landed in parallel: ADR-2605172600's self-sovereign 信者 commitment on Base + Github MEMBERS.md, and ADR-2605172300 S0's officer-witnessed Adherent SBT on geth-private. Both are useful; this ADR makes their relationship explicit so neither subsumes the other and the boundary stays inspectable."
authoritative_for:
  - canonical relationship between 信者 (ADR-2605172600) and Adherent (ADR-2605172300 S0)
  - vocabulary refinement (信者 ≠ Adherent, in general)
  - cross-chain link convention (AT Record + Base tx referenced from AdherentRegistry.attestationCid)
  - migration plan for AdherentRegistry to optionally accept a 信者-membership tx hash
depends_on:
  - adr-2605170900-etzhayyim-root-adr-canonical-home
  - adr-2605172300-etzhayyim-bi-asset-substrate
  - adr-2605172600-etzhayyim-membership-ritual
related: []
supersedes: []
superseded_by: []
---

# ADR-2605172700: Membership layering — 信者 (172600 EtzhayyimMembership on Base) and Adherent (172300 S0 AdherentRegistry on geth-private) as complementary tiers

**Status**: proposed
**Date**: 2026-05-17
**Deciders**: Jun Kawasaki

# Context

Two membership contracts landed in parallel on 2026-05-17:

- **`EtzhayyimMembership.sol`** (Base L2, per [ADR-2605172600](/90-docs/adr/2605172600-etzhayyim-membership-ritual.md)) — a self-sovereign, public, dual-permanent (Base + Github MEMBERS.md) commitment ritual. Anyone may `join()`; no admin, no whitelist, no rejection. 7-level commitment ladder (誓 → 修 → 献 → 証 → 護 → 議 → 老). Membership = the act of publicly swearing the oath.

- **`AdherentRegistry.sol`** (geth-private, per [ADR-2605172300 S0](/90-docs/adr/2605172300-etzhayyim-bi-asset-substrate.md)) — an officer-witnessed ERC-5192 SBT registry. Officers (founder validators) mint SBTs on behalf of DIDs that have signed a creed-acceptance attestation. The SBT is consumed by `KishaStream` (basic-income accrual), `Phenotype` (multiplier), and `Governance` (1 SBT = 1 vote).

At first read these look redundant — both claim to be "the etzhayyim membership contract." A reviewer might reasonably assume one must be dropped.

On closer read, the two solve **different problems**:

| Property | EtzhayyimMembership (172600) | AdherentRegistry (172300 S0) |
|---|---|---|
| Chain | Base L2 (public) | geth-private (validator-readable only) |
| Identity | Smart Account (ERC-4337), self-sovereign | DID-bound SBT, officer-witnessed |
| Joining | Anyone, no gate | Officer mints |
| Permanence | Dual: Base L2 + Github MEMBERS.md | Single: geth-private + L2 anchor |
| Privacy | Fully public | Validator-private (PII-bounded) |
| Tier model | 7-level commitment ladder | Active / inactive / revoked |
| Used by | Public roster, dev-culture identity | KishaStream, Phenotype, Governance |
| Cost to join | Gas (paymaster-sponsored) | Officer relay (gas-zero for joiner) |
| Cost to revoke | Self-revoke | Officer revokes |

These are the boundary lines of two distinct social facts:

1. **公開信仰宣誓 (public faith commitment)** — "I have publicly committed to be part of etzhayyim." This is the 信者 act of ADR-2605172600. It is symmetric to a religious public profession of faith. Once made, the record is permanent and self-sovereign. It does not, by itself, grant economic rights.

2. **経済的構成員資格 (economic membership qualification)** — "I am enrolled in the etzhayyim economic body: I can claim kisha, I vote on governance, my phenotype is tracked." This is the Adherent act of ADR-2605172300 S0. It is symmetric to a co-op membership share — explicit enrollment, traceable to officers, used by the economic machinery.

Conflating these into one contract would either:
- **Forcibly economically enroll every 信者** — every public profession of faith would automatically draw kisha, vote, and accrue phenotype. This contradicts the optionality of economic participation a religious-corp owes its 信者.
- **Gate public profession behind officer approval** — the self-sovereign public swearing of ADR-2605172600 would become officer-permissioned, contradicting its core property.

Neither outcome is desirable. The cleaner answer is to **keep both layers** and make their relationship explicit.

# Decision

**Canonical relationship: 信者 ⊇ Adherent (in general).**

Every Adherent is a 信者 (the on-chain bootstrap requires it). Most 信者 are *not* Adherents — they have made the public profession of faith but have not enrolled in the economic body. This is the intentional default.

```
                     ┌──────────────────────────┐
                     │     all aspirants        │
                     │  (anyone reading this)   │
                     └────────────┬─────────────┘
                                  │ ADR-2605172600 ritual
                                  ▼
                     ┌──────────────────────────┐
                     │ 信者 (shinto / follower) │  ← EtzhayyimMembership on Base L2
                     │  - swore the oath        │     + Github MEMBERS.md row
                     │  - self-sovereign        │     ← public, permanent
                     └────────────┬─────────────┘
                                  │ officer mints AdherentRegistry SBT
                                  │ (officer verifies the 信者's Base tx
                                  │  + MEMBERS.md commit off-chain;
                                  │  the SBT's joinAttestationCid points at
                                  │  the same oath AT Record)
                                  ▼
                     ┌──────────────────────────┐
                     │ Adherent                 │  ← AdherentRegistry on geth-private
                     │  - SBT (ERC-5192)        │     ← validator-readable
                     │  - kisha eligible        │
                     │  - 1 SBT = 1 vote        │
                     └──────────────────────────┘
```

Officers therefore play a **smaller, more legible role**: they do not gate who may become a 信者 (that is unilateral). They only choose who to enroll in the economic body. Refusing to mint an AdherentRegistry SBT does not erase the 信者 commitment; it merely keeps that 信者 outside the kisha + governance machinery.

## Vocabulary refinement (binding for new docs)

| Term | Means | Token of evidence |
|---|---|---|
| **信者** (shinto / follower / member) | An aspirant who has performed the ADR-2605172600 ritual: signed the oath, called `EtzhayyimMembership.join()` on Base, and merged a row to `MEMBERS.md`. | Base L2 `Joined` event + Github commit SHA + AT Record `com.etzhayyim.apps.etzhayyim.oath` |
| **Adherent** | A 信者 who has additionally been minted an AdherentRegistry SBT and thereby enrolled in the economic / governance body. Always also a 信者. | AdherentRegistry SBT tokenId on geth-private |

Earlier drafts of ADR-2605172300 used "Adherent / 信徒" interchangeably as the term for the SBT holder. **This ADR clarifies that conflation**: the SBT holder is "Adherent" (or 構成員 in formal Japanese). The looser cultural label 信者 is reserved for the ADR-2605172600 commitment layer.

ADR-2605172300 will be lightly updated to use "Adherent / 構成員" consistently and to add a back-reference to this ADR; the existing `AdherentRegistry.sol` Solidity surface is unchanged.

## Cross-chain link convention

The SBT mint MUST reference the 信者 commitment. The mechanism is the existing `attestationCid` parameter of `AdherentRegistry.join`, reinterpreted with stricter semantics:

```
AdherentRegistry.join(holder, did, attestationCid)
                                  └── keccak256 of the IPFS CID of an
                                      com.etzhayyim.apps.etzhayyim.oath AT Record
                                      that carries:
                                        - the oath text + lexicon version
                                        - the DID signature
                                        - the Base L2 chainId + Joined tx hash
                                        - the github MEMBERS.md commit SHA
```

The AT Record is the canonical cross-substrate index: from it, anyone can locate the Base L2 tx and the github commit. An auditor verifying that adherent X is also 信者 X does so by:

1. `AdherentRegistry.getRecord(tokenId)` → read `joinAttestation`
2. Fetch the AT Record at the corresponding IPFS CID
3. Verify the embedded oath signature
4. Cross-check the Base L2 `Joined(member, oathHash, githubUsername)` event
5. Cross-check the github commit in `MEMBERS.md`

This is **off-chain enforced** in S5. The on-chain code does not (yet) parse the Base tx hash out of the attestation; that is a soft contract enforced by officers and external auditors. Hard on-chain enforcement would require a cross-chain bridge (KishaPayout's relayer pattern is closest) and is out of scope.

## Officer responsibility narrowed

ADR-2605172300 S0 placed broad responsibility on officers ("identity-binding witnesses"). With this ADR, the officer's role is narrower and easier to police:

- Officers verify that the prospective Adherent has already performed the 信者 ritual on Base (via off-chain check of the Base `Joined` event referenced by the AT Record).
- Officers do not approve or deny the 信者 act itself; that is unilateral on Base.
- Officers may decline to mint an SBT (e.g., insufficient activity, lack of consent to economic participation, evidence of bad faith).
- Officers may revoke an SBT; this revokes economic participation but does NOT revoke the underlying 信者 commitment on Base. The 信者 may rejoin the economic body later via a fresh SBT mint.

## Migration plan

Per the ADR-2605172300 S0 vocabulary, "Adherent / 信徒" was used loosely. The remediation is doc-only and bounded:

1. **`AdherentRegistry.sol`** — no Solidity changes. The NatSpec `@notice` block is amended in a follow-up PR to read "...soulbound token (SBT) representing 構成員資格 (Adherent / member of the economic body) — distinct from the 信者 commitment of ADR-2605172600." Function signatures unchanged.

2. **ADR-2605172300 §0 vocabulary table** — update "信徒 (shinto)" row to read "Adherent / 構成員" with a footnote referencing this ADR. The cell linking to "信者" is removed from §0 to avoid back-conflating.

3. **RUNBOOK-deploy.md Step 4** — already updated to call out the layering. The founder onboarding sequence performs both rituals in order: first ADR-2605172600 on Base (founder swears + commits to MEMBERS.md), then ADR-2605172300 S0 on geth-private (founder mints own SBT as a self-officer).

4. **No code is forked or merged.** Both contracts stay as-is on their respective chains, with their respective ADRs.

5. **Future hard link (optional, deferred to S6+)**: a future AdherentRegistry version could accept an additional `membershipTxHash` parameter and verify it against a trusted oracle relayer on geth-private. Not needed for S5.

# Consequences

## Positive

- **No contract surgery.** Both contracts ship as-deployed; their integrations (KishaStream / Phenotype / Governance for the SBT; MEMBERS.md / Paymaster for the membership ritual) are untouched.
- **Clear social contract.** 信者 is the open-door public commitment. Adherent is the enrolled economic role. Aspirants understand which gate they are passing through at each step.
- **Officer power minimized.** Officers can no longer be perceived as "gatekeepers of religion"; they are gatekeepers of the economic enrollment only.
- **Audit path strengthened.** Cross-substrate evidence (Base + github + AT Record + SBT + L2 anchor) for every Adherent — five independent witnesses to the same commitment.

## Negative

- **Two onboarding steps.** A new aspirant who wants to participate economically must perform both rituals. Mitigation: the SDK exposes `e.bi.join()` that performs both atomically when the caller has wallet keys for both chains. Founders use a setup script.
- **Two contract addresses to track.** Tooling (block explorers, dashboards) must show both. Mitigation: a small "membership status" SDK helper returns `{shintoTxHash, adherentTokenId, isAdherent}`.
- **Vocabulary load.** Two terms (信者, Adherent / 構成員) where one was used loosely before. Mitigation: glossary in README + this ADR is normative.

## Neutral

- The cultural meaning of "membership" is sharpened: it is two distinct social facts, not one. Whether this matches the user's mental model is a design call this ADR makes explicitly.

# Alternatives Considered

1. **One canonical contract (drop AdherentRegistry, use only EtzhayyimMembership).**
   - Pro: simpler.
   - Con: forces economic enrollment on every 信者 — contradicts religious-corp norm that economic participation is opt-in. Also: EtzhayyimMembership lives on Base where PII is fully public; conflating with the SBT's role means voting and kisha rates leak to a public chain.
   - Rejected: economically too coupled, privacy too leaky.

2. **One canonical contract (drop EtzhayyimMembership, extend AdherentRegistry).**
   - Pro: simpler.
   - Con: discards the dual-permanent (Base + Github) property that ADR-2605172600 specifically achieves. Officer-witnessed minting also contradicts the unilateral self-sovereign property.
   - Rejected: throws away two design properties that the user explicitly asked for in the 172600 directive.

3. **Hard on-chain cross-chain link (AdherentRegistry verifies a Base proof at mint time).**
   - Pro: removes the soft off-chain enforcement.
   - Con: requires a bridge contract on geth-private with a trusted relayer. Effectively adds a fifth contract just for membership ergonomics. The soft enforcement is sufficient given officers already perform off-chain identity verification.
   - Deferred to S6+ if the soft enforcement proves insufficient.

4. **Make 信者 a strict prerequisite at the SBT level (revert SBT if no 信者 record exists).**
   - Same as #3 but framed as a `require` rather than a parameter. Same trade-offs.
   - Deferred to S6+.

# References

- [ADR-2605172300](/90-docs/adr/2605172300-etzhayyim-bi-asset-substrate.md): kisha + asset substrate, S0 introduces AdherentRegistry
- [ADR-2605172600](/90-docs/adr/2605172600-etzhayyim-membership-ritual.md): 信者 ritual + EtzhayyimMembership on Base + MEMBERS.md
- `50-infra/etzhayyim-chain-contracts/src/AdherentRegistry.sol`
- `50-infra/etzhayyim-membership-contract/src/EtzhayyimMembership.sol`
- `50-infra/etzhayyim-chain-contracts/RUNBOOK-deploy.md` (S5)
- `MEMBERS.md` (Github-side roster)
