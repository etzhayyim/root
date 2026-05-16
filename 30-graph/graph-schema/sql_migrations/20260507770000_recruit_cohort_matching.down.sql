DROP INDEX IF EXISTS idx_mv_recruit_cohort_match_filter;

DROP INDEX IF EXISTS idx_mv_recruit_cohort_match_posting;

DROP MATERIALIZED VIEW IF EXISTS mv_recruit_cohort_match_candidate;

DROP INDEX IF EXISTS idx_edge_recruit_match_for_cohort;

DROP TABLE IF EXISTS edge_recruit_match_for_cohort;

DROP INDEX IF EXISTS idx_edge_recruit_match_for_posting;

DROP TABLE IF EXISTS edge_recruit_match_for_posting;

DROP INDEX IF EXISTS idx_recruit_match_decision_event_proposal;

DROP TABLE IF EXISTS vertex_recruit_match_decision_event;

DROP INDEX IF EXISTS idx_recruit_match_proposal_cohort;

DROP INDEX IF EXISTS idx_recruit_match_proposal_state;

DROP INDEX IF EXISTS idx_recruit_match_proposal_posting;

DROP TABLE IF EXISTS vertex_recruit_match_proposal;
