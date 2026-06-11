# etzhayyim-project-global — Global Resource Flow Intelligence Platform

## Identity

| Key | Value |
|---|---|
| **Domain** | `global.etzhayyim.com` *(planned)* |
| **Nanoid** | `w5n8p3q6` |
| **App path** | `appview/global-ui-w5n8p3q6/svelte/` |
| **3D viewer** | **Threlte** (`@threlte/core` + `@threlte/extras` + `@threlte/flex`) — Svelte wrapper around three.js |
| **Graph layout** | **d3** (`d3-force-3d` + `d3-interpolate` + `d3-scale`) for force-directed time-series flow visualization |

The canonical identity + scope is in `PROJECT.jsonld`; tool surface is in `MCP_TOOLS.md`. This file is a navigation breadcrumb for operators landing on the directory cold.

## Architecture (Threlte + d3 stack)

This app uses **Threlte** (not the religious-corp `@etzhayyim/kami-engine-sdk`) for its 3D visualization layer, paired with d3 force-directed layout for graph rendering. Same Threlte pattern as `60-apps/etzhayyim-project-cad/` (per its CLAUDE.md "3D viewer 標準は Threlte") and `60-apps/etzhayyim-project-sos/`. The three.js + `@threlte/*` + d3 deps in `appview/.../svelte/package.json` are documented design intent, NOT dead deps.

The SDK three-free cutover (ADR-2605264300) does NOT apply to this app:
- this app does NOT depend on `@etzhayyim/kami-engine-sdk` (no SDK in `package.json`)
- the religious-corp SDK retired its internal three.js renderer; Threlte is a separate Svelte 3D library that consumer apps may use directly

## Scope (from PROJECT.jsonld)

Global resource flow visualization platform using:
- App actors + graph theory + systems thinking
- Worldwide resource statistics aggregated by year
- Time-series flow inference
- Interactive 3D visualizations via Threlte

Three sub-applications documented:
- Global Systems View (`/systems`)
- Resource Flow Visualization (`/resource-flow`)
- Resource Explorer (`/resources`)

## MCP tool surface

`MCP_TOOLS.md` documents JSON-RPC 2.0 tools at `POST /api/mcp` (e.g., `global.list_resources`). The app exposes MCP for agent-driven exploration of resource data.

## Current state

`appview/.../svelte/src/App.svelte` is a "Vite entry scaffold after SvelteKit cleanup" placeholder. The Threlte viewer + actual resource-flow modeling are out-of-scope for the current scaffold; the deps are aspirationally configured for the documented R1+ implementation work.

## References

- `PROJECT.jsonld` — canonical identity (schema.org/Project)
- `MCP_TOOLS.md` — MCP tool surface
- `kotodama.jsonld` — kotodama actor manifest
- `OWNERS` — ownership metadata
- ADR-2605264300 (kami-engine-sdk three.js-free cutover) §2 — confirms this app's Threlte deps are KEEP not dead
- `60-apps/etzhayyim-project-cad/CLAUDE.md` — sibling Threlte-viewer pattern
- `60-apps/etzhayyim-project-sos/CLAUDE.md` — sibling Threlte-viewer pattern
