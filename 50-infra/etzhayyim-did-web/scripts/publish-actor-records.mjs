#!/usr/bin/env node
/**
 * publish-actor-records.mjs — materialize actor identity + profile from the
 * canonical kotoba seed into (a) CF KV (`actor:<handle>` → ActorRecord JSON,
 * read by the Worker for dynamic did.json + getProfile) and (b) the kotoba
 * `actors-v1` graph (kg.ingest_batch). Per ADR-2606013800.
 *
 * SSoT: 00-contracts/schemas/actor-profile-seed.kotoba.edn
 *
 * Modes:
 *   (default)         parse seed, write materialized docs to ./out/, print summary
 *   --emit-dir <dir>  write per-actor record.json / did.json / profile.json to <dir>
 *   --put-kv          `wrangler kv key put` each ActorRecord (needs ACTOR_KV binding)
 *   --ingest-kotoba   POST kg.ingest_batch to $KOTOBA_ENDPOINT (operator-gated)
 *   --actor <handle>  restrict to one actor (debug)
 *
 * HONEST R0: --put-kv / --ingest-kotoba shell out / hit the network and are
 * operator-gated (ACTOR_KV namespace + a reachable kotoba endpoint). The default
 * mode is offline and is the functional verification of the seed → docs mapping.
 *
 * The toDidDoc / toGetProfileView logic here MIRRORS src/registry/actor-profiles.ts
 * — keep the two in sync (one is TS for the Worker, this is JS for the publisher).
 */

import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve, join } from "node:path";
import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";

// CIDv1 (raw, sha2-256) of bytes — matches `ipfs add --cid-version=1` + the
// worker's cid.ts, so the canonical DID doc is IPFS-retrievable (ADR-2606015400).
function _base32(bytes) {
  const A = "abcdefghijklmnopqrstuvwxyz234567";
  let bits = 0, val = 0, out = "";
  for (const b of bytes) { val = (val << 8) | b; bits += 8; while (bits >= 5) { out += A[(val >>> (bits - 5)) & 31]; bits -= 5; } }
  if (bits > 0) out += A[(val << (5 - bits)) & 31];
  return out;
}
function cidV1Raw(buf) {
  const d = createHash("sha256").update(buf).digest();
  return "b" + _base32(Buffer.concat([Buffer.from([0x01, 0x55, 0x12, 0x20]), d]));
}

const __dirname = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = resolve(__dirname, "../../..");
const SEED_PATH = resolve(
  REPO_ROOT,
  "00-contracts/schemas/actor-profile-seed.kotoba.edn",
);

// ── minimal EDN reader (maps / vectors / strings / keywords; comments) ──────
function parseEdn(src) {
  let i = 0;
  const isWs = (c) => c === " " || c === "\t" || c === "\n" || c === "\r" || c === ",";
  function skip() {
    while (i < src.length) {
      const c = src[i];
      if (isWs(c)) { i++; continue; }
      if (c === ";") { while (i < src.length && src[i] !== "\n") i++; continue; }
      break;
    }
  }
  function readString() {
    i++; // opening quote
    let s = "";
    while (i < src.length) {
      const c = src[i++];
      if (c === "\\") {
        const n = src[i++];
        s += n === "n" ? "\n" : n === "t" ? "\t" : n === "r" ? "\r" : n;
      } else if (c === '"') {
        return s;
      } else s += c;
    }
    throw new Error("unterminated string");
  }
  function readToken() {
    let s = "";
    while (i < src.length && !isWs(src[i]) && !"{}[]()\"".includes(src[i])) s += src[i++];
    return s;
  }
  function readValue() {
    skip();
    const c = src[i];
    if (c === '"') return readString();
    if (c === "{") return readMap();
    if (c === "[") return readVector();
    const tok = readToken();
    if (tok.startsWith(":")) return { __kw: tok.slice(1) }; // keyword
    if (tok === "nil") return null;
    if (tok === "true") return true;
    if (tok === "false") return false;
    if (/^-?\d+(\.\d+)?$/.test(tok)) return Number(tok);
    return tok;
  }
  function readVector() {
    i++; // [
    const arr = [];
    for (;;) {
      skip();
      if (src[i] === "]") { i++; break; }
      arr.push(readValue());
    }
    return arr;
  }
  function readMap() {
    i++; // {
    const o = {};
    for (;;) {
      skip();
      if (src[i] === "}") { i++; break; }
      const k = readValue();
      const v = readValue();
      const key = k && k.__kw !== undefined ? k.__kw : String(k);
      o[key] = v;
    }
    return o;
  }
  const out = readValue();
  return out;
}

// keyword values come back as {__kw}. Flatten to plain strings.
const kw = (v) => (v && typeof v === "object" && v.__kw !== undefined ? v.__kw : v);

// ── seed entity → ActorRecord ───────────────────────────────────────────────
function recordFromSeed(m) {
  const g = (k) => m[`actor/${k}`];
  const handle = String(g("handle"));
  const named = Boolean(g("glyph"));
  const service = (g("service") || []).map((svc) => {
    const o = {};
    for (const [k, v] of Object.entries(svc)) o[k] = kw(v);
    return o;
  });
  const rec = {
    handle,
    did: g("did") || `did:web:etzhayyim.com:actor:${handle}`,
    kind: kw(g("kind")) || (named ? "tier-b" : "substrate-service"),
    status: kw(g("status")) || (named ? "r0" : "landed"),
    description: g("description") || "",
    adr: (g("adr") || []).map(String),
    service,
    vm: (g("vm") || []).map((v) => v),
  };
  const opt = (k, dst) => { const v = g(k); if (v !== undefined && v !== null) rec[dst] = kw(v); };
  opt("tier", "tier");
  opt("glyph", "glyph");
  opt("display-name-ja", "displayNameJa");
  opt("display-name-en", "displayNameEn");
  opt("avatar", "avatar");
  opt("banner", "banner");
  opt("performer-type", "performerType");
  opt("ui-type", "uiType");
  opt("primary-lexicon", "primaryLexicon");
  opt("primary-schema", "primarySchema");
  opt("wasm-cid", "wasmCid");
  opt("created-at", "createdAt");
  rec.source = "kotoba";
  return rec;
}

// ── mappers (MIRROR of src/registry/actor-profiles.ts) ──────────────────────
function toDidDoc(rec, authzContract) {
  const did = `did:web:etzhayyim.com:actor:${rec.handle}`;
  const alsoKnownAs = [`did:web:${rec.handle}.etzhayyim.com`];
  const chainRef = (rec.vm.find((v) => v && v.chainRef) || {}).chainRef;
  if (chainRef) alsoKnownAs.push(chainRef);
  else if (authzContract)
    alsoKnownAs.push(`did:erc725:base:${authzContract}#__rootId-pending-chain-lookup__`);
  const service = [];
  if (rec.wasmCid) {
    const raw = /^bafkrei[a-z2-7]{52}$/.test(rec.wasmCid); // raw single-block CIDv1
    service.push({
      id: `${did}#wasm`,
      type: "EtzhayyimWasmComponent",
      serviceEndpoint: `ipfs://${rec.wasmCid}`,
      "x-exec": raw ? "browser-local|donated-mesh" : "donated-mesh",
      "x-cid-codec": raw ? "raw" : "dag-pb",
      "x-runtime": "kotoba-wasm",
    });
  }
  service.push(...rec.service.map((s) => ({ ...s })));
  return {
    "@context": [
      "https://www.w3.org/ns/did/v1",
      "https://w3id.org/security/suites/jws-2020/v1",
    ],
    id: did,
    alsoKnownAs,
    verificationMethod: rec.vm.map((v) => ({ ...v })),
    service,
    _meta: {
      adr: ["2605212030", "2605241800", "2606013800", "2606014500", ...rec.adr],
      source: rec.source,
      kind: rec.kind,
      status: rec.status,
      glyph: rec.glyph,
      wasmCid: rec.wasmCid ?? null,
      execModel: rec.wasmCid ? "wasm-local (browser/donated-mesh)" : "service",
      primaryLexicon: rec.primaryLexicon,
      primarySchema: rec.primarySchema,
      note:
        rec.vm.length === 0
          ? "verificationMethod empty — on-chain ERC725 mirror pending; did:web trust root = TLS (no server-minted key, ADR-2605231525)"
          : "verificationMethod mirrors on-chain ERC725 Root.activeKey",
    },
  };
}
function toGetProfileView(rec) {
  const displayName = rec.displayNameEn || rec.displayNameJa || rec.handle;
  return {
    did: rec.did,
    handle: `${rec.handle}.etzhayyim.com`,
    displayName,
    description: rec.description,
    avatar: rec.avatar ?? "",
    banner: rec.banner ?? "",
    followersCount: 0,
    followsCount: 0,
    postsCount: 0,
    indexedAt: rec.createdAt ? `${rec.createdAt}T00:00:00.000Z` : "1970-01-01T00:00:00.000Z",
    labels: [],
    viewer: {},
    performerType: rec.performerType ?? "system",
    uiType: rec.uiType ?? "appview",
    ...(rec.glyph ? { glyph: rec.glyph } : {}),
    ...(rec.displayNameJa ? { displayNameJa: rec.displayNameJa } : {}),
    _etzhayyim: {
      kind: rec.kind,
      tier: rec.tier ?? null,
      status: rec.status,
      adr: rec.adr,
      primaryLexicon: rec.primaryLexicon ?? null,
      primarySchema: rec.primarySchema ?? null,
      didDocument: `https://etzhayyim.com/actor/${rec.handle}/did.json`,
      source: rec.source,
    },
  };
}

// ── kotoba kg.ingest_batch entity ───────────────────────────────────────────
function recordToKgEntity(rec) {
  const claims = [];
  const add = (pred, value) => { if (value !== undefined && value !== null && value !== "") claims.push({ pred: `actor/${pred}`, value: String(value) }); };
  add("handle", rec.handle);
  add("did", rec.did);
  add("kind", rec.kind);
  add("tier", rec.tier);
  add("status", rec.status);
  add("glyph", rec.glyph);
  add("display-name-ja", rec.displayNameJa);
  add("display-name-en", rec.displayNameEn);
  add("description", rec.description);
  add("avatar", rec.avatar);
  add("banner", rec.banner);
  add("wasm-cid", rec.wasmCid);
  add("performer-type", rec.performerType);
  add("ui-type", rec.uiType);
  add("primary-lexicon", rec.primaryLexicon);
  add("primary-schema", rec.primarySchema);
  add("created-at", rec.createdAt);
  add("service-json", JSON.stringify(rec.service));
  add("vm-json", JSON.stringify(rec.vm));
  for (const a of rec.adr) claims.push({ pred: "actor/adr", value: a });
  return {
    id: `actor.${rec.handle}`,
    kind: "actor-profile",
    label_en: rec.displayNameEn || rec.handle,
    label_ja: rec.displayNameJa || undefined,
    claims,
    relations: [],
  };
}

// ── main ────────────────────────────────────────────────────────────────────
function main() {
  const args = process.argv.slice(2);
  const has = (f) => args.includes(f);
  const valOf = (f) => { const k = args.indexOf(f); return k >= 0 ? args[k + 1] : undefined; };

  // --seed <path> overrides the canonical seed (e.g. the generated clean-room
  // corpus seed 00-contracts/schemas/cleanroom-actors-seed.kotoba.edn, ADR 260607).
  const seedPath = valOf("--seed") ? resolve(REPO_ROOT, valOf("--seed")) : SEED_PATH;
  const seed = parseEdn(readFileSync(seedPath, "utf8"));
  const entities = (seed.seed || []).map(recordFromSeed);
  const only = valOf("--actor");
  const records = only ? entities.filter((r) => r.handle === only) : entities;
  if (records.length === 0) { console.error(`no actors${only ? ` matching '${only}'` : ""}`); process.exit(1); }

  const authz = process.env.AUTHZ_CONTRACT_ADDRESS || "";
  const outDir = valOf("--emit-dir") || resolve(__dirname, "../out/actor-records");
  mkdirSync(outDir, { recursive: true });

  for (const rec of records) {
    const did = toDidDoc(rec, authz);
    const profile = toGetProfileView(rec);
    // canonical (content-addressed) DID doc: _meta.source normalized → stable CID
    const canonical = { ...did, _meta: { ...did._meta, source: "ipfs" } };
    const canonicalBytes = Buffer.from(JSON.stringify(canonical), "utf8");
    const cid = cidV1Raw(canonicalBytes);
    writeFileSync(join(outDir, `${rec.handle}.record.json`), JSON.stringify(rec, null, 2) + "\n");
    writeFileSync(join(outDir, `${rec.handle}.did.json`), JSON.stringify(did, null, 2) + "\n");
    writeFileSync(join(outDir, `${rec.handle}.did.canonical.json`), canonicalBytes);
    writeFileSync(join(outDir, `${rec.handle}.diddoc.cid`), cid + "\n");
    writeFileSync(join(outDir, `${rec.handle}.profile.json`), JSON.stringify(profile, null, 2) + "\n");
  }
  console.log(`parsed ${records.length} actor(s) → ${outDir}`);
  console.log(records.map((r) => {
    const c = cidV1Raw(Buffer.from(JSON.stringify({ ...toDidDoc(r, authz), _meta: { ...toDidDoc(r, authz)._meta, source: "ipfs" } }), "utf8"));
    return `  ${r.glyph ? r.glyph + " " : ""}${r.handle}  (${r.kind}/${r.status})  did.json CID ${c}`;
  }).join("\n"));

  if (has("--pin-did")) {
    for (const rec of records) {
      const f = join(outDir, `${rec.handle}.did.canonical.json`);
      const out = execFileSync("ipfs", ["add", "-Q", "--cid-version=1", f], { encoding: "utf8" }).trim();
      const want = readFileSync(join(outDir, `${rec.handle}.diddoc.cid`), "utf8").trim();
      console.log(`pinned ${rec.handle} did.json → ${out} ${out === want ? "✓" : "✗ MISMATCH " + want}`);
    }
  }

  if (has("--put-kv")) {
    for (const rec of records) {
      const key = `actor:${rec.handle}`;
      console.log(`kv put ${key} …`);
      execFileSync("npx", ["wrangler", "kv", "key", "put", "--binding", "ACTOR_KV", key, JSON.stringify(rec)], { stdio: "inherit", cwd: resolve(__dirname, "..") });
    }
  }

  if (has("--ingest-kotoba")) {
    const endpoint = process.env.KOTOBA_ENDPOINT;
    if (!endpoint) { console.error("KOTOBA_ENDPOINT unset — cannot ingest"); process.exit(2); }
    const batch = { entities: records.map(recordToKgEntity) };
    const url = `${endpoint.replace(/\/$/, "")}/xrpc/com.etzhayyim.apps.kotobase.kg.ingest_batch`;
    console.log(`POST ${url} (${batch.entities.length} entities) …`);
    fetch(url, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(batch) })
      .then(async (r) => console.log(`  → ${r.status} ${await r.text()}`))
      .catch((e) => { console.error("ingest failed:", e.message); process.exit(3); });
  }
}

main();
