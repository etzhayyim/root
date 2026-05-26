import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

type Seed = { slug: string; op: string; processId: string; timeoutMs: number; writeTableAllowlist: string };

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const ownerDid = "did:web:stripe.etzhayyim.com";
const createdAt = "2026-04-29T22:20:00+09:00";
const actorId = "sys.bpmn.seed.stripe";

const writeAll = "vertex_stripe_cardholder,vertex_stripe_issued_card,vertex_stripe_authorization,vertex_stripe_card_credit_allocation,vertex_stripe_card_credit_consumption,vertex_stripe_spending_limit,vertex_credit_wallet,vertex_credit_transaction,vertex_credits_af_event,vertex_credits_public_fund_allocation,vertex_credits_spend_failure";

const seeds: Seed[] = [
  { slug: "create-cardholder", op: "createCardholder", processId: "stripe_create_cardholder", timeoutMs: 120000, writeTableAllowlist: "vertex_stripe_cardholder" },
  { slug: "issue-card", op: "issueCard", processId: "stripe_issue_card", timeoutMs: 120000, writeTableAllowlist: writeAll },
  { slug: "assign-card-credits", op: "assignCardCredits", processId: "stripe_assign_card_credits", timeoutMs: 120000, writeTableAllowlist: writeAll },
  { slug: "get-card-credits", op: "getCardCredits", processId: "stripe_get_card_credits", timeoutMs: 30000, writeTableAllowlist: "" },
  { slug: "handle-authorization", op: "handleAuthorization", processId: "stripe_handle_authorization", timeoutMs: 120000, writeTableAllowlist: "vertex_stripe_authorization,vertex_stripe_card_credit_consumption" },
  { slug: "get-card", op: "getCard", processId: "stripe_get_card", timeoutMs: 30000, writeTableAllowlist: "" },
  { slug: "list-cards", op: "listCards", processId: "stripe_list_cards", timeoutMs: 30000, writeTableAllowlist: "" },
  { slug: "freeze-card", op: "freezeCard", processId: "stripe_freeze_card", timeoutMs: 120000, writeTableAllowlist: "vertex_stripe_issued_card" },
  { slug: "unfreeze-card", op: "unfreezeCard", processId: "stripe_unfreeze_card", timeoutMs: 120000, writeTableAllowlist: "vertex_stripe_issued_card" },
  { slug: "cancel-card", op: "cancelCard", processId: "stripe_cancel_card", timeoutMs: 120000, writeTableAllowlist: "vertex_stripe_issued_card" },
  { slug: "update-spending-limit", op: "updateSpendingLimit", processId: "stripe_update_spending_limit", timeoutMs: 120000, writeTableAllowlist: "vertex_stripe_spending_limit" },
  { slug: "list-transactions", op: "listTransactions", processId: "stripe_list_transactions", timeoutMs: 30000, writeTableAllowlist: "" },
  { slug: "get-cardholder", op: "getCardholder", processId: "stripe_get_cardholder", timeoutMs: 30000, writeTableAllowlist: "" },
  { slug: "wave", op: "wave", processId: "stripe_wave", timeoutMs: 30000, writeTableAllowlist: "" },
  { slug: "stats", op: "stats", processId: "stripe_stats", timeoutMs: 30000, writeTableAllowlist: "" },
  { slug: "handle-commit", op: "handleCommit", processId: "stripe_handle_commit", timeoutMs: 30000, writeTableAllowlist: "" },
];

const sourcePath = (s: Seed) => `00-contracts/bpmn/ai/gftd/stripe/${s.op}.bpmn`;
const processVertexId = (s: Seed) => `at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/stripe-${s.slug}-v1`;
const bindingVertexId = (s: Seed) => `at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/stripe-${s.op}-v1`;

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
        ${bindingVertexId(s)}, ${ownerDid}, ${`app.etzhayyim.apps.stripe.${s.op}`}, ${s.processId}, 1,
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
