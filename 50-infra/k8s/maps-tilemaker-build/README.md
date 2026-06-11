# maps-tilemaker-build

One-shot Kubernetes Job that converts an OSM PBF into an OpenMapTiles-schema
PMTiles archive and uploads it to Backblaze B2, where the
`maps-tile-server-t1l3srv0` Worker serves it as standard MVT tiles.

## Pipeline

```
PBF (geofabrik / planet.osm.org / maps-osm-ingest)
  → tilemaker (OpenMapTiles config + Lua)
  → planet-{VERSION}.pmtiles
  → rclone → r2://etzhayyim-maps-tiles/v1/planet-{VERSION}.pmtiles
  → rclone → r2://etzhayyim-maps-tiles/v1/manifest.json  (atomic swap, last)
```

VERSION defaults to `YYYYMMDDHH` (UTC). Historical PMTiles are retained in B2
until an operator prunes them; the Worker only reads the key referenced by
`manifest.json`, so rollback = re-upload an older manifest.

## Files

| File | Role |
|---|---|
| `Dockerfile` | `systemed/tilemaker:v2.4.0` + rclone + curl + jq. Entry = `run-tilemaker.sh`. |
| `run-tilemaker.sh` | Downloads PBF → runs tilemaker → uploads PMTiles → writes manifest.json. |
| `openmaptiles.json` / `openmaptiles.lua` | Placeholders; set `CONFIG_FETCH_AT_RUNTIME=1` or bake pinned copies. |
| `job.yaml` | K8s Job spec. Japan extract profile by default. |

## Build & publish image

```bash
cd 50-infra/k8s/maps-tilemaker-build
docker build -t ghcr.io/etzhayyim/maps-tilemaker-build:$(date -u +%Y%m%d) -t ghcr.io/etzhayyim/maps-tilemaker-build:latest .
docker push  ghcr.io/etzhayyim/maps-tilemaker-build:latest
docker push  ghcr.io/etzhayyim/maps-tilemaker-build:$(date -u +%Y%m%d)
```

## B2 setup (one-time)

```bash
wrangler r2 bucket create etzhayyim-maps-tiles
# Create an R2 API token (Admin Read & Write) scoped to etzhayyim-maps-tiles
# and store it as a K8s secret in the maps namespace:
kubectl -n maps create secret generic etzhayyim-r2-credentials \
  --from-literal=account_id=${CF_ACCOUNT_ID} \
  --from-literal=access_key_id=${R2_ACCESS_KEY_ID} \
  --from-literal=secret_access_key=${R2_SECRET_ACCESS_KEY}
```

## Run (Japan extract)

```bash
kubectl -n maps apply -f job.yaml
kubectl -n maps logs -f job/maps-tilemaker-build
```

Edit `job.yaml` `PBF_URL`, `TILEMAKER_EXTRA`, and `resources` for other extracts
or the planet.

## Planet build

Bump `nodeSelector` → `node-class: highmem-xl` (or your 128 Gi pool), set:

```yaml
resources:
  requests: { cpu: "16", memory: "96Gi", ephemeral-storage: "300Gi" }
  limits:   { cpu: "32", memory: "128Gi", ephemeral-storage: "400Gi" }
env:
  - { name: PBF_URL, value: "https://planet.openstreetmap.org/pbf/planet-latest.osm.pbf" }
```

Expect ≈ 12 h wall clock and ≈ 100 GB output PMTiles.

## Post-run

1. Check logs for `DONE version=... key=...`.
2. `wrangler r2 object get etzhayyim-maps-tiles/v1/manifest.json --pipe` to confirm.
3. Purge the Worker's KV manifest cache (TTL 60 s) or wait for natural expiry:
   ```bash
   wrangler kv:key delete --binding=TILE_MANIFEST "manifest:v1"
   ```
4. Smoke test: `curl -I https://tiles.maps.etzhayyim.com/v1/0/0/0.pbf` — expect
   `200 application/vnd.mapbox-vector-tile` within a few hundred ms.

## TODO

- Wire `maps-osm-ingest` completion → argo workflow → this Job (currently manual).
- Diff-based incremental builds (tilemaker `--merge`) for daily updates.
- Auto-prune PMTiles older than N versions from B2.
