# uchiwake — live-ingest publish

Council-authorised G7 live ingest (2026-06-16). Persisted on DataLad + IPFS + kotobase.net.

## Artifacts (content-addressed, CIDv1/raw/sha2-256)

| file | CID | bytes | verified |
|---|---|---:|:--:|
| products.merged.kotoba.edn | `bafkreib7yagcmrxzley2eyho5b2miuncm2n6rjj3tmyvlnxvkpls5ptcfq` | 96563 | ✓ |

- **primary CID**: `bafkreib7yagcmrxzley2eyho5b2miuncm2n6rjj3tmyvlnxvkpls5ptcfq`
- **DataLad**: dataset `80-data/uchiwake-coverage` commit `e4af197101f2ee017c589e2710a927dd5aeee848` (saved=True)
- **IPNS**: k51qzi5uqu5dl5fz0a2jne4vyxfluz01ftn5t1bunolwyxhvuz6y0tgx57z968
- **kotobase.net**: operator-follow-up — no KOTOBA_PIN_TOKEN; /pins is 401 unauthed + pod isolated (ADR-2606111330). CID is locally pinned + DataLad-saved; register on kotobase.net when a CACAO/JWT token is provided.

## Fetch + verify (works for single- and multi-block)
```bash
ipfs cat bafkreib7yagcmrxzley2eyho5b2miuncm2n6rjj3tmyvlnxvkpls5ptcfq > got.edn
ipfs add -Q --cid-version=1 --raw-leaves --only-hash got.edn
# → must print bafkreib7yagcmrxzley2eyho5b2miuncm2n6rjj3tmyvlnxvkpls5ptcfq
```
