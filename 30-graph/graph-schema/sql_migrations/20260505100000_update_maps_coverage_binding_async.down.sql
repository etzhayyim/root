UPDATE vertex_bpmn_lexicon_binding
    SET result_timeout_ms = CASE nsid
      WHEN 'com.etzhayyim.apps.maps.batchCoverageCycle'  THEN 120000
      WHEN 'com.etzhayyim.apps.maps.refreshCoverageStats' THEN 90000
      ELSE result_timeout_ms
    END
    WHERE nsid IN (
      'com.etzhayyim.apps.maps.batchCoverageCycle',
      'com.etzhayyim.apps.maps.refreshCoverageStats'
    );
