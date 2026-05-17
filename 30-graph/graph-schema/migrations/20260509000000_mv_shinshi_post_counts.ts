import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * Streaming MV `mv_shinshi_post_counts` — pre-aggregated post count
 * per shinshi sub-DID (did:web:sh1n5h1x.etzhayyim.com:{slug}).
 *
 * Replaces the cold-path of the `lg_shinshi/graphs/coverage.py` graph,
 * which was hitting the live `vertex_repo_record` LEFT JOIN at 8-21s
 * under RW load. With this MV the cold path drops to <100ms (single
 * SELECT over a 1952-row pre-aggregated MV).
 *
 * RW MV memory safety pre-flight (per `30-graph/graph-schema/CLAUDE.md`):
 *   - Cardinality: COUNT(DISTINCT repo) WHERE collection='app.bsky.feed.post'
 *     AND repo LIKE 'did:web:sh1n5h1x.etzhayyim.com:%' = 1,952 rows.
 *     Well below the 500k high-cardinality forbidden threshold.
 *   - Source scan: 9,191 rows. Small enough that BACKGROUND_DDL is
 *     unnecessary.
 *   - No MAX(varchar) over wide payload columns. Just COUNT(*) per
 *     group → tiny aggregation state.
 *   - Filter is collection + LIKE prefix; both are indexed-friendly.
 *
 * The MV is incrementally updated by RW's streaming engine on every
 * commit to `vertex_repo_record`. New shinshi scene posts auto-update
 * `post_count` for the corresponding repo in <100ms.
 *
 * Read path: `lg_shinshi/graphs/coverage.py` SELECT * FROM this MV +
 * cross-join with the (cheap) DISTINCT modelProfile repos query.
 */

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_shinshi_post_counts AS
    SELECT
      repo,
      COUNT(*) AS post_count
    FROM vertex_repo_record
    WHERE collection = 'app.bsky.feed.post'
      AND repo LIKE 'did:web:sh1n5h1x.etzhayyim.com:%'
    GROUP BY repo
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_shinshi_post_counts`.execute(db);
}
