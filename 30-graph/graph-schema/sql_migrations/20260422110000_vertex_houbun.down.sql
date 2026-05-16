DROP INDEX IF EXISTS idx_edge_houbun_amends_dst;

DROP INDEX IF EXISTS idx_edge_houbun_amends_src;

DROP TABLE IF EXISTS edge_houbun_amends;

DROP INDEX IF EXISTS idx_edge_houbun_statute_article_dst;

DROP INDEX IF EXISTS idx_edge_houbun_statute_article_src;

DROP TABLE IF EXISTS edge_houbun_statute_article;

DROP INDEX IF EXISTS idx_houbun_treaty_source_record_id;

DROP TABLE IF EXISTS vertex_houbun_treaty;

DROP INDEX IF EXISTS idx_houbun_amendment_supersedes;

DROP INDEX IF EXISTS idx_houbun_amendment_statute_ref;

DROP TABLE IF EXISTS vertex_houbun_amendmentEvent;

DROP INDEX IF EXISTS idx_houbun_article_did;

DROP INDEX IF EXISTS idx_houbun_article_statute_ref;

DROP TABLE IF EXISTS vertex_houbun_article;

DROP INDEX IF EXISTS idx_houbun_statute_source;

DROP INDEX IF EXISTS idx_houbun_statute_statute_id;

DROP INDEX IF EXISTS idx_houbun_statute_jurisdiction;

DROP TABLE IF EXISTS vertex_houbun_statute;
