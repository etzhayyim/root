# legal-entity collector actor

LangServer worker for legal-entity registry collection processes.

Responsibilities:

- Fetch GLEIF LEI pages outside the Cloudflare/WASM edge.
- Fetch active country registry pages for JPN/GBR/FRA/NOR/DNK/FIN/EST/CZE/NZL/CHE/NLD/ISR outside the Cloudflare/WASM edge.
- Normalize records to `com.etzhayyim.apps.legalEntity.legalEntity`.
- Commit each page through `com.etzhayyim.apps.legalEntity.commitEntities`.

The legal-entity edge worker remains the XRPC contract and PDS write boundary.
