# media-gamers-ingest — one-shot bulk importer scripts

One-shot offline importers that feed `media-gamers.etzhayyim.com` via its XRPC endpoints.
Pacing + 3-attempt retry built in. **Do NOT turn these into cron jobs** — they hit
PDS `createRecord` at 200+ items/hour which is exactly the burst pattern that
triggered the 2026-04-18/19 RisingWave OOM spiral. Run locally, watch infra, stop
if Worker hangs.

## Scripts

| script | source | target NSID | ~rows |
|---|---|---|---|
| `pokedex.mjs` | Serebii pokédex | `com.etzhayyim.apps.media_gamers.knowledge.publishPokemon` | ~500 per game |
| `items.mjs` | Serebii items DB | `com.etzhayyim.apps.media_gamers.knowledge.publishGameItem` | ~150-180 per game |

## Usage

```bash
# Preflight — check RisingWave has no multi-minute slow queries + 503 rate <10/min.
KUBECONFIG=50-infra/linode/risingwave-iceberg/kubeconfig.yaml \
  kubectl top pod risingwave-compute-0 -n risingwave

# Run importer
BEARER_TOKEN=<your-pds-jwt> \
  node 70-tools/scripts/media-gamers-ingest/pokedex.mjs \
  --game pokemon-legends-z-a \
  --start 1 --end 50

# Resume on failure
node 70-tools/scripts/media-gamers-ingest/pokedex.mjs \
  --game pokemon-legends-z-a \
  --start 51 --end 100 \
  --state /tmp/pokedex-state.json
```

## Pacing (built-in, don't tune up)

- 2 req/s against Serebii (polite)
- 3s delay between PDS writes
- 3 attempt retry per record, 8s backoff
- exit code 1 if >30% records still fail after retries

## Why not a Worker cron?

Design E Follow-based input is the AT-native pattern for continuous ingestion:
scraper worker publishes to its own repo, media-gamers follows + `onCommit`.
That's a separate PR — builds its own kotodama.jsonld + DID + profile. Don't
build the cron scraper before infra is stable.
