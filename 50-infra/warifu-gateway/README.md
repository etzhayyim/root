# warifu-gateway — drop-in compatibility surfaces

Translation layer that maps the existing card ecosystem onto `com.etzhayyim.card.*` lexicons →
kotoba EAVT + ERC-4337 USDC settlement (ADR-2605302000). "全く同じ api 規格" across three surfaces:

| Surface | File | Drop-in target |
|---|---|---|
| A. Online REST | `stripe-compat.openapi.yaml` | merchant points SDK `baseURL` here; `payment_intents`/`charges`/`refunds`/`customers`/`payment_methods` + idempotency + webhooks, request/response-compatible |
| B. Card-present | `iso8583-map.md` | existing EMV/POS terminals send `0100`; we translate `0100→on-chain auth→0110` |
| C. Mobile NFC | `nfc-hce.md` | Host Card Emulation + self Token Service Provider (replaces VTS/MDES); network-tokenized, no raw PAN |

## Hard rules

- **No third-party processor**: we do NOT import or route through Stripe/Visa/MC. These are
  *interoperable open re-implementations* of public interface shapes, not clones of proprietary
  schemas or marks.
- **fee = 0** on every response; **credit interest = 0**.
- **Purpose allow-list**: Phase 1 SBT↔SBT carve-out only. External `purchase`/`subscription`
  return a gated error until the Council Lv7+ amendment (ADR-2605192115).
- **No platform-held key** (ADR-2605231525): cardholder auth = WebAuthn passkey (3DS-equiv);
  signing is smart-account only.

## Reality note (Surface B)

R0 publishes the ISO 8583 message map only. Physical terminal acceptance needs a BIN range +
acquirer/network membership or a co-badge bridge — deferred to R2+. Surfaces A and C are
end-to-end self-controlled and ship first.

## Implementation (R0 stub)

```
50-infra/warifu-gateway/
├── package.json / tsconfig.json
└── src/
    ├── common/
    │   ├── purpose.js        # payment-purpose allow-list — SHARED SoT (runnable ESM)
    │   ├── idempotency.js    # anti-double-charge (withIdempotency + store); kotoba-backed in R1
    │   ├── iso8583-codec.js  # DE4 amount scaling + decision->DE39 (pure SoT for Surface B)
    │   ├── webhook.js        # merchant webhook HMAC sign/verify (replay-protected; per-merchant secret)
    │   ├── purpose.test.mjs  # node-only tests (npm test)
    │   ├── gateway.test.mjs  # idempotency + iso8583 codec tests (node-only)
    │   ├── settle-flow.js    # SHARED authorize->settle core (one SoT for all 3 surfaces)
    │   ├── memory-substrate.js  # gateway-layer WarifuSubstrate fake (e2e tests)
    │   ├── types.ts          # substrate-native card shapes (mirror com.etzhayyim.card.*)
    │   └── sdk.ts            # @etzhayyim/sdk facade (fail-closed stub; no key held)
    ├── stripe-compat/
    │   ├── handler.js               # Surface A: payment_intents/capture/refund (451 on gate)
    │   ├── stripe-compat.test.mjs   # e2e tests over memory-substrate (node-only)
    │   └── translate.ts             # typed wrapper delegating to handler.js
    ├── iso8583/
    │   ├── handler.js               # Surface B: 0100 -> auth/settle -> 0110 (DE39 00/05/57/12)
    │   ├── iso8583.test.mjs         # e2e tests
    │   └── translate.ts             # typed wrapper (mapping imported from handler.js)
    ├── nfc/
    │   ├── handler.js               # Surface C: HCE tap -> auth/settle (passkey CVM)
    │   ├── nfc.test.mjs             # e2e tests
    │   └── translate.ts             # typed wrapper (mapping imported from handler.js)
    ├── iso8583/translate.ts         # Surface B: 0100 DE-map <-> authorize; decision -> DE39
    └── nfc/translate.ts             # Surface C: HCE tap -> authorize (passkey CVM)
```

**Purpose allow-list is a 3-point invariant** — `src/common/purpose.js` MUST stay in lockstep with:
- Solidity `SettlementRouter._checkPurpose` (`50-infra/warifu-contracts/src/SettlementRouter.sol`)
- Python `AuthorizeCell._purpose_ok` (`orgs/etzhayyim/com-etzhayyim-warifu/cells/authorize.py`)

Run: `npm test` (purpose-gate, no deps) · `npm run typecheck` (tsc, needs `npm i`).
Fail-closed: every surface refuses a non-Phase-1 purpose *before* touching the substrate;
`phase2Enabled()` defaults to `false` until the on-chain SettlementRouter read is wired (R1).
