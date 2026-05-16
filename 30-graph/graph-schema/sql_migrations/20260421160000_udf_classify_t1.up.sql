DROP FUNCTION IF EXISTS classify_t1(varchar, varchar, varchar, varchar, varchar, varchar, varchar);

CREATE FUNCTION classify_t1(
      spf_result     varchar,
      dkim_result    varchar,
      dmarc_result   varchar,
      reply_to       varchar,
      from_addr      varchar,
      subject        varchar,
      body_urls_json varchar
    ) RETURNS int
    LANGUAGE sql
    AS $$
      SELECT LEAST(100,
        CASE WHEN spf_result = 'fail'     THEN 25
             WHEN spf_result = 'softfail' THEN 10
             ELSE 0
        END
        + CASE WHEN dkim_result IN ('fail', 'none') THEN 20 ELSE 0 END
        + CASE WHEN dmarc_result = 'fail'            THEN 20 ELSE 0 END
        + CASE WHEN reply_to IS NOT NULL
                AND reply_to <> ''
                AND reply_to <> from_addr            THEN 15 ELSE 0 END
        + CASE
            WHEN LOWER(body_urls_json) ~ '(bit\.ly|tinyurl|t\.co|is\.gd|buff\.ly)' THEN 10
            WHEN body_urls_json         ~ '\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}'     THEN 15
            WHEN LOWER(body_urls_json) ~ '(login|signin|verify|account|secure|update|confirm)' THEN 10
            ELSE 0
          END
        + CASE WHEN LOWER(subject) ~ '(urgent|immediate|action required|verify your|suspended|locked)' THEN 10 ELSE 0 END
      )
    $$;
