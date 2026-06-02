# media-gamers guide actor

LangServer worker for `media_gamers_guide_generate`.

Responsibilities:

- Resolve guide targets from LangServer run variables.
- Generate English guide bodies with Murakumo/OpenAI-compatible inference.
- Translate title/body into Pattern C target languages.
- Draft social posts.
- Commit final records through `com.etzhayyim.apps.media_gamers.guide.commitGuide`.

Cloudflare worker responsibility is intentionally thin: validate XRPC input, write AT/PDS records, create sub-DIDs, and publish social posts.

Required env:

- `AGENTGATEWAY_MCP_URL`
- `MEDIA_GAMERS_COMMIT_GUIDE_URL`
- `MURAKUMO_OPENAI_URL`
- `MURAKUMO_API_KEY`
- `MURAKUMO_MODEL`

Optional fallback env:

- `RUNPOD_OPENAI_URL`
- `RUNPOD_API_KEY`
- `RUNPOD_MODEL`
