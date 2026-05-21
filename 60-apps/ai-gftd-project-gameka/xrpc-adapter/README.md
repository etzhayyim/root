# gameka XRPC Adapter

CF Worker that exposes the 13 rw-free commands as XRPC endpoints.

## Endpoints

- `GET /xrpc/ai.gftd.gameka.getGameSpec?gameId=...` — spec + metadata
- `GET /xrpc/ai.gftd.gameka.listGameSpecs?limit=...` — paginated specs
- `GET /xrpc/ai.gftd.gameka.getBuildArtifact?artifactId=...` — artifact
- `GET /xrpc/ai.gftd.gameka.listBuildArtifacts?limit=...` — artifacts
- `GET /xrpc/ai.gftd.gameka.getGameQa?qaId=...` — QA record
- `GET /xrpc/ai.gftd.gameka.listGameQas?limit=...` — QA logs
- `GET /xrpc/ai.gftd.gameka.getGameTitle?titleId=...` — title
- `GET /xrpc/ai.gftd.gameka.listGameTitles?limit=...` — titles
- `POST /xrpc/ai.gftd.gameka.generateGame` — generate game
- `POST /xrpc/ai.gftd.gameka.proposeGame` — propose game
- `POST /xrpc/ai.gftd.gameka.playtestGame` — playtest
- `POST /xrpc/ai.gftd.gameka.publishGame` — publish
- `POST /xrpc/ai.gftd.gameka.tickStudio` — trend tick

## Setup

```bash
cd 60-apps/ai-gftd-project-gameka/xrpc-adapter
npm install && npm run dev
```

## Deploy

```bash
wrangler deploy
```

See ADR-2605210000 for design context.
