#!/usr/bin/env node
// Emit the kotoba `kg.ingest_batch` body that materializes the entity mirror
// actors as `:actor/*` datoms in the `actors-v1` graph — the SOURCE the
// `actor-ns-count` MaterializedView (00-contracts/schemas/actor-count-mv.kotoba.edn)
// is maintained from (ADR-2606042330 D4 / ADR-2606041151 B).
//
// Also computes the per-namespace + total counts the MV's `GROUP BY namespace`
// would maintain — so the count semantics are verifiable offline (no kotoba
// server needed). `--verify` asserts the counts equal the generated registries.
//
// Reads the generated entity-handles.<ns>.gen.ts registries (the same SSoT the
// apex Worker uses). Node stdlib only. Charter: mirror-only (isMirror const),
// person-excluded (performerType ∈ {organization,system}).
//
//   node 70-tools/scripts/entity-actors/emit_ingest_batch.mjs            # → batch JSON
//   node 70-tools/scripts/entity-actors/emit_ingest_batch.mjs --verify   # counts only
//
import { readFileSync, existsSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..", "..", "..");
const REG = join(ROOT, "50-infra/etzhayyim-did-web/src/registry");

// namespace → {performerType} (mirror of entity-actors.ts ENTITY_NAMESPACES; the
// charter invariants live in the lexicon + TS, repeated here only for the datom).
const NS = {
  gov: "organization",
  corp: "organization",
  cable: "system",
  station: "system",
  craft: "system",
};

/** Parse `["handle", "displayName"],` entries out of a generated .gen.ts Map. */
function readRegistry(ns) {
  const p = join(REG, `entity-handles.${ns}.gen.ts`);
  if (!existsSync(p)) return [];
  const text = readFileSync(p, "utf8");
  const out = [];
  const re = /\[\s*"((?:[^"\\]|\\.)*)"\s*,\s*"((?:[^"\\]|\\.)*)"\s*\]/g;
  let m;
  while ((m = re.exec(text)) !== null) {
    out.push([JSON.parse(`"${m[1]}"`), JSON.parse(`"${m[2]}"`)]);
  }
  return out;
}

/** One mirror actor → a `:actor/*` entity for kg.ingest_batch. */
function actorEntity(handle, name, ns) {
  return {
    id: handle,
    type: "MirrorActor",
    labelEn: name,
    claims: [
      { pred: "actor/handle", value: handle },
      { pred: "actor/namespace", value: ns }, // ← count MV GROUP-BY key
      { pred: "actor/displayName", value: name },
      { pred: "actor/isMirror", value: "true" }, // G1
      { pred: "actor/performerType", value: NS[ns] }, // G3 (never person)
      { pred: "actor/did", value: `did:web:etzhayyim.com:actor:${handle}` },
    ],
  };
}

export function build() {
  const entities = [];
  const counts = {}; // the MV's `GROUP BY namespace` output, computed offline
  for (const ns of Object.keys(NS)) {
    const rows = readRegistry(ns);
    counts[ns] = rows.length;
    for (const [handle, name] of rows) entities.push(actorEntity(handle, name, ns));
  }
  const total = Object.values(counts).reduce((a, n) => a + n, 0);
  return { entities, counts, total };
}

export { NS };

/** Reference of `MvRegistry::maintain` for the `actor-ns-count` COUNT-GROUP-BY
 *  MV: fold a stream of {ns, op} deltas (op: +1 assert / −1 retract) into the
 *  maintained per-namespace tally. Mirrors kotoba-kqe mv.rs assert/retract
 *  semantics (assert→+1, retract→−1, assert+retract of same datom nets 0). */
export function maintainCount(deltas) {
  const counts = {};
  for (const { ns, op } of deltas) counts[ns] = (counts[ns] ?? 0) + op;
  return counts;
}

// CLI side-effects only when run directly (not when imported by the test).
const RUN_DIRECTLY =
  process.argv[1] && process.argv[1].endsWith("emit_ingest_batch.mjs");
if (!RUN_DIRECTLY) {
  // imported as a module — export-only, no stdout/exit.
} else {
const { entities, counts, total } = build();
const verify = process.argv.includes("--verify");

if (verify) {
  // Re-derive ENTITY_TOTAL_COUNT from the same gen files and assert equality.
  console.log("actor-ns-count MV (GROUP BY namespace) — offline materialization:");
  for (const [ns, n] of Object.entries(counts)) {
    console.log(`  :actor.ns.count/${ns.padEnd(8)} ${String(n).padStart(6)}`);
  }
  console.log(`  :actor.count/total      ${String(total).padStart(6)}`);
  if (entities.length !== total) {
    console.error(`FAIL: entity count ${entities.length} != total ${total}`);
    process.exit(1);
  }
  console.log(`OK: ${entities.length} :actor/* datoms === total ${total}`);
} else {
  // The kg.ingest_batch body — POST to com.etzhayyim.apps.kotobase.kg.ingest_batch
  // (operator-gated, G8). Carries the MV source + the precomputed count datoms.
  const countEntities = [
    {
      id: ":actor.count/total",
      type: "MvCount",
      labelEn: "entity mirror-actor total (actor-total-count MV)",
      claims: [{ pred: "actor.count/total", value: String(total) }],
    },
    ...Object.entries(counts).map(([ns, n]) => ({
      id: `:actor.ns.count/${ns}`,
      type: "MvCount",
      labelEn: `${ns} mirror-actor count (actor-ns-count MV)`,
      claims: [{ pred: `actor.ns.count/${ns}`, value: String(n) }],
    })),
  ];
  process.stdout.write(
    JSON.stringify({ graph: "actors-v1", entities: [...entities, ...countEntities] }) + "\n",
  );
}
}
