#!/usr/bin/env node
/**
 * e7m WASM-actor serving surface (ADR-2606015400) — turns the runner (CLI) into a
 * real T2 donated-mesh service. Exposes one XRPC-shaped HTTP endpoint that
 * resolves an actor → CID/CAR-verifies → runs → returns the JSON result:
 *
 *   GET /xrpc/com.etzhayyim.actor.run?actor=<did|handle>[&cid=<cidv1>]
 *   GET /healthz
 *
 * Trust is unchanged: bytes are CID/CAR-verified before execution (no trusted
 * upstream, no server key — ADR-2605231525). Results are content-addressed →
 * cached by CID. This is the HTTP bridge the apex Worker can proxy and the
 * surface a libp2p `/x/etzhayyim/xrpc/1.0` handler will wrap next.
 *
 *   node serve.mjs [--port 8787] [--gateway https://etzhayyim.com]
 */
import { createServer } from "node:http";
import { fetchVerified, didToCid, runBytes } from "./runner.mjs";

const ACTOR_DID = /^did:web:etzhayyim\.com:actor:[a-z0-9][a-z0-9-]*$/;
const HANDLE = /^[a-z0-9][a-z0-9-]{0,62}$/;
const CIDV1 = /^baf[a-z2-7]{56}$/;

/** Resolve + verify + run, caching by CID (content-addressed → immutable). */
export function makeRunner({ gatewayBase = "https://etzhayyim.com", fetchImpl = fetch } = {}) {
  const cache = new Map(); // cid → result
  return async function runActorRequest({ actor, cid }) {
    let resolvedCid = cid;
    if (!resolvedCid) {
      if (!actor) throw new Error("actor or cid required");
      const did = ACTOR_DID.test(actor)
        ? actor
        : HANDLE.test(actor)
          ? `did:web:etzhayyim.com:actor:${actor}`
          : (() => { throw new Error(`invalid actor: ${actor}`); })();
      resolvedCid = await didToCid({ did, gatewayBase, fetchImpl });
    }
    if (!CIDV1.test(resolvedCid)) throw new Error(`invalid cid: ${resolvedCid}`);
    if (cache.has(resolvedCid)) return { cid: resolvedCid, cached: true, result: cache.get(resolvedCid) };
    const bytes = await fetchVerified({ cid: resolvedCid, gatewayBase, fetchImpl });
    const result = await runBytes(bytes);
    cache.set(resolvedCid, result);
    return { cid: resolvedCid, cached: false, result };
  };
}

const JSON_HEADERS = {
  "content-type": "application/json; charset=utf-8",
  "access-control-allow-origin": "*",
  "x-etzhayyim-no-cookie": "1",
};

/** Start the HTTP serving surface. Returns the node http.Server. */
export function serveActor({ port = 8787, gatewayBase, fetchImpl } = {}) {
  const run = makeRunner({ gatewayBase, fetchImpl });
  const server = createServer(async (req, res) => {
    try {
      const url = new URL(req.url, "http://localhost");
      if (req.method !== "GET") {
        res.writeHead(405, JSON_HEADERS).end(JSON.stringify({ error: "MethodNotAllowed" }));
        return;
      }
      if (url.pathname === "/healthz") {
        res.writeHead(200, JSON_HEADERS).end(JSON.stringify({ ok: true, service: "e7m-wasm-runner" }));
        return;
      }
      if (url.pathname === "/xrpc/com.etzhayyim.actor.run") {
        const out = await run({
          actor: url.searchParams.get("actor") ?? undefined,
          cid: url.searchParams.get("cid") ?? undefined,
        });
        res.writeHead(200, JSON_HEADERS).end(JSON.stringify(out));
        return;
      }
      res.writeHead(404, JSON_HEADERS).end(JSON.stringify({ error: "NotFound" }));
    } catch (e) {
      res.writeHead(502, JSON_HEADERS).end(JSON.stringify({ error: "RunFailed", message: e instanceof Error ? e.message : String(e) }));
    }
  });
  server.listen(port);
  return server;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const args = process.argv.slice(2);
  const val = (f) => { const i = args.indexOf(f); return i >= 0 ? args[i + 1] : undefined; };
  const port = Number(val("--port") ?? 8787);
  serveActor({ port, gatewayBase: val("--gateway") });
  console.log(`e7m-wasm-runner serving on :${port} — GET /xrpc/com.etzhayyim.actor.run?actor=<did|handle>`);
}
