---
id: 2605160800
title: "Itonami Lifecycle Dashboard and Pregel UI Alignment"
status: accepted
doc_type: adr
topic: itonami-lifecycle-dashboard-pregel-ui
date: 2026-05-16
---
# ADR 2605160800: Itonami Lifecycle Dashboard and Pregel UI Alignment

## Status
Accepted

## Context
The project requires a unified dashboard to visualize the end-to-end lifecycle of an aircraft, traversing through design (Kami), procurement (Open-UNSPSC/ISIC), assembly and testing (Robotics), and operation (Digital Twin flight tracking). We needed to decide on the UI architecture and how it integrates with the underlying LangGraph (Pregel) orchestrator.

## Decision
1. **Domain Name**: We selected `itonami.etzhayyim.com` (営み) as the canonical domain, reflecting the continuous, interconnected human, robotic, and data-driven activities of the lifecycle.
2. **UI Architecture (Modular Dashboard)**: We adopted a "Modular Dashboard" approach over a single immersive 3D canvas. The left sidebar acts as a Pregel Timeline, explicitly visualizing the LangGraph "Supersteps" and State updates. The main content area dynamically switches widgets based on the active phase (e.g., 3D CAD viewer for Design, data grids for Procurement, metrics/3D for Testing, and MapLibre for Operation).
3. **Physical Simulation Visualization**: The Testing phase utilizes a native Three.js WebGL canvas (bypassing Threlte due to Svelte 5 compatibility issues) to render a 3D turbofan engine that visually reacts (heat glow, vibration shake) in real-time to streaming physical metrics.
4. **Routing Gateway Exception**: Since the dashboard is hosted on Cloudflare Pages (`etzhayyim-project-itonami.pages.dev`), we updated the `routing-gateway` Cloudflare Worker at `*.etzhayyim.com` to passthrough requests for `itonami` while stripping the `Host` header to prevent Cloudflare 522 infinite loop timeouts.

## Consequences
- **Positive**: The UI perfectly mirrors the discrete, step-by-step nature of LangGraph's Pregel architecture, making the agent's workflow transparent and interactive.
- **Positive**: Native Three.js integration avoids bleeding-edge framework compatibility issues while delivering high-performance, real-time physical simulation visual feedback.
- **Negative/Risk**: Adding explicit passthrough rules in the `routing-gateway` requires manual maintenance for new Cloudflare Pages apps hosted on `*.etzhayyim.com` subdomains that aren't formal AT Protocol actors.
