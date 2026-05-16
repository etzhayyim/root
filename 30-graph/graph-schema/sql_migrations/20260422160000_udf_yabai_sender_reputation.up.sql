CREATE FUNCTION yabai_sender_reputation(from_addr_arg varchar)
      RETURNS int
      LANGUAGE sql
      AS $$
        WITH stats AS (
          SELECT
            count(*)::int AS total_mails,
            sum(CASE WHEN spf_result  = 'pass' THEN 1 ELSE 0 END)::double precision
              / NULLIF(count(*), 0)   AS spf_pass_rate,
            sum(CASE WHEN dmarc_result = 'pass' THEN 1 ELSE 0 END)::double precision
              / NULLIF(count(*), 0)   AS dmarc_pass_rate,
            (now()::date - min(created_date))::int AS days_since_first_seen
          FROM vertex_gmail_email
          WHERE from_addr = from_addr_arg
            AND created_date > (now()::date - interval '30 days')
        ),
        prior AS (
          SELECT count(*)::int AS phish_hits
          FROM vertex_gmail_phishing_alert
          WHERE from_addr = from_addr_arg
            AND phishing_score >= 60
            AND created_date > (now()::date - interval '30 days')
        )
        SELECT LEAST(100,
            CASE WHEN COALESCE(stats.total_mails, 0) < 5 THEN 40 ELSE 0 END
          + CASE WHEN stats.days_since_first_seen IS NULL
                  OR stats.days_since_first_seen < 7 THEN 20 ELSE 0 END
          + CASE WHEN COALESCE(stats.spf_pass_rate, 0.0) < 0.5 THEN 30 ELSE 0 END
          + CASE WHEN COALESCE(stats.dmarc_pass_rate, 0.0) < 0.5 THEN 20 ELSE 0 END
          + CASE WHEN COALESCE(prior.phish_hits, 0) > 0 THEN 10 ELSE 0 END
        )::int AS score
        FROM stats, prior
      $$;
