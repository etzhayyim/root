UPDATE vertex_bpmn_lexicon_binding
    SET result_timeout_ms = 0
    WHERE nsid IN (
      'com.etzhayyim.apps.maps.batchCoverageCycle',
      'com.etzhayyim.apps.maps.refreshCoverageStats'
    );
