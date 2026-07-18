# etzhayyim-project-maps-collection — Maps Collection Control Plane

> **T1 Logical Actor**: Manifest-driven (`orgs/etzhayyim/com-etzhayyim-maps-collection/actor-manifest.jsonld`).

`v1m9k2q8.etzhayyim.com` (nanoid: `v1m9k2q8`) — Maps collection control plane. Coordinates Overpass / OSM diff / Microsoft Building Footprint / Google Places / OpenAddresses / NaturalEarth / Wikidata POI / web crawl ingestion for maps.etzhayyim.com.

## Lexicons
`mapsCollection/` (2 files): registerJob, listJobs. 8 jobType.

## cross-actor
- `maps` — parent app receiving collected vertex/edge records
- `common-crawl` — web crawl source
- `livecam` — geo-tagged stream metadata
