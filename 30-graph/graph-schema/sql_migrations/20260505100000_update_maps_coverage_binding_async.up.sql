UPDATE vertex_bpmn_lexicon_binding
    SET result_timeout_ms = 0
    WHERE nsid IN (
      'ai.gftd.apps.maps.batchCoverageCycle',
      'ai.gftd.apps.maps.refreshCoverageStats'
    );
