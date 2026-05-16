DROP INDEX IF EXISTS idx_vector_embedding_768_hnsw;

DROP INDEX IF EXISTS idx_vector_embedding_768_shard;

DROP INDEX IF EXISTS idx_vector_embedding_768_lookup;

DROP INDEX IF EXISTS idx_vector_embedding_projection_model;

DROP INDEX IF EXISTS idx_vector_embedding_chunk_source;

DROP INDEX IF EXISTS idx_vector_embedding_source_shard;

DROP INDEX IF EXISTS idx_vector_embedding_source_modality;

DROP INDEX IF EXISTS idx_vector_embedding_source_uri;

DROP INDEX IF EXISTS idx_vector_embedding_space_id;

DROP INDEX IF EXISTS idx_vector_embedding_model_id;

DROP TABLE IF EXISTS vertex_vector_embedding_768;

DROP TABLE IF EXISTS vertex_vector_embedding_projection;

DROP TABLE IF EXISTS vertex_vector_embedding_chunk;

DROP TABLE IF EXISTS vertex_vector_embedding_source;

DROP TABLE IF EXISTS vertex_vector_embedding_space;

DROP TABLE IF EXISTS vertex_vector_embedding_model;

FLUSH;
