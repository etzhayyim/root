import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const readContract = (p: string) => readFileSync(path.resolve(repoRoot, p), "utf8");
const seedCreatedAt = "2026-05-08T00:00:00Z";
const seedOwnerDid = "did:web:lawfirm.gftd.ai";
const seedActorTag = "sys.bpmn.seed.lawfirm";

const PROCESSES = [
  {
    vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/lawfirm-sales-cadence-tick-v1",
    bpmnProcessId: "lawfirm_sales_cadence_tick",
    sourcePath: "00-contracts/bpmn/ai/gftd/lawfirm/salesCadenceTick.bpmn",
  },
  {
    vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/lawfirm-pipeline-stage-transition-v1",
    bpmnProcessId: "lawfirm_pipeline_stage_transition",
    sourcePath: "00-contracts/bpmn/ai/gftd/lawfirm/pipelineStageTransition.bpmn",
  },
];
const BINDING = {
  vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/lawfirm-pipeline-stage-transition-xrpc-v1",
  nsid: "ai.gftd.apps.lawfirm.pipelineTransition",
  bpmnProcessId: "lawfirm_pipeline_stage_transition",
  resultTimeoutMs: 30_000,
};

/**
 * lawfirm.gftd.ai sales cadence + lead tracking schema.
 *
 * Tables:
 *   vertex_lawfirm_lead            One row per target firm/individual
 *   vertex_lawfirm_outreach_event  Per touchpoint (mail sent, reply received, meeting held)
 *   vertex_lawfirm_pipeline_stage  Stage transition log (lead → contact → meet → pilot → paid)
 *
 * Streaming MVs:
 *   mv_lawfirm_lead_stale          5+ business days no follow-up
 *   mv_lawfirm_pipeline_funnel     stage × count × cumulative conversion
 *
 * BPMN: salesCadenceTick R/PT24H — scans stale leads + emits re-outreach drafts
 * via lawfirm-marketing-ops outreach_agent.
 *
 * ADR-0036 Hyperdrive direct.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_lawfirm_lead (
      vertex_id          varchar PRIMARY KEY,
      lead_id            varchar NOT NULL,
      lead_kind          varchar NOT NULL,
      target_name        varchar NOT NULL,
      target_email       varchar,
      target_country     varchar DEFAULT 'IN',
      target_city        varchar,
      firm_size          varchar,
      practice_area      varchar,
      source             varchar,
      assigned_to_did    varchar,
      stage              varchar DEFAULT 'lead',
      next_action        varchar,
      next_action_at     varchar,
      last_touch_at      varchar,
      last_reply_at      varchar,
      pwc_clearance_uri  varchar,
      conversion_value_usd double precision,
      notes              varchar,
      created_at         varchar,
      sensitivity_ord    int DEFAULT 200,
      owner_did          varchar)
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_lawfirm_outreach_event (
      vertex_id        varchar PRIMARY KEY,
      lead_id          varchar NOT NULL,
      event_kind       varchar NOT NULL,
      channel          varchar,
      direction        varchar,
      subject          varchar,
      body_preview     varchar,
      asset_uri        varchar,
      occurred_at      varchar,
      actor_did        varchar,
      sentiment        double precision,
      created_at       varchar,
      sensitivity_ord  int DEFAULT 200,
      owner_did        varchar)
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_lawfirm_pipeline_stage (
      vertex_id      varchar PRIMARY KEY,
      lead_id        varchar NOT NULL,
      from_stage     varchar,
      to_stage       varchar NOT NULL,
      transitioned_at varchar,
      reason         varchar,
      decided_by_did varchar,
      created_at     varchar,
      sensitivity_ord int DEFAULT 200,
      owner_did      varchar)
  `.execute(db);

  // VIEW (plain, not MV) — RW does not allow now() inside MV WHERE.
  // Query-time now() is fine in regular VIEW.
  await sql`
    CREATE VIEW IF NOT EXISTS mv_lawfirm_lead_stale AS
    SELECT
      lead_id,
      target_name,
      target_email,
      stage,
      last_touch_at,
      next_action,
      assigned_to_did,
      conversion_value_usd
    FROM vertex_lawfirm_lead
    WHERE stage IN ('lead', 'contacted', 'meeting_requested')
      AND last_touch_at IS NOT NULL
      AND CAST(last_touch_at AS timestamptz) < now() - INTERVAL '5 days'
  `.execute(db);

  // MV: pipeline funnel
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_lawfirm_pipeline_funnel AS
    SELECT
      stage,
      COUNT(*) AS lead_count,
      COALESCE(SUM(conversion_value_usd), 0) AS pipeline_value_usd
    FROM vertex_lawfirm_lead
    GROUP BY stage
  `.execute(db);

  // BPMN seeds (canonical schema)
  for (const p of PROCESSES) {
    const xml = readContract(p.sourcePath);
    const size = Buffer.byteLength(xml, "utf8");
    await sql`
      INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id)
      SELECT ${p.vertexId}, ${seedOwnerDid}, ${p.bpmnProcessId}, 1, ${xml}, CAST(${size} AS integer), ${p.sourcePath}, 'active', ${seedCreatedAt}, 1, ${seedOwnerDid}, ${seedOwnerDid}, ${seedActorTag}
      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${p.vertexId})
    `.execute(db);
  }

  await sql`
    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id)
    SELECT ${BINDING.vertexId}, ${seedOwnerDid}, ${BINDING.nsid}, ${BINDING.bpmnProcessId}, 1, CAST(${BINDING.resultTimeoutMs} AS integer), 'active', ${seedCreatedAt}, 1, ${seedOwnerDid}, ${seedOwnerDid}, ${seedActorTag}
    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${BINDING.vertexId})
  `.execute(db);

  // Seed Y1 target leads (3 SaaS pilot logos + Day-0 individual lead pipeline)
  await sql`
    INSERT INTO vertex_lawfirm_lead
      (vertex_id, lead_id, lead_kind, target_name, target_email, target_country,
       target_city, firm_size, practice_area, source, assigned_to_did,
       stage, next_action, next_action_at, conversion_value_usd, notes,
       created_at, owner_did)
    VALUES
      (
        'at://did:web:bpmn.gftd.ai/ai.gftd.apps.lawfirm.lead/nishith-desai-2026',
        'nishith-desai-2026', 'saas_pilot', 'Nishith Desai Associates',
        'TBD@nishithdesai.com', 'IN', 'Mumbai', '90+', 'tech-funds-PE',
        'k-bakshi-warm-intro', 'did:web:k-bakshi.gftd.ai',
        'contacted', 'send warm intro mail', now()::varchar, 60000.0,
        'Pilot 1 of 3, k-bakshi 1-hop intro to Vyapak Desai / Gowree Gokhale / Vivek Kathpalia',
        now()::varchar, 'did:web:lawfirm.gftd.ai'
      ),
      (
        'at://did:web:bpmn.gftd.ai/ai.gftd.apps.lawfirm.lead/trilegal-2026',
        'trilegal-2026', 'saas_pilot', 'Trilegal',
        'TBD@trilegal.com', 'IN', 'Bangalore', '600', 'mid-market-deal',
        'k-bakshi-linkedin', 'did:web:k-bakshi.gftd.ai',
        'lead', 'send warm intro mail Week 2', '2026-05-12', 60000.0,
        'Pilot 2 of 3, target Sridhar Gorthi / Yogesh Singh / Karthik Mahalingam',
        now()::varchar, 'did:web:lawfirm.gftd.ai'
      ),
      (
        'at://did:web:bpmn.gftd.ai/ai.gftd.apps.lawfirm.lead/induslaw-2026',
        'induslaw-2026', 'saas_pilot', 'IndusLaw',
        'TBD@induslaw.com', 'IN', 'Bangalore', '250', 'startup-advisory',
        'k-bakshi-event', 'did:web:k-bakshi.gftd.ai',
        'lead', 'send warm intro mail Week 3', '2026-05-19', 60000.0,
        'Pilot 3 of 3, target Avimukt Dar / Suneeth Katarki / Gaurav Dani',
        now()::varchar, 'did:web:lawfirm.gftd.ai'
      )
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE bpmn_process_id = 'lawfirm_pipeline_stage_transition'`.execute(db);
  await sql`DELETE FROM vertex_bpmn_process_def WHERE bpmn_process_id IN ('lawfirm_sales_cadence_tick','lawfirm_pipeline_stage_transition')`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_lawfirm_pipeline_funnel`.execute(db);
  await sql`DROP VIEW IF EXISTS mv_lawfirm_lead_stale`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_lawfirm_pipeline_stage`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_lawfirm_outreach_event`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_lawfirm_lead`.execute(db);
}
