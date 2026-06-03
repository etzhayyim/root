DELETE FROM edge_feature_replaces
  WHERE src_vid IN (
    SELECT feature_vertex_id FROM vertex_codebase_feature_usage
    WHERE analysis_vertex_id = 'at://did:web:amanomibashira.etzhayyim.com/com.etzhayyim.analysis.codebase/langchain-langgraph-pregel-20260509'
  );

DELETE FROM edge_analysis_covers_feature
  WHERE src_vid = 'at://did:web:amanomibashira.etzhayyim.com/com.etzhayyim.analysis.codebase/langchain-langgraph-pregel-20260509';

DELETE FROM vertex_codebase_feature_usage
  WHERE analysis_vertex_id = 'at://did:web:amanomibashira.etzhayyim.com/com.etzhayyim.analysis.codebase/langchain-langgraph-pregel-20260509';

DELETE FROM vertex_codebase_feature
  WHERE vertex_id LIKE 'feature/langgraph/%'
     OR vertex_id LIKE 'feature/langchain%'
     OR vertex_id LIKE 'feature/anthropic/%'
     OR vertex_id LIKE 'feature/internal/%';

DELETE FROM vertex_codebase_analysis
  WHERE vertex_id = 'at://did:web:amanomibashira.etzhayyim.com/com.etzhayyim.analysis.codebase/langchain-langgraph-pregel-20260509';
