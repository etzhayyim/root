DELETE FROM vertex_orbital_body
    WHERE body_id IN (
      'orbital-body:tdrs-3',
      'orbital-body:tdrs-12',
      'orbital-body:goes-16',
      'orbital-body:himawari-9',
      'orbital-body:goes-18',
      'orbital-body:elektro-l-3',
      'orbital-body:ses-17'
    );
