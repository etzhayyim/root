import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

type Seed = {
  slug: string;
  processId: string;
  nsid: string;
  sourcePath: string;
  timeoutMs: number;
  writeTableAllowlist: string;
};

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const ownerDid = "did:web:arb.etzhayyim.com";
const createdAt = "2026-04-29T20:20:00+09:00";
const actorId = "sys.bpmn.seed.arb";
const project = "arb";

const seeds: Seed[] = [
  {
    slug: "scout-quotes",
    processId: "arb_scout_quotes",
    nsid: "app.etzhayyim.apps.arb.scoutQuotes",
    sourcePath: "00-contracts/bpmn/ai/gftd/arb/scoutQuotes.bpmn",
    timeoutMs: 120000,
    writeTableAllowlist: "vertex_arb_quote",
  },
  {
    slug: "ingest-quote",
    processId: "arb_ingest_quote",
    nsid: "app.etzhayyim.apps.arb.ingestQuote",
    sourcePath: "00-contracts/bpmn/ai/gftd/arb/ingestQuote.bpmn",
    timeoutMs: 30000,
    writeTableAllowlist: "vertex_arb_quote",
  },
  {
    slug: "detect-spread",
    processId: "arb_detect_spread",
    nsid: "app.etzhayyim.apps.arb.detectSpread",
    sourcePath: "00-contracts/bpmn/ai/gftd/arb/detectSpread.bpmn",
    timeoutMs: 30000,
    writeTableAllowlist: "",
  },
  {
    slug: "propose-trade",
    processId: "arb_propose_trade",
    nsid: "app.etzhayyim.apps.arb.proposeTrade",
    sourcePath: "00-contracts/bpmn/ai/gftd/arb/proposeTrade.bpmn",
    timeoutMs: 30000,
    writeTableAllowlist: "vertex_arb_proposal,edge_arb_proposal_leg",
  },
  {
    slug: "score-proposal",
    processId: "arb_score_proposal",
    nsid: "app.etzhayyim.apps.arb.scoreProposal",
    sourcePath: "00-contracts/bpmn/ai/gftd/arb/scoreProposal.bpmn",
    timeoutMs: 30000,
    writeTableAllowlist: "vertex_arb_score",
  },
  {
    slug: "publish-proposal",
    processId: "arb_publish_proposal",
    nsid: "app.etzhayyim.apps.arb.publishProposal",
    sourcePath: "00-contracts/bpmn/ai/gftd/arb/publishProposal.bpmn",
    timeoutMs: 120000,
    writeTableAllowlist: "vertex_arb_publication",
  },
  {
    slug: "list-proposals",
    processId: "arb_list_proposals",
    nsid: "app.etzhayyim.apps.arb.listProposals",
    sourcePath: "00-contracts/bpmn/ai/gftd/arb/listProposals.bpmn",
    timeoutMs: 30000,
    writeTableAllowlist: "",
  },
  {
    slug: "get-proposal",
    processId: "arb_get_proposal",
    nsid: "app.etzhayyim.apps.arb.getProposal",
    sourcePath: "00-contracts/bpmn/ai/gftd/arb/getProposal.bpmn",
    timeoutMs: 30000,
    writeTableAllowlist: "",
  },
];

const readContract = (rel: string) => readFileSync(path.resolve(repoRoot, rel), "utf8");
const processVertexId = (s: Seed) =>
  `at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/${project}-${s.slug}-v1`;
const bindingVertexId = (s: Seed) =>
  `at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/${project}-${s.slug}-v1`;

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const s of seeds) {
    const xml = readContract(s.sourcePath);
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
        ${bindingVertexId(s)}, ${ownerDid}, ${s.nsid}, ${s.processId}, 1,
        CAST(${s.timeoutMs} AS integer), ${s.writeTableAllowlist}, 'active', ${createdAt},
        1, ${ownerDid}, ${ownerDid}, ${actorId}, ${ownerDid}, 'anon'
      WHERE NOT EXISTS (
        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVertexId(s)}
      )
    `.execute(db);

    await sql`
      UPDATE vertex_bpmn_lexicon_binding
      SET write_table_allowlist = ${s.writeTableAllowlist}
      WHERE bpmn_process_id = ${s.processId}
        AND nsid = ${s.nsid}
        AND (write_table_allowlist IS NULL OR write_table_allowlist <> ${s.writeTableAllowlist})
    `.execute(db);
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const s of seeds) {
    await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVertexId(s)}`.execute(db);
    await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${processVertexId(s)}`.execute(db);
  }
}
