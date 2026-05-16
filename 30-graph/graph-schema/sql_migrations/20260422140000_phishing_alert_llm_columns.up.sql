ALTER TABLE vertex_gmail_phishing_alert ADD COLUMN llm_score INTEGER;

ALTER TABLE vertex_gmail_phishing_alert ADD COLUMN llm_verdict VARCHAR;

ALTER TABLE vertex_gmail_phishing_alert ADD COLUMN llm_rationale VARCHAR;
