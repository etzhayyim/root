# 10-protocol/warifu — `com.etzhayyim.card.*` lexicons

Wire-level protocol surface for the `warifu` 割符 Open Zero-Fee Card (ADR-2605302000).

These lexicons are the substrate-native contract. The three drop-in compatibility surfaces
(Stripe-shaped REST, EMV/ISO 8583, mobile NFC) are translation layers that map onto these:

```
Stripe REST  ─┐
ISO 8583     ─┼─►  com.etzhayyim.card.{authorize,capture,settle,refund,dispute}  ─►  kotoba EAVT + ERC-4337
HCE/NFC      ─┘                                                                        (USDC, Base L2)
```

| Lexicon | NSID | Maps to compat |
|---|---|---|
| issue | `com.etzhayyim.card.issue` | (provisioning; HCE) |
| authorize | `com.etzhayyim.card.authorize` | REST `payment_intents` / ISO 8583 `0100→0110` / NFC tap |
| capture | `com.etzhayyim.card.capture` | REST capture |
| settle | `com.etzhayyim.card.settle` | on-chain settlement (T+0) |
| refund | `com.etzhayyim.card.refund` | REST `refunds` / ISO 8583 `0400` |
| dispute | `com.etzhayyim.card.dispute` | chargeback → chigiri |

**Invariants**: `fee = 0` everywhere; credit interest = 0; Phase-1 purpose allow-list
(external `purchase`/`subscription` gated on Council Lv7+ per ADR-2605192115). See
`90-docs/adr/2605302000-warifu-open-zero-fee-card.md`.
