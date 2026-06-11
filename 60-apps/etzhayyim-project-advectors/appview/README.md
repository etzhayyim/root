# etzhayyim-project-advectors App layout

`etzhayyim-project-advectors` provides two App components under `advectors.etzhayyim.com`:

- `advectors-submit-mcp-component`
  - Handles ad submission workflows.
  - Text ads are grounded with explicit publisher references.
  - Image ads produce generation prompts that include publisher context.

- `advectors-delivery-mcp-component`
  - Handles creative registration for serving.
  - Serves ads and records impression/click telemetry.

## Endpoint split on advectors.etzhayyim.com

- Submit: `/api/v1/submit/*`, `/api/v1/submissions/*`, `/api/mcp`
- Delivery: `/api/v1/register`, `/api/v1/serve`, `/api/v1/impression`, `/api/v1/click`, `/api/v1/metrics`

## Release flow

1. `etzhayyim build`
2. `oras push ghcr.io/etzhayyim/<component>:<tag> build/<component>.wasm`
3. `mage Deploy WADM_MANIFEST=wadm/<name>.wadm.yaml LATTICE=default`
4. `kubectl apply -f k8s/http-routes.yaml`
