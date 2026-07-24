// Serving-surface tests (ADR-2606015400): start the HTTP server with a stub
// gateway (serves the committed kanae did.json + WASM), then make REAL http
// requests to /xrpc/com.etzhayyim.actor.run and /healthz. Proves a donated mesh
// node serves CID-verified actor results over the network.
//   node --experimental-strip-types --test tests/serve.test.mjs
import { test, after } from "node:test";
import assert from "node:assert/strict";
import { once } from "node:events";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { serveActor } from "../serve.mjs";

const DIR = dirname(fileURLToPath(import.meta.url));
const WASM = readFileSync(join(DIR, "../../../orgs/etzhayyim/com-etzhayyim-kanae/wasm/loader/kanae-core.wasm"));
const KANAE_CID = "bafkreielhr6l5jy7ml5l62ncyva34lhjw52q2onwxwy6ubep4wqxjyjnie";

// Stub gateway: serves the kanae DID doc + the verified WASM bytes.
function stubGateway() {
  let wasmFetches = 0;
  const fetchImpl = async (input) => {
    const u = String(input);
    if (u.includes("/actor/kanae/did.json")) {
      return new Response(JSON.stringify({
        id: "did:web:etzhayyim.com:actor:kanae",
        service: [{ type: "EtzhayyimWasmComponent", serviceEndpoint: `ipfs://${KANAE_CID}` }],
      }), { headers: { "content-type": "application/json" } });
    }
    if (u.includes(`/ipfs/${KANAE_CID}`)) {
      wasmFetches++;
      return new Response(WASM, { status: 200 });
    }
    throw new Error(`unexpected fetch: ${u}`);
  };
  return { fetchImpl, fetches: () => wasmFetches };
}

async function startServer() {
  const gw = stubGateway();
  const server = serveActor({ port: 0, fetchImpl: gw.fetchImpl });
  await once(server, "listening");
  const { port } = server.address();
  return { server, port, gw };
}

test("serve: /healthz", async () => {
  const { server, port } = await startServer();
  after(() => server.close());
  const r = await (await fetch(`http://localhost:${port}/healthz`)).json();
  assert.equal(r.ok, true);
  assert.equal(r.service, "e7m-wasm-runner");
});

test("serve: actor.run resolves + verifies + runs kanae, then caches", async () => {
  const { server, port, gw } = await startServer();
  after(() => server.close());
  const base = `http://localhost:${port}/xrpc/com.etzhayyim.actor.run?actor=kanae`;

  const a = await (await fetch(base)).json();
  assert.equal(a.cid, KANAE_CID);
  assert.equal(a.cached, false);
  assert.equal(a.result.actor, "kanae");
  assert.equal(a.result.top[0].node, "Prefectures");

  const b = await (await fetch(base)).json();
  assert.equal(b.cached, true); // content-addressed → served from cache
  assert.equal(gw.fetches(), 1); // WASM fetched once
});

test("serve: bad actor → 502 RunFailed", async () => {
  const { server, port } = await startServer();
  after(() => server.close());
  const res = await fetch(`http://localhost:${port}/xrpc/com.etzhayyim.actor.run?actor=Invalid_Handle`);
  assert.equal(res.status, 502);
  const j = await res.json();
  assert.equal(j.error, "RunFailed");
});
