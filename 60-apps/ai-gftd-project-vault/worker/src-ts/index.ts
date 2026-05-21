// vault.etzhayyim.com — Cloudflare Worker entry point.
//
// Zero-knowledge secret manager. All ciphertext + wrapped keys are opaque to
// this Worker; client (gftd CLI / browser) handles AES-GCM + AES-key-wrap.
// Identity is delegated to AUTH_SERVICE (auth.etzhayyim.com).
//
// Routes (XRPC):
//   POST /xrpc/ai.gftd.vault.createVault
//   GET  /xrpc/ai.gftd.vault.listVaults
//   POST /xrpc/ai.gftd.vault.putItem
//   GET  /xrpc/ai.gftd.vault.getItem
//   GET  /xrpc/ai.gftd.vault.listItems
//   POST /xrpc/ai.gftd.vault.deleteItem
//   POST /xrpc/ai.gftd.vault.addMember
//   POST /xrpc/ai.gftd.vault.removeMember
//   POST /xrpc/ai.gftd.vault.rotateVaultKey
//   GET  /xrpc/ai.gftd.vault.listAccessEvents
//   POST /xrpc/ai.gftd.vault.injectWorkerSecret
//
// Health: GET /health

import { AuthError } from "./auth";
import { err } from "./util";
import {
  handleCreateVault, handleListVaults,
  handlePutItem, handleGetItem, handleListItems, handleDeleteItem,
  handleAddMember, handleRemoveMember, handleRotateVaultKey,
  handleListAccessEvents, handleInjectWorkerSecret,
} from "./handlers";

export interface Env {
  VAULT_DB: D1Database;
  AUTH_SERVICE: Fetcher;
  VAULT_AUDIT_HASH_SALT: string;
  CF_API_TOKEN: { get(): Promise<string | null> };
  CF_ACCOUNT_ID: { get(): Promise<string | null> };
}

interface RouteEntry {
  method: "GET" | "POST";
  handler: (req: Request, env: Env) => Promise<Response>;
}

const ROUTES: Record<string, RouteEntry> = {
  "/xrpc/ai.gftd.vault.createVault":        { method: "POST", handler: handleCreateVault },
  "/xrpc/ai.gftd.vault.listVaults":         { method: "GET",  handler: handleListVaults },
  "/xrpc/ai.gftd.vault.putItem":            { method: "POST", handler: handlePutItem },
  "/xrpc/ai.gftd.vault.getItem":            { method: "GET",  handler: handleGetItem },
  "/xrpc/ai.gftd.vault.listItems":          { method: "GET",  handler: handleListItems },
  "/xrpc/ai.gftd.vault.deleteItem":         { method: "POST", handler: handleDeleteItem },
  "/xrpc/ai.gftd.vault.addMember":          { method: "POST", handler: handleAddMember },
  "/xrpc/ai.gftd.vault.removeMember":       { method: "POST", handler: handleRemoveMember },
  "/xrpc/ai.gftd.vault.rotateVaultKey":     { method: "POST", handler: handleRotateVaultKey },
  "/xrpc/ai.gftd.vault.listAccessEvents":   { method: "GET",  handler: handleListAccessEvents },
  "/xrpc/ai.gftd.vault.injectWorkerSecret": { method: "POST", handler: handleInjectWorkerSecret },
};

export default {
  async fetch(req: Request, env: Env): Promise<Response> {
    const url = new URL(req.url);
    const { pathname } = url;
    const method = req.method;

    if (method === "OPTIONS") {
      return new Response(null, {
        status: 204,
        headers: {
          "Access-Control-Allow-Origin": "*",
          "Access-Control-Allow-Headers": "Authorization, Content-Type, X-Active-DID",
          "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
          "Access-Control-Max-Age": "86400",
        },
      });
    }

    if (method === "GET" && pathname === "/health") {
      return new Response("ok", { status: 200 });
    }

    const route = ROUTES[pathname];
    if (!route) return err(404, "NotFound", `unknown route: ${method} ${pathname}`);
    if (route.method !== method) return err(405, "MethodNotAllowed", `${pathname} requires ${route.method}`);

    try {
      return await route.handler(req, env);
    } catch (e) {
      if (e instanceof AuthError) return err(e.status, e.code, e.message);
      console.error(`vault handler error ${pathname}:`, e);
      const msg = e instanceof Error ? e.message : String(e);
      return err(500, "InternalError", msg);
    }
  },
};
