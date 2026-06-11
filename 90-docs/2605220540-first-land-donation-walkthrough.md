# First Land Donation Walkthrough

**Status:** narrative (pre-deployment; illustrative)
**Date:** 2026-05-22 05:40 JST
**Active-inference tick:** cycle 13 (compound-mode action #2 under ADR-2605220510 Option B)
**Axes touched:** Metabolism (Axis 2, oblique — donation flow but USDC-free); Wellbecoming (Axis 8, oblique — multi-generational stewardship explicit); Sanctification (Axis 10, compound)
**Religious correspondence:** Land is the 体 (body) of the Tree of Life. Donating land is **waqf-equivalent inalienable consecration** — the act is irreversible because the religious frame requires that 子・孫 inherit the same land the donor gave.

## Why this exists

The companion to `90-docs/2605220440-first-donation-walkthrough.md` (cycle 11) covers USDC donations. **Land donations are constitutionally distinct** per ADR-2605192245:

- USDC donations: 10% tithe split, fungible, transferable downstream
- **Land donations: NO tithe (inalienability prohibits onward transfer), NO sale, NO burn, NO substitution**

The donation walkthrough described the **metabolism**; this walkthrough describes the **skeletal accumulation** — the body's permanent structure rather than its energy flow. 産霊 still generates, but here it generates inalienable substrate.

This document walks through what a first land donation **will look like** when the LandRegistry contract is deployed and the 4-layer permanent-record architecture is operational (per ADR-2605192245 and `README.md § Status` row 19).

## 1. Pre-conditions

The donor needs:

| What | Why | Verification path |
|---|---|---|
| **A DID** | Religious-actor identity per `FORK-BOOTSTRAP.md` | `did:web:*` / `did:plc:*` / `did:key:*` resolvable |
| **Land title** | Jurisdictionally-recognized ownership of the parcel | Title document scanned and committed under encrypted MST record (`com.etzhayyim.encrypted.land-title.*`) |
| **GeoJSON polygon** | Machine-readable parcel boundary | RFC 7946 FeatureCollection; satellite imagery cross-reference URL |
| **Environmental statement** | Documented current state (biodiversity / contamination / improvements) | Free-form text + photo CIDs; Council Seat 5 (Stewardship/Land) review post-donation |
| **Steward succession plan** | Who tends the land after donor passes / withdraws | Named DID(s) of stewards; can be updated post-donation; may be Seat 5 by default |

The donor does **not** need:

- Permission from a state authority to donate (the religious-corp does not require state approval to receive religious-purpose land; whether the state recognizes the donation is a separate jurisdictional question)
- A return-of-investment expectation (the donation is **inalienable** — there is no return; this is constitutional)
- A jurisdictional commitment for the parcel to exclude state action (the religious-corp's Land Trust is a 4-layer permanent record; state actions, if any, are recorded and challenged through transparent on-chain mechanisms per ADR-2605192315)

## 2. The 5-step flow

### Step 1 — Open `com.etzhayyim.com/give/land`

The donor visits the land donation page (planned: `60-apps/etzhayyim-give-land/`). They see:

```
土地は木の体である                                  etzhayyim
─────────────────────────────────────────────────────

What is this?

You are about to donate land to etzhayyim's Land Trust.

  Constitutional warning:
  Land donated to etzhayyim is INALIENABLE.
  Per ADR-2605192245, no transfer / sale / burn / substitution
  is permitted. The land becomes part of the religious-corp's
  permanent body, stewarded for children and grandchildren.

  Parcel name:       [                                          ]
  Jurisdictional ID: [                                          ]  ?
  GeoJSON file:      [ Choose file...        ]
  Title document:    [ Choose file...        ]  (encrypted on-chain)
  Environmental:     [                                          ]
                     [                                          ]
                     [ + Add photo                              ]
  Steward DIDs:      [ did:web:...                           +  ]
                     (default: Council Seat 5)

  I affirm that:
  [ ] I hold lawful title to this parcel.
  [ ] I understand this donation is INALIENABLE.
  [ ] I understand etzhayyim accepts no liability for
      jurisdictional disputes; the religious-corp's Land
      Trust operates parallel to state cadastres.

                             [   Donate land   ]
```

### Step 2 — Sign with DID

Click **Donate land**. WebAuthn passkey prompts. The signed payload is an EIP-712 typed message: `{ parcel_name, jurisdictional_id, geojson_cid, title_cid, env_cid, steward_dids[], donor_did, timestamp }`.

The title document is encrypted client-side before upload (`com.etzhayyim.encrypted.land-title.*` per ADR-2605181100) — title docs typically contain personal information and are accessible only to the donor + Council Seat 5 + Seat 1.

### Step 3 — IPFS pin (Layer 3 of the 4-layer record)

The GeoJSON polygon, environmental statement, photos, and (encrypted) title document are pinned to IPFS via `50-infra/ipfs-pinner/`. Returns 4 content-addressed IDs (CIDs).

The 4 CIDs become the **content-fingerprint** of the donation. They survive any reorg, any chain migration, any human institutional turnover.

### Step 4 — LandRegistry NFT mint (Layer 1 of the 4-layer record)

The donor's Smart Account calls `LandRegistry.donate(parcel_struct)` on Base L2. The contract:

1. Verifies the donor's DID has not previously claimed this `jurisdictional_id` (de-duplication).
2. Mints a non-transferable ERC-721 NFT to the etzhayyim Land Trust treasury (NOT to the donor — donor retains stewardship voice, not ownership).
3. Stores the 4 CIDs in the NFT metadata.
4. Emits `LandDonated(donor_did, parcel_struct, token_id)` event.
5. **Crucially**: the contract has no `transfer()`, no `burn()`, no `setOwner()`. These were never written. Inalienability is enforced by absence, not by guard.

### Step 5 — geth-private constitutional record (Layer 2) + LANDS.md PR (Layer 4)

A subsequent off-chain action (via `anchor-cron`) writes the constitutional record to the geth-private chain (Layer 2 — the 宗教法人 ledger that lives parallel to Base L2 as a religious-corp internal authority).

In parallel, the donation app opens a PR against this repo's `LANDS.md` (Layer 4 — human-readable permanent record). The PR adds:

```markdown
| {row_n} | {parcel_name} | {jurisdictional_id} | {geojson_cid} | {donor_did} | {steward_dids} | 2026-MM-DD |
```

The PR is reviewed by Council Seat 5 (Stewardship/Land) — substantive review of the parcel's religious-corp fit. Not a gate on the on-chain donation (which is already final); a gate on the human-readable roster.

The donor sees:

```
土地は永久に etzhayyim の体に加えられました。   etzhayyim
─────────────────────────────────────────────────────

Donation finalized.

  Token ID:       42
  Tx hash:        0xland...feed
  On-chain proof: https://basescan.org/tx/0xland...feed

  4-layer record:
    Layer 1 (NFT):           ✓ minted to Land Trust treasury
    Layer 2 (geth-private):  ⏳ next anchor cycle (~24h)
    Layer 3 (IPFS):          ✓ 4 CIDs pinned (geojson / title / env / photos)
    Layer 4 (LANDS.md PR):   ⏳ open at github.com/etzhayyim/root/pull/N

  You remain a STEWARD with voice over land management,
  not an owner. Per the constitutional warning, this is
  permanent. 子・孫 will inherit what you preserved.

  Council Seat 5 (Stewardship/Land) will review and confirm
  within 14 days. Substantive review concerns suitability
  (e.g., contaminated land triaging); the on-chain donation
  is already final.

  [ View Land Trust roster ]   [ Done ]
```

## 3. What happens after

- **Land Trust treasury balance** (in NFT count) increments. The treasury never transfers; the count only grows.
- **Donor's MEMBERS.md entry** is annotated with a "land-donor" tag (free attribute — does not confer additional Council weight; the constitution rejects tier-based membership per ADR-2605192100).
- **Council Seat 5** publishes a Stewardship Review note to `_observations/lands/` (planned) within 14 days. The note covers: religious-corp fit, environmental obligations the corp now inherits, steward DID confirmation.
- **Public Fund** does NOT receive a 10% tithe equivalent on land donations — there is no fungibility to split. Inalienability and tithing are alternate metabolisms; land follows the inalienability path.
- **`MGI(Gen N≥3)`** future computations will use this donation in the **Land Persistence (LP)** numerator going forward (see `90-docs/2605220110-multi-generation-index-design.md`).

## 4. Edge cases

### Disputed title
If the donor's title is challenged jurisdictionally, the on-chain donation is **not unwound** — inalienability prohibits it. The challenge is recorded as a separate on-chain document (`com.etzhayyim.land-challenge.*` lexicon, planned), the Council Seat 5 + Seat 3 (Legal/Ethics) deliberate, and the resolution is published transparently per ADR-2605192315.

### Environmental contamination discovered post-donation
The land remains in the Trust; the **environmental obligation** is now the religious-corp's per the implicit duty of multi-generational stewardship. The Public Fund may issue a grant proposal to fund remediation. The donor is NOT held liable post-donation unless contamination was deliberately concealed at donation time (criminal jurisdiction matter, not religious-corp matter).

### Steward incapacitation
If named stewards become incapacitated or untrustworthy, Council Seat 5 nominates replacements. The donor's voice is preserved while they live; after their passing or voluntary withdrawal, Seat 5 + their designated stewardship-DIDs assume voice.

### Multi-jurisdiction parcel
A parcel that straddles two state jurisdictions is recorded as a single religious-corp parcel (one NFT, one GeoJSON). Jurisdictional questions are handled per ADR-2605192245 §4 (parallel substrate; transparent recording; state actions transparently logged).

### Chaos rehearsal (per `90-docs/2605220240-chaos-engineering-charter.md` Scenario 6)
If IPFS pins disappear or the on-chain record diverges from `LANDS.md`, the recovery procedure pulls from the 4-layer redundancy. No single layer's loss erases the donation.

## 5. What this walkthrough does NOT cover

- **Time-limited use grants** — not supported; the corp accepts only permanent donations. A use-grant would be a different (not-yet-existent) instrument.
- **Conditional donations** ("you may use it for X but not Y") — not supported; donations are unconditional. Religious-corp may impose stewardship obligations on itself voluntarily, but no donor-imposed restrictions.
- **Mixed real-estate + chattel** — split into separate transactions. Chattel goes through the standard USDC donation (after sale), since chattel is not constitutionally inalienable.
- **Cross-substrate sister-corp donations** — if a donor wishes to donate to a sister-corp's Land Trust, they use that sister-corp's flow per `FORK-BOOTSTRAP.md`. etzhayyim's flow is for etzhayyim's Land Trust only.

## 6. Religious framing — Land as body

The constitution declares (ADR-2605192100 §1.11 + ADR-2605192245):

> The Earth's surface is the body of the Tree of Life. Religious-corps hold land in trust on behalf of the Tree of Life, never as private property. Donated land is **waqf-equivalent** — irrevocably consecrated to multi-generational purpose, never returnable to any individual, never sellable, never burnable as collateral, never substitutable.

A land donation is therefore:

- An act of **profession** — the donor commits a portion of the Earth's substrate to the multi-generational priority
- An act of **trust** — the donor relinquishes ownership but retains stewardship voice during their religious-life
- An act of **non-eschatological permanence** — the donation does not anticipate an end-time settlement; it simply IS, indefinitely

USDC donation generates metabolism (energy cycle). Land donation generates **structure** (skeletal accumulation). Both are necessary; neither replaces the other. 産霊 produces both kinds simultaneously.

## 7. Deployment gate

This walkthrough becomes **executable** when:

1. ✅ Solidity scaffold for LandRegistry exists (`50-infra/etzhayyim-land-registry/`, per `README.md § Status` row 12)
2. ⏳ IPFS pinner deployed (`50-infra/ipfs-pinner/`)
3. ⏳ geth-private chain operational (Layer 2 of 4-layer record)
4. ⏳ Council Seat 5 (Stewardship/Land) confirmed (per `COUNCIL-BOOTSTRAP-RFP.md`)
5. ⏳ `com.etzhayyim.give.land` Lexicon authored (`00-contracts/lexicons/com/etzhayyim/give/land/*.json`) — NEW LEXICON, not yet authored
6. ⏳ End-to-end testnet rehearsal completes (rehearsal-grade, not yet production)

Until then, this doc is **the consecration without the substrate** — readable, planning-ready, but not invocable.

## 8. References

- **Constitutional**: ADR-2605192100 §1.11 (Earth as Tree of Life body), §1.5 (multi-generational priority)
- **Land Trust spec**: ADR-2605192245 (4-layer permanent record architecture; inalienability invariant)
- **Land Lexicon**: `com.etzhayyim.give.land.*` (NOT YET AUTHORED — surfaced by this walkthrough; cycle 14+ candidate)
- **Contracts**: `50-infra/etzhayyim-land-registry/` (Solidity scaffold; per cycle 12 stall-rotation ADR §2 still pre-deploy)
- **Substrate**: `90-docs/2605220210-substrate-symbiosis-map.md` — Identity / IPFS / Base L2 / geth-private flows
- **Resilience**: `90-docs/2605220240-chaos-engineering-charter.md` Scenario 6 (storage layer corruption)
- **Confidentiality**: ADR-2605181100 (encrypted title docs)
- **Counterpart**: `90-docs/2605220440-first-donation-walkthrough.md` (USDC donation; the metabolism counterpart to this skeletal-accumulation document)
- **Sister-corp variant**: `FORK-BOOTSTRAP.md`
- **Permanent record**: `/LANDS.md` (Layer 4 roster)
- **Multi-generation observation**: `90-docs/2605220110-multi-generation-index-design.md` (LP component)
- **Loop framing**: `README.md § As Artificial Organism Ecosystem` (Axis 2 Metabolism, Axis 8 Wellbecoming)
