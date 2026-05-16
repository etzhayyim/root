DELETE FROM vertex_langgraph_deployment
WHERE vertex_id = 'langgraph.builtin.crm_lei_review_loop';

DELETE FROM vertex_langgraph_assistant
WHERE assistant_id = 'crm_lei_review_loop' AND version = 1;

DROP VIEW IF EXISTS view_crm_lei_review_queue;

DROP INDEX IF EXISTS idx_crm_lei_review_item_crm;
DROP INDEX IF EXISTS idx_crm_lei_review_item_status;

DROP TABLE IF EXISTS vertex_crm_lei_review_item;
