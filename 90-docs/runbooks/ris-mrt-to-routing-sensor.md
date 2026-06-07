# RIPE-RIS / Routeviews MRT → NDJSON → `RisRoutingSensor` (operator runbook)

Per **ADR-2605262400** §3 + §4.2 + W2. Bridges the gap between
`e7m-dataset pull` of a raw MRT bview (binary Protocol Buffers-ish
RFC 6396) and the cold-path corpus assembler which streams NDJSON.
The conversion runs on the operator's workstation via the
[mrtparse](https://github.com/t2mune/mrtparse) Python library —
explicitly NOT inside the religious-corp inference / organism
heartbeat path (per §7 passive-only invariant + G8 lint enforces this).

For organism heartbeat use against raw MRT (no conversion), see
`RisRoutingSensor.stream_bounded` / `hot_sample_bounded` in
`sensors/base.py` (commit `4d23f5f24`).

## Prerequisites

- `e7m-dataset` CLI installed (per `70-tools/e7m-dataset/README.md`).
- Python ≥ 3.11 with `mrtparse` installed:
  ```sh
  pip3 install --user mrtparse              # Linux / macOS
  # On systems with PEP 668 restriction (Homebrew Python 3.14+):
  pip3 install --user --break-system-packages mrtparse
  ```
- `~/.etzhayyim/local-paths.toml` resolved (run `e7m-dataset where`
  to confirm `staging` / `annex_store`).

## End-to-end smoke (RIPE-RIS rrc00, ~421 MB)

Real measurements from `mac-260317`, 2026-05-27. The bview was the
2026-05-25T08:00 UTC RIPE-RIS rrc00 snapshot.

### 1. Fetch the bview

```sh
PYTHONPATH=70-tools/e7m-dataset/src python3 << 'PY'
from e7m_dataset.fetchers import ripe_ris
from e7m_dataset.paths import resolve
import datetime
paths = resolve()
y = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1)
result = ripe_ris.fetch(paths.staging, ripe_ris.RipeRisFetchOpts(
    collector="rrc00", year=y.year, month=y.month, day=y.day,
    hour=8, minute=0,
))
print(result.staging_path, result.size_bytes)
PY
```

Stages a `bview.<yyyymmdd>.<hhmm>.gz` (~400-500 MB compressed)
at `$ETZ_DATASET_ROOT/datasets-staging/ris-mrt-rrc00-<yyyymmdd>-<hhmm>-<captureTs>/`.

For Routeviews substitute `from e7m_dataset.fetchers import
routeviews` and `RouteviewsFetchOpts(collector="route-views.wide", …)`
(.bz2 suffix instead of .gz).

### 2. Decode MRT → NDJSON via mrtparse

The sensor reads either compressed MRT directly (heartbeat path) OR
a derived NDJSON sidecar (cold-path corpus assembly). For corpus
work, generate the sidecar once:

```sh
cd $STAGING/ris-mrt-rrc00-*/
python3 << 'PY'
"""mrtparse MRT → NDJSON sidecar. One row per RIB prefix entry.

Schema (matches RisRoutingSensor's `_extract_prefix_records` output):
  {"prefix": "1.0.0.0/24", "peerIndex": 0, "originAsn": 64500,
   "asPath": [64500, 64501, 64502]}
"""
import json
from mrtparse import Reader

def extract(record):
    data = getattr(record, 'data', record)
    prefix = data.get('prefix', '')
    plen = data.get('prefix_length', '')
    for ent in data.get('rib_entries', []) or []:
        peer_idx = ent.get('peer_index', '')
        as_path = []
        for attr in ent.get('path_attributes', []) or []:
            t = attr.get('type', {})
            tcodes = list(t.values()) if isinstance(t, dict) else [t]
            if not any('AS_PATH' in str(c) or c == 2 for c in tcodes):
                continue
            for seg in attr.get('value', []) or []:
                for asn in (seg.get('value', []) if isinstance(seg, dict) else []):
                    try: as_path.append(int(asn))
                    except (TypeError, ValueError): continue
        yield {
            "prefix": f"{prefix}/{plen}" if prefix and plen != "" else prefix,
            "peerIndex": peer_idx,
            "originAsn": as_path[-1] if as_path else None,
            "asPath": as_path,
        }

with open('bview.20260525.0800.ndjson', 'w') as out:
    for record in Reader('bview.20260525.0800.gz'):
        for row in extract(record):
            out.write(json.dumps(row) + '\n')
PY
ls -lh bview.*.ndjson
```

Expected: ~5-10M rows / ~1-3 GB uncompressed NDJSON / wall **~5-8
minutes** on `mac-260317` at 15K obs/s. The sidecar IS the canonical
input for `assemble-corpus`; the raw `.gz` stays for sensor
hot-path use.

For Routeviews, swap `.gz` → `.bz2` in the input filename (mrtparse
auto-detects compression).

### 3. Promote to a DataLad subdataset

```sh
SUBDS=routing/ris-mrt/rrc00
cd $REPO/90-docs/baien/datasets
datalad create -d . $SUBDS
mkdir -p $SUBDS/snap-$(date -u +%Y%m%dT%H%M%SZ)
cp $STAGING/bview.20260525.0800.gz       $SUBDS/snap-*/
cp $STAGING/bview.20260525.0800.ndjson   $SUBDS/snap-*/   # optional — only if corpus consumer wants pinned NDJSON
cd $SUBDS && datalad save -m "ingest ris-mrt rrc00 <snap> bview — Tier A ripe-tou-open"
```

NOTE: the verified 2026-05-26 commit landed only the `.gz` (NDJSON
was operator-derived and pre-existing on staging). See real anchor
below.

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
  --name "ris-mrt:rrc00:<yyyymmddThhmmZ>" \
  --revision "sha256:<from-fetch-result-or-recompute>" \
  --kind "reference" \
  --license "ripe-tou-open"
```

### 6. Verify roundtrip

```sh
e7m-dataset verify $SUBDS --map-cid <map-cid-from-step-5>
```

Expect `ok: true / fail_count: 0`. A 421 MB bview chunks into ~7
IPFS blocks (UnixFS default chunker, 256 KiB chunks); `verify`
sha256s each block independently.

### 7. Wire into a `RisRoutingSensor` or a corpus recipe

**Heartbeat path** (consumes the raw `.gz` directly — no NDJSON
sidecar needed):

```python
from pathlib import Path
from kotodama.organism.sensors import (
    DatasetPin, RisRoutingSensor, StaticPinResolver,
    stream_bounded, hot_sample_bounded,
)

pin = DatasetPin(
    name="routing/ris-mrt/rrc00",
    revision="sha256:<from-publish-ipfs>",
    cid_map_cid="<map-cid>",
    license="ripe-tou-open",
    tier="A",
    created_at="<RFC3339>",
    assigned_nodes=("did:web:mac-260317.etzhayyim.com",),
)
sensor = RisRoutingSensor(
    name="routing/ris-mrt/rrc00",
    annex_root=Path("/path/to/90-docs/baien/datasets"),
    pin_resolver=StaticPinResolver(pins={"routing/ris-mrt/rrc00": pin}),
)

# Bounded sampling — heartbeat-friendly:
sample = hot_sample_bounded(sensor, sensor.latest_pin(), n=20, max_iter=10000)
# → 20 typed BGP observations in ~0.7s on real 421 MB bview
```

**Cold-path corpus assembly** (consumes the NDJSON sidecar): write
a `corpus-recipe.toml` source entry pointing at the sidecar:

```toml
[[source]]
subdataset    = "routing/ris-mrt/rrc00"
datasetPin_at = "at://did:web:dataset-pinner.etzhayyim.com/com.etzhayyim.substrate.datasetPin/<rkey>"
shard_glob    = "bview.*.ndjson"     # <-- the operator-derived sidecar
tier          = "A"
license       = "ripe-tou-open"
weight        = 0.10
```

Then `e7m-dataset assemble-corpus --recipe <path>`.

## License + Charter Rider notes

- **Upstream license**: RIPE NCC RIS data is published under the
  RIPE NCC Terms of Use; Routeviews data is published under the
  University of Oregon Terms of Use. Both permit research +
  operational redistribution with attribution.
- **Attribution forms**:
  - `Source: RIPE NCC Routing Information Service (RIS) —
    https://www.ripe.net/analyse/internet-measurements/routing-information-service-ris/`
  - `Source: University of Oregon Route Views Project —
    http://www.routeviews.org/routeviews/`
- **Tier**: A (publishable). The fetcher's `source.license` field
  records `ripe-tou-open` / `uo-tou-open` so the corpus assembler
  can propagate per-row attribution.
- **No share-alike** (unlike OSM ODbL): downstream derivatives may
  be Apache-2.0 + Charter Rider v2.0 without inheriting RIPE/UO
  share-alike obligations.

## Real anchor measurements (2026-05-26 / 2026-05-27, mac-260317)

| Stage | Wall | Output |
|---|---:|---|
| `e7m-dataset pull` rrc00 8:00 UTC bview | 74s | 421,319,004 byte `.gz` |
| (optional) `mrtparse` MRT → NDJSON | ~5-8 min | ~5-10M rows, ~1-3 GB |
| `RisRoutingSensor.stream` first 100 | 0.01s | 15,446 obs/s |
| `RisRoutingSensor.hot_sample_bounded(n=10, max_iter=5000)` | 0.07s | 10 typed observations |
| `git annex copy --to=local-store` | ~1s on local SSD | 402 MB → external |
| `e7m-dataset publish-ipfs` | ~30s | map CID + 7 IPFS chunks |
| `e7m-dataset verify --map-cid` | ~10s | 7/7 OK |

Real ASNs surfaced via `hot_sample_bounded`:
`AS9808 (China Mobile / 112.0.0.0)`, `AS20940 (Akamai / 23.192.0.0)`,
`AS3320 (Deutsche Telekom / 31.224.0.0)`, `AS396982 (Google / 34.32.0.0)`,
`AS16509 (AWS / 3.0.0.0)`, `AS749 (AT&T / 11.0.0.0)`,
`AS22394 (Verizon / 72.96.0.0)`, `AS7018 (AT&T / 32.0.0.0)`.

## When NOT to decode MRT

MRT decoding inside the organism heartbeat is OUT OF SCOPE for the
religious-corp substrate per ADR-2605262400 §7 (passive-only) + G8
lint. The sensor's `stream_bounded` / `hot_sample_bounded` methods
read **bounded windows from the raw `.gz`** without ever materializing
the full NDJSON sidecar — sufficient for situational-awareness
sampling on tick cadence.

Pre-decoded NDJSON is only needed for **cold-path corpus assembly**
where the assembler iterates the full file and depends on the
NDJSON-shaped streaming interface.

## Troubleshooting

- **`mrtparse` raises on a truncated archive**: confirm the
  download finished — Geofabrik / RIPE / UO archives sometimes
  serve partial bytes during a regional outage. Re-fetch
  (`e7m-dataset pull osm` is idempotent; same for `ripe_ris.fetch`).
- **NDJSON sidecar shows all rows with `prefix=0.0.0.0`**: the
  first ~100 records of an MRT bview are the PEER_INDEX_TABLE +
  default-route advertisements from many peers. Increase
  `max_iter` to sample further into the table.
- **`AS_PATH` field empty on a row**: some MRT subtypes
  (e.g. TABLE_DUMP_V1 IPv4_MULTICAST) don't include a path. The
  sensor returns `originAsn=None` + `asPath=[]` for these; the
  corpus assembler filters them out at row emission via
  `if as_path: ...` in `_extract_prefix_records`.
- **High memory during MRT → NDJSON conversion**: mrtparse loads
  the full file's prefix table into memory. Process in chunks via
  `--prefix-range` (custom split) or use a bz2-aware streaming
  decoder for large Routeviews dumps.

## Related

- ADR-2605262400 — public-data organism ingestion
- ADR-2605241500 — dataset substrate (DataLad + annex + IPFS)
- ADR-2605192200 — Charter Rider §3 (license + attribution propagation)
- `70-tools/e7m-dataset/src/e7m_dataset/fetchers/ripe_ris.py` —
  RIPE RIS fetcher
- `70-tools/e7m-dataset/src/e7m_dataset/fetchers/routeviews.py` —
  Routeviews fetcher (sibling)
- `40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/organism/sensors/ris_routing_sensor.py` —
  Sensor (heartbeat + cold-path)
- `90-docs/runbooks/osm-region-to-osm-region-sensor.md` — sibling
  runbook for the OSM bucket
