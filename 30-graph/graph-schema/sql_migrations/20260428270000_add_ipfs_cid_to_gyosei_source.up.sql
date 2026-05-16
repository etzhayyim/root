ALTER TABLE vertex_gyosei_source_blob
      ADD COLUMN IF NOT EXISTS ipfs_cid_document  VARCHAR,
      ADD COLUMN IF NOT EXISTS ipfs_cid_thumbnail VARCHAR;
