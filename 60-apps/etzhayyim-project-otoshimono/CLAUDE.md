# otoshimono.etzhayyim.com

落とし物 (lost-and-found) ZK two-choice proof — Blake3 commitment with Murakumo decoy.

A claimant proves they can identify a found item from a two-choice challenge
(real attribute vs Murakumo-generated decoy) without the finder learning the
claimant's private description. Ownership is established via a Blake3 commitment
opened only on a correct two-choice selection.

## Status

Migrated from gftd vendor 2026-06-03 (candidate for etzhayyim front per 3-axis
OR-test — pending review). Identity-only port — the vendor side held no
implementation beyond a deploy stub. Build proceeds here.

## Primitives

- **Commitment**: Blake3(item_secret ‖ salt) published by the finder.
- **Two-choice challenge**: real attribute vs Murakumo-generated decoy; claimant
  selects; correct selection opens the commitment.
- **Zero-knowledge**: finder learns only pass/fail, not the claimant's description.
