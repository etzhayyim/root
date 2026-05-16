import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

type Seed = {
  proc: string;
  bpmnProcessId: string;
  nsid: string;
  resultTimeoutMs: number;
  writeTableAllowlist: string;
};

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const ownerDid = "did:web:omise.gftd.ai";
const createdAt = "2026-05-07T01:15:00Z";
const actorId = "sys.bpmn.seed.omise";

const snake = (proc: string) => proc.replace(/([A-Z])/g, "_$1").toLowerCase();
const slug = (proc: string) => proc.replace(/([A-Z])/g, "-$1").toLowerCase();
const writeTables: Record<string, string> = {
  acceptOrder: "vertex_OmiseOrder",
  addToCart: "vertex_OmiseCart",
  approveSeller: "vertex_OmiseSeller",
  archiveProduct: "vertex_OmiseProduct",
  clearCart: "vertex_OmiseCart",
  createCoupon: "vertex_OmiseCoupon",
  createOrder: "vertex_OmiseOrder,vertex_OmiseCart",
  createProduct: "vertex_OmiseProduct",
  createShipment: "vertex_OmiseShipment",
  deactivateCoupon: "vertex_OmiseCoupon",
  markReadyToShip: "vertex_OmiseOrder",
  registerSeller: "vertex_OmiseSeller",
  rejectOrder: "vertex_OmiseOrder",
  removeFromCart: "vertex_OmiseCart",
  requestPayout: "vertex_OmisePayout",
  requestPickup: "vertex_OmisePickupRequest",
  resolveDispute: "vertex_OmiseDispute",
  submitReview: "vertex_OmiseReview",
  suspendSeller: "vertex_OmiseSeller",
  updateInventory: "vertex_OmiseProduct",
  updateProduct: "vertex_OmiseProduct",
  updateSellerProfile: "vertex_OmiseSeller",
  updateShipmentStatus: "vertex_OmiseShipment",
};

const procs = [
  "acceptOrder",
  "addToCart",
  "applyCoupon",
  "approveSeller",
  "archiveProduct",
  "cardHome",
  "clearCart",
  "createCoupon",
  "createOrder",
  "createProduct",
  "createShipment",
  "deactivateCoupon",
  "getCart",
  "getOrder",
  "getProduct",
  "getSellerBalance",
  "getSellerProfile",
  "getSellerRevenue",
  "getShipment",
  "listCoupons",
  "listOrders",
  "listPendingSellers",
  "listReviews",
  "listSellerOrders",
  "listSellerProducts",
  "listSellers",
  "listSettlements",
  "listShipments",
  "markReadyToShip",
  "platformAnalytics",
  "registerSeller",
  "rejectOrder",
  "removeFromCart",
  "requestPayout",
  "requestPickup",
  "resolveDispute",
  "searchProducts",
  "submitReview",
  "suspendSeller",
  "updateInventory",
  "updateProduct",
  "updateSellerProfile",
  "updateShipmentStatus",
];

const seeds: Seed[] = procs.map((proc) => ({
  proc,
  bpmnProcessId: `omise_${snake(proc)}`,
  nsid: `ai.gftd.apps.omise.${proc}`,
  resultTimeoutMs: 30000,
  writeTableAllowlist: writeTables[proc] ?? "",
}));

const bpmnPath = (s: Seed) => `00-contracts/bpmn/ai/gftd/omise/${s.proc}.bpmn`;
const processVid = (s: Seed) => `at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/omise-${slug(s.proc)}-v1`;
const bindingVid = (s: Seed) => `at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/omise-${slug(s.proc)}-v1`;

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const s of seeds) {
    const xml = readFileSync(path.resolve(repoRoot, bpmnPath(s)), "utf8");
    const size = Buffer.byteLength(xml, "utf8");
    await sql`
      INSERT INTO vertex_bpmn_process_def (
        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
        source_path, status, created_at, sensitivity_ord,
        org_id, user_id, actor_id, actor_did, org_did
      )
      SELECT
        ${processVid(s)}, ${ownerDid}, ${s.bpmnProcessId}, 1,
        ${xml}, CAST(${size} AS integer), ${bpmnPath(s)}, 'active',
        ${createdAt}, 100, ${ownerDid}, ${ownerDid}, ${actorId},
        ${ownerDid}, 'anon'
      WHERE NOT EXISTS (
        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${processVid(s)}
      )
    `.execute(db);

    await sql`
      INSERT INTO vertex_bpmn_lexicon_binding (
        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,
        result_timeout_ms, write_table_allowlist, status, created_at,
        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did
      )
      SELECT
        ${bindingVid(s)}, ${ownerDid}, ${s.nsid}, ${s.bpmnProcessId}, 1,
        ${s.resultTimeoutMs}, ${s.writeTableAllowlist}, 'active', ${createdAt},
        100, ${ownerDid}, ${ownerDid}, ${actorId}, ${ownerDid}, 'anon'
      WHERE NOT EXISTS (
        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVid(s)}
      )
    `.execute(db);
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const s of seeds) {
    await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVid(s)}`.execute(db);
    await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${processVid(s)}`.execute(db);
  }
}
