// Tests for the kotoba-premise deploy (ADR-2606064600): deploy() manifest +
// kotoba registration body + the Cloudflare-free run loop (a deployed CID, served
// by an injected IPFS gateway, re-verifies + runs through runner.fetchVerified).
//
//   node --experimental-strip-types --test tests/deploy.test.mjs
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync, mkdtempSync, existsSync, readdirSync } from "node:fs";
import { tmpdir } from "node:os";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { deploy } from "../deploy.mjs";
import { buildIngestBody, registerInKotoba } from "../kotoba-register.mjs";
import { buildCar } from "../wasmcar.mjs";
import { fetchVerified, didToCid, defaultIpfsGateways } from "../runner.mjs";

const DIR = dirname(fileURLToPath(import.meta.url));
const KANAE = join(DIR, "../../../orgs/etzhayyim/com-etzhayyim-kanae/wasm/loader/kanae-core.wasm");

test("deploy(pin=none) produces a gateway-independent manifest", async () => {
  const m = await deploy({ file: KANAE, actor: "kanae", pin: "none" });
  assert.equal(m.actor, "kanae");
  assert.equal(m.did, "did:web:etzhayyim.com:actor:kanae");
  assert.equal(m.image.codec, "raw");
  assert.match(m.image.cid, /^bafkrei[a-z2-7]{52}$/);
  assert.equal(m.image.ipfsUri, `ipfs://${m.image.cid}`);
  assert.deepEqual(m.exec, ["browser-local", "donated-mesh"]);
  // the did.json service hint points at IPFS, not a Cloudflare URL
  assert.equal(m.didDocServiceHint.serviceEndpoint, `ipfs://${m.image.cid}`);
  assert.equal(m.didDocServiceHint.type, "EtzhayyimWasmComponent");
  // no operator token in the env → kotoba leg is a dry run (no-server-key posture)
  assert.equal(m.kotoba.posted, false);
});

test("kotoba registration body binds handle→CID (dry run, no token)", async () => {
  const cid = "bafkreiaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
  const body = buildIngestBody({ cid, actor: "tsumugi", codec: "raw", byteSize: 100, blockCount: 1, did: "did:web:etzhayyim.com:actor:tsumugi" });
  assert.equal(body.entities.length, 2);
  const [image, binding] = body.entities;
  assert.equal(image.type, "WasmActorImage");
  assert.equal(image.id, cid);
  assert.ok(image.claims.some((c) => c.pred === "wasm/programCid" && c.value === cid));
  assert.ok(image.claims.some((c) => c.pred === "wasm/actor" && c.value === "tsumugi"));
  // the mutable binding the did.json reader consumes
  assert.equal(binding.id, "actor.tsumugi");
  assert.equal(binding.graph, "actors-v1");
  assert.ok(binding.claims.some((c) => c.pred === "actor/wasm-cid" && c.value === cid));

  const dry = await registerInKotoba({ cid, actor: "tsumugi", codec: "raw", byteSize: 100, blockCount: 1, token: undefined });
  assert.equal(dry.posted, false);
  assert.match(dry.endpoint, /com\.etzhayyim\.apps\.kotobase\.kg\.ingest_batch$/);
});

test("kotoba registration POSTs with an operator token (no-server-key: token required)", async () => {
  let captured;
  const fakeFetch = async (url, init) => {
    captured = { url, init };
    return { ok: true, status: 200 };
  };
  const out = await registerInKotoba({
    cid: "bafkreiaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    actor: "kanae", codec: "raw", byteSize: 1, blockCount: 1,
    kotobaUrl: "http://127.0.0.1:8077", token: "op-jwt", fetchImpl: fakeFetch,
  });
  assert.equal(out.posted, true);
  assert.equal(captured.init.method, "POST");
  assert.equal(captured.init.headers.authorization, "Bearer op-jwt");
});

test("deploy(pin=pinner) drops a discoverable CAR for the ipfs-pinner daemon", async () => {
  const dataDir = mkdtempSync(join(tmpdir(), "e7m-pinner-"));
  const m = await deploy({ file: KANAE, actor: "kanae", pin: "pinner", pinnerDir: dataDir, shardKey: "com.etzhayyim.kanae" });
  assert.equal(m.pin.mode, "pinner");
  assert.ok(existsSync(m.pin.carPath));
  // layout matches discoverCars: <dataDir>/<encodeURIComponent(shardKey)>/<cid>.car
  const shardDir = join(dataDir, encodeURIComponent("com.etzhayyim.kanae"));
  assert.deepEqual(readdirSync(shardDir), [`${m.image.cid}.car`]);
});

test("deploy(pin=kubo) imports the CAR and matches our CID (injected kubo)", async () => {
  const m0 = await buildCar(new Uint8Array(readFileSync(KANAE)));
  const fakeKubo = async (url) => {
    assert.match(url, /\/api\/v0\/dag\/import\?pin-roots=true$/);
    return { ok: true, text: async () => JSON.stringify({ Root: { Cid: { "/": m0.cid } } }) };
  };
  const m = await deploy({ file: KANAE, actor: "kanae", pin: "kubo", kuboApi: "http://127.0.0.1:5001", fetchImpl: fakeKubo });
  assert.equal(m.pin.mode, "kubo");
  assert.deepEqual(m.pin.roots, [m.image.cid]);
});

test("Cloudflare-free run loop: deployed CID, served by an injected IPFS gateway, verifies + runs", async () => {
  const wasm = new Uint8Array(readFileSync(KANAE));
  const { cid } = await buildCar(wasm);
  // an injected gateway that serves the raw bytes at /ipfs/<cid> (kubo-shaped)
  const gatewayFetch = async (u) => {
    assert.ok(u.endsWith(`/ipfs/${cid}`), `unexpected url ${u}`);
    return { ok: true, arrayBuffer: async () => wasm.buffer.slice(wasm.byteOffset, wasm.byteOffset + wasm.byteLength) };
  };
  const bytes = await fetchVerified({ cid, gatewayBase: "http://127.0.0.1:8080", fetchImpl: gatewayFetch });
  assert.deepEqual(Buffer.from(bytes), Buffer.from(wasm)); // verified against the CID
});

test("fetchVerified falls back across gateways (first fails, second serves)", async () => {
  const wasm = new Uint8Array(readFileSync(KANAE));
  const { cid } = await buildCar(wasm);
  let calls = 0;
  const flakyFetch = async (u) => {
    calls++;
    if (u.startsWith("http://127.0.0.1:8080")) throw new Error("connection refused");
    return { ok: true, arrayBuffer: async () => wasm.buffer.slice(wasm.byteOffset, wasm.byteOffset + wasm.byteLength) };
  };
  const bytes = await fetchVerified({ cid, gateways: ["http://127.0.0.1:8080", "https://ipfs.io"], fetchImpl: flakyFetch });
  assert.deepEqual(Buffer.from(bytes), Buffer.from(wasm));
  assert.equal(calls, 2);
});

test("default gateways are kubo-local-first, NOT Cloudflare", () => {
  const gws = defaultIpfsGateways();
  assert.equal(gws[0], "http://127.0.0.1:8080");
  assert.ok(!gws.some((g) => g.includes("etzhayyim.com")));
});

test("didToCid resolves kotoba-first from the canonical Datom log binding", async () => {
  const cid = "bafkreiaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
  const kotobaFetch = async (u) => {
    assert.match(u, /kg\.entity\?id=actor\.tsumugi$/);
    return { ok: true, json: async () => ({ entity: { claims: [{ pred: "actor/wasm-cid", value: cid }] } }) };
  };
  const got = await didToCid({ did: "did:web:etzhayyim.com:actor:tsumugi", kotobaUrl: "http://127.0.0.1:8077", fetchImpl: kotobaFetch });
  assert.equal(got, cid);
});
