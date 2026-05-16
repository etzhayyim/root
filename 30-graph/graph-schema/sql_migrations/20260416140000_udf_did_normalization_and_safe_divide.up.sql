DROP FUNCTION IF EXISTS did_web_root(varchar);

CREATE FUNCTION did_web_root(did varchar)
    RETURNS varchar
    LANGUAGE sql
    AS $$
      SELECT CASE
        WHEN did LIKE 'did:web:%'
          THEN CONCAT(
            SPLIT_PART(did, ':', 1), ':',
            SPLIT_PART(did, ':', 2), ':',
            SPLIT_PART(did, ':', 3)
          )
        ELSE did
      END
    $$;

DROP FUNCTION IF EXISTS normalize_actor_did(varchar);

CREATE FUNCTION normalize_actor_did(did varchar)
    RETURNS varchar
    LANGUAGE sql
    AS $$
      SELECT CASE
        WHEN did LIKE 'did:web:site.gftd.ai:%'
          THEN CONCAT(
            'did:web:',
            SPLIT_PART(SPLIT_PART(did, 'did:web:site.gftd.ai:', 2), ':', 1),
            '.gftd.ai'
          )
        WHEN did LIKE 'did:web:%'
          THEN CONCAT(
            'did:web:',
            SPLIT_PART(SPLIT_PART(did, ':', 3), '/', 1)
          )
        ELSE did
      END
    $$;

DROP FUNCTION IF EXISTS safe_divide(double precision, double precision, double precision);

CREATE FUNCTION safe_divide(
      numerator   double precision,
      denominator double precision,
      fallback    double precision
    )
    RETURNS double precision
    LANGUAGE sql
    AS $$
      SELECT CASE
        WHEN denominator IS NOT NULL AND denominator > 0
          THEN numerator / denominator
        ELSE fallback
      END
    $$;
