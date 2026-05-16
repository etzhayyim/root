import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

type Seed = { slug: string; op: string; processId: string; timeoutMs: number; writeTableAllowlist: string };

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const ownerDid = "did:web:mold-allergy.gftd.ai";
const createdAt = "2026-04-30T21:31:00+09:00";
const actorId = "sys.bpmn.seed.mold-allergy";

const seeds: Seed[] = [
  { slug: "seed-allergen-catalog", op: "seedAllergenCatalog", processId: "mold_allergy_seed_allergen_catalog", timeoutMs: 120000, writeTableAllowlist: "vertex_mold_allergen" },
  { slug: "record-air-sampling", op: "recordAirSampling", processId: "mold_allergy_record_air_sampling", timeoutMs: 30000, writeTableAllowlist: "vertex_mold_air_sampling" },
  { slug: "propose-slit-candidate", op: "proposeSlitCandidate", processId: "mold_allergy_propose_slit_candidate", timeoutMs: 30000, writeTableAllowlist: "vertex_mold_slit_candidate" },
  { slug: "list-allergens", op: "listAllergens", processId: "mold_allergy_list_allergens", timeoutMs: 30000, writeTableAllowlist: "" },
  { slug: "list-slit-candidates", op: "listSlitCandidates", processId: "mold_allergy_list_slit_candidates", timeoutMs: 30000, writeTableAllowlist: "" },
];

const sourcePath = (s: Seed) => `00-contracts/bpmn/ai/gftd/moldAllergy/${s.op}.bpmn`;
const processVertexId = (s: Seed) => `at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/mold-allergy-${s.slug}-v1`;
const bindingVertexId = (s: Seed) => `at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/mold-allergy-${s.op}-v1`;

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const s of seeds) {
    const xml = readFileSync(path.resolve(repoRoot, sourcePath(s)), "utf8");
    const size = Buffer.byteLength(xml, "utf8");
    await sql`
      INSERT INTO vertex_bpmn_process_def (
        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,
        actor_did, org_did
      )
      SELECT
        ${processVertexId(s)}, ${ownerDid}, ${s.processId}, 1,
        ${xml}, CAST(${size} AS integer), ${sourcePath(s)}, 'active',
        ${createdAt}, 100, ${ownerDid}, ${ownerDid}, ${actorId},
        ${ownerDid}, 'anon'
      WHERE NOT EXISTS (
        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${processVertexId(s)}
      )
    `.execute(db);

    await sql`
      INSERT INTO vertex_bpmn_lexicon_binding (
        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,
        result_timeout_ms, write_table_allowlist, status, created_at,
        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did
      )
      SELECT
        ${bindingVertexId(s)}, ${ownerDid}, ${`ai.gftd.apps.moldAllergy.${s.op}`}, ${s.processId}, 1,
        CAST(${s.timeoutMs} AS integer), ${s.writeTableAllowlist}, 'active', ${createdAt},
        100, ${ownerDid}, ${ownerDid}, ${actorId}, ${ownerDid}, 'anon'
      WHERE NOT EXISTS (
        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVertexId(s)}
      )
    `.execute(db);
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const s of seeds) {
    await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVertexId(s)}`.execute(db);
    await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${processVertexId(s)}`.execute(db);
  }
}
