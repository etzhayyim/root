import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * lawfirm.etzhayyim.com Y1 KPI views.
 *
 * Plain VIEWs only — query-time evaluation since aggregations reference
 * now() (forbidden in MVs, see ADR-0004 amendment in 010000 migration).
 *
 * Powers `kpi-lawfirm.etzhayyim.com` CEO dashboard. All views read-only,
 * cohort-bounded so cardinality stays small (top-3 + tier-2 = ~10 rows).
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  // ── Funnel: stage → count, conversion% from prior stage ────────────────────
  await sql`
    CREATE VIEW IF NOT EXISTS view_lawfirm_funnel_snapshot AS
    SELECT
      stage,
      COUNT(*) AS lead_count,
      COALESCE(SUM(conversion_value_usd), 0) AS pipeline_value_usd,
      COUNT(*) FILTER (WHERE last_touch_at IS NOT NULL
                         AND CAST(last_touch_at AS timestamptz) > now() - INTERVAL '7 days')
        AS active_last_7d
    FROM vertex_lawfirm_lead
    GROUP BY stage
  `.execute(db);

  // ── Stale-by-stage: per-stage stale lead detail ─────────────────────────────
  await sql`
    CREATE VIEW IF NOT EXISTS view_lawfirm_lead_stale_by_stage AS
    SELECT
      stage,
      lead_id,
      target_name,
      target_country,
      assigned_to_did,
      last_touch_at,
      CAST(now() - CAST(last_touch_at AS timestamptz) AS varchar) AS staleness,
      conversion_value_usd
    FROM vertex_lawfirm_lead
    WHERE last_touch_at IS NOT NULL
      AND CAST(last_touch_at AS timestamptz) < now() - INTERVAL '5 days'
      AND stage NOT IN ('paid', 'lost', 'parked')
    ORDER BY CAST(last_touch_at AS timestamptz) ASC
  `.execute(db);

  // ── Outreach event volume (per-day, last 30d) ──────────────────────────────
  await sql`
    CREATE VIEW IF NOT EXISTS view_lawfirm_outreach_volume_30d AS
    SELECT
      SUBSTRING(occurred_at, 1, 10) AS event_date,
      event_kind,
      direction,
      COUNT(*) AS event_count,
      AVG(sentiment) AS avg_sentiment
    FROM vertex_lawfirm_outreach_event
    WHERE occurred_at IS NOT NULL
      AND CAST(occurred_at AS timestamptz) > now() - INTERVAL '30 days'
    GROUP BY SUBSTRING(occurred_at, 1, 10), event_kind, direction
  `.execute(db);

  // ── Pilot success leading indicator ─────────────────────────────────────────
  // 3-of-4 success criteria from pilot-success-criteria.md
  await sql`
    CREATE VIEW IF NOT EXISTS view_lawfirm_pilot_success_signal AS
    SELECT
      l.lead_id,
      l.target_name,
      l.stage,
      COUNT(DISTINCT oe.vertex_id) FILTER (WHERE oe.event_kind = 'meeting_held') AS meetings_held,
      COUNT(DISTINCT oe.vertex_id) FILTER (WHERE oe.event_kind = 'demo_completed') AS demos_completed,
      COUNT(DISTINCT oe.vertex_id) FILTER (WHERE oe.event_kind = 'sow_sent') AS sows_sent,
      COUNT(DISTINCT oe.vertex_id) FILTER (WHERE oe.event_kind = 'reference_call_granted') AS references,
      MAX(CAST(oe.occurred_at AS timestamptz)) AS last_event_at
    FROM vertex_lawfirm_lead l
    LEFT JOIN vertex_lawfirm_outreach_event oe ON oe.lead_id = l.lead_id
    WHERE l.lead_kind = 'saas_pilot'
    GROUP BY l.lead_id, l.target_name, l.stage
  `.execute(db);

  // ── Stage-transition velocity (avg days per stage) ──────────────────────────
  // RW does not yet support window functions inside aggregates; compute lag
  // in a sub-query first, then aggregate the projected delta column.
  await sql`
    CREATE VIEW IF NOT EXISTS view_lawfirm_stage_velocity AS
    SELECT
      from_stage,
      to_stage,
      COUNT(*) AS transition_count,
      AVG(delta_days) AS avg_days_in_prior_stage
    FROM (
      SELECT
        from_stage,
        to_stage,
        EXTRACT(EPOCH FROM (CAST(transitioned_at AS timestamptz) -
          LAG(CAST(transitioned_at AS timestamptz)) OVER (PARTITION BY lead_id ORDER BY transitioned_at)
        )) / 86400 AS delta_days
      FROM vertex_lawfirm_pipeline_stage
    ) sub
    GROUP BY from_stage, to_stage
  `.execute(db);

  // ── Y1 cumulative ARR projection ────────────────────────────────────────────
  await sql`
    CREATE VIEW IF NOT EXISTS view_lawfirm_y1_arr_projection AS
    SELECT
      stage,
      COUNT(*) AS lead_count,
      SUM(conversion_value_usd) AS pipeline_value_usd,
      SUM(conversion_value_usd) *
        CASE stage
          WHEN 'paid'              THEN 1.00
          WHEN 'pilot_active'      THEN 0.60
          WHEN 'sow_signed'        THEN 0.85
          WHEN 'pilot_committed'   THEN 0.40
          WHEN 'meeting_requested' THEN 0.20
          WHEN 'contacted'         THEN 0.10
          WHEN 'lead'              THEN 0.05
          ELSE 0.00
        END AS expected_value_usd
    FROM vertex_lawfirm_lead
    GROUP BY stage
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP VIEW IF EXISTS view_lawfirm_y1_arr_projection`.execute(db);
  await sql`DROP VIEW IF EXISTS view_lawfirm_stage_velocity`.execute(db);
  await sql`DROP VIEW IF EXISTS view_lawfirm_pilot_success_signal`.execute(db);
  await sql`DROP VIEW IF EXISTS view_lawfirm_outreach_volume_30d`.execute(db);
  await sql`DROP VIEW IF EXISTS view_lawfirm_lead_stale_by_stage`.execute(db);
  await sql`DROP VIEW IF EXISTS view_lawfirm_funnel_snapshot`.execute(db);
}
