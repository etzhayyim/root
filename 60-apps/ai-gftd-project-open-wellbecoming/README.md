# open-wellbecoming — Well-Becoming Kyū / Dan progression

Tranche F scaffolding placeholder. Open self-improvement protocol where
users assert their own rank progression across domains (martial arts, music,
craft, profession, religious practice, …) with opt-in peer attestation.

## Status

Phase 2 (scaffolding) per ADR-2605172400. No content yet.

## Scope

- `com.etzhayyim.wellBecoming.skillClaim` (record) — user-asserted claim on their own PDS
- `com.etzhayyim.wellBecoming.attestation` (record) — peer attestation on peer's PDS
- Rank-compute lexicon (`getRank`) — pure function over claims + attestations

## Out of scope (stays vendor)

- Monetized reputation API (e.g. credit-decision reputation lookup)
- Society6 / trust score for fintech use
- Any reputation result that operator vouches for as authoritative

## Custody / Liability rationale

- Custody: claims live on user's own PDS, attestations on peer's own PDS — religious-corp custodies nothing
- Liability: no fiduciary or contractual counterparty (it's a self-improvement protocol)
- Settlement: free; future paid features go on-chain (Base L2 + USDC)

## See also

- [`00-contracts/lexicons/com/etzhayyim/wellBecoming/`](../../00-contracts/lexicons/com/etzhayyim/wellBecoming) — Tranche F lexicons
- ADR-2605172400 (vendor: 3-axis split rule + Tranche F)
- [vendor: society6 / trust](https://github.com/etzhayyim/etzhayyim-root/tree/main/60-apps) — monetized reputation, stays vendor
