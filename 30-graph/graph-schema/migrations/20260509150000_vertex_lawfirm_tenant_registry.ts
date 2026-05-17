import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * vertex_lawfirm_tenant — registry table backing the
 * ai.gftd.apps.lawfirm.tenantBootstrap procedure.
 *
 * Companion to 20260509060000 which added tenant_id columns to all
 * lawfirm scope-tables for query-time isolation. This migration adds
 * the *registry* (one row per provisioned firm) plus an audit log table
 * for promote / suspend / restore transitions.
 *
 * tier values:
 *   - sandbox   : pilot tier, USD 0, 90-day post-suspend retention
 *   - saas-prod : paid tier, recurring billing via Stripe
 *
 * status values:
 *   - active    : provisioned and operational
 *   - suspended : pilot ended (lost or paused), data preserved 90d
 *   - promoted  : transitioned sandbox -> saas-prod (audit-only marker)
 *   - purged    : 90-day retention elapsed, data hard-deleted
 *
 * Idempotency: tenantBootstrap handler MUST insert via
 * INSERT ... WHERE NOT EXISTS on (slug, tier) and surface
 * status='already_exists' to clients.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_lawfirm_tenant (
      vertex_id        varchar PRIMARY KEY,
      tenant_id        varchar NOT NULL,
      slug             varchar NOT NULL,
      tenant_did       varchar NOT NULL,
      legal_name       varchar NOT NULL,
      country          varchar,
      data_region      varchar,
      tier             varchar NOT NULL,
      status           varchar DEFAULT 'active',
      pilot_lead_id    varchar,
      admin_email_ct   varchar,
      consent_regions  varchar,
      pds_url          varchar,
      xrpc_endpoint    varchar,
      kpi_dashboard_url varchar,
      racic_doc_uri    varchar,
      provisioned_at   varchar,
      promoted_at      varchar,
      suspended_at     varchar,
      created_at       varchar,
      sensitivity_ord  int DEFAULT 200,
      owner_did        varchar)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_vertex_lawfirm_tenant_slug
      ON vertex_lawfirm_tenant (slug)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_vertex_lawfirm_tenant_tier_status
      ON vertex_lawfirm_tenant (tier, status)
  `.execute(db);

  // ── audit log ───────────────────────────────────────────────────────────────
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_lawfirm_tenant_event (
      vertex_id        varchar PRIMARY KEY,
      tenant_id        varchar NOT NULL,
      event_kind       varchar NOT NULL,
      from_status      varchar,
      to_status        varchar,
      from_tier        varchar,
      to_tier          varchar,
      reason           varchar,
      actor_did        varchar,
      occurred_at      varchar,
      created_at       varchar,
      sensitivity_ord  int DEFAULT 200,
      owner_did        varchar)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_vertex_lawfirm_tenant_event_tenant_id
      ON vertex_lawfirm_tenant_event (tenant_id)
  `.execute(db);

  // ── tenant <-> lead edge (sandbox tier links to originating lead) ──────────
  await sql`
    CREATE TABLE IF NOT EXISTS edge_lawfirm_tenant_lead (
      edge_id          varchar PRIMARY KEY,
      src_vid          varchar NOT NULL,
      dst_vid          varchar NOT NULL,
      tenant_id        varchar NOT NULL,
      lead_id          varchar NOT NULL,
      rel_kind         varchar NOT NULL DEFAULT 'sandbox_for_lead',
      created_at       varchar,
      sensitivity_ord  int DEFAULT 200,
      owner_did        varchar)
  `.execute(db);

  // ── operational MV: per-tier active tenant count ────────────────────────────
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_lawfirm_tenant_summary AS
    SELECT
      tier,
      status,
      COUNT(*) AS tenant_count,
      MAX(provisioned_at) AS most_recent_provisioned_at
    FROM vertex_lawfirm_tenant
    GROUP BY tier, status
  `.execute(db);

  // ── seed sandbox bootstrap row for the pilot leads already in the table ────
  // Idempotent: WHERE NOT EXISTS guards against re-apply.
  // tenant_did follows did:web:<slug>.lawfirm.etzhayyim.com per ADR-0029 depth-1 root.
  const SEED = [
    { slug: "nishith",  legal: "Nishith Desai Associates", lead: "nishith-desai-2026", country: "IN" },
    { slug: "trilegal", legal: "Trilegal",                 lead: "trilegal-2026",      country: "IN" },
    { slug: "induslaw", legal: "IndusLaw",                 lead: "induslaw-2026",      country: "IN" },
  ];

  const NOW = "2026-05-08T00:00:00Z";
  const OWNER = "did:web:lawfirm.etzhayyim.com";

  for (const t of SEED) {
    const tenantId = `sandbox-${t.slug}`;
    const vertexId = `at://did:web:lawfirm.etzhayyim.com/ai.gftd.apps.lawfirm.tenant/${tenantId}`;
    const tenantDid = `did:web:${t.slug}.sandbox.lawfirm.etzhayyim.com`;
    const pdsUrl = `https://${t.slug}.sandbox.lawfirm.etzhayyim.com`;
    const kpi = `https://kpi-lawfirm.etzhayyim.com/${t.slug}`;
    await sql`
      INSERT INTO vertex_lawfirm_tenant
        (vertex_id, tenant_id, slug, tenant_did, legal_name, country,
         data_region, tier, status, pilot_lead_id,
         pds_url, xrpc_endpoint, kpi_dashboard_url,
         provisioned_at, created_at, sensitivity_ord, owner_did)
      SELECT
        ${vertexId}, ${tenantId}, ${t.slug}, ${tenantDid}, ${t.legal}, ${t.country},
        'vultr-lax', 'sandbox', 'pending_kickoff', ${t.lead},
        ${pdsUrl}, 'https://lawfirm.etzhayyim.com', ${kpi},
        ${NOW}, ${NOW}, 200, ${OWNER}
      WHERE NOT EXISTS (SELECT 1 FROM vertex_lawfirm_tenant WHERE vertex_id = ${vertexId})
    `.execute(db);

    // tenant <-> lead edge
    const leadVid = `at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.lawfirm.lead/${t.lead}`;
    const edgeId = `edge:tenant:${tenantId}:for-lead:${t.lead}`;
    await sql`
      INSERT INTO edge_lawfirm_tenant_lead
        (edge_id, src_vid, dst_vid, tenant_id, lead_id, rel_kind,
         created_at, sensitivity_ord, owner_did)
      SELECT
        ${edgeId}, ${vertexId}, ${leadVid}, ${tenantId}, ${t.lead}, 'sandbox_for_lead',
        ${NOW}, 200, ${OWNER}
      WHERE NOT EXISTS (SELECT 1 FROM edge_lawfirm_tenant_lead WHERE edge_id = ${edgeId})
    `.execute(db);

    // audit-log: provisioning event (status: '' -> pending_kickoff)
    const eventVid = `at://did:web:lawfirm.etzhayyim.com/ai.gftd.apps.lawfirm.tenantEvent/${tenantId}-provisioned`;
    await sql`
      INSERT INTO vertex_lawfirm_tenant_event
        (vertex_id, tenant_id, event_kind, from_status, to_status,
         from_tier, to_tier, reason, actor_did, occurred_at,
         created_at, sensitivity_ord, owner_did)
      SELECT
        ${eventVid}, ${tenantId}, 'provisioned', NULL, 'pending_kickoff',
        NULL, 'sandbox', 'seeded by 20260509150000 migration',
        'sys.lawfirm.tenant-bootstrap', ${NOW},
        ${NOW}, 200, ${OWNER}
      WHERE NOT EXISTS (SELECT 1 FROM vertex_lawfirm_tenant_event WHERE vertex_id = ${eventVid})
    `.execute(db);
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_lawfirm_tenant_summary`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_lawfirm_tenant_lead`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_lawfirm_tenant_event`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_lawfirm_tenant`.execute(db);
}
