UPDATE vertex_bpmn_lexicon_binding
    SET write_table_allowlist = array_to_string(
      array_remove(
        array_remove(string_to_array(write_table_allowlist, ','), 'vertex_other'),
        'edge_other'
      ),
      ','
    )
    WHERE write_table_allowlist LIKE '%vertex_other%'
       OR write_table_allowlist LIKE '%edge_other%';
