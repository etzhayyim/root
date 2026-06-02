# app.etzhayyim.give.* — Lexicons

Giving / donation-side records for the religious-corp. All flows are **non-profit,
donation-only** (ADR-2605192115 + ADR-2605192100 §2). On-chain settlement is
`TitheRouter.donate()` on Base L2 (90% recipient / 10% Public Fund auto-split,
ADR-2605192130); these Lexicons are the AT Protocol counterparts.

| Lexicon | Purpose |
|---|---|
| `usdc.donation` | A USDC donation (donor DID, amount micros, purpose, tx hash) |
| `land.donation` | In-kind land donation → LandRegistry NFT (inalienable, ADR-2605192245) |
| `land.stewardSuccession` | Rotate stewardship voice on donated land (NFT never transferred) |
| `vendorMissionDonationAttestation` | Vendor (etzhayyim.com) mission-surplus donation → Public Fund (ADR-2605301036) |
| `vendorSurplusPolicy` | Council-attested vendor payout-ratio + reserve policy (ADR-2605301036 §6) |

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
