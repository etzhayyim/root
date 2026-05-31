import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

type Seed = { slug: string; op: string; processId: string; sourcePath: string; timeoutMs: number; writeTableAllowlist: string };

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const ownerDid = "did:web:credits.etzhayyim.com";
const createdAt = "2026-04-29T22:01:00+09:00";
const actorId = "sys.bpmn.seed.credits";

const ledgerTables = "vertex_credit_wallet,vertex_credit_transaction,vertex_credits_af_event,vertex_credits_public_fund_allocation,vertex_credits_spend_failure";

const seeds: Seed[] = [
  { slug: "check-spend-allowed", op: "checkSpendAllowed", processId: "credits_check_spend_allowed", sourcePath: "00-contracts/bpmn/ai/gftd/credits/checkSpendAllowed.bpmn", timeoutMs: 30000, writeTableAllowlist: "" },
  { slug: "spend-credits", op: "spendCredits", processId: "credits_spend_credits", sourcePath: "00-contracts/bpmn/ai/gftd/credits/spendCredits.bpmn", timeoutMs: 30000, writeTableAllowlist: ledgerTables },
  { slug: "reward-from-compute", op: "rewardFromCompute", processId: "credits_reward_from_compute", sourcePath: "00-contracts/bpmn/ai/gftd/credits/rewardFromCompute.bpmn", timeoutMs: 30000, writeTableAllowlist: "vertex_credit_wallet,vertex_credit_transaction,vertex_credits_af_event" },
  { slug: "reward-from-hc", op: "rewardFromHC", processId: "credits_reward_from_hc", sourcePath: "00-contracts/bpmn/ai/gftd/credits/rewardFromHC.bpmn", timeoutMs: 30000, writeTableAllowlist: "vertex_credit_wallet,vertex_credit_transaction,vertex_credits_af_event" },
  { slug: "process-commit-spend", op: "processCommitSpend", processId: "credits_process_commit_spend", sourcePath: "00-contracts/bpmn/ai/gftd/credits/processCommitSpend.bpmn", timeoutMs: 30000, writeTableAllowlist: ledgerTables },
  { slug: "heartbeat", op: "heartbeat", processId: "credits_heartbeat", sourcePath: "00-contracts/bpmn/ai/gftd/credits/heartbeat.bpmn", timeoutMs: 30000, writeTableAllowlist: "" },
];

const processVertexId = (s: Seed) => `at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/credits-${s.slug}-v1`;
const bindingVertexId = (s: Seed) => `at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/credits-${s.op}-v1`;

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const s of seeds) {
    const xml = readFileSync(path.resolve(repoRoot, s.sourcePath), "utf8");
    const size = Buffer.byteLength(xml, "utf8");
    await sql`
      INSERT INTO vertex_bpmn_process_def (
        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,
        actor_did, org_did
      )
      SELECT
        ${processVertexId(s)}, ${ownerDid}, ${s.processId}, 1,
        ${xml}, CAST(${size} AS integer), ${s.sourcePath}, 'active',
        ${createdAt}, 1, ${ownerDid}, ${ownerDid}, ${actorId},
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
        ${bindingVertexId(s)}, ${ownerDid}, ${`app.etzhayyim.apps.credits.${s.op}`}, ${s.processId}, 1,
        CAST(${s.timeoutMs} AS integer), ${s.writeTableAllowlist}, 'active', ${createdAt},
        1, ${ownerDid}, ${ownerDid}, ${actorId}, ${ownerDid}, 'anon'
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
