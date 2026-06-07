/**
 * did:etzhayyim Resolver Worker — `did.etzhayyim.com` HTTP surface.
 *
 * Implements W3C DID Resolution v0.3 for the did:etzhayyim method (ADR-0029).
 *
 * Endpoints:
 *   GET  /1.0/identifiers/{did}              → application/did+ld+json (resolution result)
 *   GET  /{did}                              → alias of above
 *   GET  /{did}/log                          → application/json (op log, newest first)
 *   GET  /{did}/path-context                 → application/json (platform extension: graph metadata)
 *   POST /                                   → 501 — submit ops via PDS XRPC com.etzhayyim.identity.submitOp
 *   GET  /health                             → "ok"
 *
 * Storage: HYPERDRIVE (RisingWave) + Kysely. Tables:
 *   - vertex_etzhayyim_identity      (DID + path metadata)
 *   - vertex_etzhayyim_op_log        (signed op history)
 *   - edge_etzhayyim_path_child      (path lineage)
 */

import {
  isValidDidetzhayyim,
  didDepth,
  resolutionOk,
  resolutionErr,
  buildDidDocument,
  type DidetzhayyimDocument,
} from "../src/index";
import { createKyselyDb, sql } from "@etzhayyim/kotodama-host-sdk/kysely";

export interface Env {
  HYPERDRIVE: Hyperdrive;
}

interface IdentityRow {
  did: string;
  controller_did: string | null;
  root_did: string | null;
  parent_did: string | null;
  path_segment: string | null;
  depth: number | null;
  public_key_multibase: string | null;
  authentication_methods: string | null;
  status: string | null;
  created_at: string | null;
  updated_at: string | null;
  genesis_op_cid: string | null;
}

function rowToDoc(row: IdentityRow): DidetzhayyimDocument {
  const vms = row.public_key_multibase
    ? [{ id: "#key-1" as const, type: "Multikey" as const, publicKeyMultibase: row.public_key_multibase }]
    : [];
  const aka = row.authentication_methods ? safeJsonArray(row.authentication_methods) : undefined;
  return buildDidDocument(row.did, vms, {
    controller: row.controller_did ? [row.controller_did] : undefined,
    alsoKnownAs: aka,
  });
}

function safeJsonArray(s: string): string[] | undefined {
  try {
    const v = JSON.parse(s);
    if (Array.isArray(v) && v.every((x) => typeof x === "string")) return v;
    return undefined;
  } catch {
    return undefined;
  }
}

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      "content-type": "application/json",
      "cache-control": "public, max-age=60",
      "access-control-allow-origin": "*",
    },
  });
}

function didDocResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      "content-type": "application/did+ld+json",
      "cache-control": "public, max-age=60",
      "access-control-allow-origin": "*",
    },
  });
}

function extractDid(pathname: string): { did: string; suffix: "" | "log" | "path-context" } | null {
  const stripped = pathname.replace(/^\/1\.0\/identifiers\//, "/");
  const m = stripped.match(/^\/(did:etzhayyim:[a-zA-Z0-9:]+?)(\/(log|path-context))?$/);
  if (!m) return null;
  return { did: m[1], suffix: (m[3] ?? "") as "" | "log" | "path-context" };
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    if (request.method === "OPTIONS") {
      return new Response(null, {
        status: 204,
        headers: {
          "access-control-allow-origin": "*",
          "access-control-allow-methods": "GET, POST, OPTIONS",
          "access-control-allow-headers": "content-type, authorization",
          "access-control-max-age": "86400",
        },
      });
    }

    if (request.method === "GET" && url.pathname === "/health") {
      return new Response("ok");
    }

    if (request.method === "GET") {
      const parsed = extractDid(url.pathname);
      if (!parsed) {
        return didDocResponse(resolutionErr("invalidDid", "DID not parseable from URL"), 400);
      }
      if (!isValidDidetzhayyim(parsed.did)) {
        return didDocResponse(resolutionErr("invalidDid", "did syntax invalid for did:etzhayyim"), 400);
      }
      if (didDepth(parsed.did) > 6) {
        return didDocResponse(resolutionErr("invalidDid", "exceeds MAX_PATH_DEPTH"), 400);
      }

      const db = createKyselyDb(env.HYPERDRIVE);

      const idRows = await sql<IdentityRow>`
        SELECT did, controller_did, root_did, parent_did, path_segment, depth,
               public_key_multibase, authentication_methods, status,
               created_at, updated_at, genesis_op_cid
        FROM vertex_etzhayyim_identity WHERE did = ${parsed.did} LIMIT 1
      `.execute(db);
      const row = idRows.rows[0];
      if (!row || row.status === "deleted") {
        return didDocResponse(resolutionErr("notFound", `did not found: ${parsed.did}`), 404);
      }

      if (parsed.suffix === "log") {
        const log = await sql<{
          op_seq: number; op_type: string; op_cid: string; prev_cid: string | null;
          op_cbor_hex: string; sig: string | null; sig_kid: string | null; created_at: string;
        }>`
          SELECT op_seq, op_type, op_cid, prev_cid, op_cbor_hex, sig, sig_kid, created_at
          FROM vertex_etzhayyim_op_log WHERE did = ${parsed.did} ORDER BY op_seq DESC LIMIT 1000
        `.execute(db);
        return jsonResponse(log.rows);
      }

      if (parsed.suffix === "path-context") {
        const childRows = await sql<{ dst_vid: string; segment: string | null }>`
          SELECT dst_vid, segment FROM edge_etzhayyim_path_child
          WHERE src_vid = ${parsed.did} LIMIT 5000
        `.execute(db);
        return jsonResponse({
          did: row.did,
          root: row.root_did,
          parent: row.parent_did,
          segment: row.path_segment,
          depth: row.depth,
          children: childRows.rows.map((r) => ({ did: r.dst_vid, segment: r.segment })),
        });
      }

      const doc = rowToDoc(row);
      return didDocResponse(resolutionOk(doc, {
        created: row.created_at ?? undefined,
        updated: row.updated_at ?? undefined,
        deactivated: row.status === "deactivated" ? true : undefined,
        versionId: row.genesis_op_cid ?? undefined,
      }));
    }

    if (request.method === "POST" && url.pathname === "/") {
      return jsonResponse(
        { error: "notImplemented", message: "submit ops via PDS XRPC com.etzhayyim.identity.submitOp" },
        501,
      );
    }

    return new Response("Not Found", { status: 404 });
  },
};
