// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 etzhayyim Japan株式会社 / etzhayyim. All rights reserved.
// Licensed under the Apache License, Version 2.0 — see LICENSE at repo root.

import { Hono } from "hono";
import {
  addMembership,
  addWorkspace,
  createTenant,
  getBlueprint,
  getOverview,
  getTenantSnapshot,
  listAudit,
  listPlans,
  listSubscriptions,
  listTenantSnapshots,
  listUsage,
  recordUsage,
  transitionSubscription,
} from "./open-saas-domain";

type AssetFetcher = {
  fetch(request: Request): Promise<Response>;
};

type Env = {
  Bindings: {
    ASSETS: AssetFetcher;
  };
};

const app = new Hono<Env>();

async function readJsonBody<T>(request: Request): Promise<T> {
  try {
    return (await request.json()) as T;
  } catch {
    throw new Error("request body must be valid JSON");
  }
}

app.get("/healthz", (c) =>
  c.json({
    ok: true,
    service: "open-saas-console-os4a5s1",
    timestamp: new Date().toISOString(),
  }),
);

app.get("/api/open-saas/blueprint", (c) => c.json(getBlueprint()));

app.get("/api/open-saas/overview", (c) => c.json(getOverview()));
app.get("/api/open-saas/plans", (c) => c.json({ items: listPlans() }));
app.get("/api/open-saas/tenants", (c) => c.json({ items: listTenantSnapshots() }));
app.get("/api/open-saas/tenants/:tenantId", (c) => {
  const snapshot = getTenantSnapshot(c.req.param("tenantId"));
  if (!snapshot) return c.json({ error: "tenantNotFound" }, 404);
  return c.json(snapshot);
});
app.post("/api/open-saas/tenants", async (c) => {
  try {
    const created = createTenant(
      await readJsonBody<{
        name: string;
        ownerEmail: string;
        planId: string;
        workspaceName?: string;
      }>(c.req.raw),
    );
    return c.json(created, 201);
  } catch (error) {
    return c.json({ error: error instanceof Error ? error.message : "tenant create failed" }, 400);
  }
});
app.post("/api/open-saas/tenants/:tenantId/workspaces", async (c) => {
  try {
    const workspace = addWorkspace(
      c.req.param("tenantId"),
      await readJsonBody<{
        name: string;
        region: string;
        environment: "production" | "staging" | "sandbox";
        seatLimit: number;
      }>(c.req.raw),
    );
    return c.json(workspace, 201);
  } catch (error) {
    return c.json({ error: error instanceof Error ? error.message : "workspace create failed" }, 400);
  }
});
app.post("/api/open-saas/tenants/:tenantId/memberships", async (c) => {
  try {
    const membership = addMembership(
      c.req.param("tenantId"),
      await readJsonBody<{
        workspaceId: string;
        email: string;
        role: "owner" | "billing-admin" | "operator" | "member";
      }>(c.req.raw),
    );
    return c.json(membership, 201);
  } catch (error) {
    return c.json({ error: error instanceof Error ? error.message : "membership create failed" }, 400);
  }
});
app.get("/api/open-saas/subscriptions", (c) => c.json({ items: listSubscriptions() }));
app.post("/api/open-saas/subscriptions/:subscriptionId/transition", async (c) => {
  try {
    const updated = transitionSubscription({
      subscriptionId: c.req.param("subscriptionId"),
      ...(await readJsonBody<{ status: "trial" | "active" | "grace" | "paused" | "canceled"; actor: string; reason: string }>(c.req.raw)),
    });
    return c.json(updated);
  } catch (error) {
    return c.json({ error: error instanceof Error ? error.message : "subscription transition failed" }, 400);
  }
});
app.get("/api/open-saas/usage", (c) => c.json({ items: listUsage(c.req.query("tenantId") || undefined) }));
app.post("/api/open-saas/usage", async (c) => {
  try {
    const usage = recordUsage(
      await readJsonBody<{
        tenantId: string;
        workspaceId: string;
        metric: "automation-runs" | "seats" | "api-calls";
        quantity: number;
      }>(c.req.raw),
    );
    return c.json(usage, 201);
  } catch (error) {
    return c.json({ error: error instanceof Error ? error.message : "usage record failed" }, 400);
  }
});
app.get("/api/open-saas/audit", (c) => {
  const limit = Number(c.req.query("limit") || "20");
  return c.json({ items: listAudit(c.req.query("tenantId") || undefined, Number.isFinite(limit) ? limit : 20) });
});

app.all("/api/*", (c) =>
  c.json(
    {
      error: "notFound",
      path: new URL(c.req.url).pathname,
    },
    404,
  ),
);

app.all("*", async (c) => {
  const response = await c.env.ASSETS.fetch(c.req.raw);
  if (response.status !== 404) return response;
  return c.env.ASSETS.fetch(
    new Request(new URL("/", c.req.url).toString(), {
      method: "GET",
      headers: c.req.raw.headers,
    }),
  );
});

export default app;
