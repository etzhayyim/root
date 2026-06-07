# etzhayyim-project-advectors

LLM-first ad project for:

- grounded ad submission (text/image)
- policy-aware ad delivery
- split routing on `advectors.etzhayyim.com`

## Components

1. `advectors-submit-mcp-component`
- Handles ad submission.
- Text flow: builds drafts from `publisher_refs`.
- Image flow: builds generation prompts with publisher context.
- Exposes MCP (`/api/mcp`) and REST (`/api/v1/submit/*`).

2. `advectors-delivery-mcp-component`
- Registers approved creatives for serving.
- Serves ads and collects impression/click telemetry.
- Exposes REST (`/api/v1/register`, `/api/v1/serve`, `/api/v1/impression`, `/api/v1/click`, `/api/v1/metrics`).

## Host Routing (`advectors.etzhayyim.com`)

- Submit paths:
  - `/api/v1/submit/*`
  - `/api/v1/submissions/*`
  - `/api/mcp`
- Delivery paths:
  - `/api/v1/register`
  - `/api/v1/serve`
  - `/api/v1/impression`
  - `/api/v1/click`
  - `/api/v1/metrics`

## Submission -> Delivery contract

Submit responses include `delivery_payload`:

```json
{
  "campaign_id": "camp-...",
  "creative_type": "text|image",
  "grounding_summary": "...",
  "publisher_refs": [],
  "text_creative": {},
  "image_creative": {}
}
```

Delivery accepts the same shape (with required fields) at `POST /api/v1/register`.

## Namespace and image conventions

- WADM namespace: `kotodama-runtime`
- Route backend namespace: `kotodama-system`
- Image registry: `ghcr.io/etzhayyim/*`
