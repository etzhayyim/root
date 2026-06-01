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

async function fetchVerified({ cid, gatewayBase = "https://etzhayyim.com", fetchImpl = fetch }) {
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

async function didToCid({ did, didDoc, gatewayBase = "https://etzhayyim.com", fetchImpl = fetch }) {
  const slug = did.replace(/^did:web:etzhayyim\.com:actor:/, "");
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
  const opts = { file: val("--file"), cid: val("--cid"), did: val("--did"), gatewayBase: val("--gateway") };
  resolveAndRun(opts)
    .then((r) => { console.log(JSON.stringify(r, null, 2)); })
    .catch((e) => { console.error("runner failed:", e.message); process.exit(1); });
}
