# com.etzhayyim.give.* — Lexicons

Giving / donation-side records for the religious-corp. All flows are **non-profit,
donation-only** (ADR-2605192115 + ADR-2605192100 §2). On-chain settlement is
`TitheRouter.donate()` on Base L2 (90% recipient / 10% Public Fund auto-split,
ADR-2605192130); these Lexicons are the AT Protocol counterparts.

| Lexicon | Purpose |
|---|---|
| `usdc.donation` | A USDC donation (donor DID, amount micros, purpose, tx hash) |
| `land.donation` | In-kind land donation → LandRegistry NFT (inalienable, ADR-2605192245) |
| `land.stewardSuccession` | Rotate stewardship voice on donated land (NFT never transferred) |
| `stock.donation` | Donated publicly-traded securities (DTC/brokerage transfer) — never held as an equity position, liquidated promptly, proceeds cross-link to a `usdc.donation` record |
| `vendorMissionDonationAttestation` | Vendor (etzhayyim.com) mission-surplus donation → Public Fund (ADR-2605301036) |
| `vendorSurplusPolicy` | Council-attested vendor payout-ratio + reserve policy (ADR-2605301036 §6) |
| `computeDonationAttestation` | **In-kind COMPUTE donation** — compute/storage given to the Murakumo mesh + kotoba substrate by a donated node (ameno browser inference / e7m CLI / kotoba pod). Non-titheable, uncompensated, imputed-value (ADR-2606012100) |
| `displacementTenureAttestation` | **Displacement Dividend registration** — a human displaced from an ISCO occupation by an etzhayyim OSS-robotics actor is registered for the tenure-weighted dividend, delivered as in-kind Basic High Income (`cashStipendUsdMicros` is a structural const-0 field = on-chain proof N1 cash≡0; aggregate-per-cohort only, 要配慮 PII via encrypted-envelope ref) (ADR-2606032130) |

## Mission-Funding Earned-Revenue arm (ADR-2605301036)

`vendorMissionDonationAttestation` + `vendorSurplusPolicy` implement the
**earned-income-as-non-profit-MEANS** model: a separate commercial vendor entity
earns revenue and **donates its surplus** to the religious-corp arm's-length. Two
structural invariants are enforced (and locked by
`70-tools/scripts/audit/test_basic_high_income_invariants.py`):

- **purpose ∈ {donation, grant} only** — no external-commercial purpose ever
  reaches the religious-corp substrate (ADR-2605192115 §4; commercial paid tiers
  stay on the vendor's own rails).
- **never adherent cash** — the surplus funds the *services* (Basic High Income
  in-kind, ADR-2605301020); `cashStipendUsdMicros ≡ 0` stays invariant
  (ADR-2605261000 §5 N1).

Aggregate-only, no customer PII (toritate G10). Donated surplus routes via
TitheRouter and is accounted by toritate (ADR-2605262900).

## In-kind compute donation (ADR-2606012100)

`computeDonationAttestation` recognizes **donating compute** as a donation. A
supporter joins the Murakumo mesh (ADR-2605215000) and/or the kotoba substrate
(ADR-2605262130) as a *donated first-party node* in one of three forms:

- **ameno** — browser WebGPU/WebNN inference on frozen baien edge models (zero install, WASM-32, baien edge-target ADR-2605241900).
- **e7m** — `e7m node join` registers a laptop/workstation as an Ollama/WASM node.
- **kotoba** — a kotoba pod contributes IPFS block storage + Datom replication.

It is the **mirror image of Basic High Income** (ADR-2605301020): there the
religious-corp values in-kind *provision to* adherents at market-equivalent while
no cash crosses; here a donor's in-kind *contribution* is imputed-valued for
transparency while no cash crosses. Locked invariants on the record (`const`
fields): `titheable=false` (no USDC to split — kisha precedent, ADR-2605192130 §5),
`compensatedUsdMicros=0` (uncompensated gift — paying would be commercial GPU
rental, Charter Rider §2(i)), `grantsBenefit=false` (never a path to benefits —
anti-class G4), `bestEffort=true` (donated capacity is never an SLA). Public
declaration lives on `https://etzhayyim.com/donate` + `/.well-known/donation.json`.

## Donated securities (stock/equity) — mandatory prompt liquidation

`stock.donation` records the standard non-profit appreciated-securities gift: a donor
transfers publicly-traded shares via DTC/brokerage to etzhayyim's receiving account. Per
Charter Rider §2(b) (no speculative finance) — the same doctrine already enforced on
wakai's mutual-aid pool and toritate's ledger — donated securities are **never** retained
as an equity position: `heldAsEquityPosition` is a structural `const false`. The
receiving brokerage liquidates promptly; the USDC-equivalent proceeds enter the ordinary
`usdc.donation` / TitheRouter flow (cross-linked via `liquidationDonationRef`), and
toritate accounts the proceeds as a `ledgerEntry` (`securities-donation-liquidation-proceeds`
category, ADR-2605262900). The donation record itself is durable content-addressed
attestation of the original gift — for donor fair-market-value substantiation — not an
on-chain-custodied or transferable asset. No new token is minted; unlike land (a
constitutionally inalienable commons asset, hence a soulbound NFT), a donated security is
mission-fungible working capital, so it converts to the same USDC rail every other
donation uses rather than acquiring a bespoke on-chain representation.

## Privacy / constitutional invariants

- No donor PII beyond the donor/vendor DID; vendor records are period-aggregate.
- `additionalProperties: false` on every record (structural no-extra-fields).
- Integer-with-implied-units (USD micros / bps), no float types — ADR-2605190900.

## Related ADRs

- ADR-2605192115 — non-profit / donation-only / no-ads (+ §4 backend limit)
- ADR-2605192130 — TitheRouter 10% auto-split
- ADR-2605192145 — Public Fund (recipient)
- ADR-2605192245 — Land Trust inalienability
- ADR-2605301036 — Mission-Funding Earned-Revenue Arm
- ADR-2605301020 — Basic High Income (what the surplus ultimately funds)
- ADR-2605262900 — toritate (accounts the donation inflow)
- ADR-2606062100 — **moyai** 舫い (the reciprocity-reward carve-out to `computeDonationAttestation` G4)

## Inference reciprocity reward (moyai 舫い, ADR-2606062100)

`computeDonationAttestation` records a *gift* of compute that earns the donor **nothing**
(G4). Its charter-clean **carve-out** — keeping a *reward* for inference participation
without breaching any invariant — is **moyai** (`com.etzhayyim.moyai.*`, sibling lexicon
dir). Verified contribution mints a **non-monetary, non-transferable, decaying reciprocity
credit** spendable only to draw *discretionary surplus* inference from the same commons
(情報を得るには情報を生成する; the 入会権 / commons-use-right model). It does **not** touch
Basic High Income: an unconditional subsistence inference floor (information-as-BHI) is
always served by need, never by contribution. See `../moyai/README.md` +
`50-infra/etzhayyim-moyai-credit/`.
