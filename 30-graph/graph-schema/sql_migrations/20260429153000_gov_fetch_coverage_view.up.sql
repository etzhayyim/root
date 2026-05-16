CREATE VIEW IF NOT EXISTS view_gov_fetch_coverage AS
    SELECT
      domain_code,
      COUNT(*)::INT AS total,
      COUNT(*) FILTER (WHERE COALESCE(website, '') <> '')::INT AS with_website,
      COUNT(*) FILTER (
        WHERE COALESCE(website, '') <> ''
          AND COALESCE(last_fetch_checked_at, '') <> ''
      )::INT AS fetch_checked,
      COUNT(*) FILTER (
        WHERE COALESCE(website, '') <> ''
          AND COALESCE(last_fetch_checked_at, '') <> ''
          AND (
            COALESCE(last_content_hash, '') <> ''
            OR COALESCE(last_fetch_status, '') IN ('direct_ok', 'proxy_ok', 'wet_chunk')
          )
      )::INT AS reachable,
      COUNT(*) FILTER (
        WHERE COALESCE(website, '') <> ''
          AND (
            COALESCE(last_content_hash, '') <> ''
            OR COALESCE(last_fetch_status, '') IN ('direct_ok', 'proxy_ok', 'wet_chunk')
          )
      )::INT AS hashable,
      COUNT(*) FILTER (
        WHERE COALESCE(website, '') <> ''
          AND COALESCE(last_content_hash, '') <> ''
      )::INT AS hashed,
      COUNT(*) FILTER (
        WHERE COALESCE(website, '') <> ''
          AND COALESCE(last_fetch_checked_at, '') <> ''
          AND COALESCE(last_content_hash, '') = ''
          AND COALESCE(last_fetch_status, '') NOT IN ('direct_ok', 'proxy_ok', 'wet_chunk')
      )::INT AS unreachable
    FROM vertex_gov_org
    GROUP BY domain_code;
