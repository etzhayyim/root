import { compileKysely, graphSql, ksql, sqlString } from '$lib/graph-sql';

export const YORO_EVOLUTION_COLLECTIONS = {
	koji: 'com.etzhayyim.apps.yoro.kojiDiscovery',
	kyumei: 'com.etzhayyim.apps.yoro.kyumeiValidation',
	shinka: 'com.etzhayyim.apps.yoro.shinkaEvolution',
	hinshitsu: 'com.etzhayyim.apps.yoro.hinshitsuAssessment',
	shinkaKnowledge: 'com.etzhayyim.apps.yoro.shinkaKnowledge',
} as const;

export interface EvolutionActorCandidateRow {
	did: string;
	name: string;
	desc: string;
	kyumei_count: number;
	shinka_count: number;
	hinshitsu_count: number;
	knowledge_count: number;
}

export interface EvolutionStatsRow {
	koji_count: number;
	kyumei_count: number;
	shinka_count: number;
	hinshitsu_count: number;
	shinka_knowledge_count: number;
}

export interface EvolutionRecentRow {
	label: string;
	actorDid: string;
	actorName: string;
	readinessGrade: string | null;
	summary: string | null;
	validationScore: string | null;
	mood: string | null;
	qualityScore: string | null;
	grade: string | null;
	domainSummary: string | null;
	createdAt: string;
}

export interface EvolutionEvidenceProfileRow {
	name: string;
	description: string;
}

export interface EvolutionEvidenceRow {
	label: string;
	readinessGrade: string | null;
	validationScore: string | null;
	qualityScore: string | null;
	grade: string | null;
	domainSummary: string | null;
	createdAt: string;
}

export async function listEvolutionActorCandidates(limit = 20): Promise<EvolutionActorCandidateRow[]> {
	return graphSql<EvolutionActorCandidateRow>(compileKysely(ksql`
		SELECT
			p.did AS did,
			coalesce(p.display_name, '') AS name,
			coalesce(p.description, '') AS desc,
			coalesce(ec.kyumei_count, 0) AS kyumei_count,
			coalesce(ec.shinka_count, 0) AS shinka_count,
			coalesce(ec.hinshitsu_count, 0) AS hinshitsu_count,
			coalesce(ec.knowledge_count, 0) AS knowledge_count
		FROM vertex_profile AS p
		LEFT JOIN mv_yoro_actor_evolution_counts AS ec ON ec.actor_did = p.did
		WHERE p.did >= 'did:web:'
			AND p.did < 'did:web;'
		ORDER BY p.created_date DESC
		LIMIT ${Math.max(1, Math.floor(limit))}
	`));
}

export async function fetchEvolutionStats(): Promise<EvolutionStatsRow | null> {
	const rows = await graphSql<EvolutionStatsRow>(compileKysely(ksql`
		SELECT koji_count, kyumei_count, shinka_count, hinshitsu_count, shinka_knowledge_count
		FROM mv_yoro_evolution_stats
		LIMIT 1
	`));
	return rows[0] ?? null;
}

export async function listRecentEvolutionResults(limit = 10): Promise<EvolutionRecentRow[]> {
	return graphSql<EvolutionRecentRow>(compileKysely(ksql`
		SELECT label, "actorDid", "actorName", "readinessGrade", summary, "validationScore", mood, "qualityScore", grade, "domainSummary", "createdAt"
		FROM mv_yoro_evolution_recent
		WHERE source = 'browser'
		ORDER BY "createdAt" DESC
		LIMIT ${Math.max(1, Math.floor(limit))}
	`));
}

export async function fetchEvolutionEvidenceProfile(actorDid: string): Promise<EvolutionEvidenceProfileRow | null> {
	const rows = await graphSql<EvolutionEvidenceProfileRow>(`
		SELECT
			coalesce(display_name, '') AS name,
			coalesce(description, '') AS description
		FROM vertex_profile
		WHERE did = ${sqlString(actorDid)}
		LIMIT 1
	`);
	return rows[0] ?? null;
}

export async function listEvolutionEvidence(actorDid: string): Promise<EvolutionEvidenceRow[]> {
	return graphSql<EvolutionEvidenceRow>(compileKysely(ksql`
		SELECT label, "readinessGrade", "validationScore", "qualityScore", grade, "domainSummary", "createdAt"
		FROM (
			SELECT
				label,
				"readinessGrade",
				"validationScore",
				"qualityScore",
				grade,
				"domainSummary",
				"createdAt",
				row_number() OVER (PARTITION BY label ORDER BY "createdAt" DESC) AS rn
			FROM mv_yoro_evolution_recent
			WHERE "actorDid" = ${actorDid}
				AND label IN ('KojiDiscovery', 'KyumeiValidation', 'HinshitsuAssessment', 'ShinkaKnowledge')
		) evidence
		WHERE rn <= 2
		ORDER BY "createdAt" DESC
		LIMIT 8
	`));
}
