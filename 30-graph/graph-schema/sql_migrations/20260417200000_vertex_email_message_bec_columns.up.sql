CREATE MATERIALIZED VIEW IF NOT EXISTS mv_email_first_contact_senders AS
    SELECT
      account_did,
      from_address,
      from_domain,
      MIN(received_at) AS first_seen,
      MAX(received_at) AS last_seen,
      COUNT(*) AS msg_count
    FROM vertex_email_message
    WHERE account_did IS NOT NULL AND from_address IS NOT NULL
    GROUP BY account_did, from_address, from_domain;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_email_auth_fail AS
    SELECT
      account_did,
      from_address,
      from_domain,
      received_at,
      spf_result,
      dkim_result,
      dmarc_result,
      subject_hash
    FROM vertex_email_message
    WHERE
      spf_result = 'fail' OR dkim_result = 'fail' OR dmarc_result = 'fail' OR
      spf_result = 'softfail' OR dmarc_result = 'softfail';

CREATE INDEX IF NOT EXISTS idx_email_first_contact ON mv_email_first_contact_senders (account_did, first_seen);

CREATE INDEX IF NOT EXISTS idx_email_from_name ON vertex_email_message (from_name);

CREATE INDEX IF NOT EXISTS idx_email_dmarc ON vertex_email_message (dmarc_result);
