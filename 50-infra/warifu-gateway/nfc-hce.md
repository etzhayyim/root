# Mobile NFC — HCE + self Token Service Provider (Surface C)

Mobile contactless for warifu (ADR-2605302000). The app emulates a contactless EMV card via
**Host Card Emulation (HCE)**; tokens are issued by our **own Token Service Provider (TSP)**
replacing Visa Token Service / Mastercard MDES. **Raw PAN is never stored** — network tokens map
to on-chain card references (`WarifuCard`).

## Provisioning

```
com.etzhayyim.card.issue ──► WarifuCard.sol (ERC-5192 soulbound) bound to ERC-4337 smart account
                          └► self-TSP issues network token (cardToken) → device keystore (HCE)
```

## Tap → authorize

```
NFC tap (ISO 14443 + EMV contactless kernel)
   │  cryptogram + token
   ▼
hce-tsp detokenize → com.etzhayyim.card.authorize (surface=nfc)
   │  CVM = WebAuthn passkey (device biometric) — 3DS-equivalent, no platform key
   ▼
{approve|decline|gated}
```

## Properties

- Tokens are scoped + rotatable; compromise of a device token does not expose the smart account
  (signing remains passkey/smart-account, ADR-2605231525).
- Surface C is end-to-end self-controlled (both card emulation and acceptance app are ours), so it
  ships in R1 ahead of the BIN-dependent terminal surface.
- fee 0; credit via 0% CreditLine.
