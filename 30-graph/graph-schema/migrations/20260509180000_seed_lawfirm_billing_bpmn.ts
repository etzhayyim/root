import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const readContract = (p: string) => readFileSync(path.resolve(repoRoot, p), "utf8");

const SEED_CREATED_AT = "2026-05-08T00:00:00Z";
const SEED_OWNER_DID = "did:web:lawfirm.etzhayyim.com";
const SEED_ACTOR_TAG = "sys.bpmn.seed.lawfirm";

const PROCESSES = [
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/lawfirm-subscription-start-v1",
    bpmnProcessId: "lawfirm_subscription_start",
    sourcePath: "00-contracts/bpmn/ai/gftd/lawfirm/subscriptionStart.bpmn",
  },
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/lawfirm-connect-onboard-v1",
    bpmnProcessId: "lawfirm_connect_onboard",
    sourcePath: "00-contracts/bpmn/ai/gftd/lawfirm/connectOnboard.bpmn",
  },
];

const BINDINGS = [
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/lawfirm-subscription-start-xrpc-v1",
    nsid: "app.etzhayyim.apps.lawfirm.subscriptionStart",
    bpmnProcessId: "lawfirm_subscription_start",
    resultTimeoutMs: 60_000,
  },
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/lawfirm-connect-onboard-xrpc-v1",
    nsid: "app.etzhayyim.apps.lawfirm.connectOnboard",
    bpmnProcessId: "lawfirm_connect_onboard",
    resultTimeoutMs: 60_000,
  },
];

/**
 * Seed: lawfirm.billing.* BPMN process_def + lexicon bindings.
 *
 * Closes the lexicon → BPMN → primitive chain for the W11-W12 conversion path:
 *
 *   app.etzhayyim.apps.lawfirm.subscriptionStart  (lexicon)
 *     → vertex_bpmn_lexicon_binding         (this seed)
 *       → vertex_bpmn_process_def           (this seed)
 *         → BPMN serviceTask: lawfirm.billing.modeAStartSubscription
 *           → task_billing_mode_a_start_subscription (lawfirm_billing.py)
 *             → vertex_lawfirm_tenant.{stripe_customer_id, billing_mode}
 *
 *   app.etzhayyim.apps.lawfirm.connectOnboard     (lexicon)
 *     → ... lawfirm.billing.modeBOnboardConnect
 *       → vertex_lawfirm_tenant.{stripe_connect_account_id, billing_mode='rev_share_y1'}
 *
 * The existing app.etzhayyim.apps.lawfirm.stripeWebhook lexicon + paymentIntake
 * BPMN (seeded earlier in 20260508998000) handle invoice.paid events; the
 * webhook handler delegates to lawfirm.billing.processWebhookInvoicePaid
 * task type which is registered alongside the others (not surfaced as XRPC).
 *
 * F5 watcher auto-deploys both process_def rows on insert.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  for (const p of PROCESSES) {
    const xml = readContract(p.sourcePath);
    const size = Buffer.byteLength(xml, "utf8");
    await sql`
      INSERT INTO vertex_bpmn_process_def
        (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
         source_path, status, created_at, sensitivity_ord,
         org_id, user_id, actor_id)
      SELECT
        ${p.vertexId}, ${SEED_OWNER_DID}, ${p.bpmnProcessId}, 1,
        ${xml}, CAST(${size} AS integer), ${p.sourcePath}, 'active',
        ${SEED_CREATED_AT}, 1, ${SEED_OWNER_DID}, ${SEED_OWNER_DID}, ${SEED_ACTOR_TAG}
      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${p.vertexId})
    `.execute(db);
  }

  for (const b of BINDINGS) {
    await sql`
      INSERT INTO vertex_bpmn_lexicon_binding
        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,
         result_timeout_ms, status, created_at, sensitivity_ord,
         org_id, user_id, actor_id)
      SELECT
        ${b.vertexId}, ${SEED_OWNER_DID}, ${b.nsid}, ${b.bpmnProcessId}, 1,
        CAST(${b.resultTimeoutMs} AS integer), 'active',
        ${SEED_CREATED_AT}, 1, ${SEED_OWNER_DID}, ${SEED_OWNER_DID}, ${SEED_ACTOR_TAG}
      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${b.vertexId})
    `.execute(db);
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const b of BINDINGS) {
    await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${b.vertexId}`.execute(db);
  }
  for (const p of PROCESSES) {
    await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${p.vertexId}`.execute(db);
  }
}
