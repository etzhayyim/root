# open-airplane.gftd.ai — Aviation Operations & Airport Network (OSS)

**Status**: MVP scaffold (2026-04-20). Reference implementation for
DID-addressed aviation operations — airport / aircraft / flight / incident.
Apache-2.0.

## Scope (MVP)

| NSID | Type | Description |
|---|---|---|
| `ai.gftd.apps.openAirplane.defineAirport` | procedure | airport (ICAO + IATA + runways) |
| `ai.gftd.apps.openAirplane.listAirports` | query | airport directory |
| `ai.gftd.apps.openAirplane.registerAircraft` | procedure | aircraft registration (tail no. + ICAO 24-bit) |
| `ai.gftd.apps.openAirplane.scheduleFlight` | procedure | publish a single flight (origin → destination) |
| `ai.gftd.apps.openAirplane.recordFlightStatus` | procedure | OOOI events (off, out, on, in) + cancel |
| `ai.gftd.apps.openAirplane.listFlights` | query | flights by airport / date / status |
| `ai.gftd.apps.openAirplane.reportIncident` | procedure | safety incident with severity DMN |
| `ai.gftd.apps.openAirplane.listIncidents` | query | incidents by aircraft / since |

## Architecture

- **Runtime**: Single CF Worker (`src/app.ts`)
- **Storage**: D1. Tables: `airports`, `aircraft`, `flights`, `flight_status`, `incidents`
- **Identity**: airport / aircraft / flight / incident = path-based DIDs
- **OOOI**: each flight has 4 timestamp checkpoints — Off-block / Take-off
  (Out) / Touch-down (On) / In-block. Status machine: `scheduled →
  off-block → airborne → landed → in-block → completed | diverted | cancelled`
- **Severity** by DMN (`openAirplane.incidentSeverity`):
  injuries + hull-loss + atc-incident → ICAO Annex 13 alignment
  (incident / serious-incident / accident)
- **Audit**: serious-incident or accident → `app.bsky.feed.post` (regulator visible)

## Not in MVP

- ADS-B realtime track ingest, ATC clearances
- Aircraft maintenance / MEL
- Crew rostering, FTL
- IATA NDC / ARC settlement

## Local Dev / Deploy

```bash
cd 60-apps/ai-gftd-project-open-airplane/worker
wrangler d1 create ai-gftd-open-airplane
e7m actor deploy .
```
