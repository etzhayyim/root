ALTER TABLE vertex_gov_org ADD COLUMN IF NOT EXISTS last_fetch_status VARCHAR;

ALTER TABLE vertex_gov_org ADD COLUMN IF NOT EXISTS last_fetch_error VARCHAR;

ALTER TABLE vertex_gov_org ADD COLUMN IF NOT EXISTS last_fetch_checked_at VARCHAR;
