#!/usr/bin/env node
/**
 * gen-gov-atlas-index.mjs — build the public machine-readable gov-atlas index
 * (`gov-units.json`) from the SAME authoritative sources ooyake ingests into the
 * kotoba `gov-atlas-v1` graph. Per ADR-2606021600.
 *
 * Sources (no fabrication, G5; synthetic tiers excluded — see ingest_states_global.py):
 *   - orgs/etzhayyim/com-etzhayyim-ooyake/registry/gov-units.seed.edn          (proof-of-model chain + world tops)
 *   - orgs/etzhayyim/com-etzhayyim-ooyake/registry/gov-units.jp-central.seed.edn (JP 府省庁)
 *   - 60-apps/etzhayyim-project-states/data/gov/jpn/{prefecture,municipality}.ndjson
 *   - 60-apps/etzhayyim-project-states/data/gov/<cc>/municipality.ndjson  (real-named only)
 *
 * Emits a compact array of {id,name,nameEn,level,jurisdiction,parent,url,sourcing}
 * to ./out/gov-units.json. Put into ACTOR_KV (key `gov-atlas:index`) with
 * `wrangler kv key put --binding ACTOR_KV gov-atlas:index --path out/gov-units.json --remote`;
 * the Worker serves it at /.well-known/gov-units.json.
 *
 * Offline, deterministic. No network.
 */
import { readFileSync, writeFileSync, mkdirSync, readdirSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve, join } from "node:path";

const __dirname = dirname(fileURLToPath(import.meta.url));
const REPO = resolve(__dirname, "../../..");
const OOYAKE = join(REPO, "orgs/etzhayyim/com-etzhayyim-ooyake/registry");
const STATES = join(REPO, "60-apps/etzhayyim-project-states/data/gov");

// ── tiny EDN reader (maps/vectors/strings/keywords/numbers/comments) ──────────
function parseEdn(src) {
  let i = 0; const n = src.length;
  const skip = () => { while (i < n) { const c = src[i]; if (" \t\r\n,".includes(c)) { i++; continue; } if (c === ";") { while (i < n && src[i] !== "\n") i++; continue; } break; } };
  function read() { skip(); const c = src[i]; if (c === '"') return rs(); if (c === "{") return rm(); if (c === "[") return rv(); return ra(); }
  function rs() { i++; let s = ""; while (i < n) { const c = src[i++]; if (c === "\\") { const e = src[i++]; s += e === "n" ? "\n" : e === "t" ? "\t" : e; } else if (c === '"') return s; else s += c; } throw new Error("str"); }
  function rv() { i++; const a = []; for (;;) { skip(); if (src[i] === "]") { i++; return a; } a.push(read()); } }
  function rm() { i++; const d = {}; for (;;) { skip(); if (src[i] === "}") { i++; return d; } const k = read(); d[k] = read(); } }
  function ra() { const s = i; while (i < n && !" \t\r\n,;{}[]\"".includes(src[i])) i++; const t = src.slice(s, i); if (t === "true") return true; if (t === "false") return false; if (t === "nil") return null; if (t[0] === ":") return t; const num = Number(t); return Number.isNaN(num) ? t : num; }
  skip(); return read();
}
const kw = (v) => (typeof v === "string" && v[0] === ":" ? v.slice(1) : v);
const ndjson = (p) => existsSync(p) ? readFileSync(p, "utf8").split("\n").filter((l) => l.trim()).map((l) => JSON.parse(l)) : [];
const slug = (s) => (s || "x").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") || "x";
const isSynthetic = (r) => { const nm = r.name || ""; return !nm || nm.startsWith("Dst ") || ["Executive", "Cabinet", "Ministry Of"].includes(nm) || (r.tags || []).some((t) => t.includes("nanoid")); };

// cc -> real English country name, extracted from the INTERPOL NCB row in each
// country's lea.ndjson ("<Country> INTERPOL National Central Bureau"). Real in-repo
// data (not fabricated, G5); 169/195 countries carry it. Used to label the ISO3
// country units instead of the bare code.
const _NCB = " INTERPOL National Central Bureau";
function buildCountryNames() {
  const m = {};
  for (const cc of readdirSync(STATES)) {
    for (const r of ndjson(join(STATES, cc, "lea.ndjson"))) {
      const ne = r.nameEn || "";
      if (ne.endsWith(_NCB)) { m[cc] = ne.slice(0, -_NCB.length).trim(); break; }
    }
  }
  return m;
}
const ccName = buildCountryNames();

const byId = new Map();
const put = (u) => { if (u && u.id && !byId.has(u.id)) byId.set(u.id, u); };

// 1) ooyake EDN seeds (:units)
// FULL committed atlas — every registry/gov-units*.edn (seeds + g20 / world-* /
// oversight-* / adm1-* / intergov / capitals / hq-locations / …). The PUBLISHED index
// conservatively marks ALL units :representative; only the Council bootstrap-attested
// JP pref/city backbone is promoted :authoritative below (validate_atlas check #5).
// (The committed EDN's :maintainer-verified/:authoritative tier is the registry record,
// a distinct thing from what is published as authoritative.)
// hq-location coordinates + romanizations enrich the published record so the /gov
// map can plot real seats and render endonyms with a Latin reading. lat/lon come from
// the committed :gov.address :headquarters rows (building-level where a real seat
// exists; null elsewhere — never fabricated, G5). Additive fields; the validator
// (validate_atlas.py) checks only id/level/sourcing/summary, so this stays in-scope.
const hq = new Map(); // unit-id -> {lat, lon}
for (const f of readdirSync(OOYAKE).filter((n) => /^gov-units.*\.edn$/.test(n)).sort()) {
  const doc = parseEdn(readFileSync(join(OOYAKE, f), "utf8"));
  for (const u of doc[":units"] || []) {
    put({
      id: u[":gov.unit/id"], name: u[":gov.unit/name-local"] || u[":gov.unit/name-en"], nameEn: u[":gov.unit/name-en"],
      nameLocal: u[":gov.unit/name-local"] || "", nameRomanized: u[":gov.unit/name-romanized"] || "",
      level: kw(u[":gov.unit/level"]), jurisdiction: u[":gov.unit/jurisdiction"],
      parent: u[":gov.unit/parent"] || null, url: u[":gov.unit/official-url"] || "",
      sourcing: "representative",
    });
  }
  for (const a of doc[":addresses"] || []) {
    const uid = a[":gov.address/unit"];
    const lat = a[":gov.address/lat"], lon = a[":gov.address/lon"];
    if (uid && typeof lat === "number" && typeof lon === "number" && !hq.has(uid)) hq.set(uid, { lat, lon });
  }
}
// 2) JP prefectures + municipalities (official codes)
for (const r of ndjson(join(STATES, "jpn/prefecture.ndjson"))) {
  const c = r.adminCode;
  put({ id: `gov.jpn.pref.${c}`, name: r.name, nameEn: r.nameEn, level: "prefecture", jurisdiction: `jpn-${c}`, parent: "gov.jpn", url: r.website || "", sourcing: "representative" });
}
for (const r of ndjson(join(STATES, "jpn/municipality.ndjson"))) {
  const c = r.adminCode; const lvl = ["special-ward", "ward"].includes(r.municipalType) ? "ward" : "municipality";
  put({ id: `gov.jpn.city.${c}`, name: r.name, nameEn: r.nameEn, level: lvl, jurisdiction: `jpn-${c.slice(0, 2)}`, parent: `gov.jpn.pref.${c.slice(0, 2)}`, url: r.website || "", sourcing: "representative" });
}
// 3) global real municipalities + ISO3 country stubs
const REAL_COUNTRIES = new Set(["jpn", "usa", "gbr", "deu", "kor"]);
const seenCC = new Set();
for (const cc of readdirSync(STATES).sort()) {
  if (cc === "jpn" || cc === "0" || cc === "intl") continue;
  const rows = ndjson(join(STATES, cc, "municipality.ndjson")).filter((r) => !isSynthetic(r));
  if (!rows.length) continue;
  seenCC.add(cc);
  for (const r of rows) {
    const lvl = ["special-ward", "ward"].includes(r.municipalType) ? "ward" : "municipality";
    put({ id: `gov.${cc}.muni.${slug(r.path || r.name)}`, name: r.name, nameEn: r.nameEn || r.name, level: lvl, jurisdiction: cc, parent: `gov.${cc}`, url: r.website || "", sourcing: "representative" });
  }
}
for (const cc of [...seenCC].sort()) {
  if (REAL_COUNTRIES.has(cc)) continue;
  const nm = ccName[cc] || cc.toUpperCase();  // real name when available, else ISO3 code
  put({ id: `gov.${cc}`, name: nm, nameEn: nm, level: "country", jurisdiction: cc, parent: null, url: "", sourcing: "representative" });
}

const units = [...byId.values()];
// attach hq-location coordinates (building-level seat where one exists; G5: only real
// committed coords, never fabricated). lat/lon omitted entirely when absent.
let withCoords = 0;
for (const u of units) { const c = hq.get(u.id); if (c) { u.lat = c.lat; u.lon = c.lon; withCoords++; } }
const withNameLocal = units.filter((u) => u.nameLocal).length;
// Authoritative tier (BOOTSTRAP-ATTESTATION-reconcile-live.md, Seat 1 Lv7, re-ratify
// at Council 3-of-5): the JP official-code backbone (全国地方公共団体コード / ISO 3166-2:JP)
// is promoted :representative → :authoritative. Mirrors the kotoba node promotion by
// deploy/promote_authoritative.py. Everything else stays :representative (G5).
for (const u of units) {
  if (/^gov\.jpn\.(pref|city)\./.test(u.id)) u.sourcing = "authoritative";
}
const byLevel = {};
for (const u of units) byLevel[u.level] = (byLevel[u.level] || 0) + 1;
const bySourcing = {};
for (const u of units) bySourcing[u.sourcing] = (bySourcing[u.sourcing] || 0) + 1;
const countries = new Set(units.map((u) => u.jurisdiction.split("-")[0])).size;
const index = {
  graph: "gov-atlas-v1",
  generatedFrom: "ooyake seeds + etzhayyim-project-states (real-named municipalities only; synthetic district/ministry/office/lea tiers excluded per G5)",
  adr: "2606021600",
  note: "All units :sourcing :representative / :unverified-seed (G5). Observational mirror + civic wayfinding — never the government, never a target-list (G3/G10).",
  count: units.length,
  countries,
  withCoords,
  withNameLocal,
  byLevel,
  bySourcing,
  units,
};
const outDir = join(__dirname, "../out");
mkdirSync(outDir, { recursive: true });
writeFileSync(join(outDir, "gov-units.json"), JSON.stringify(index));
console.log(`gov-atlas index: ${units.length} units across ${countries} jurisdictions`);
console.log(`enriched: ${withCoords} with hq coords, ${withNameLocal} with name-local`);
console.log(`byLevel:`, JSON.stringify(byLevel));
console.log(`wrote ${join(outDir, "gov-units.json")} (${(JSON.stringify(index).length / 1024).toFixed(1)} KiB)`);
