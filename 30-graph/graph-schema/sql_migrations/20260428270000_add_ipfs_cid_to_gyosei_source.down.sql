ALTER TABLE vertex_gyosei_source_blob
      DROP COLUMN IF EXISTS ipfs_cid_document,
      DROP COLUMN IF EXISTS ipfs_cid_thumbnail;
