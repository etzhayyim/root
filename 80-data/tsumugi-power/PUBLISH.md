# tsumugi 紡ぎ — published power-graph (80-data/tsumugi-power)

> etzhayyim power-dynamics knowledge graph (tsumugi 紡ぎ)  ·  ADR-2606092000  ·  published 2026-06-11  ·  publisher `did:web:etzhayyim.com:actor:tsumugi`

Self-sovereign linked-data power-graph, content-addressed to kotoba IPFS (CIDv1, raw,
sha2-256). The CID is byte-identical to `ipfs add --cid-version=1 --raw-leaves` and
verifiable with `orgs/etzhayyim/com-etzhayyim-rasen/methods/cid.py` — no daemon required. The data lives
on IPFS (host-independent); `https://etzhayyim.com/dataset/tsumugi-power.json` only
advertises the CIDs + gateway links, and `/ns/power` resolves the vocabulary.

License: Apache-2.0 + etzhayyim Charter Compliance Rider v3.1 (/CHARTER-RIDER.md)

## Artifacts (gzip, mtime=0 → deterministic CID)

| artifact | file | bytes | CID |
|---|---|---:|---|
| graph | `power-graph.kotoba.edn.gz` | 35644 | `bafkreier4zyuw6dfma3t2kmawbzfupfdusdzabt44raki2m5dv7cuvfb4m` |
| ntriples | `power-graph.nt.gz` | 38869 | `bafkreicgiay7tdgcnekjs5cfvu7zznl2hjvuheja4fgfqqyio6t3zg4ipy` |
| jsonld | `power-graph.jsonld.gz` | 20557 | `bafkreiejgkjmemrdukcmjrwokvqkjc4qzarse74sn5g6l7csqjqjkkhppe` |

counts: 619 nodes · 631 edges · 5100 triples · N-Triples sha256 `sha256:4aff1113c1b98877df85207c9e18ce7791806b3f9d542812b14705b4d812b76e`

## Pin + fetch + verify (trustless, no daemon trust)

```bash
# operator pins (the CID will match the manifest):
ipfs add --cid-version=1 --raw-leaves 80-data/tsumugi-power/power-graph.kotoba.edn.gz
# anyone fetches from a public gateway and re-content-addresses:
curl -sSL https://ipfs.io/ipfs/bafkreier4zyuw6dfma3t2kmawbzfupfdusdzabt44raki2m5dv7cuvfb4m -o g.edn.gz
python3 orgs/etzhayyim/com-etzhayyim-rasen/methods/cid.py g.edn.gz   # must equal the CID above
gunzip -c g.edn.gz | head
```

