import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

const __filename  = fileURLToPath(import.meta.url);
const __dirname   = path.dirname(__filename);
const repoRoot    = path.resolve(__dirname, "..", "..", "..");
const ownerDid    = "did:web:kiyo.etzhayyim.com";
const createdAt   = "2026-04-30T23:01:00+09:00";
const actorId     = "sys.bpmn.seed.kiyo";

type Seed = {
  slug:       string;
  op:         string;
  processId:  string;
  nsid:       string;
  timeoutMs:  number;
  allowlist:  string;
};

const seeds: Seed[] = [
  {
    slug:      "submit-paper",
    op:        "submitPaper",
    processId: "kiyo_submit_paper",
    nsid:      "com.etzhayyim.apps.kiyo.submitPaper",
    timeoutMs: 60_000,
    allowlist: "vertex_kiyo_paper,vertex_kiyo_revision,edge_kiyo_authored_by",
  },
  {
    slug:      "submit-revision",
    op:        "submitRevision",
    processId: "kiyo_submit_revision",
    nsid:      "com.etzhayyim.apps.kiyo.submitRevision",
    timeoutMs: 60_000,
    allowlist: "vertex_kiyo_revision,vertex_kiyo_paper",
  },
  {
    slug:      "citation-sync",
    op:        "citationSync",
    processId: "kiyo_citation_sync",
    nsid:      "com.etzhayyim.apps.kiyo.citationSync",
    timeoutMs: 300_000,
    allowlist: "edge_kiyo_cites",
  },
  {
    slug:      "embedding-index",
    op:        "embeddingIndex",
    processId: "kiyo_embedding_index",
    nsid:      "com.etzhayyim.apps.kiyo.embeddingIndex",
    timeoutMs: 180_000,
    allowlist: "vertex_kiyo_paper",
  },
  {
    slug:      "weekly-digest",
    op:        "weeklyDigest",
    processId: "kiyo_weekly_digest",
    nsid:      "com.etzhayyim.apps.kiyo.weeklyDigest",
    timeoutMs: 60_000,
    allowlist: "",
  },
];

const bpmnPath    = (s: Seed) => `00-contracts/bpmn/com/etzhayyim/kiyo/${s.op}.bpmn`;
const processVid  = (s: Seed) => `at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/kiyo-${s.slug}-v1`;
const bindingVid  = (s: Seed) => `at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/kiyo-${s.slug}-v1`;

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const s of seeds) {
    const xml  = readFileSync(path.resolve(repoRoot, bpmnPath(s)), "utf8");
    const size = Buffer.byteLength(xml, "utf8");

    await sql`
      INSERT INTO vertex_bpmn_process_def (
        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
        source_path, status, created_at, sensitivity_ord,
        org_id, user_id, actor_id, actor_did, org_did
      )
      SELECT
        ${processVid(s)}, ${ownerDid}, ${s.processId}, 1,
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
        ${bindingVid(s)}, ${ownerDid}, ${s.nsid}, ${s.processId}, 1,
        ${s.timeoutMs}, ${s.allowlist}, 'active', ${createdAt},
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
    await sql`DELETE FROM vertex_bpmn_process_def    WHERE vertex_id = ${processVid(s)}`.execute(db);
  }
}
