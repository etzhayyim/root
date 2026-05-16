ALTER TABLE vertex_repo_record ADD COLUMN IF NOT EXISTS actor_did VARCHAR;

ALTER TABLE vertex_repo_record ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon';

CREATE INDEX IF NOT EXISTS idx_vertex_repo_record_actor_did
      ON vertex_repo_record (actor_did);

ALTER TABLE vertex_ipaddress_access_log ADD COLUMN IF NOT EXISTS actor_did VARCHAR;

ALTER TABLE vertex_ipaddress_access_log ADD COLUMN IF NOT EXISTS org_did VARCHAR DEFAULT 'anon';

CREATE INDEX IF NOT EXISTS idx_ipaddress_access_log_actor_did
      ON vertex_ipaddress_access_log (actor_did);
