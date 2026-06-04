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
		const result = await atProcedure<{ rows?: Record<string, unknown>[] }>('com.etzhayyim.apps.celler.getEsimProfile', {});
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

// ── Cards (Stripe Issuing) ──

export interface IssuingCard {
	id: string;
	last4: string;
	cardType: string;
	status: string;
	currency: string;
	cardholderName: string;
	spendingLimit?: { amount: number; interval: string };
	createdAt: string;
}

export interface IssuingBalance {
	amount: number;
	currency: string;
}

export async function fetchCards(): Promise<{ cards: IssuingCard[]; balance: IssuingBalance | null }> {
	try {
		const [cardsResult, balanceResult] = await Promise.all([
			atProcedure<{ data?: any[] }>('com.etzhayyim.apps.cards.listCards', { limit: 25 }),
			atProcedure<{ issuingAvailable?: Array<{ amount: number; currency: string }> }>('com.etzhayyim.apps.cards.getBalance', {}),
		]);
		const rawCards = cardsResult?.data ?? (cardsResult as any)?.items ?? [];
			const cards: IssuingCard[] = rawCards.map((c: any) => ({
				id: String(c.id ?? ''),
				last4: String(c.last4 ?? ''),
				cardType: String(c.cardType ?? c.type ?? 'virtual'),
				status: String(c.status ?? 'unknown'),
				currency: String(c.currency ?? 'jpy'),
				cardholderName: String(c.cardholderName ?? c.cardholder?.name ?? ''),
				spendingLimit: c.spendingControls?.spendingLimits?.[0]
					? { amount: Number(c.spendingControls.spendingLimits[0].amount), interval: String(c.spendingControls.spendingLimits[0].interval) }
					: undefined,
				createdAt: String(c.createdAt ?? (c.created ? new Date(c.created * 1000).toISOString() : '')),
			}));
			const avail = balanceResult?.issuingAvailable;
		const balance = Array.isArray(avail) && avail.length > 0
			? { amount: avail[0].amount, currency: avail[0].currency }
			: null;
		return { cards, balance };
	} catch (e) {
		console.warn('fetchCards failed', e);
		return { cards: [], balance: null };
	}
}

export async function freezeCard(cardId: string): Promise<boolean> {
	try {
		await atProcedure('com.etzhayyim.apps.cards.freezeCard', { 'cardId': cardId });
		return true;
	} catch (e) {
		console.warn('freezeCard failed', e);
		return false;
	}
}

export async function unfreezeCard(cardId: string): Promise<boolean> {
	try {
		await atProcedure('com.etzhayyim.apps.cards.unfreezeCard', { 'cardId': cardId });
		return true;
	} catch (e) {
		console.warn('unfreezeCard failed', e);
		return false;
	}
}

// ── Actor Scores (Dojo / Joucho) ──

export async function fetchActorScores(actorDid: string): Promise<ActorScores | undefined> {
	try {
		const normalizedDid = actorDid.trim();
		if (!normalizedDid) return undefined;
		const scores: ActorScores = {};
		const [dojoProfileRes, jouchoReviewsRes] = await Promise.allSettled([
			atProcedure<Record<string, unknown>>('com.etzhayyim.apps.dojo.getXpProfile', { did: normalizedDid }).catch((_err: unknown) => null),
			listRecords(normalizedDid, 'com.etzhayyim.apps.joucho.review', { limit: 100 }).catch((_err: unknown) => null),
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
	{ value: 'cards', label: 'カード' },
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
