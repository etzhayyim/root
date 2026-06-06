#!/usr/bin/env node
/**
 * e7m WASM-actor runner — the T2 donated-mesh execution node (ADR-2606015200).
 *
 * Resolves an actor's content-addressed WASM, VERIFIES it (sha256 for raw CIDs;
 * full CAR re-hash + DAG walk for dag-pb componentize-py actors — `car.ts`), and
 * RUNS it headlessly:
 *   - core module  → WebAssembly.instantiate + the compute()/result_ptr() ABI
 *   - WASI component → jco transpile → import → call compute()
 * The gateway/source is never trusted (CID is the trust anchor, no server key,
 * ADR-2605231525). This is what a kotoba/e7m donated node runs; it would expose
 * the result over libp2p `/x/etzhayyim/xrpc/1.0` (transport wiring = next step).
 *
 * Usage:
 *   node runner.mjs --file <path.wasm>
 *   node runner.mjs --cid <cidv1> [--gateway https://etzhayyim.com]
 *   node runner.mjs --did did:web:etzhayyim.com:actor:<h> [--gateway ...]
 */
import { readFileSync, writeFileSync, mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { execFileSync } from "node:child_process";
import { verifyRawCid, isRawCidV1, isDagPbCidV1, cidV1Raw } from "../etzhayyim-did-web/src/cid.ts";
import { verifyCarToBytes } from "../etzhayyim-did-web/src/car.ts";

/** Detect a WASM Component (vs a core module) from the layer/version bytes. */
export function isComponent(bytes) {
  // \0asm magic, then 4 version/layer bytes. core: 01 00 00 00; component: 0d 00 01 00
  return bytes[0] === 0x00 && bytes[1] === 0x61 && bytes[2] === 0x73 && bytes[3] === 0x6d && bytes[6] === 0x01;
}

/** Ordered IPFS gateways to try — kotoba/IPFS-premise, NOT Cloudflare-premise
 *  (ADR-2606064500). Local kubo first (a donated mesh node serves its own pins),
 *  then public trustless gateways. Override with E7M_IPFS_GATEWAYS (comma list).
 *  The apex `https://etzhayyim.com` is no longer the default — it is just one
 *  more gateway you can pass explicitly. The CID is the trust anchor either way. */
export function defaultIpfsGateways() {
  const env = process.env.E7M_IPFS_GATEWAYS;
  if (env) return env.split(",").map((s) => s.trim()).filter(Boolean);
  return ["http://127.0.0.1:8080", "https://ipfs.io", "https://dweb.link"];
}

/** Fetch + CID/CAR-verify from ONE gateway. */
async function fetchFromGateway({ cid, gatewayBase, fetchImpl = fetch }) {
  const base = `${gatewayBase.replace(/\/$/, "")}/ipfs/${cid}`;
  if (isRawCidV1(cid)) {
    const res = await fetchImpl(base);
    if (!res.ok) throw new Error(`gateway ${res.status}`);
    const buf = await res.arrayBuffer();
    if (!(await verifyRawCid(cid, buf))) throw new Error("raw CID mismatch");
    return new Uint8Array(buf);
  }
  if (isDagPbCidV1(cid)) {
    const res = await fetchImpl(`${base}?format=car`, { headers: { accept: "application/vnd.ipld.car" } });
    if (!res.ok) throw new Error(`gateway ${res.status}`);
    return await verifyCarToBytes(cid, new Uint8Array(await res.arrayBuffer()));
  }
  throw new Error(`unsupported CID: ${cid}`);
}

/** Resolve + verify bytes for a CID across an ordered gateway list (first that
 *  serves verifiable bytes wins). `gatewayBase` (single) still works for back-compat. */
export async function fetchVerified({ cid, gatewayBase, gateways, fetchImpl = fetch }) {
  const list = gateways ?? (gatewayBase ? [gatewayBase] : defaultIpfsGateways());
  let lastErr;
  for (const gw of list) {
    try {
      return await fetchFromGateway({ cid, gatewayBase: gw, fetchImpl });
    } catch (e) {
      lastErr = e;
    }
  }
  throw new Error(`all gateways failed for ${cid}: ${lastErr?.message ?? "unknown"}`);
}

/** Resolve a did:web actor handle → wasm CID, kotoba-first (the canonical Datom
 *  log binding `actor/wasm-cid`, ADR-2606064500), falling back to the did.json
 *  EtzhayyimWasmComponent service. `kotobaUrl` (or KOTOBA_URL) enables the
 *  Cloudflare-free path; without it, did:web TLS still anchors the handle→CID. */
export async function didToCid({ did, didDoc, kotobaUrl = process.env.KOTOBA_URL, gatewayBase = "https://etzhayyim.com", fetchImpl = fetch }) {
  const slug = did.replace(/^did:web:etzhayyim\.com:actor:/, "");
  // 1. kotoba Datom log (canonical) — no apex Worker in the loop.
  if (kotobaUrl && !didDoc) {
    try {
      const url = `${kotobaUrl.replace(/\/$/, "")}/xrpc/com.etzhayyim.apps.kotobase.kg.entity?id=${encodeURIComponent(`actor.${slug}`)}`;
      const body = await fetchImpl(url, { headers: { accept: "application/json" } }).then((r) => (r.ok ? r.json() : null));
      const claims = body?.entity?.claims ?? body?.claims ?? [];
      const c = claims.find((x) => x?.pred === "actor/wasm-cid")?.value;
      if (typeof c === "string" && c) return c;
    } catch {
      /* fall through to did.json */
    }
  }
  // 2. did.json EtzhayyimWasmComponent service (did:web TLS-anchored).
  const doc = didDoc ?? (await fetchImpl(`${gatewayBase.replace(/\/$/, "")}/actor/${slug}/did.json`).then((r) => r.json()));
  const svc = (doc.service ?? []).find((s) => s.type === "EtzhayyimWasmComponent");
  if (!svc) throw new Error(`no EtzhayyimWasmComponent for ${did}`);
  return svc.serviceEndpoint.replace(/^ipfs:\/\//, "");
}

/** Run already-verified WASM bytes and return the parsed JSON result. */
export async function runBytes(bytes) {
  if (isComponent(bytes)) {
    // WASI component → jco transpile → import → compute()
    const dir = mkdtempSync(join(tmpdir(), "e7m-runner-"));
    writeFileSync(join(dir, "actor.wasm"), bytes);
    execFileSync("npx", ["-y", "@bytecodealliance/jco@latest", "transpile", join(dir, "actor.wasm"), "-o", join(dir, "t"), "--name", "actor"], { stdio: "ignore" });
    const mod = await import(join(dir, "t", "actor.js"));
    return JSON.parse(mod.compute());
  }
  // core module → compute()/result_ptr()/memory ABI
  const { instance } = await WebAssembly.instantiate(bytes, {});
  const { compute, result_ptr, memory } = instance.exports;
  const len = compute();
  return JSON.parse(Buffer.from(memory.buffer, result_ptr(), len).toString("utf8"));
}

export async function resolveAndRun(opts) {
  let bytes;
  if (opts.file) bytes = new Uint8Array(readFileSync(opts.file));
  else {
    const cid = opts.cid ?? (await didToCid(opts));
    bytes = await fetchVerified({ ...opts, cid });
  }
  return runBytes(bytes);
}

// ── CLI ──────────────────────────────────────────────────────────────────────
function isMain() {
  return import.meta.url === `file://${process.argv[1]}`;
}
if (isMain()) {
  const args = process.argv.slice(2);
  const val = (f) => { const i = args.indexOf(f); return i >= 0 ? args[i + 1] : undefined; };
  const gws = val("--gateways");
  const opts = {
    file: val("--file"),
    cid: val("--cid"),
    did: val("--did"),
    gatewayBase: val("--gateway"),
    gateways: gws ? gws.split(",").map((s) => s.trim()).filter(Boolean) : undefined,
    kotobaUrl: val("--kotoba"),
  };
  resolveAndRun(opts)
    .then((r) => { console.log(JSON.stringify(r, null, 2)); })
    .catch((e) => { console.error("runner failed:", e.message); process.exit(1); });
}
