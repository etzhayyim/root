/**
 * Shared profile utilities — single source for functions duplicated across
 * ProfilePanel.svelte and routes/profile/[handle]/+page.svelte.
 */
import { atProcedure, listRecords } from '$lib/atproto-agent';
import type { ActorScores } from '../actor/types.js';

// ── eSIM ──

export interface ESimProfile {
	iccid: string;
	provider: string;
	coverage: string;
	dataRemainingMb: number;
	dataUsedMb: number;
	status: string;
	qrCodeUrl?: string;
	activationCode?: string;
}

export async function fetchEsimProfile(): Promise<ESimProfile | null> {
	try {
		const result = await atProcedure<{ rows?: Record<string, unknown>[] }>('ai.gftd.apps.celler.getEsimProfile', {});
		if (result?.rows?.[0]) {
			const row = result.rows[0];
			return {
				iccid: String(row.iccid ?? ''),
				provider: String(row.provider ?? 'telnyx'),
				coverage: String(row.coverage ?? 'global'),
				dataRemainingMb: Number(row.dataRemainingMb ?? 0),
				dataUsedMb: Number(row.dataUsedMb ?? 0),
				status: String(row.status ?? 'unknown'),
				qrCodeUrl: row.qrCodeUrl ? String(row.qrCodeUrl) : undefined,
				activationCode: row.activationCode ? String(row.activationCode) : undefined,
			};
		}
		return null;
	} catch (e) {
		console.warn('fetchEsimProfile failed', e);
		return null;
	}
}

// ── Actor Scores (Dojo / Joucho) ──

export async function fetchActorScores(actorDid: string): Promise<ActorScores | undefined> {
	try {
		const normalizedDid = actorDid.trim();
		if (!normalizedDid) return undefined;
		const scores: ActorScores = {};
		const [dojoProfileRes, jouchoReviewsRes] = await Promise.allSettled([
			atProcedure<Record<string, unknown>>('ai.gftd.apps.dojo.getXpProfile', { did: normalizedDid }).catch((_err: unknown) => null),
			listRecords(normalizedDid, 'ai.gftd.apps.joucho.review', { limit: 100 }).catch((_err: unknown) => null),
		]);

		const dojoProfile = dojoProfileRes.status === 'fulfilled' ? dojoProfileRes.value : null;
		if (dojoProfile && !('error' in dojoProfile)) {
			const drills = Number(dojoProfile.trackCount ?? dojoProfile.drillsCompleted ?? 0);
			const totalXp = Number(dojoProfile.totalXp ?? 0);
			if (drills > 0) {
				scores.dojo = {
					drillsCompleted: drills,
					avgScore: Math.round(totalXp / drills),
				};
			}
		}

		const jouchoRecords = jouchoReviewsRes.status === 'fulfilled'
			? (((jouchoReviewsRes.value as { records?: Array<Record<string, unknown>> })?.records) ?? [])
			: [];
		if (jouchoRecords.length > 0) {
			const numericScores = jouchoRecords
				.map((record) => {
					const value = (record.value ?? record) as Record<string, unknown>;
					return Number(value.avgScore ?? value.qualityScore ?? value.score ?? 0);
				})
				.filter((value) => Number.isFinite(value) && value > 0);
			if (numericScores.length > 0) {
				const rounded = Math.round(numericScores.reduce((sum, value) => sum + value, 0) / numericScores.length);
				const grade = rounded >= 90 ? 'S' : rounded >= 75 ? 'A' : rounded >= 60 ? 'B' : rounded >= 40 ? 'C' : 'D';
				scores.joucho = { reviewCount: numericScores.length, avgScore: rounded, grade };
			}
		}
		return (scores.dojo || scores.joucho) ? scores : undefined;
	} catch (e) {
		console.warn('fetchActorScores failed', e);
		return undefined;
	}
}

// ── Time Formatting ──

export function timeAgo(ts: string): string {
	const date = new Date(ts);
	if (Number.isNaN(date.getTime())) return '';
	const diff = Date.now() - date.getTime();
	const mins = Math.max(0, Math.floor(diff / 60000));
	if (mins < 60) return `${mins}m`;
	const hrs = Math.floor(mins / 60);
	if (hrs < 24) return `${hrs}h`;
	return `${Math.floor(hrs / 24)}d`;
}

// ── Profile Tab Definitions ──

export const PROFILE_TABS_SELF = [
	{ value: 'posts', label: '投稿' },
	{ value: 'replies', label: '返信' },
	{ value: 'media', label: 'メディア' },
	{ value: 'video', label: 'ビデオ' },
	{ value: 'likes', label: 'いいね' },
	{ value: 'dojo', label: 'Dojo' },
	{ value: 'sim', label: 'SIM' },
	{ value: 'feeds', label: 'フィード' },
	{ value: 'starter', label: 'スターターパック' },
];

export const PROFILE_TABS_OTHER = [
	{ value: 'posts', label: '投稿' },
	{ value: 'replies', label: '返信' },
	{ value: 'media', label: 'メディア' },
	{ value: 'video', label: 'ビデオ' },
	{ value: 'likes', label: 'いいね' },
	{ value: 'dojo', label: 'Dojo' },
	{ value: 'feeds', label: 'フィード' },
	{ value: 'starter', label: 'スターターパック' },
];
