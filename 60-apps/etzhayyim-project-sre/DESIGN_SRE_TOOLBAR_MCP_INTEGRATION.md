# SRE Toolbar MCP + Svelte Component Integration Design

## Goal

Prepare `60-apps/etzhayyim-project-sre` deployment flow with:

1. Shared Svelte components extracted from `extension`.
2. `etzhayyim-project-sre-toolbar` integrated into common `components` so other Svelte apps can reuse it.
3. All API access migrated to MCP only (no REST-style or direct service `fetch`).

## Current State (inventory)

- Toolbar UI exists only in extension component:
  - `60-apps/etzhayyim-project-sre/extension/src/lib/components/SreToolbar.svelte`
- Extension content script injects custom element:
  - `60-apps/etzhayyim-project-sre/extension/src/content/toolbar.ts`
- Toolbar feedback currently uses direct HTTP `fetch` to service URL:
  - `60-apps/etzhayyim-project-sre/extension/src/lib/components/SreToolbar.svelte`
- Toolbar backend proto defines RPCs (`SubmitFeedback`, `GetSystemStatus`, `UpdateTheme`):
  - `60-apps/etzhayyim-project-sre/legacy-runtime/sre-5q1z8oag/proto/toolbar.proto`
- Existing MCP pattern exists in another performer (`serveMCP` with tools):
  - `60-apps/etzhayyim-project-sre/legacy-runtime/etzhayyim-performer-sys-activity--monitor/cmd/actor/main.go`

## Target Architecture

### 1) Shared Svelte UI module

Create reusable Svelte toolbar module under SRE project and consume it from extension + SvelteKit UI.

Proposed structure:

- `60-apps/etzhayyim-project-sre/shared/sre-toolbar-ui/`
- `60-apps/etzhayyim-project-sre/shared/sre-toolbar-ui/src/components/SreToolbarShell.svelte`
- `60-apps/etzhayyim-project-sre/shared/sre-toolbar-ui/src/components/SystemStatusTab.svelte`
- `60-apps/etzhayyim-project-sre/shared/sre-toolbar-ui/src/components/FeedbackTab.svelte`
- `60-apps/etzhayyim-project-sre/shared/sre-toolbar-ui/src/components/PerfTab.svelte`
- `60-apps/etzhayyim-project-sre/shared/sre-toolbar-ui/src/index.ts`

Rules:

- Keep presentational components pure (no direct network calls).
- Accept `props` + event callbacks only.
- Keep custom element wrapper only in extension adapter layer.

### 2) Adapter per runtime

- Extension adapter:
  - keeps `<svelte:options customElement="etzhayyim-project-sre-toolbar" />`
  - owns Clerk token bridge and page injection
  - imports shared `SreToolbarShell`

- SvelteKit adapter (`wasm/sre-ui-7bjdh9p3/svelte`):
  - imports same shared toolbar component in `src/lib/components`
  - can render demo/live toolbar in `+page.svelte`

### 3) MCP-only service layer

Introduce frontend MCP client and remove direct service URL calls.

Proposed frontend module:

- `60-apps/etzhayyim-project-sre/shared/sre-toolbar-ui/src/mcp/client.ts`
- `60-apps/etzhayyim-project-sre/shared/sre-toolbar-ui/src/mcp/toolbar.ts`

Client responsibilities:

- `listTools()` and `callTool(name, args)`
- auth header propagation (Bearer token)
- consistent error shape for UI

## MCP Tool Contract

Map current capabilities to MCP tools:

1. `sre_toolbar.submit_feedback`
- input: `{ content, page_url, component_id, user_id? }`
- result: `{ feedback_id, status }`

2. `sre_toolbar.get_system_status`
- input: `{ component_id }`
- result: `{ status, version, components[] }`

3. `sre_toolbar.update_theme`
- input: `{ theme }`
- result: `{ success }`

Design notes:

- Use stable snake_case field names in tool args/results.
- Keep tool outputs aligned with UI state shape to reduce adapter code.

## Backend Changes (legacy runtime performer)

Target actor:

- `60-apps/etzhayyim-project-sre/legacy-runtime/sre-5q1z8oag/cmd/actor/main.go`

Changes:

1. Add MCP server entrypoint (same binary mode switch pattern as monitor actor).
2. Implement `ListTools` + `CallTool` handlers (or equivalent with mcp-go server helpers).
3. Reuse existing business logic currently behind proto RPC handlers.
4. Keep ConnectRPC temporarily only during migration window; then disable non-MCP ingress.

Optional stronger end-state:

- expose only `/api/mcp/*` at gateway and return `410` for old non-MCP API paths.

## Frontend Migration Plan

1. Extract UI from `extension/src/lib/components/SreToolbar.svelte` into shared components.
2. Keep extension wrapper component minimal (custom element + token bridge).
3. Replace direct `fetch` submit call with MCP tool call in shared service module.
4. Add status/theme MCP reads so all tabs are MCP-backed.
5. In SvelteKit UI (`cdn/sre-ui-7bjdh9p3`), import shared component under `src/lib/components` and mount as reusable toolbar block.

## etzhayyim Deploy Design

Deploy units:

1. Static UI
- `60-apps/etzhayyim-project-sre/wasm/sre-ui-7bjdh9p3/svelte/etzhayyim.json`

2. Toolbar MCP backend
- evolve `60-apps/etzhayyim-project-sre/legacy-runtime/sre-5q1z8oag/etzhayyim.json`
- recommended final type: MCP-oriented App manifest (similar to existing MCP projects in repo)
- include route host for MCP endpoint and health checks

3. Extension artifact
- built by Vite and published as static downloadable asset from SRE UI

Rollout order:

1. Deploy MCP backend first.
2. Deploy Svelte UI consuming shared components.
3. Publish extension build consuming same shared components and MCP client.
4. Remove legacy direct endpoint usage.

## Validation Checklist

### Static checks

- `rg -n "fetch\(" 60-apps/etzhayyim-project-sre/extension/src`
- confirm no direct service URL calls remain
- allow only MCP client transport calls

### Runtime checks

- Tool discovery works (`ListTools`) with expected 3 tools.
- `submit_feedback` returns success from extension and SvelteKit UI.
- toolbar renders correctly in both:
  - extension custom element
  - SvelteKit page component

### Build/deploy checks

- extension build passes (`vite build`)
- SvelteKit check/build passes (`svelte-check`, `vite build`)
- actor build/test passes (`go test ./...` for target performer)
- `mage Deploy` dry-run and deploy succeed for CDN + legacy runtime units

## Risks and Mitigations

1. Risk: mixed protocol drift (ConnectRPC + MCP both active too long)
- Mitigation: define cutover date and remove old handlers in same release train.

2. Risk: extension auth token bridge mismatch with MCP gateway auth
- Mitigation: unify auth header contract in one shared MCP client.

3. Risk: duplicated UI logic between extension and SvelteKit
- Mitigation: strict shared component ownership; adapters only for runtime glue.

## Implementation Phases

1. Phase A: Shared components extraction + adapters.
2. Phase B: MCP server tools on toolbar backend.
3. Phase C: Frontend MCP migration and removal of direct calls.
4. Phase D: deployment updates and final protocol cleanup.
