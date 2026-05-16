ALTER TABLE vertex_bpmn_lexicon_binding ADD COLUMN IF NOT EXISTS write_table_allowlist varchar;

UPDATE vertex_bpmn_lexicon_binding
       SET write_table_allowlist = 'vertex_open_defence_event'
     WHERE actor_id LIKE 'sys.bpmn.seed.open-defence%'
       AND write_table_allowlist IS NULL;
