import { compileKysely, graphSql, ksql } from '$lib/graph-sql';

export interface BrowsingHistoryRow {
	path: string;
	title: string;
	historyType: string;
	avatar: string | null;
	handle: string | null;
	createdAt: string;
	rkey: string | null;
}

export async function listBrowsingHistory(repoDid: string, limit = 200): Promise<BrowsingHistoryRow[]> {
	return graphSql<BrowsingHistoryRow>(compileKysely(ksql`
		SELECT
			coalesce(path, '') AS path,
			coalesce(title, '') AS title,
			coalesce(history_type, 'post') AS "historyType",
			avatar,
			handle,
			coalesce(created_at, indexed_at, '') AS "createdAt",
			rkey
		FROM vertex_yoro_browsing_history
		WHERE repo = ${repoDid}
		ORDER BY created_at DESC
		LIMIT ${Math.max(1, Math.floor(limit))}
	`));
}
