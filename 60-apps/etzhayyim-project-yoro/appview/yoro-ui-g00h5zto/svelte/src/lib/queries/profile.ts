import { compileKysely, graphSql, ksql } from '$lib/graph-sql';

export interface ActorScoreCountsRow {
	drills: number;
	reviews: number;
}

export async function fetchActorScoreCounts(actorDid: string): Promise<ActorScoreCountsRow> {
	const rows = await graphSql<Record<string, unknown>>(compileKysely(ksql`
		SELECT drills, reviews
		FROM mv_yoro_actor_score_counts
		WHERE actor_did = ${actorDid}
		LIMIT 1
	`));

	return {
		drills: Number(rows[0]?.drills ?? 0),
		reviews: Number(rows[0]?.reviews ?? 0),
	};
}
