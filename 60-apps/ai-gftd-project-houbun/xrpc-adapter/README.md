# houbun XRPC Adapter

CF Worker exposing 12 rw-free commands as XRPC endpoints.

## Endpoints

- `POST /xrpc/ai.gftd.houbun.registerStatute` — register statute
- `GET /xrpc/ai.gftd.houbun.getStatute` — statute by ID
- `GET /xrpc/ai.gftd.houbun.listStatutes` — paginated list
- `POST /xrpc/ai.gftd.houbun.registerArticle` — register article
- `GET /xrpc/ai.gftd.houbun.getArticle` — article by DID
- `POST /xrpc/ai.gftd.houbun.registerTreaty` — register treaty
- `GET /xrpc/ai.gftd.houbun.getTreaty` — treaty by ID
- `POST /xrpc/ai.gftd.houbun.recordAmendment` — record amendment
- `POST /xrpc/ai.gftd.houbun.ingestStatuteJpn` — Japanese statutes
- `POST /xrpc/ai.gftd.houbun.ingestStatuteUsa` — US statutes
- `POST /xrpc/ai.gftd.houbun.ingestEurLex` — EU legislation
- `POST /xrpc/ai.gftd.houbun.ingestTreatyUn` — UN treaties

## Deploy

```bash
wrangler deploy
```

See ADR-2605210000.
