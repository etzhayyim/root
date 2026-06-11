# e7m-dataset

Operator wrapper for the etzhayyim dataset substrate. Per **ADR-2605241500**.

Glues four substrate components together:

1. **DataLad superdataset** at `90-docs/baien/datasets/` — catalog + provenance.
2. **git-annex `directory` special remote** (`local-store`) at
   `${ETZ_DATASET_ROOT}/annex-store/<subdataset>/` — bytes at rest.
3. **Sidecar IPFS pinner** — walks the directory remote, `ipfs add`s each
   annex object, emits a SHA256E-key → IPFS-CID map JSON, pins the map.
4. **PDS `com.etzhayyim.substrate.datasetPin` record** — religious-corp-canonical receipt.

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
| `e7m-dataset add hf://<owner>/<repo>@<rev>`    | HF fetch + Charter scan + DataLad save + annex copy + publish-ipfs + manifest + datasetPin emit |
| `e7m-dataset verify <subdataset>`              | Fetch map CID, fetch each entry, sha256 against the SHA256E key, size-cross-check vs annex object |

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

### One-shot HF ingestion (`add` chain)

`add` performs the whole pipeline in a single invocation:

```sh
e7m-dataset add hf://hf-internal-testing/fixtures_image_utils@main \
    --kind reference \
    --license Apache-2.0 \
    --max-bytes $((500 * 1024 * 1024))    # -1 disables the cap
# → fetch + charter scan + datalad save + annex copy + publish-ipfs +
#   manifest row + datasetPin (dry-run by default; add --emit to POST)
```

### Re-verifying a pin

```sh
e7m-dataset verify HF/hf-internal-testing-fixtures_image_utils [--verbose]
# Map CID is taken from the latest manifest row for the subdataset (override with --map-cid).
# Exit 0 = all entries OK, exit 4 = at least one mismatch.
```

## Charter Rider scanner

The §2(a)..(h) gate is implemented in
`kotodama.organism.sensors.charter_rider` (heuristic regex scanner,
ADR-2605192200 / ADR-2605241500 §D7).

Three import strategies, tried in order:

1. **Production**: `pip install kotodama` into the venv.
2. **Operator override**: set `ETZ_PYKOTODAMA_SRC=/path/to/kotodama/py/src`.
3. **Auto-discovery** (default for in-repo invocation): the wrapper walks
   up from cwd, finds `40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/organism/sensors/charter_rider.py`,
   and prepends to `sys.path`.

```sh
ETZ_DATASET_CHARTER_STRICT=1 e7m-dataset add hf://...        # fail-closed if scanner missing
```

Hits raise `CharterViolation` and abort the `add` flow before any IPFS
write or PDS emission.

## PDS emit credential setup

`add` / `publish-ipfs` default to dry-run for the PDS step. To go live,
provide credentials for the dataset-pinner DID and pass `--emit`:

```sh
# One-time setup — store the password in macOS Keychain so it never
# touches a shell history file.
security add-generic-password \
    -s 'etzhayyim' \
    -a 'E7M_DATASET_PDS_PASSWORD' \
    -w 'YOUR_APP_PASSWORD_HERE' \
    -U

# At invocation time, decant from Keychain to the env var:
export ETZ_E7M_PDS_URL='https://pds.etzhayyim.com'
export ETZ_E7M_PDS_DID='did:web:dataset-pinner.etzhayyim.com'   # repo to write under
export ETZ_E7M_PDS_AUTH="$(printf '{"handle":"dataset-pinner.etzhayyim.com","password":"%s"}' \
    "$(security find-generic-password -s etzhayyim -a E7M_DATASET_PDS_PASSWORD -w)")"

e7m-dataset add hf://owner/repo@v1 --kind training-corpus --license CC-BY-4.0 --emit
```

Long-lived deployments should prefer a refresh-token-bearing **session**
JSON over the password fallback:

```sh
export ETZ_E7M_PDS_SESSION='{"did":"...","handle":"...","accessJwt":"...","refreshJwt":"..."}'
```

The pinner's atproto identity is
**`did:web:dataset-pinner.etzhayyim.com`** — scaffolded under
[`50-infra/etzhayyim-dataset-pinner-did-web/`](../../50-infra/etzhayyim-dataset-pinner-did-web/),
mirroring the esign / pinner DID Worker pattern. Before going live the
operator must:

1. `wrangler deploy` the Worker.
2. Provision the AAAA record on the etzhayyim.com zone (CF dashboard).
3. Generate the Ed25519 keypair, populate `did.json verificationMethod`.
4. Have PDS issue an app-password for the `dataset-pinner.etzhayyim.com`
   handle, decant via Keychain as above.

Until step 1+2 land the DID resolves only via local `wrangler dev`;
`--emit` will still POST to PDS using the app-password but the resolver
won't yet trust the DID.

## Second-node replication runbook

ADR-2605241500 §D6 requires `replicationMin: 2` for production. Current
deployment is warn-only single-node. To bring a second node online:

```sh
# On node B:
brew install kubo git-annex datalad
mkdir -p /Volumes/<vol-on-node-B>/etzhayyim/{ipfs-data,annex-store,datasets-staging}
IPFS_PATH=/Volumes/<vol>/etzhayyim/ipfs-data ipfs init --profile=server
launchctl bootstrap gui/$UID ~/Library/LaunchAgents/com.etzhayyim.kubo.plist
cat > ~/.etzhayyim/local-paths.toml <<EOF
[machine.$(hostname -s)]
dataset_root = "/Volumes/<vol>/etzhayyim"
kubo_api     = "http://127.0.0.1:5001"
node_did     = "did:web:<this-node>.etzhayyim.com"
EOF

# Clone the superdataset (pointers only; bytes follow):
datalad clone <node-A-superdataset-url-or-path> /path/to/clone
cd /path/to/clone
git annex initremote local-store \
    type=directory \
    directory=/Volumes/<vol>/etzhayyim/annex-store/superdataset \
    encryption=none chunk=64MiB

# Subscribe to a specific subdataset's bytes:
datalad get HF/hf-internal-testing-fixtures_image_utils
# This pulls bytes from the network (node A's remote, if exposed, or
# any peer that has copied to its own annex-store).

# Pin to node-B's IPFS:
e7m-dataset publish-ipfs HF/hf-internal-testing-fixtures_image_utils
# The map CID will be identical to node A's (deterministic from
# annex objects), confirming substrate-level convergence.
```

Update the affected manifest row's `assignedNodes` to include the new
DID (append a new row — datasets.jsonl is append-only). Once two DIDs
hold the bytes, set `replicationMin: 2` on subsequent additions.

## Layout

```
70-tools/e7m-dataset/
├── pyproject.toml
├── README.md
├── src/e7m_dataset/
│   ├── cli.py         # argparse entry point (where / publish-ipfs / pull / add / verify)
│   ├── paths.py       # ETZ_DATASET_ROOT + ~/.etzhayyim/local-paths.toml resolver
│   ├── ipfs.py        # Kubo HTTP API client (httpx) — add/cat/pin
│   ├── pinner.py      # publish-ipfs sidecar: walk annex objects + key→CID map JSON
│   ├── verifier.py    # round-trip + sha256 verification
│   ├── manifest.py    # 90-docs/baien/datasets.jsonl append + lookup
│   ├── charter.py     # Charter Rider scan wrapper (3-strategy import)
│   ├── pds.py         # datasetPin record emit (dry-run default; live via httpx)
│   ├── subdataset.py  # DataLad/git-annex orchestration (ensure/save/copy)
│   └── fetchers/
│       ├── __init__.py   # FetchResult dataclass
│       ├── hf.py         # Hugging Face Hub API
│       ├── geonames.py   # GeoNames bulk dumps
│       ├── osm.py        # Geofabrik OSM PBF
│       └── wikidata.py   # Wikidata SPARQL
└── tests/                # 37 unit tests (httpx.MockTransport for HF/Kubo)
```

## See also

- ADR-2605241500 — design
- `90-docs/baien/datasets/README.md` — superdataset entry point
- `50-infra/ipfs-pinner/` — MST CAR pinner; shares the Kubo HTTP API contract
