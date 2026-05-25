# houbun XRPC Adapter

CF Worker exposing 12 rw-free commands as XRPC endpoints.

## Endpoints

- `POST /xrpc/app.etzhayyim.houbun.registerStatute` — register statute
- `GET /xrpc/app.etzhayyim.houbun.getStatute` — statute by ID
- `GET /xrpc/app.etzhayyim.houbun.listStatutes` — paginated list
- `POST /xrpc/app.etzhayyim.houbun.registerArticle` — register article
- `GET /xrpc/app.etzhayyim.houbun.getArticle` — article by DID
- `POST /xrpc/app.etzhayyim.houbun.registerTreaty` — register treaty
- `GET /xrpc/app.etzhayyim.houbun.getTreaty` — treaty by ID
- `POST /xrpc/app.etzhayyim.houbun.recordAmendment` — record amendment
- `POST /xrpc/app.etzhayyim.houbun.ingestStatuteJpn` — Japanese statutes
- `POST /xrpc/app.etzhayyim.houbun.ingestStatuteUsa` — US statutes
- `POST /xrpc/app.etzhayyim.houbun.ingestEurLex` — EU legislation
- `POST /xrpc/app.etzhayyim.houbun.ingestTreatyUn` — UN treaties

## Deploy

```bash
wrangler deploy
```

See ADR-2605210000.
