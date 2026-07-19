# `com.etzhayyim.wellBecoming.*` — Well-Becoming Kyu / Dan progression spec

Open spec for the Well-Becoming kyū / dan skill progression system. Tracks
user-self-asserted skill claims across domains (martial arts, music, craft,
profession, religious practice, etc.) with optional peer attestation.

## Status

Tranche F scaffolding (Phase 2) per ADR-2605172400.

Custody axis is clean because claims are **user-self-asserted** and live on
the user's own PDS (AT MST). Peer attestation is opt-in and also lives on
each peer's PDS. The religious-corp does not custody any claim.

Liability axis is clean because well-becoming progression has no fiduciary
or contractual counterparty — it's a self-improvement protocol, not a
credentialing authority.

## NSIDs (planned)

- `com.etzhayyim.wellBecoming.skillClaim` (record) — user-asserted skill at a given rank
- `com.etzhayyim.wellBecoming.attestation` (record) — peer attestation of someone else's claim
- `com.etzhayyim.wellBecoming.getRank` — compute current effective rank from claims + attestations
- `com.etzhayyim.wellBecoming.listClaims` — list a user's claims (paginated)

## Vendor SPLIT note

Monetized reputation API (e.g. credit-decision reputation score) stays in
vendor scope. The well-becoming spec here is the open primitive; commercial
reputation lookups built on top of it remain vendor.

## See also

- `00-contracts/specs/open-wellbecoming.edn` (canonical contract specification)
- ADR-2605172400 (vendor: 3-axis split rule + Tranche F)
- [vendor: `projects/etzhayyim-project-{society6,trust}/CLAUDE.md`](https://github.com/etzhayyim/etzhayyim-root/tree/main/60-apps) (monetized reputation, stays vendor)
