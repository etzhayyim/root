import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

type Seed = { proc: string; bpmnProcessId: string; nsid: string; resultTimeoutMs: number; writeTableAllowlist: string };

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const ownerDid = "did:web:handotai.etzhayyim.com";
const createdAt = "2026-05-07T01:45:00Z";
const actorId = "sys.bpmn.seed.handotai";

const snake = (proc: string) => proc.replace(/([A-Z])/g, "_$1").toLowerCase();
const slug = (proc: string) => proc.replace(/([A-Z])/g, "-$1").toLowerCase();
const writeProcs = new Set([
  "alertCreate",
  "alertDelete",
  "backfillWriterPosts",
  "crawlTrigger",
  "handleDailyEvolution",
  "registerSemiEntities",
  "registerWriterProfiles",
  "reportGenerate",
  "seedArticles",
  "sourceAdd",
  "subscribe",
  "translateArticle",
  "updateTranslation",
  "wave",
]);
const handotaiWriteTableAllowlist = [
  "vertex_handotai_alert",
  "vertex_handotai_article",
  "vertex_handotai_collection_job",
  "vertex_handotai_digest",
  "vertex_handotai_report",
  "vertex_handotai_semi_entity",
  "vertex_handotai_source",
  "vertex_handotai_subscription",
  "edge_handotai_article_entity",
  "edge_handotai_source_article",
  "edge_handotai_subscription_entity",
  // vertex_repo_record is reserved for social posts:
  // backfillWriterPosts writes app.bsky.feed.post rows only.
  "vertex_repo_record",
].join(",");
const procs = [
  "alertCreate",
  "alertDelete",
  "alertList",
  "backfillWriterPosts",
  "crawlTrigger",
  "getArticle",
  "getDailyDigest",
  "getSubscription",
  "getWeeklyReport",
  "handleDailyEvolution",
  "listArticles",
  "listSemiEntities",
  "registerSemiEntities",
  "registerWriterProfiles",
  "reportGenerate",
  "searchArticles",
  "seedArticles",
  "sourceAdd",
  "sourceList",
  "subscribe",
  "translateArticle",
  "updateTranslation",
  "wave",
];

const seeds: Seed[] = procs.map((proc) => ({
  proc,
  bpmnProcessId: `handotai_${snake(proc)}`,
  nsid: `ai.gftd.apps.handotai.${proc}`,
  resultTimeoutMs: 30000,
  writeTableAllowlist: writeProcs.has(proc) ? handotaiWriteTableAllowlist : "",
}));

const bpmnPath = (s: Seed) => `00-contracts/bpmn/ai/gftd/handotai/${s.proc}.bpmn`;
const processVid = (s: Seed) => `at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/handotai-${slug(s.proc)}-v1`;
const bindingVid = (s: Seed) => `at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/handotai-${slug(s.proc)}-v1`;

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
