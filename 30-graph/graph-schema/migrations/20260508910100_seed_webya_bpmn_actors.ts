import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * webya.etzhayyim.com BPMN-as-actor seeding (ADR-0056 + ADR-2605080600).
 *
 * createSite / reviseSite  → routing_target='langgraph'  (LangGraph Server)
 * domainSslMonitor         → Zeebe timer-start R/PT30M
 * seoAudit                 → Zeebe cron timer 0 0 0 ? * MON
 *
 * XRPC bindings (2):
 *   com.etzhayyim.apps.webya.createSite   → webya_create_site   (langgraph)
 *   com.etzhayyim.apps.webya.reviseSite   → webya_revise_site   (langgraph)
 *
 * Process defs (4): createSite + reviseSite stubs + domainSslMonitor + seoAudit
 */

type P = {
  vertexId: string;
  bpmnProcessId: string;
  sourcePath: string;
  ownerDid: string;
};
type B = {
  vertexId: string;
  nsid: string;
  bpmnProcessId: string;
  ownerDid: string;
  resultTimeoutMs: number;
  routingTarget: "zeebe" | "langgraph";
};

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const readContract = (p: string) => readFileSync(path.resolve(repoRoot, p), "utf8");
const createdAt = "2026-05-08T09:10:00Z";
const ownerDid = "did:web:webya.etzhayyim.com";

const processSeeds: P[] = [
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/webya-create-site-v1",
    bpmnProcessId: "webya_create_site",
    sourcePath: "00-contracts/bpmn/com/etzhayyim/webya/createSite.bpmn",
    ownerDid,
  },
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/webya-revise-site-v1",
    bpmnProcessId: "webya_revise_site",
    sourcePath: "00-contracts/bpmn/com/etzhayyim/webya/reviseSite.bpmn",
    ownerDid,
  },
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/webya-domain-ssl-monitor-v1",
    bpmnProcessId: "webya_domain_ssl_monitor",
    sourcePath: "00-contracts/bpmn/com/etzhayyim/webya/domainSslMonitor.bpmn",
    ownerDid,
  },
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/webya-seo-audit-v1",
    bpmnProcessId: "webya_seo_audit",
    sourcePath: "00-contracts/bpmn/com/etzhayyim/webya/seoAudit.bpmn",
    ownerDid,
  },
];

const bindingSeeds: B[] = [
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/webya-createSite-v1",
    nsid: "com.etzhayyim.apps.webya.createSite",
    bpmnProcessId: "webya_create_site",
    ownerDid,
    resultTimeoutMs: 300_000,
    routingTarget: "langgraph",
  },
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/webya-reviseSite-v1",
    nsid: "com.etzhayyim.apps.webya.reviseSite",
    bpmnProcessId: "webya_revise_site",
    ownerDid,
    resultTimeoutMs: 180_000,
    routingTarget: "langgraph",
  },
];

export async function up(db: Kysely<unknown>): Promise<void> {
  // Process defs
  for (const s of processSeeds) {
    const bpmnXml = readContract(s.sourcePath);
    await sql`
      INSERT INTO vertex_bpmn_process_def
        (vertex_id, bpmn_process_id, version, xml,
         owner_did, status, deployed_at, created_at)
      VALUES (
        ${s.vertexId}, ${s.bpmnProcessId}, 1, ${bpmnXml},
        ${s.ownerDid}, 'active', NULL, ${createdAt}
      )
    `.execute(db);
  }

  await sql`FLUSH`.execute(db);

  // Lexicon bindings (createSite + reviseSite, langgraph routed)
  for (const b of bindingSeeds) {
    await sql`
      INSERT INTO vertex_bpmn_lexicon_binding
        (vertex_id, nsid, bpmn_process_id, owner_did,
         result_timeout_ms, routing_target, status, created_at)
      VALUES (
        ${b.vertexId}, ${b.nsid}, ${b.bpmnProcessId}, ${b.ownerDid},
        ${b.resultTimeoutMs}, ${b.routingTarget}, 'active', ${createdAt}
      )
    `.execute(db);
  }

  await sql`FLUSH`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const b of bindingSeeds) {
    await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${b.vertexId}`.execute(db);
  }
  for (const s of processSeeds) {
    await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${s.vertexId}`.execute(db);
  }
}
