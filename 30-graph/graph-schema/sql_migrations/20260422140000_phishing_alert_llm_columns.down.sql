ALTER TABLE vertex_gmail_phishing_alert DROP COLUMN IF EXISTS llm_rationale;

ALTER TABLE vertex_gmail_phishing_alert DROP COLUMN IF EXISTS llm_verdict;

ALTER TABLE vertex_gmail_phishing_alert DROP COLUMN IF EXISTS llm_score;
