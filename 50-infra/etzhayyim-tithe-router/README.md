# etzhayyim-tithe-router

`TitheRouter.sol` — donation / kisha / grant 受領時に **10% を Public Fund Safe へ atomic split**。

**Per [ADR-2605192130](../../90-docs/adr/2605192130-etzhayyim-tithe-redistribution.md)** (10% Tithe Redistribution).

## Constitutional constant

`economic.tithe_to_public_fund_bps = 1000` (= 10.00%, ADR-2605192100 §2 改定不可)

## Flow

```
[donor]
  → e.pay({ to: recipient, amount: 100 USDC, purpose: "donation" })
  → SDK: usdc.approve(TitheRouter, 100 USDC)
  → SDK: TitheRouter.route(recipient, 100 USDC, keccak256("donation"))
        ├─ usdc.transferFrom(donor, publicFund, 10 USDC)
        └─ usdc.transferFrom(donor, recipient, 90 USDC)
  → SDK: MST: emit ai.gftd.apps.payment.sent + ai.gftd.apps.payment.tithe records
```

## Exceptions (NOT titheable)

- `purpose = "kisha"` — Treasury → adherent BI flow (ADR-2605172300)
- `purpose = "tithe"` — tithe 自体 (二重課税防止)
- `purpose = "escrow-refund"` — refund preserves original purpose
- `purpose = "grant"` — already Public Fund 由来 (ADR-2605192145)
- `purpose = "internal-purchase"` / `"internal-subscription"` / `"internal-promo"` — internal carve-out (ADR-2605192115 §3)

Only `purpose = "donation"` triggers tithe routing (initial scope; future ADRs may expand).

## Charter Compliance gate (per ADR-2605192230)

`route()` requires:
- `!charters.isNonAlignedAddress(recipient)`
- `!charters.isNonAlignedAddress(msg.sender)`  // payer

A Non-Aligned address cannot pay through nor receive through TitheRouter.

## Foundry layout

```
src/
├── TitheRouter.sol
└── interfaces/
    ├── IConstitution.sol  (re-exports from 50-infra/etzhayyim-chain-contracts/)
    └── IChartersComplianceRegistry.sol
test/
└── TitheRouter.t.sol
script/
└── Deploy.s.sol
```

## Deploy targets

- Base L2 (mainnet `8453` + sepolia `84532`)

## SDK integration

`20-actors/etzhayyim-sdk/src/pay.ts` is rewired in [ADR-2605192130](../../90-docs/adr/2605192130-etzhayyim-tithe-redistribution.md) §3:

```ts
async pay(args: PayArgs): Promise<PayReceipt> {
  if (isTitheablePurpose(args.reason.purpose)) {
    await this.usdc.approve(TITHE_ROUTER_ADDRESS, args.amount);
    const tx = await this.titheRouter.route(recipient, args.amount, keccak256(purposeStr));
    // ... emit MST records
  }
}
```

## Pregel cell

`20-actors/magatama/cells/tithe_routing/` — MST listener on `ai.gftd.apps.payment.sent` records, pre-flight validation (charter compliance + amount + purpose enum).
