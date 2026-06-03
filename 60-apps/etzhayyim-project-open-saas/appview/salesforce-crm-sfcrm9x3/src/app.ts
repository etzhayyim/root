// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 etzhayyim Japan株式会社 / etzhayyim. All rights reserved.
// Licensed under the Apache License, Version 2.0 — see LICENSE at repo root.

import { Hono } from "hono";
import {
  advanceStage,
  convertLead,
  createLead,
  getBlueprint,
  getOverview,
  listAccounts,
  listActivities,
  listCases,
  listContacts,
  listLeads,
  listPipeline,
} from "./salesforce-domain";

type AssetFetcher = { fetch(request: Request): Promise<Response> };
type Env = { Bindings: { ASSETS: AssetFetcher } };

const app = new Hono<Env>();

async function readJsonBody<T>(request: Request): Promise<T> {
  try {
    return (await request.json()) as T;
  } catch {
    throw new Error("request body must be valid JSON");
  }
}

app.get("/healthz", (c) =>
  c.json({ ok: true, service: "salesforce-crm-sfcrm9x3", timestamp: new Date().toISOString() }),
);

app.get("/api/salesforce/blueprint", (c) => c.json(getBlueprint()));
app.get("/api/salesforce/overview", (c) => c.json(getOverview()));

app.get("/api/salesforce/accounts", (c) => c.json({ items: listAccounts() }));
app.get("/api/salesforce/contacts", (c) =>
  c.json({ items: listContacts(c.req.query("accountDid") || undefined) }),
);

app.get("/api/salesforce/leads", (c) => {
  const status = c.req.query("status") as Parameters<typeof listLeads>[0];
  return c.json({ items: listLeads(status) });
});
app.post("/api/salesforce/leads", async (c) => {
  try {
    const lead = createLead(await readJsonBody(c.req.raw));
    return c.json(lead, 201);
  } catch (error) {
    return c.json({ error: error instanceof Error ? error.message : "createLead failed" }, 400);
  }
});
app.post("/api/salesforce/leads/convert", async (c) => {
  try {
    return c.json(convertLead(await readJsonBody(c.req.raw)));
  } catch (error) {
    return c.json({ error: error instanceof Error ? error.message : "convertLead failed" }, 400);
  }
});

app.get("/api/salesforce/pipeline", (c) => {
  const tenantDid = c.req.query("tenantDid");
  if (!tenantDid) return c.json({ error: "tenantDid required" }, 400);
  const limit = Number(c.req.query("limit") || "50");
  const offset = Number(c.req.query("offset") || "0");
  return c.json(
    listPipeline({
      tenantDid,
      ownerDid: c.req.query("ownerDid") || undefined,
      stage: c.req.query("stage") as Parameters<typeof listPipeline>[0]["stage"],
      forecastCategory: c.req.query("forecastCategory") as Parameters<typeof listPipeline>[0]["forecastCategory"],
      limit: Number.isFinite(limit) ? limit : 50,
      offset: Number.isFinite(offset) ? offset : 0,
    }),
  );
});

app.post("/api/salesforce/opportunities/:uri/stage", async (c) => {
  try {
    const body = await readJsonBody<{ stage: Parameters<typeof advanceStage>[0]["stage"]; actorDid?: string }>(c.req.raw);
    return c.json(advanceStage({ opportunityUri: decodeURIComponent(c.req.param("uri")), ...body }));
  } catch (error) {
    return c.json({ error: error instanceof Error ? error.message : "advanceStage failed" }, 400);
  }
});

app.get("/api/salesforce/cases", (c) => {
  const status = c.req.query("status") as Parameters<typeof listCases>[0];
  return c.json({ items: listCases(status) });
});

app.get("/api/salesforce/activities", (c) => {
  const limit = Number(c.req.query("limit") || "50");
  return c.json({ items: listActivities(Number.isFinite(limit) ? limit : 50) });
});

app.all("/api/*", (c) =>
  c.json({ error: "notFound", path: new URL(c.req.url).pathname }, 404),
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
