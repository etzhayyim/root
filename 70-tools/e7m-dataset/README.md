# e7m-dataset

Operator wrapper for the etzhayyim dataset substrate. Per **ADR-2605241500**.

Glues four substrate components together:

1. **DataLad superdataset** at `90-docs/baien/datasets/` — catalog + provenance.
2. **git-annex `directory` special remote** (`local-store`) at
   `${ETZ_DATASET_ROOT}/annex-store/<subdataset>/` — bytes at rest.
3. **Sidecar IPFS pinner** — walks the directory remote, `ipfs add`s each
   annex object, emits a SHA256E-key → IPFS-CID map JSON, pins the map.
4. **PDS `app.etzhayyim.substrate.datasetPin` record** — religious-corp-canonical receipt.

It does NOT reimplement DataLad / git-annex semantics — it orchestrates
existing commands and adds the **Charter Rider §2 scan** gate and the
**PDS emit** step.

## Install

```sh
brew install kubo git-annex datalad
pipx install -e 70-tools/e7m-dataset/
```

`pipx` is preferred but `pip install --user -e .` works too.

## Setup (per machine)

```sh
# Either:
export ETZ_DATASET_ROOT=/Volumes/260317/etzhayyim

# Or persistently:
mkdir -p ~/.etzhayyim
cat > ~/.etzhayyim/local-paths.toml <<'EOF'
[machine.mac-mini-jun]
dataset_root = "/Volumes/260317/etzhayyim"
kubo_api     = "http://127.0.0.1:5001"
node_did     = "did:web:mac-260317.etzhayyim.com"
EOF
```

## Commands

| Command | Purpose |
|---|---|
| `e7m-dataset where`                            | Print resolved paths + Kubo / annex / staging dirs |
| `e7m-dataset publish-ipfs <subdataset>`        | Walk annex-store, ipfs-add each object, write key→CID map, pin map → return map CID |
| `e7m-dataset pull wikidata --query <name>`     | Run a canned Wikidata SPARQL query → stage JSONL (Phase 3 Tier B seeds: `legal-entities-with-lei` / `admin-areas`) |
| `e7m-dataset pull geonames --dataset <name>`   | Download a GeoNames bulk dump (cities500/1000/5000/15000/allCountries) |
| `e7m-dataset pull osm --region <slug>`         | Download a Geofabrik OSM PBF extract (alias-friendly: `japan` → `asia/japan`; full path also accepted) |
| `e7m-dataset add hf://<owner>/<repo>@<rev>`    | (TODO) HF clone + Charter scan + annex add + publish-ipfs + PDS emit |
| `e7m-dataset verify <subdataset>`              | (TODO) Fetch map CID, fetch each entry, sha-check |

`pull` shipped 2026-05-23 (this round) — stages upstream Wikidata / GeoNames / OSM data
into the staging dir. Operator chains:

```sh
# 1. Stage
e7m-dataset pull wikidata --query legal-entities-with-lei --limit 5000
# → { name: "wikidata:legal-entities-with-lei", revision: "sha256:...",
#     stagingPath: ".../datasets-staging/wikidata-...-202605231530Z/", ... }

# 2. Curate + datalad save (operator)
cd 90-docs/baien/datasets/<kind>/<name>/
cp -r <stagingPath>/* .
datalad save -m "ingest <name> at <revision>"

# 3. Publish IPFS + emit datasetPin record
e7m-dataset publish-ipfs <subdataset> \
    --append-manifest \
    --name 'wikidata:legal-entities-with-lei' \
    --revision 'sha256:...' \
    --kind reference \
    --license CC0-1.0

# 4. The resulting datasetPin AT URI feeds maps Tier B register helpers:
#    feature.registerFeature({ ..., sourceDid: 'did:web:maps.etzhayyim.com:registry:wikidata' })
#    ingest.registerVisionResult({ payloadKind: 'datalad-pin', datasetPinUri: 'at://...', ... })
```

`add` / `verify` remain scaffolded for the next session.

## Layout

```
70-tools/e7m-dataset/
├── pyproject.toml
├── README.md
└── src/e7m_dataset/
    ├── cli.py        # argparse entry point
    ├── paths.py      # ETZ_DATASET_ROOT + ~/.etzhayyim/local-paths.toml resolver
    ├── ipfs.py       # Kubo HTTP API client (POST /api/v0/add, /api/v0/pin/add)
    ├── pinner.py     # publish-ipfs sidecar: walk annex objects + map JSON
    ├── manifest.py   # append to 90-docs/baien/datasets.jsonl
    ├── charter.py    # Charter Rider scan wrapper (calls pymagatama.organism.sensors.charter_rider)
    └── pds.py        # datasetPin lexicon record emit (stub w/ --dry-run)
```

## See also

- ADR-2605241500 — design
- `90-docs/baien/datasets/README.md` — superdataset entry point
- `50-infra/ipfs-pinner/` — MST CAR pinner; shares the Kubo HTTP API contract
