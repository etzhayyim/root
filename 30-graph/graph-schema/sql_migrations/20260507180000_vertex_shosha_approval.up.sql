CREATE TABLE IF NOT EXISTS vertex_shosha_approval (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      approval_id varchar NOT NULL,
      ref_trade_id varchar NOT NULL,
      decision varchar NOT NULL,
      approver_did varchar,
      approver_role varchar,
      amount_usd_at_decision double precision,
      rationale varchar,
      decided_at varchar NOT NULL,
      status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_shosha_approval_summary AS
      SELECT
        ref_trade_id,
        decision,
        COUNT(*) AS decision_count,
        MAX(decided_at) AS last_decided_at,
        SUM(COALESCE(amount_usd_at_decision, 0)) AS total_amount_usd
      FROM vertex_shosha_approval
      WHERE status = 'active'
      GROUP BY ref_trade_id, decision;

GRANT SELECT, INSERT, UPDATE ON vertex_shosha_approval TO root;

GRANT SELECT, INSERT, UPDATE ON vertex_shosha_approval TO kaisya_app;
