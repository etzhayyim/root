# open-rail.gftd.ai — Railway Operations & Network Design (OSS)

**Status**: MVP scaffold (2026-04-20). Reference implementation for railway
operations management (timetable / train running / incidents) and network
design (line / station topology). Apache-2.0.

## Scope (MVP)

| NSID | Type | Description |
|---|---|---|
| `ai.gftd.apps.openRail.defineLine` | procedure | declare a line + its station sequence (network design) |
| `ai.gftd.apps.openRail.getLine` | query | line + stations + km posts |
| `ai.gftd.apps.openRail.listLines` | query | paginated line list |
| `ai.gftd.apps.openRail.scheduleTrain` | procedure | publish a single train run (origin→destination, stop pattern) |
| `ai.gftd.apps.openRail.listTrainRuns` | query | runs by line / day / status |
| `ai.gftd.apps.openRail.reportIncident` | procedure | safety / delay incident with severity |
| `ai.gftd.apps.openRail.listIncidents` | query | incidents by line / since |

## Architecture

- **Runtime**: Single CF Worker (`src/app.ts`, single-file principle)
- **Storage**: D1 (SQLite). Tables: `lines`, `stations`, `train_runs`, `incidents`
- **Identity**: line / station / train run = path-based DIDs
  `did:web:open-rail.gftd.ai:line:{id}`, `:station:{id}`, `:run:{id}`
- **Network = ordered station list per line** (km post + dwell time). MVP =
  single-track linear graph; double-track + branching deferred
- **Incident severity** is computed by DMN (`openRail.incidentSeverity`):
  delay minutes + injury count → `{severity, requireGovReport}`
- **Audit**: large incidents (severity ≥ "major") emit `app.bsky.feed.post`
  via PDS service binding (Design E Tier 1)

## Not in MVP (future)

- Realtime train position (GTFS-RT / `getTrainPositions`)
- Branching / junctions (graph-based topology)
- Rolling stock asset registry, maintenance windows
- Slot/path allocation between operators (open access)
- Federation with JR / private operators via AT Protocol follow

## Local Dev

```bash
cd 60-apps/ai-gftd-project-open-rail/worker
npm i -g wrangler
wrangler d1 create ai-gftd-open-rail
wrangler dev --local
```

## Deploy

```bash
cd 60-apps/ai-gftd-project-open-rail/worker
e7m actor deploy .
```

## OSS Split

Mirror to `gftdcojp/ai-gftd-project-open-rail` (Apache-2.0) via subtree.
