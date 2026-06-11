# mehikari (眼光り)

JP 警察向け監視カメラ シーン/人物検索 + B2G 営業 LangGraph。

- **設計**: `_working/mehikari/DESIGN.md`
- **法令ガード**: `_working/mehikari/COMPLIANCE-MEMO.md`
- **営業 pipeline**: `_working/mehikari/LEAD-PIPELINE-SEED.md`
- **国内拘束**: `_working/mehikari/MURAKUMO-DOMESTIC-CONSTRAINT.md`
- **CLAUDE.md**: `60-apps/etzhayyim-project-mehikari/CLAUDE.md`

## Status

Phase 0 (法務 / プロトタイプ)。本 Worker は法務クリア前は deploy しない。

## Operating entity

- 運営 = etzhayyim (operating entity)
- 開発受託 = etzhayyim Japan株式会社 (vendor)

## Domains

| Subdomain | Role |
|---|---|
| `mehikari.etzhayyim.com` | XRPC + Svelte appview (operator UI, opt-in form, unsubscribe) |
| `mhk7r2vq.etzhayyim.com` | direct route (development) |
| `reply.mehikari.etzhayyim.com` | inbound email worker (replies → handleInboundReply) |
