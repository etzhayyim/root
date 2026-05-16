REVOKE ALL ON vertex_training_shard FROM root;

REVOKE ALL ON vertex_training_shard FROM kaisya_app;

DROP TABLE IF EXISTS vertex_training_shard;

DROP VIEW IF EXISTS v_training_triple;

DROP VIEW IF EXISTS v_training_text;
