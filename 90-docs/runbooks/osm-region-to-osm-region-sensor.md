# OSM PBF → GeoJSON-NDJSON → `OsmRegionSensor` (operator runbook)

Per **ADR-2605262400** §3 + §4.2 + W1. Bridges the gap between
`e7m-dataset pull osm --region <slug>` (Geofabrik `.osm.pbf` fetch)
and the `kotodama.organism.sensors.OsmRegionSensor` which consumes
a **GeoJSON-NDJSON sidecar** (one Feature per line). The conversion
runs on the operator's workstation via the
[osmium-tool](https://osmcode.org/osmium-tool/) suite — explicitly
NOT inside the religious-corp inference / organism heartbeat path
(per §7 passive-only invariant + G8 lint).

## Prerequisites

- `e7m-dataset` CLI installed (per `70-tools/e7m-dataset/README.md`).
- `osmium-tool` ≥ 1.16 on the operator workstation:
  ```sh
  brew install osmium-tool          # macOS
  apt install osmium-tool           # Debian / Ubuntu
  ```
- `~/.etzhayyim/local-paths.toml` resolved (run `e7m-dataset where`
  to confirm `staging` / `annex_store`).

## End-to-end smoke (Liechtenstein, ~3 MB)

The smallest practical region. Reproduces every step from fetch to
sensor stream. Verified 2026-05-26 on `mac-260317`:

| Stage | Wall | Output |
|---|---:|---|
| `e7m-dataset pull osm --region europe/liechtenstein` | ~3s | 3,371,178 byte `.osm.pbf`, md5 `012143442d952cb622db84ea61f994e3` |
| `osmium export -f geojsonseq` | 0.4s | 31 MB `.geojsonl` (RFC 8142 RS-prefixed) |
| `OsmRegionSensor.stream()` (full file) | 0.63s | **86,129 typed observations** at ~152K features/s |
| `hot_sample(5)` deterministic across 2 calls | <1ms | G9 ✓ |

Feature breakdown (first 5K sampled from full stream):

| OSM key | Count |
|---|---:|
| `natural` | 3,309 (mountain peaks dominate — Liechtenstein is alpine) |
| `highway` | 750 |
| `amenity` | 195 |
| `place` | 40 |
| `railway` | 29 |

Bounding box of all 86,129 observed features: `lat [46.98, 47.52]`,
`lon [9.45, 9.67]` — consistent with Liechtenstein's geographic
extent (the slight overshoot beyond the strict country box is
boundary features extending into neighboring AT / CH).

### 1. Fetch the PBF

```sh
e7m-dataset pull osm --region europe/liechtenstein
```

This stages the file at
`$ETZ_DATASET_ROOT/datasets-staging/osm-europe-liechtenstein-<captureTs>/`
with both `*.osm.pbf` and `*.osm.pbf.md5`. Verify the md5 against
the sidecar:

```sh
cd $ETZ_DATASET_ROOT/datasets-staging/osm-europe-liechtenstein-*/
md5 europe-liechtenstein-latest.osm.pbf
diff <(md5 -q europe-liechtenstein-latest.osm.pbf) \
     <(awk '{print $1}' europe-liechtenstein-latest.osm.pbf.md5)
```

### 2. Export GeoJSON-NDJSON via osmium

```sh
osmium export \
  --output-format=geojsonseq \
  --output europe-liechtenstein-latest.geojsonl \
  europe-liechtenstein-latest.osm.pbf
```

Notes:

- `geojsonseq` emits one Feature per line (RS-delimited per RFC
  8142). `OsmRegionSensor` accepts both the canonical RS form and
  pure newline-delimited JSON.
- Default tag set keeps `name`, `place`, `amenity`, etc. To filter
  (e.g. railway stations only):
  ```sh
  osmium tags-filter -o stations.osm.pbf \
    europe-liechtenstein-latest.osm.pbf railway=station
  osmium export -f geojsonseq -o stations.geojsonl stations.osm.pbf
  ```

### 3. Promote to a DataLad subdataset

```sh
SUBDS=geo/osm/europe-liechtenstein
cd $REPO/90-docs/baien/datasets
datalad create -d . $SUBDS
mkdir -p $SUBDS/snap-$(date -u +%Y%m%dT%H%M%SZ)
cp $STAGING/europe-liechtenstein-latest.geojsonl $SUBDS/snap-*/
cd $SUBDS && datalad save -m "ingest europe-liechtenstein OSM region — Tier A ODbL"
```

### 4. Push to the `local-store` annex remote

```sh
git annex initremote local-store \
  type=directory \
  directory=$ETZ_DATASET_ROOT/annex-store/$SUBDS \
  encryption=none chunk=64MiB
git annex copy --to=local-store
```

### 5. Publish to IPFS + manifest row

```sh
e7m-dataset publish-ipfs $SUBDS \
  --append-manifest \
  --name "osm:europe/liechtenstein" \
  --revision "md5:<from-fetch-result>" \
  --kind "reference" \
  --license "ODbL-1.0"
```

This emits a map CID (sha256e → IPFS CID) and appends a row to
`90-docs/baien/datasets.jsonl`. **The license must be `ODbL-1.0` —
derivative corpora inherit the share-alike obligation per
ADR-2605192200 §3.**

### 6. Verify roundtrip

```sh
e7m-dataset verify $SUBDS --map-cid <map-cid-from-step-5>
```

Expects `ok: true / fail_count: 0`.

### 7. Wire into an `OsmRegionSensor`

```python
from pathlib import Path
from kotodama.organism.sensors import (
    DatasetPin, OsmRegionSensor, StaticPinResolver,
)

pin = DatasetPin(
    name="geo/osm/europe-liechtenstein",
    revision="sha256:<from-publish-ipfs>",
    cid_map_cid="<map-cid>",
    license="ODbL-1.0",
    tier="A",
    created_at="<RFC3339>",
    assigned_nodes=("did:web:mac-260317.etzhayyim.com",),
)
sensor = OsmRegionSensor(
    name="geo/osm/europe-liechtenstein",
    annex_root=Path("/path/to/90-docs/baien/datasets"),
    pin_resolver=StaticPinResolver(pins={"geo/osm/europe-liechtenstein": pin}),
)
for obs in sensor.stream(sensor.latest_pin()):
    print(obs.payload["name"], obs.payload["lat"], obs.payload["lon"],
          obs.payload["feature_tags"])
```

## License + Charter Rider notes

- **Upstream license**: OpenStreetMap data is **ODbL 1.0**
  (Open Database License). Geofabrik's regional extracts inherit
  that license unchanged.
- **Share-alike**: any derivative work (database, NDJSON sidecar,
  trained corpus that incorporates OSM rows) MUST itself be licensed
  ODbL 1.0 + carry attribution per ADR-2605192200 §3.
- **Attribution**: required form is **"© OpenStreetMap contributors,
  ODbL 1.0"** — propagated into the assembled-corpus manifest
  automatically by `assemble-public-corpus.py` when the recipe
  declares `license = "ODbL-1.0"`.
- **Tier**: A (publishable). Not Tier C / `-nc-` infix required.

## When NOT to use osmium

OSM region streaming inside the organism heartbeat is OUT OF SCOPE
for the religious-corp substrate per ADR-2605262400 §7 (passive-only)
+ G8 lint. The sensor ONLY consumes a pre-converted NDJSON sidecar —
PBF decoding happens ONCE on the operator workstation, not on every
tick.

## Troubleshooting

- **`osmium export` runs out of memory on large regions**: use
  `--id-tracking=byid` (slower but less memory) or pre-filter with
  `osmium tags-filter` to reduce the active feature set.
- **Sensor raises `no GeoJSON-NDJSON sidecar in <snapshot_dir>`**:
  confirm step 2 ran successfully. `OsmRegionSensor` accepts
  `*.geojsonl`, `*.geojsonl.gz`, `*.geojsonseq`, `*.geojsonseq.gz`,
  and `*.ndjson`.
- **Centroid anchors look weird on cross-IDL geometries**: known
  limitation of the coarse coordinate-average centroid (see
  ADR-2605262400 §3 — sensor returns a "coarse anchor", not a
  geodetic centroid). For IDL-crossing or polar features use the
  `feature_tags` block to access the full geometry indirectly via
  the assembler.

## Related

- ADR-2605262400 — public-data organism ingestion
- ADR-2605241500 — dataset substrate (DataLad + annex + IPFS)
- ADR-2605192200 — Charter Rider §3 (license SA propagation)
- `70-tools/e7m-dataset/src/e7m_dataset/fetchers/osm.py` — fetcher
- `40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/organism/sensors/osm_region_sensor.py` — sensor
