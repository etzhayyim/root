ALTER TABLE vertex_open_lei_gleif_shard
    ADD COLUMN IF NOT EXISTS request_url VARCHAR;

ALTER TABLE vertex_open_lei_gleif_shard
    ADD COLUMN IF NOT EXISTS next_url VARCHAR;
