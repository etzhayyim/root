// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 etzhayyim Japan株式会社 / etzhayyim. All rights reserved.
// Licensed under the Apache License, Version 2.0 — see LICENSE at repo root.

// etzhayyim-project-open-cofog — UN COFOG (Classification of the Functions of
// Government, 1999/2014) open taxonomy.
//
// 4 XRPC methods under com.etzhayyim.apps.openCofog.*:
//   listDivisions  (query) — 10 divisions (01–10)
//   listGroups     (query) — ~65 groups, filterable by division
//   listClasses    (query) — 4-digit classes, filterable by division/group
//   getClass       (query) — one class with full description + includes/excludes
//
// 4-digit classes are loaded from data/classes/*.json. Each class is added
// one-at-a-time by PR (one per 10-min iteration), mirroring open-isic.
//
// DID pattern:
//   did:web:open-cofog.etzhayyim.com:{division|group|class}:{code}

import {
  DIVISIONS, GROUPS,
  didForDivision, didForGroup, didForClass,
  divisionOf, groupOf,
} from "./taxonomy";
import { CLASSES, IMPLEMENTED_COUNT, TOTAL_CLASSES } from "./classes-index";

export interface Env {
  PDS?: Fetcher;
  APP_HANDLE: string;
  PRIMARY_DID: string;
}

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
}
const err = (error: string, message: string, status = 400) =>
  json({ error, message }, status);

function listDivisions(): Response {
  return json({
    divisions: DIVISIONS.map((d) => ({ ...d, did: didForDivision(d.code) })),
  });
}

function listGroups(params: URLSearchParams): Response {
  const division = params.get("division");
  const groups = GROUPS
    .filter((g) => !division || g.division === division)
    .map((g) => ({ ...g, did: didForGroup(g.code) }));
  return json({ groups, total: groups.length });
}

function listClasses(params: URLSearchParams): Response {
  const division = params.get("division");
  const group = params.get("group");
  const limit = Math.min(500, Math.max(1, Number(params.get("limit") ?? 50)));
  const offset = Math.max(0, Number(params.get("offset") ?? 0));

  const all = Object.values(CLASSES)
    .map((c) => ({
      code: c.code,
      did: didForClass(c.code),
      nameEn: c.nameEn,
      division: divisionOf(c.group),
      group: c.group,
    }))
    .filter((c) => (!division || c.division === division)
                && (!group || c.group === group));

  return json({
    classes: all.slice(offset, offset + limit),
    total: all.length,
    offset,
    limit,
  });
}

function getClass(params: URLSearchParams): Response {
  const code = params.get("code");
  if (!code) return err("InvalidRequest", "code required");
  const c = CLASSES[code];
  if (!c) {
    return err(
      "NotFound",
      `class ${code} not yet implemented (${IMPLEMENTED_COUNT}/${TOTAL_CLASSES})`,
      404,
    );
  }
  const division = divisionOf(c.group);
  const divisionEntry = DIVISIONS.find((d) => d.code === division);
  const groupEntry = GROUPS.find((g) => g.code === c.group);
  return json({
    code: c.code,
    did: didForClass(c.code),
    nameEn: c.nameEn,
    division,
    divisionNameEn: divisionEntry?.nameEn ?? "",
    group: c.group,
    groupNameEn: groupEntry?.nameEn ?? "",
    description: c.description,
    includes: c.includes ?? [],
    excludes: c.excludes ?? [],
    cofogVersion: "1999 (rev. 2014)",
    implementedAt: c.implementedAt,
  });
}

export default {
  async fetch(req: Request, env: Env): Promise<Response> {
    try {
      const url = new URL(req.url);
      if (url.pathname === "/health" || url.pathname === "/_worker/health") {
        return json({
          ok: true,
          did: env.PRIMARY_DID,
          progress: `${IMPLEMENTED_COUNT}/${TOTAL_CLASSES}`,
        });
      }
      if (url.pathname === "/_app/meta") {
        return json({
          did: env.PRIMARY_DID,
          handle: env.APP_HANDLE,
          xrpc: [
            "com.etzhayyim.apps.openCofog.listDivisions",
            "com.etzhayyim.apps.openCofog.listGroups",
            "com.etzhayyim.apps.openCofog.listClasses",
            "com.etzhayyim.apps.openCofog.getClass",
          ],
          cofogVersion: "1999 (rev. 2014)",
          divisions: DIVISIONS.length,
          groups: GROUPS.length,
          classesImplemented: IMPLEMENTED_COUNT,
          classesTotal: TOTAL_CLASSES,
        });
      }

      if (!url.pathname.startsWith("/xrpc/"))
        return err("InvalidRequest", "only /xrpc/*", 404);
      const nsid = url.pathname.slice("/xrpc/".length);
      if (req.method !== "GET") return err("InvalidRequest", "GET only", 405);
      switch (nsid) {
        case "com.etzhayyim.apps.openCofog.listDivisions": return listDivisions();
        case "com.etzhayyim.apps.openCofog.listGroups":    return listGroups(url.searchParams);
        case "com.etzhayyim.apps.openCofog.listClasses":   return listClasses(url.searchParams);
        case "com.etzhayyim.apps.openCofog.getClass":      return getClass(url.searchParams);
        default: return err("InvalidRequest", `unknown NSID: ${nsid}`, 404);
      }
    } catch (e: any) {
      return err("InternalError", e?.message ?? String(e), 500);
    }
  },
};
