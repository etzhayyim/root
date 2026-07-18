# coverage-publish — Council-authorised live-ingest + durable persistence

Council attestation (founder Lv7+ 1/1, 2026-06-16): the **G7 live-ingest gate is OPEN** for the
coverage actors, and ingested artifacts are persisted on the three operator-named stores —
**DataLad + IPFS + kotobase.net** (ADR-2605241500 dataset substrate, ADR-2606111330 kotobase,
ADR-2606142300 clj-native). Bounded + polite by default; full-universe ingest stays a continued
operator/loop process.

## Tools

| script | what it does |
|---|---|
| `off_batch.py` | uchiwake 内訳 — fetch curated real GTINs (`curated/gtins.txt`) from Open Food Facts (CC-BY-SA), GTIN-validate via the OFF adapter, merge into `products.merged.kotoba.edn`. Gate: `UCHIWAKE_OPERATOR_GATE=1`. |
| `edgar_batch.py` | kanjō 勘定 — fetch curated real CIKs (`curated/ciks.txt`) from SEC EDGAR companyfacts (primary disclosure only, G1), parse FY 10-K/20-F facts as `:authoritative`, merge **additively** into `facts.merged.kotoba.edn` (never clobbers prior filings). Gate: `KANJO_OPERATOR_GATE=1`. |
| `publish.py` | persist any artifact(s): `ipfs add --cid-version=1 --raw-leaves --pin` (verify CID for ≤256 KiB single-block; daemon CID for chunked) + DataLad dataset save under `80-data/<name>/` + per-dataset IPNS key + kotobase.net `/pins` attempt + manifest/PUBLISH.md → `80-data/coverage-manifests/`. |

## Run

```bash
UCHIWAKE_OPERATOR_GATE=1 python3 off_batch.py
python3 publish.py --name uchiwake-coverage --actor uchiwake \
  --artifacts orgs/etzhayyim/com-etzhayyim-uchiwake/data/products.merged.kotoba.edn --ipns --kotobase

KANJO_OPERATOR_GATE=1 python3 edgar_batch.py
python3 publish.py --name kanjo-coverage --actor kanjo \
  --artifacts orgs/etzhayyim/com-etzhayyim-kanjo/data/facts.merged.kotoba.edn --ipns --kotobase
```

## Storage layout

- **IPFS** — `ipfs add` pin on the local kubo node (verified, content-addressed CIDv1). The
  durable provider today (ADR-2606111330 "honest boundary").
- **DataLad** — a standalone dataset per artifact set at `80-data/<name>/` (git-annex content +
  git metadata, ADR-2605241500). NOT registered as a monorepo subdataset (no `.gitmodules` race);
  gitignored from the monorepo. The data lives here + IPFS, never as monorepo git-lfs (G8).
- **kotobase.net** — IPFS Pinning Service API `/pins`, bearer `KOTOBA_PIN_TOKEN`. Per
  ADR-2606111330 the deployed pod is isolated (peer_count:0) and `/pins` is 401 unauthed, so
  without a token this is recorded `operator-follow-up` (CID is locally pinned + DataLad-saved);
  with a token it registers a real pin. **No fabricated success.**
- **pointer** — `80-data/coverage-manifests/<name>-manifest.json` + `-PUBLISH.md` (the small,
  git-tracked record: CIDs, IPNS, DataLad commit, kotobase status, gateways, fetch+verify steps).

`curated/{gtins,ciks}.txt` are the reproducible target lists; extend them to grow coverage.
