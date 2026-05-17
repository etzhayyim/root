import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

type Seed = {
  actor: string;
  op: string;
  slug: string;
  processId: string;
  timeoutMs: number;
  writeTableAllowlist: string;
};

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const ownerDid = "did:web:bpmn.etzhayyim.com";
const createdAt = "2026-05-08T16:30:00+09:00";
const actorId = "sys.bpmn.seed.moneyforward-control";

const seeds: Seed[] = [
  { actor: "kaikei", op: "generateStatutoryReport", slug: "generate-statutory-report", processId: "kaikei_generate_statutory_report", timeoutMs: 120000, writeTableAllowlist: "vertex_kaikei_statutory_report" },
  { actor: "kaikei", op: "validateMoneyForwardParity", slug: "validate-moneyforward-parity", processId: "kaikei_validate_moneyforward_parity", timeoutMs: 120000, writeTableAllowlist: "vertex_kaikei_moneyforward_parity_run" },
  { actor: "kaisya", op: "registerSaasAsset", slug: "register-saas-asset", processId: "kaisya_register_saas_asset", timeoutMs: 120000, writeTableAllowlist: "vertex_kaisya_saas_asset" },
  { actor: "jinji", op: "recordYearEndAdjustment", slug: "record-year-end-adjustment", processId: "jinji_record_year_end_adjustment", timeoutMs: 120000, writeTableAllowlist: "vertex_atrecord_jinji_year_end_adjustment" },
  { actor: "jinji", op: "registerMynumberVaultRef", slug: "register-mynumber-vault-ref", processId: "jinji_register_mynumber_vault_ref", timeoutMs: 120000, writeTableAllowlist: "vertex_atrecord_jinji_mynumber_vault_ref" },
];

const sourcePath = (s: Seed) => `00-contracts/bpmn/ai/gftd/${s.actor}/${s.op}.bpmn`;
const processVertexId = (s: Seed) => `at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/${s.actor}-${s.slug}-v1`;
const bindingVertexId = (s: Seed) => `at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/${s.actor}-${s.op}-v1`;

export async function up(db: Kysely<unknown>): Promise<void> {
  const existingProcesses = new Set(
    (await sql<{ vertex_id: string }>`
      SELECT vertex_id FROM vertex_bpmn_process_def
      WHERE vertex_id IN (${sql.join(seeds.map(processVertexId))})
    `.execute(db)).rows.map((r) => r.vertex_id),
  );
  const existingBindings = new Set(
    (await sql<{ vertex_id: string }>`
      SELECT vertex_id FROM vertex_bpmn_lexicon_binding
      WHERE vertex_id IN (${sql.join(seeds.map(bindingVertexId))})
    `.execute(db)).rows.map((r) => r.vertex_id),
  );

  for (const s of seeds) {
    const xml = readFileSync(path.resolve(repoRoot, sourcePath(s)), "utf8");
    const size = Buffer.byteLength(xml, "utf8");
    const actorDid = `did:web:${s.actor}.etzhayyim.com`;

    if (!existingProcesses.has(processVertexId(s))) {
      await sql`
        INSERT INTO vertex_bpmn_process_def (
          vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
          source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,
          actor_did, org_did
        )
        VALUES (
          ${processVertexId(s)}, ${ownerDid}, ${s.processId}, 1,
          ${xml}, CAST(${size} AS integer), ${sourcePath(s)}, 'active',
          ${createdAt}, 100, ${ownerDid}, ${ownerDid}, ${actorId},
          ${actorDid}, 'anon'
        )
      `.execute(db);
    }

    if (!existingBindings.has(bindingVertexId(s))) {
      await sql`
        INSERT INTO vertex_bpmn_lexicon_binding (
          vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,
          result_timeout_ms, write_table_allowlist, status, created_at,
          sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did
        )
        VALUES (
          ${bindingVertexId(s)}, ${ownerDid}, ${`ai.gftd.apps.${s.actor}.${s.op}`}, ${s.processId}, 1,
          CAST(${s.timeoutMs} AS integer), ${s.writeTableAllowlist}, 'active', ${createdAt},
          100, ${ownerDid}, ${ownerDid}, ${actorId}, ${actorDid}, 'anon'
        )
      `.execute(db);
    }
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const s of seeds) {
    await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVertexId(s)}`.execute(db);
    await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${processVertexId(s)}`.execute(db);
  }
}
