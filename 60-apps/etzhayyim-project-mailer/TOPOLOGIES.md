# Mailer Topologies

## 1) Current Runtime Topology (2026-04-14)

### Public Entry Points
- `mailer.etzhayyim.com` / `etzhayyim-project-mailer.etzhayyim.com` / `a8wwtz73.etzhayyim.com`
  - UI + XRPC proxy (`mailer-mcp-component` Worker)
- `*@etzhayyim.com` inbound SMTP
  - Cloudflare Email Routing -> `etzhayyim-email-relay` Worker `email()` handler

### Service/Data Topology
- `email-relay` (account-level Worker)
  - Reads inbound MIME
  - Resolves/creates email<->DID binding
  - Writes records to PDS collections:
    - `ai.etzhayyim.apps.mailer.inboundEmail`
    - `ai.etzhayyim.apps.mailer.emailBinding`
    - `ai.etzhayyim.apps.mailer.inboundEmailStatus`
  - Publishes to projector convo APIs
  - Stores relay state in `EMAIL_STATE` KV
- `mailer-mcp-component` (appview Worker)
  - Serves static assets
  - Proxies `ai.etzhayyim.apps.mailer.*` XRPC calls to the BPMN dispatcher
  - Falls through non-mailer `/xrpc/*` calls to the PDS origin

### Trust Boundaries
- Boundary A: Internet -> Cloudflare edge Workers
- Boundary B: Worker -> BPMN dispatcher / PDS origin
- Boundary C: Worker -> `EMAIL_STATE` KV
- Boundary D: Worker -> Resend API (debug/test flow only)

## 2) Security Topology (Target)

### Control Plane (Admin)
- Admin API operations (`register-email`, `bindings`)
  - Requires shared admin token (`ADMIN_API_TOKEN`)

### Data Plane (Inbound Mail)
- Email payload protection at write time
  - `fromAddress`, `toLocal`, `subject`, `bodyText`, `headersJson` are stored encrypted
  - Uses AES-256-GCM with `DATA_ENCRYPTION_KEY` (base64, 32 bytes)
  - Hash fields kept for lookup/analytics (`fromAddressHash`, `toLocalHash`)

### State/Telemetry Plane
- Public status endpoint (`GET /`) returns only minimal health/count
- `EMAIL_STATE:last` stores redacted operational summary, not full PII payload

## 3) Operational Notes
- Required secrets for secure operation:
  - `ADMIN_API_TOKEN`
  - `DATA_ENCRYPTION_KEY`
- Recommended policy:
  - `APP_ENV=production`
- Archived endpoints:
  - `_archive/50-infra/cloudflare/workers/email-relay/2026-04-14-removed-debug-routes.md`
