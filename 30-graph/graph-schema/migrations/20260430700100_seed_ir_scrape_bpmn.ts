import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

type Seed = {
  file: string;
  processId: string;
  nsid: string;
  writeTableAllowlist: string;
  resultTimeoutMs: number;
};

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const ownerDid = "did:web:news.etzhayyim.com";
const createdAt = "2026-04-30T21:00:00+09:00";
const actorId = "sys.bpmn.seed.irScrape";

const seeds: Seed[] = [
  {
    file: "queueSeeds",
    processId: "ir_scrape_queue_seeds",
    nsid: "app.etzhayyim.apps.irScrape.queueSeeds",
    writeTableAllowlist: "vertex_ir_company,vertex_ir_scraper_run",
    resultTimeoutMs: 120_000,
  },
  {
    file: "processQueue",
    processId: "ir_scrape_process_queue",
    nsid: "app.etzhayyim.apps.irScrape.processQueue",
    writeTableAllowlist: "vertex_ir_scraper_run,vertex_ir_pressrelease",
    resultTimeoutMs: 300_000,
  },
];

const sourcePath = (s: Seed) =>
  `00-contracts/bpmn/ai/gftd/irScrape/${s.file}.bpmn`;

const slug = (s: Seed) =>
  s.file.replace(/[A-Z]/g, (m) => `-${m.toLowerCase()}`);

const processVid = (s: Seed) =>
  `at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/ir-scrape-${slug(s)}-v1`;

const bindingVid = (s: Seed) =>
  `at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/ir-scrape-${slug(s)}-v1`;

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const s of seeds) {
    const xml = readFileSync(path.resolve(repoRoot, sourcePath(s)), "utf8");
    const size = Buffer.byteLength(xml, "utf8");
    await sql`INSERT INTO vertex_bpmn_process_def
      (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, source_path, status,
       created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did)
      SELECT ${processVid(s)}, ${ownerDid}, ${s.processId}, 1, ${xml}, CAST(${size} AS integer),
             ${sourcePath(s)}, 'active', ${createdAt}, 100,
             ${ownerDid}, ${ownerDid}, ${actorId}, ${ownerDid}, 'anon'
      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${processVid(s)})`.execute(db);

    await sql`INSERT INTO vertex_bpmn_lexicon_binding
      (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,
       write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id,
       actor_id, actor_did, org_did)
      SELECT ${bindingVid(s)}, ${ownerDid}, ${s.nsid}, ${s.processId}, 1,
             CAST(${s.resultTimeoutMs} AS integer), ${s.writeTableAllowlist},
             'active', ${createdAt}, 100,
             ${ownerDid}, ${ownerDid}, ${actorId}, ${ownerDid}, 'anon'
      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVid(s)})`.execute(db);
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const s of seeds) {
    await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVid(s)}`.execute(db);
    await sql`DELETE FROM vertex_bpmn_process_def   WHERE vertex_id = ${processVid(s)}`.execute(db);
  }
}
