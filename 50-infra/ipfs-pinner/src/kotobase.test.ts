/**
 * kotobase provider tests — pure internals (CID-from-filename, auth header
 * selection) + the PSA POST /pins round-trip against a mocked `fetch`, so the
 * tests run with no network and no kotobase account.
 */

import { test } from "node:test";
import assert from "node:assert/strict";

import { __testing, kotobase } from "./providers/kotobase.js";

type FetchArgs = [input: string | URL, init?: RequestInit];

interface MockResponse {
  ok: boolean;
  status?: number;
  json?: unknown;
}

function installFetch(handler: (...args: FetchArgs) => MockResponse): {
  calls: FetchArgs[];
  restore: () => void;
} {
  const original = globalThis.fetch;
  const calls: FetchArgs[] = [];
  globalThis.fetch = (async (...args: FetchArgs) => {
    calls.push(args);
    const resp = handler(...args);
    return {
      ok: resp.ok,
      status: resp.status ?? (resp.ok ? 200 : 500),
      async json() {
        return resp.json ?? {};
      },
    } as Response;
  }) as typeof fetch;
  return { calls, restore: () => { globalThis.fetch = original; } };
}

const ROOT_CID = "bafyreigh2akiscaildc7obb6q3vbiqd5gukvvr44e7lsdgowf2c5sb6e44";

test("rootCidFromCarPath takes the CID from the <rootCid>.car filename stem", () => {
  assert.equal(
    __testing.rootCidFromCarPath(`/data/mst/did%3Aweb%3Ax/${ROOT_CID}.car`),
    ROOT_CID,
  );
});

test("rootCidFromCarPath rejects a non-CID stem (defensive against an upstream rename)", () => {
  assert.throws(() => __testing.rootCidFromCarPath("/data/shard.car"), /does not encode a CID/);
});

test("kotobaseAuth prefers the Bearer JWT", () => {
  const a = __testing.kotobaseAuth({ ETZ_KOTOBASE_JWT: "jwt123" } );
  assert.equal(a.kind, "bearer");
  assert.equal(a.headers.authorization, "Bearer jwt123");
});

test("kotobaseAuth falls back to a self-signed CACAO + x-kotoba-did", () => {
  const a = __testing.kotobaseAuth({
    ETZ_KOTOBASE_CACAO: "b64cbor",
    ETZ_KOTOBASE_DID: "did:web:tenant.example",
  } );
  assert.equal(a.kind, "cacao");
  assert.equal(a.headers.authorization, "CACAO b64cbor");
  assert.equal(a.headers["x-kotoba-did"], "did:web:tenant.example");
});

test("kotobaseAuth throws when no credential is configured (no platform key is held)", () => {
  assert.throws(() => __testing.kotobaseAuth({} ), /needs ETZ_KOTOBASE_JWT/);
});

test("postPin POSTs {cid,name} to {base}/pins and returns the PinStatus", async () => {
  const { calls, restore } = installFetch(() => ({
    ok: true,
    status: 202,
    json: { requestid: "req-1", status: "queued", pin: { cid: ROOT_CID, name: ROOT_CID } },
  }));
  try {
    const st = await __testing.postPin(
      "https://kotobase.net",
      { headers: { authorization: "Bearer jwt123" }, kind: "bearer" },
      ROOT_CID,
      ROOT_CID,
    );
    assert.equal(st.requestid, "req-1");
    assert.equal(st.status, "queued");
    assert.equal(calls.length, 1);
    const [url, init] = calls[0];
    assert.equal(url.toString(), "https://kotobase.net/pins");
    assert.equal(init?.method, "POST");
    assert.equal(
      (init?.headers as Record<string, string>).authorization,
      "Bearer jwt123",
    );
    assert.deepEqual(JSON.parse(init?.body as string), { cid: ROOT_CID, name: ROOT_CID });
  } finally {
    restore();
  }
});

test("postPin rejects a PinStatus whose cid does not match what was submitted", async () => {
  const { restore } = installFetch(() => ({
    ok: true,
    status: 202,
    json: { requestid: "r", status: "queued", pin: { cid: "bafyOTHERoootcidxxxxxxxxxxxxxxxxxxxxxxxxx" } },
  }));
  try {
    await assert.rejects(
      __testing.postPin("https://kotobase.net", { headers: {}, kind: "bearer" }, ROOT_CID, ROOT_CID),
      /cid mismatch/,
    );
  } finally {
    restore();
  }
});

test("postPin surfaces the PSA error reason on a non-2xx", async () => {
  const { restore } = installFetch(() => ({
    ok: false,
    status: 401,
    json: { error: { reason: "Unauthorized", details: "bad token" } },
  }));
  try {
    await assert.rejects(
      __testing.postPin("https://kotobase.net", { headers: {}, kind: "bearer" }, ROOT_CID, ROOT_CID),
      /POST \/pins failed: Unauthorized/,
    );
  } finally {
    restore();
  }
});

test("kotobase() end-to-end: filename CID → /pins → receipt carrying the configured gateway", async () => {
  const prev = {
    jwt: process.env.ETZ_KOTOBASE_JWT,
    url: process.env.ETZ_KOTOBASE_URL,
    gw: process.env.ETZ_KOTOBASE_GATEWAY,
  };
  process.env.ETZ_KOTOBASE_JWT = "jwt123";
  delete process.env.ETZ_KOTOBASE_URL; // exercise the default base
  // The gateway is now set explicitly. It used to be asserted as
  // https://ipfs.gftd.ai/ipfs/<cid>, which came from a default that no
  // longer resolves — so the test was pinning down a dead URL as correct.
  process.env.ETZ_KOTOBASE_GATEWAY = "https://gw.example/";
  const { calls, restore } = installFetch(() => ({
    ok: true,
    status: 202,
    json: { requestid: "req-9", status: "pinning", pin: { cid: ROOT_CID } },
  }));
  try {
    const out = await kotobase(`/data/mst/shard/${ROOT_CID}.car`);
    assert.equal(out.cid, ROOT_CID);
    assert.equal(out.receipt.provider, "kotobase");
    assert.equal(out.receipt.requestid, "req-9");
    assert.equal(out.receipt.status, "pinning");
    assert.equal(out.receipt.auth, "bearer");
    assert.equal(out.receipt.gatewayUrl, `https://gw.example/ipfs/${ROOT_CID}`);
    assert.equal(calls[0][0].toString(), "https://kotobase.net/pins");
  } finally {
    restore();
    if (prev.jwt === undefined) delete process.env.ETZ_KOTOBASE_JWT;
    else process.env.ETZ_KOTOBASE_JWT = prev.jwt;
    if (prev.url !== undefined) process.env.ETZ_KOTOBASE_URL = prev.url;
    if (prev.gw === undefined) delete process.env.ETZ_KOTOBASE_GATEWAY;
    else process.env.ETZ_KOTOBASE_GATEWAY = prev.gw;
  }
});

test("kotobase() falls back to kotobase's own gateway when none is configured", async () => {
  // Unconfigured now means ipfs.kotobase.net, live since 2026-07-29. The old
  // default was ipfs.gftd.ai, which answers 530 — a URL that looks usable and
  // is not. Naming kotobase's own retrieval surface is the one guess this
  // provider can make without guessing: same service, same pin.
  const prev = { jwt: process.env.ETZ_KOTOBASE_JWT, gw: process.env.ETZ_KOTOBASE_GATEWAY };
  process.env.ETZ_KOTOBASE_JWT = "jwt123";
  delete process.env.ETZ_KOTOBASE_GATEWAY;
  const { restore } = installFetch(() => ({
    ok: true,
    status: 202,
    json: { requestid: "req-10", status: "pinning", pin: { cid: ROOT_CID } },
  }));
  try {
    const out = await kotobase(`/data/mst/shard/${ROOT_CID}.car`);
    assert.equal(out.receipt.gatewayUrl, `https://ipfs.kotobase.net/ipfs/${ROOT_CID}`);
    assert.equal(out.receipt.status, "pinning");
  } finally {
    restore();
    if (prev.jwt === undefined) delete process.env.ETZ_KOTOBASE_JWT;
    else process.env.ETZ_KOTOBASE_JWT = prev.jwt;
    if (prev.gw !== undefined) process.env.ETZ_KOTOBASE_GATEWAY = prev.gw;
  }
});
