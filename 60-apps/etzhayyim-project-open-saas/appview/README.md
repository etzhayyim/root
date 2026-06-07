# open-saas appview

`open-saas-console-os4a5s1` は、OSS SaaS の設計を可視化するための appview です。

- `/`: ランディング兼コントロールプレーン UI
- `/api/open-saas/blueprint`: 設計ブループリント
- `/api/open-saas/demo-tenants`: デモ tenant 一覧
- `/healthz`: ヘルスチェック

## salesforce-crm-sfcrm9x3

Salesforce 相当の OSS CRM appview (M2.5)。

- Lexicons: `00-contracts/lexicons/com/etzhayyim/apps/opensaas/salesforce/` (account, contact, lead, opportunity, case, activity, createLead, convertLead, listPipeline)
- Route: `https://salesforce.opensaas.etzhayyim.com/`
- Tenancy: `did:web:<slug>.opensaas.etzhayyim.com` per tenant, seat DID = `did:web:<slug>.opensaas.etzhayyim.com:seat:<role>-<nn>`
- PII split (ADR-0018): emailHash / phoneHash を Tier 1 AT Record、raw PII は Tier 3 Preferences
- Write-Only Derived (η=100%): opportunity.stage / case.status / lead→converted の変化で `activity` を `kotodama.jsonld` derive rule が自動生成

API:

- `GET /api/salesforce/overview`
- `GET /api/salesforce/pipeline?tenantDid=...`
- `GET /api/salesforce/{accounts,contacts,leads,cases,activities}`
- `POST /api/salesforce/leads` — createLead (emailHash は `sha256:<hex>` 必須、raw PII は拒否)
- `POST /api/salesforce/leads/convert` — convertLead (Account+Contact+Opportunity 原子書き込み)
- `POST /api/salesforce/opportunities/:uri/stage` — stage 遷移 (activity 自動派生)

ローカル:

```sh
pnpm exec wrangler dev --config 60-apps/etzhayyim-project-open-saas/appview/salesforce-crm-sfcrm9x3/wrangler.jsonc
```
