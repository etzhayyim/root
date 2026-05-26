# gameka XRPC Adapter

CF Worker that exposes the 13 rw-free commands as XRPC endpoints.

## Endpoints

- `GET /xrpc/app.etzhayyim.gameka.getGameSpec?gameId=...` — spec + metadata
- `GET /xrpc/app.etzhayyim.gameka.listGameSpecs?limit=...` — paginated specs
- `GET /xrpc/app.etzhayyim.gameka.getBuildArtifact?artifactId=...` — artifact
- `GET /xrpc/app.etzhayyim.gameka.listBuildArtifacts?limit=...` — artifacts
- `GET /xrpc/app.etzhayyim.gameka.getGameQa?qaId=...` — QA record
- `GET /xrpc/app.etzhayyim.gameka.listGameQas?limit=...` — QA logs
- `GET /xrpc/app.etzhayyim.gameka.getGameTitle?titleId=...` — title
- `GET /xrpc/app.etzhayyim.gameka.listGameTitles?limit=...` — titles
- `POST /xrpc/app.etzhayyim.gameka.generateGame` — generate game
- `POST /xrpc/app.etzhayyim.gameka.proposeGame` — propose game
- `POST /xrpc/app.etzhayyim.gameka.playtestGame` — playtest
- `POST /xrpc/app.etzhayyim.gameka.publishGame` — publish
- `POST /xrpc/app.etzhayyim.gameka.tickStudio` — trend tick

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
