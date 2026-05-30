# warifu-gateway — drop-in compatibility surfaces

Translation layer that maps the existing card ecosystem onto `app.etzhayyim.card.*` lexicons →
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
