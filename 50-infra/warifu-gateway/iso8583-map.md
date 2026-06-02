# ISO 8583 ↔ warifu on-chain mapping (Surface B)

Maps standard card-present authorization messages onto `com.etzhayyim.card.authorize` /
`.settle` so existing EMV/POS terminals interoperate without code changes (ADR-2605302000).

> **R0 scope**: message map only. Physical terminal acceptance needs a BIN range + acquirer/
> network membership or co-badge bridge (deferred R2+).

## Message flow

```
Terminal ──0100 (auth request)──►  iso8583-gateway ──► com.etzhayyim.card.authorize
Terminal ◄─0110 (auth response)──  iso8583-gateway ◄── {approve|decline|gated}
Terminal ──0200 (financial req)──►  iso8583-gateway ──► com.etzhayyim.card.settle
Terminal ◄─0210 (fin response)───  iso8583-gateway ◄── settled (T+0)
Terminal ──0400 (reversal)───────►  iso8583-gateway ──► com.etzhayyim.card.refund
```

## Field mapping (key DEs)

| ISO 8583 DE | Name | warifu field |
|---|---|---|
| DE 2 | PAN | network token → `cardToken` (no raw PAN; self TSP) |
| DE 3 | Processing code | `funding` (00=debit purchase, 30=balance inq) |
| DE 4 | Amount, transaction | `amountUsdc` (minor-unit normalize to 6dp USDC) |
| DE 11 | STAN | correlation id (→ `idempotencyKey`) |
| DE 39 | Response code | `decision` → `00` approve / `05` decline / `57` gated (purpose) |
| DE 41/42 | Terminal/Merchant id | `merchantDid` lookup |
| DE 55 | EMV/ICC data | EMV cryptogram → verified; passkey/attestation for CVM |

## Response codes

- `00` approve · `05` do-not-honor (insufficient funds/credit) · `57` transaction-not-permitted
  (purpose gated — Phase 2 not enabled) · `12` invalid transaction (unknown purpose).

**Invariants**: settlement carries fee 0; credit auth uses the 0% CreditLine.
