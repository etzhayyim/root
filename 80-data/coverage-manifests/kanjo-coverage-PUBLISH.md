# kanjo — live-ingest publish

Council-authorised G7 live ingest (2026-06-16). Persisted on DataLad + IPFS + kotobase.net.

## Artifacts (content-addressed, CIDv1/raw/sha2-256)

| file | CID | bytes | verified |
|---|---|---:|:--:|
| facts.merged.kotoba.edn | `bafybeiae7xbotq4m2m55mycpsh3qrn4g67xz52dporyf4sfxoj6hcj7quq` | 4376382 | ✓ |

- **primary CID**: `bafybeiae7xbotq4m2m55mycpsh3qrn4g67xz52dporyf4sfxoj6hcj7quq`
- **DataLad**: dataset `80-data/kanjo-coverage` commit `0c47519c478e498110fb0dd07b955c91f8ad3fef` (saved=True)
- **IPNS**: k51qzi5uqu5dhf94ts55lpo24kieru77wqwbwg2agwwzbqu2ug36cw9jpjktoc
- **kotobase.net**: operator-follow-up — no KOTOBA_PIN_TOKEN; /pins is 401 unauthed + pod isolated (ADR-2606111330). CID is locally pinned + DataLad-saved; register on kotobase.net when a CACAO/JWT token is provided.

## Fetch + verify (works for single- and multi-block)
```bash
ipfs cat bafybeiae7xbotq4m2m55mycpsh3qrn4g67xz52dporyf4sfxoj6hcj7quq > got.edn
ipfs add -Q --cid-version=1 --raw-leaves --only-hash got.edn
# → must print bafybeiae7xbotq4m2m55mycpsh3qrn4g67xz52dporyf4sfxoj6hcj7quq
```
