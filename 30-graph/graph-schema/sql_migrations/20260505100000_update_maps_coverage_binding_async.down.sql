UPDATE vertex_bpmn_lexicon_binding
    SET result_timeout_ms = CASE nsid
      WHEN 'ai.gftd.apps.maps.batchCoverageCycle'  THEN 120000
      WHEN 'ai.gftd.apps.maps.refreshCoverageStats' THEN 90000
      ELSE result_timeout_ms
    END
    WHERE nsid IN (
      'ai.gftd.apps.maps.batchCoverageCycle',
      'ai.gftd.apps.maps.refreshCoverageStats'
    );
