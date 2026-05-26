import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const ownerDid = "did:web:flight-offer.etzhayyim.com";
const createdAt = "2026-04-27T14:00:00Z";
const actorTag = "sys.bpmn.seed.flight-offer";

interface Entry {
  bpmnProcessId: string;
  nsid: string;
  sourcePath: string;
  resultTimeoutMs: number;
  slug: string;
}

const entries: Entry[] = [
  {
    bpmnProcessId: "flight_offer_remove_watch",
    nsid: "app.etzhayyim.apps.flightOffer.removeWatch",
    sourcePath: "00-contracts/bpmn/ai/gftd/flight-offer/removeWatch.bpmn",
    resultTimeoutMs: 15000,
    slug: "flight-offer-remove-watch-v1",
  },
  {
    bpmnProcessId: "flight_offer_list_watch",
    nsid: "app.etzhayyim.apps.flightOffer.listWatch",
    sourcePath: "00-contracts/bpmn/ai/gftd/flight-offer/listWatch.bpmn",
    resultTimeoutMs: 15000,
    slug: "flight-offer-list-watch-v1",
  },
  {
    bpmnProcessId: "flight_offer_get_cheapest",
    nsid: "app.etzhayyim.apps.flightOffer.getCheapest",
    sourcePath: "00-contracts/bpmn/ai/gftd/flight-offer/getCheapest.bpmn",
    resultTimeoutMs: 10000,
    slug: "flight-offer-get-cheapest-v1",
  },
];

function processVertexId(slug: string): string {
  return `at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/${slug}`;
}
function bindingVertexId(slug: string): string {
  return `at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/${slug}`;
}

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const entry of entries) {
    const body = readFileSync(path.resolve(repoRoot, entry.sourcePath), "utf8");
    const size = Buffer.byteLength(body, "utf8");
    const pVid = processVertexId(entry.slug);
    const bVid = bindingVertexId(entry.slug);
    await sql`
      INSERT INTO vertex_bpmn_process_def (
        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id
      )
      SELECT ${pVid}, ${ownerDid}, ${entry.bpmnProcessId},
             1, ${body}, CAST(${size} AS integer), ${entry.sourcePath}, 'active',
             ${createdAt}, 1, ${ownerDid}, ${ownerDid}, ${actorTag}
      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${pVid})
    `.execute(db);
    await sql`
      INSERT INTO vertex_bpmn_lexicon_binding (
        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,
        result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id
      )
      SELECT ${bVid}, ${ownerDid}, ${entry.nsid},
             ${entry.bpmnProcessId}, 1, CAST(${entry.resultTimeoutMs} AS integer), 'active',
             ${createdAt}, 1, ${ownerDid}, ${ownerDid}, ${actorTag}
      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bVid})
    `.execute(db);
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const entry of entries) {
    const pVid = processVertexId(entry.slug);
    const bVid = bindingVertexId(entry.slug);
    await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bVid}`.execute(db);
    await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${pVid}`.execute(db);
  }
}
