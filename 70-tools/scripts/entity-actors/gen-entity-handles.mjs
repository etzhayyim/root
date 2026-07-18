#!/usr/bin/env node
// AUTOGENERATOR for entity-as-actor handle registries (ADR-2606042330).
//
// Reads each knowledge-graph actor's seed/merged EDN, extracts public-entity
// ids, derives a single-label `did:web:etzhayyim.com:actor:<handle>` handle
// (namespace-prefixed), and emits one
//   50-infra/etzhayyim-did-web/src/registry/entity-handles.<ns>.gen.ts
// per namespace — each a `ReadonlyMap<handle, displayName>` + TOTAL_COUNT +
// GENERATED_AT, mirroring unispsc-handles.gen.ts.
//
// Charter (ADR-2606042330): mirror-actors only, public/power entities only,
// person-entities are not a source here (none of these seeds carry natural
// persons). Node stdlib only (no deps). Regenerate:
//   node 70-tools/scripts/entity-actors/gen-entity-handles.mjs
//
import { readFileSync, writeFileSync, existsSync, readdirSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..", "..", "..");
const OUT_DIR = join(ROOT, "50-infra/etzhayyim-did-web/src/registry");
// Deterministic stamp (ADR date) so re-running produces no spurious churn.
const GENERATED_AT = "2026-06-14T00:00:00+00:00";

// ── namespace config ──────────────────────────────────────────────────────
// Each namespace unions one or more EDN sources. `idKey`/`nameKey` are the EDN
// attribute keywords; `idStrip` is removed from the id before dot→hyphen so the
// handle carries the namespace prefix (e.g. org.corp.tw.tsmc → corp-tw-tsmc).
const NAMESPACES = [
  {
    ns: "gov",
    sources: [{ dir: "orgs/etzhayyim/com-etzhayyim-ooyake/registry", glob: /^gov-units\..*\.edn$/ }],
    idKey: ":gov.unit/id",
    nameKey: ":gov.unit/name-en",
    idStrip: "", // ids already start with "gov."
  },
  {
    ns: "corp",
    sources: [
      { file: "orgs/etzhayyim/com-etzhayyim-kabuto/data/companies.merged.kotoba.edn" },
      { file: "orgs/etzhayyim/com-etzhayyim-tsumugi/data/seed-power-graph.kotoba.edn" },
    ],
    // corp unifies kabuto :company/* + tsumugi :organism/* (both org.corp.*)
    idKeys: [":company/id", ":organism/id"],
    nameKey: ":company/name",
    idStrip: "org.", // org.corp.tw.tsmc → corp.tw.tsmc → corp-tw-tsmc
  },
  {
    ns: "cable",
    sources: [{ file: "orgs/etzhayyim/com-etzhayyim-watatsuna/data/seed-cable-graph.kotoba.edn" }],
    idKey: ":cable/id",
    nameKey: ":cable/name",
    idStrip: "",
  },
  {
    ns: "station",
    sources: [{ file: "orgs/etzhayyim/com-etzhayyim-watatsuna/data/seed-cable-graph.kotoba.edn" }],
    idKey: ":station/id",
    nameKey: ":station/name",
    idStrip: "",
  },
  {
    ns: "craft",
    sources: [{ file: "orgs/etzhayyim/com-etzhayyim-watari/data/seed-craft-graph.kotoba.edn" }],
    idKey: ":craft/id",
    nameKey: ":craft/name",
    idStrip: "",
  },
];

// id → single-label handle: strip prefix, dot→hyphen, sanitize to HANDLE_REGEX
// (lowercase alnum + hyphen, no leading/trailing hyphen, ≤63 chars).
function toHandle(id, idStrip) {
  let s = id;
  if (idStrip && s.startsWith(idStrip)) s = s.slice(idStrip.length);
  s = s
    .toLowerCase()
    .replace(/[._\s/]+/g, "-")
    .replace(/[^a-z0-9-]/g, "-")
    .replace(/-+/g, "-")
    .replace(/^-+|-+$/g, "");
  if (s.length > 63) s = s.slice(0, 63).replace(/-+$/g, "");
  return s;
}

// Extract {id,name} pairs. For each idKey occurrence, find the nearest nameKey
// within a bounded forward window (records are small; both one-line and
// multi-line record shapes are covered).
function extractPairs(text, idKeys, nameKey) {
  const keys = Array.isArray(idKeys) ? idKeys : [idKeys];
  const pairs = [];
  for (const idKey of keys) {
    const re = new RegExp(escapeRe(idKey) + '\\s+"([^"]+)"', "g");
    let m;
    while ((m = re.exec(text)) !== null) {
      const id = m[1];
      const windowText = text.slice(m.index, m.index + 600);
      const nameMatch = new RegExp(escapeRe(nameKey) + '\\s+"([^"]+)"').exec(
        windowText,
      );
      pairs.push({ id, name: nameMatch ? nameMatch[1] : null });
    }
  }
  return pairs;
}

function escapeRe(s) {
  return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

// Fallback display name derived from the handle (Title Case of the tail).
function deriveName(handle) {
  return handle
    .split("-")
    .slice(1) // drop the namespace prefix
    .map((w) => (w.length <= 3 ? w.toUpperCase() : w[0].toUpperCase() + w.slice(1)))
    .join(" ")
    .trim();
}

function readSources(sources) {
  let text = "";
  for (const src of sources) {
    if (src.file) {
      const p = join(ROOT, src.file);
      if (existsSync(p)) text += "\n" + readFileSync(p, "utf8");
    } else if (src.dir) {
      const d = join(ROOT, src.dir);
      if (!existsSync(d)) continue;
      for (const f of readdirSync(d)) {
        if (src.glob.test(f)) text += "\n" + readFileSync(join(d, f), "utf8");
      }
    }
  }
  return text;
}

const summary = [];

for (const cfg of NAMESPACES) {
  const text = readSources(cfg.sources);
  const pairs = extractPairs(text, cfg.idKeys ?? cfg.idKey, cfg.nameKey);

  // Union by handle; first non-null name wins, else derive.
  const byHandle = new Map();
  for (const { id, name } of pairs) {
    const handle = toHandle(id, cfg.idStrip);
    if (!handle) continue;
    const existing = byHandle.get(handle);
    const display = name ?? existing ?? null;
    if (!byHandle.has(handle) || (existing == null && display != null)) {
      byHandle.set(handle, display);
    }
  }
  // Resolve null names to derived; sort for deterministic output.
  const entries = [...byHandle.keys()]
    .sort()
    .map((h) => [h, byHandle.get(h) ?? deriveName(h)]);

  const NS = cfg.ns.toUpperCase();
  const lines = entries
    .map(([h, n]) => `  [${JSON.stringify(h)}, ${JSON.stringify(n)}],`)
    .join("\n");

  const out = `// AUTOGENERATED — do not edit.
// Source: knowledge-graph actor seed EDN (see gen-entity-handles.mjs config).
// Regenerate: node 70-tools/scripts/entity-actors/gen-entity-handles.mjs
// ADR-2606042330 — entity-as-actor mirror registry (namespace: ${cfg.ns}).
//
// Each entry is [handle, displayName] for a PUBLIC/POWER entity mirror-actor.
// did:web:etzhayyim.com:actor:${cfg.ns}-<...> — keyless mirror, NOT the entity
// itself (no impersonation; verificationMethod:[]; isMirror=true).

export const ${NS}_TOTAL_COUNT = ${entries.length};
export const ${NS}_GENERATED_AT = ${JSON.stringify(GENERATED_AT)};

// handle → displayName. Membership check is O(1) via .has(); name powers the
// searchActors short-circuit + getProfile view in the apex Worker.
export const ${NS}_ENTITIES: ReadonlyMap<string, string> = new Map([
${lines}
]);
`;

  const outPath = join(OUT_DIR, `entity-handles.${cfg.ns}.gen.ts`);
  writeFileSync(outPath, out);
  summary.push({ ns: cfg.ns, count: entries.length, file: outPath });
}

console.log("entity-actor handle registries generated (ADR-2606042330):");
for (const s of summary) {
  console.log(`  ${s.ns.padEnd(8)} ${String(s.count).padStart(6)}  ${s.file.replace(ROOT + "/", "")}`);
}
console.log(`  ${"TOTAL".padEnd(8)} ${String(summary.reduce((a, s) => a + s.count, 0)).padStart(6)}`);
