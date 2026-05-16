ALTER TABLE vertex_jp_ashiba_rental_contract ADD COLUMN IF NOT EXISTS contract_id VARCHAR;

ALTER TABLE vertex_jp_ashiba_rental_contract ADD COLUMN IF NOT EXISTS customer_did VARCHAR;

ALTER TABLE vertex_jp_ashiba_rental_contract ADD COLUMN IF NOT EXISTS site_address VARCHAR;

ALTER TABLE vertex_jp_ashiba_rental_contract ADD COLUMN IF NOT EXISTS total_amount DOUBLE PRECISION;

ALTER TABLE vertex_jp_ashiba_rental_contract ADD COLUMN IF NOT EXISTS deposit_amount DOUBLE PRECISION;

ALTER TABLE vertex_jp_ashiba_rental_contract ADD COLUMN IF NOT EXISTS start_date VARCHAR;

ALTER TABLE vertex_jp_ashiba_rental_contract ADD COLUMN IF NOT EXISTS end_date VARCHAR;

ALTER TABLE vertex_jp_ashiba_subscription_plan ADD COLUMN IF NOT EXISTS subscription_id VARCHAR;

ALTER TABLE vertex_jp_ashiba_subscription_plan ADD COLUMN IF NOT EXISTS customer_did VARCHAR;

ALTER TABLE vertex_jp_ashiba_subscription_plan ADD COLUMN IF NOT EXISTS tier VARCHAR;

ALTER TABLE vertex_jp_ashiba_subscription_plan ADD COLUMN IF NOT EXISTS monthly_fee DOUBLE PRECISION;

ALTER TABLE vertex_jp_ashiba_subscription_plan ADD COLUMN IF NOT EXISTS renewal_date VARCHAR;

ALTER TABLE vertex_jp_ashiba_subscription_plan ADD COLUMN IF NOT EXISTS cancelled_at VARCHAR;

ALTER TABLE vertex_jp_ashiba_site_schedule ADD COLUMN IF NOT EXISTS schedule_id VARCHAR;

ALTER TABLE vertex_jp_ashiba_site_schedule ADD COLUMN IF NOT EXISTS contract_id VARCHAR;

ALTER TABLE vertex_jp_ashiba_site_schedule ADD COLUMN IF NOT EXISTS task_type VARCHAR;

ALTER TABLE vertex_jp_ashiba_site_schedule ADD COLUMN IF NOT EXISTS scheduled_date VARCHAR;

ALTER TABLE vertex_jp_ashiba_site_schedule ADD COLUMN IF NOT EXISTS assigned_crew_did VARCHAR;

ALTER TABLE vertex_jp_ashiba_inspection ADD COLUMN IF NOT EXISTS inspection_id VARCHAR;

ALTER TABLE vertex_jp_ashiba_inspection ADD COLUMN IF NOT EXISTS contract_id VARCHAR;

ALTER TABLE vertex_jp_ashiba_inspection ADD COLUMN IF NOT EXISTS item_id VARCHAR;

ALTER TABLE vertex_jp_ashiba_inspection ADD COLUMN IF NOT EXISTS inspector_did VARCHAR;

ALTER TABLE vertex_jp_ashiba_inspection ADD COLUMN IF NOT EXISTS inspection_type VARCHAR;

ALTER TABLE vertex_jp_ashiba_inspection ADD COLUMN IF NOT EXISTS overall_result VARCHAR;

ALTER TABLE vertex_jp_ashiba_inspection ADD COLUMN IF NOT EXISTS severity VARCHAR;

ALTER TABLE vertex_jp_ashiba_inspection ADD COLUMN IF NOT EXISTS inspected_at VARCHAR;

CREATE INDEX IF NOT EXISTS idx_jp_ashiba_contract_id ON vertex_jp_ashiba_rental_contract (contract_id);

CREATE INDEX IF NOT EXISTS idx_jp_ashiba_contract_customer ON vertex_jp_ashiba_rental_contract (customer_did, status);

CREATE INDEX IF NOT EXISTS idx_jp_ashiba_subscription_id ON vertex_jp_ashiba_subscription_plan (subscription_id);

CREATE INDEX IF NOT EXISTS idx_jp_ashiba_subscription_customer ON vertex_jp_ashiba_subscription_plan (customer_did, status);

CREATE INDEX IF NOT EXISTS idx_jp_ashiba_schedule_contract ON vertex_jp_ashiba_site_schedule (contract_id, scheduled_date);

CREATE INDEX IF NOT EXISTS idx_jp_ashiba_inspection_contract ON vertex_jp_ashiba_inspection (contract_id, inspected_at);

CREATE INDEX IF NOT EXISTS idx_jp_ashiba_inspection_result ON vertex_jp_ashiba_inspection (overall_result, severity);

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_jp_ashiba_contract_status_counts AS
    SELECT status, count(*) AS cnt, sum(coalesce(total_amount, 0)) AS total_amount_sum
    FROM vertex_jp_ashiba_rental_contract
    GROUP BY status;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_jp_ashiba_subscription_tier_counts AS
    SELECT tier, status, count(*) AS cnt, sum(coalesce(monthly_fee, 0)) AS monthly_fee_sum
    FROM vertex_jp_ashiba_subscription_plan
    GROUP BY tier, status;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_jp_ashiba_inspection_result_counts AS
    SELECT overall_result, severity, count(*) AS cnt
    FROM vertex_jp_ashiba_inspection
    GROUP BY overall_result, severity;
