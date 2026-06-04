/**
 * XP & Gamification Store — Duolingo-inspired progression system.
 *
 * Data source: dojo.etzhayyim.com via PDS XRPC (authoritative).
 * localStorage = cache only (offline fallback).
 *
 * Graph labels (dojo app):
 *   (:XpProfile {actorDid, xp, totalXp, level, streak, ...})
 *   (:Achievement {actorDid, achievementId, unlockedAt, ...})
 *   (:XpEvent {actorDid, amount, source, ...})
 */
import { getSessionToken } from '$lib/auth';

const CACHE_KEY = 'yoroXpCache';
const PDS = 'https://atproto.etzhayyim.com';
const DOJO_NSID = 'com.etzhayyim.apps.dojo';

async function authHeaders(): Promise<Record<string, string>> {
	const token = await getSessionToken().catch(() => null);
	return {
		'Content-Type': 'application/json',
		...(token ? { Authorization: `Bearer ${token}` } : {}),
	};
}

// ── XP Amounts (must match dojo app.ts XP_VALUES) ──
export const XP_VALUES = {
	dailyLogin: 10,
	post: 15,
	reply: 10,
	likeGiven: 2,
	likeReceived: 3,
	followGiven: 5,
	followReceived: 8,
	drillComplete: 50,
	drillPerfect: 100,
	aarSubmit: 30,
	dmSent: 5,
	streakBonus7: 50,
	streakBonus30: 200,
	achievementUnlock: 25,
} as const;

// ── Level Thresholds (Duolingo-style exponential, must match dojo) ──
export function xpForLevel(level: number): number {
	if (level <= 1) return 0;
	return Math.floor(100 * Math.pow(1.3, level - 2));
}

export function levelFromXP(xp: number): number {
	let level = 1;
	let total = 0;
	while (total + xpForLevel(level + 1) <= xp) {
		level++;
		total += xpForLevel(level);
	}
	return level;
}

export function xpProgressInLevel(xp: number): { current: number; needed: number; pct: number } {
	let level = 1;
	let total = 0;
	while (total + xpForLevel(level + 1) <= xp) {
		level++;
		total += xpForLevel(level);
	}
	const current = xp - total;
	const needed = xpForLevel(level + 1);
	return { current, needed, pct: needed > 0 ? Math.min(current / needed, 1) : 1 };
}

// ── Kyu/Dan Mapping (society6) ──
export type KyuDanRank = {
	rank: string;
	label: string;
	color: string;
	minScore: number;
};

export const KYU_DAN_LADDER: KyuDanRank[] = [
	{ rank: 'Kyu 6', label: '白', color: 'text-gray-300', minScore: 0 },
	{ rank: 'Kyu 5', label: '金', color: 'text-yellow-400', minScore: 100 },
	{ rank: 'Kyu 4', label: '橙', color: 'text-orange-400', minScore: 300 },
	{ rank: 'Kyu 3', label: '緑', color: 'text-emerald-400', minScore: 600 },
	{ rank: 'Kyu 2', label: '青', color: 'text-blue-400', minScore: 1000 },
	{ rank: 'Kyu 1', label: '茶', color: 'text-amber-600', minScore: 1500 },
	{ rank: 'Dan 1', label: '黒', color: 'text-white', minScore: 2000 },
	{ rank: 'Dan 2', label: '黒', color: 'text-white', minScore: 3000 },
	{ rank: 'Dan 3', label: '黒', color: 'text-white', minScore: 4000 },
	{ rank: 'Dan 4', label: '黒', color: 'text-white', minScore: 5000 },
	{ rank: 'Dan 5', label: '黒', color: 'text-white', minScore: 6000 },
];

export function rankFromScore(score: number): KyuDanRank {
	for (let i = KYU_DAN_LADDER.length - 1; i >= 0; i--) {
		if (score >= KYU_DAN_LADDER[i].minScore) return KYU_DAN_LADDER[i];
	}
	return KYU_DAN_LADDER[0];
}

// ── Achievement Definitions ──
export type AchievementId =
	| 'firstPost' | 'firstDrill' | 'firstFollow' | 'firstDm'
	| 'streak7' | 'streak30' | 'streak100'
	| 'xp100' | 'xp1000' | 'xp5000' | 'xp10000'
	| 'drills5' | 'drills25' | 'drills100'
	| 'perfectDrill' | 'socialButterfly' | 'nightOwl'
	| 'kyu5' | 'kyu3' | 'kyu1' | 'dan1'
	| 'posts10' | 'posts50' | 'posts100'
	| 'followers10' | 'followers100';

export type AchievementDef = {
	id: AchievementId;
	icon: string;
	name: string;
	description: string;
	xpReward: number;
	category: 'social' | 'dojo' | 'streak' | 'milestone' | 'rank';
	rarity: 'common' | 'rare' | 'epic' | 'legendary';
};

export const ACHIEVEMENTS: AchievementDef[] = [
	{ id: 'firstPost', icon: '📝', name: 'First Post', description: 'はじめての投稿', xpReward: 25, category: 'social', rarity: 'common' },
	{ id: 'firstFollow', icon: '🤝', name: 'First Follow', description: 'はじめてのフォロー', xpReward: 25, category: 'social', rarity: 'common' },
	{ id: 'firstDm', icon: '💬', name: 'First DM', description: 'はじめてのメッセージ', xpReward: 25, category: 'social', rarity: 'common' },
	{ id: 'posts10', icon: '✍️', name: '10 Posts', description: '10 回投稿', xpReward: 50, category: 'social', rarity: 'common' },
	{ id: 'posts50', icon: '🖊️', name: '50 Posts', description: '50 回投稿', xpReward: 100, category: 'social', rarity: 'rare' },
	{ id: 'posts100', icon: '📚', name: '100 Posts', description: '100 回投稿', xpReward: 200, category: 'social', rarity: 'epic' },
	{ id: 'socialButterfly', icon: '🦋', name: 'Social Butterfly', description: '1 日に 5 人フォロー', xpReward: 50, category: 'social', rarity: 'rare' },
	{ id: 'followers10', icon: '🌟', name: 'Rising Star', description: 'フォロワー 10 人', xpReward: 50, category: 'social', rarity: 'common' },
	{ id: 'followers100', icon: '👑', name: 'Influencer', description: 'フォロワー 100 人', xpReward: 200, category: 'social', rarity: 'epic' },
	{ id: 'firstDrill', icon: '🥋', name: 'First Drill', description: 'はじめてのドリル完了', xpReward: 50, category: 'dojo', rarity: 'common' },
	{ id: 'drills5', icon: '🔥', name: '5 Drills', description: '5 回ドリル完了', xpReward: 75, category: 'dojo', rarity: 'common' },
	{ id: 'drills25', icon: '⚔️', name: '25 Drills', description: '25 回ドリル完了', xpReward: 150, category: 'dojo', rarity: 'rare' },
	{ id: 'drills100', icon: '🏯', name: 'Drill Master', description: '100 回ドリル完了', xpReward: 500, category: 'dojo', rarity: 'legendary' },
	{ id: 'perfectDrill', icon: '💯', name: 'Perfect Score', description: 'ドリルで 100 点', xpReward: 100, category: 'dojo', rarity: 'epic' },
	{ id: 'streak7', icon: '🔥', name: 'Week Warrior', description: '7 日連続ログイン', xpReward: 50, category: 'streak', rarity: 'common' },
	{ id: 'streak30', icon: '🌙', name: 'Monthly Master', description: '30 日連続ログイン', xpReward: 200, category: 'streak', rarity: 'rare' },
	{ id: 'streak100', icon: '💎', name: 'Legendary Streak', description: '100 日連続ログイン', xpReward: 500, category: 'streak', rarity: 'legendary' },
	{ id: 'nightOwl', icon: '🦉', name: 'Night Owl', description: '深夜 2 時にアクティブ', xpReward: 25, category: 'streak', rarity: 'rare' },
	{ id: 'xp100', icon: '⚡', name: 'Spark', description: 'XP 100 到達', xpReward: 0, category: 'milestone', rarity: 'common' },
	{ id: 'xp1000', icon: '⚡', name: 'Thunder', description: 'XP 1,000 到達', xpReward: 0, category: 'milestone', rarity: 'rare' },
	{ id: 'xp5000', icon: '⚡', name: 'Lightning', description: 'XP 5,000 到達', xpReward: 0, category: 'milestone', rarity: 'epic' },
	{ id: 'xp10000', icon: '⚡', name: 'Storm', description: 'XP 10,000 到達', xpReward: 0, category: 'milestone', rarity: 'legendary' },
	{ id: 'kyu5', icon: '🥇', name: 'Kyu 5', description: '級 5 到達', xpReward: 50, category: 'rank', rarity: 'common' },
	{ id: 'kyu3', icon: '🥈', name: 'Kyu 3', description: '級 3 到達', xpReward: 100, category: 'rank', rarity: 'rare' },
	{ id: 'kyu1', icon: '🥉', name: 'Kyu 1', description: '級 1 到達', xpReward: 200, category: 'rank', rarity: 'epic' },
	{ id: 'dan1', icon: '🏆', name: 'Dan 1', description: '段 1 到達 — 黒帯', xpReward: 500, category: 'rank', rarity: 'legendary' },
];

export function getAchievement(id: AchievementId): AchievementDef | undefined {
	return ACHIEVEMENTS.find(a => a.id === id);
}

// ── Gamification State (client-side view of PDS data) ──
export interface GamificationState {
	xp: number;
	totalXP: number;
	streak: number;
	streakLastDate: string;
	gems: number;
	achievements: AchievementId[];
	dailyXPEarned: number;
	dailyXPDate: string;
	drillsCompleted: number;
	postsCount: number;
	weeklyXP: number[];
	loading: boolean;
}

const DEFAULT_STATE: GamificationState = {
	xp: 0, totalXP: 0, streak: 0, streakLastDate: '', gems: 0,
	achievements: [], dailyXPEarned: 0, dailyXPDate: '',
	drillsCompleted: 0, postsCount: 0, weeklyXP: [0, 0, 0, 0, 0, 0, 0],
	loading: true,
};

// ── PDS XRPC helpers ──
async function dojoRpc(method: string, body: Record<string, unknown>): Promise<Record<string, unknown> | null> {
	try {
		if (method === 'addXp') {
			const token = await getSessionToken().catch(() => null);
			if (!token) return null;
		}
		const res = await fetch(`${PDS}/xrpc/${DOJO_NSID}.${method}`, {
			method: 'POST',
			headers: await authHeaders(),
			body: JSON.stringify(body),
		});
		if (!res.ok) return null;
		return await res.json();
	} catch {
		return null;
	}
}

function loadCache(): GamificationState {
	if (typeof window === 'undefined') return { ...DEFAULT_STATE };
	try {
		const raw = localStorage.getItem(CACHE_KEY);
		if (!raw) return { ...DEFAULT_STATE };
		return { ...DEFAULT_STATE, ...JSON.parse(raw) };
	} catch {
		return { ...DEFAULT_STATE };
	}
}

function saveCache(s: GamificationState) {
	try { localStorage.setItem(CACHE_KEY, JSON.stringify(s)); } catch (error) { console.warn("[silent-fail] xp-store: suppressed error", error); }
}

// ── Reactive Store (singleton) ──
let _state = $state<GamificationState>(loadCache());
let _pendingAchievements = $state<AchievementDef[]>([]);
let _levelUpFrom = $state<number | null>(null);
let _actorDid = '';

export function useGamification() {
	return {
		get state() { return _state; },
		get level() { return levelFromXP(_state.totalXP); },
		get progress() { return xpProgressInLevel(_state.totalXP); },
		get rank() { return rankFromScore(_state.totalXP); },
		get pendingAchievements() { return _pendingAchievements; },
		get levelUpFrom() { return _levelUpFrom; },

		/** Set actor DID for PDS queries */
		setActorDid(did: string) { _actorDid = did; },

		/** Initialize — fetch profile from PDS, send dailyLogin XP */
		async init() {
			// Load cache immediately for fast render
			const cached = loadCache();
			if (cached.totalXP > 0) {
				_state = { ...cached, loading: true };
			}

			// Determine actor DID
			if (!_actorDid) {
				// Pull DID from local atproto session (set by auth bootstrap). No XRPC — avoids 401 when signed out.
				try {
					const { getSession } = await import('$lib/atproto-agent');
					const session = getSession();
					_actorDid = session?.did ?? '';
				} catch (error) { console.warn("[silent-fail] xp-store: suppressed error", error); }
			}

			if (!_actorDid) {
				_state = { ...cached, loading: false };
				return;
			}

			// Send dailyLogin XP (dojo handles streak logic server-side)
			const addResult = await dojoRpc('addXp', { did: _actorDid, source: 'dailyLogin' });

			// Fetch full profile from dojo
			const profile = await dojoRpc('getXpProfile', { did: _actorDid });
			if (profile && !profile.error) {
				const prevLevel = levelFromXP(_state.totalXP);
				_state = {
					xp: Number(profile.xp ?? 0),
					totalXP: Number(profile.totalXp ?? 0),
					streak: Number(profile.streak ?? 0),
					streakLastDate: String(profile.streakLastDate ?? ''),
					gems: Number(profile.gems ?? 0),
					dailyXPEarned: Number(profile.dailyXpEarned ?? 0),
					dailyXPDate: String(profile.dailyXpDate ?? ''),
					drillsCompleted: Number(profile.drillsCompleted ?? 0),
					postsCount: Number(profile.postsCount ?? 0),
					weeklyXP: (profile.weeklyXp as number[]) ?? [0, 0, 0, 0, 0, 0, 0],
					achievements: ((profile.achievements as Array<{id: string}>) ?? []).map(a => a.id as AchievementId),
					loading: false,
				};
				saveCache(_state);

				// Check level-up from addXp
				if (addResult && addResult.levelUp) {
					_levelUpFrom = Number(addResult.prevLevel ?? prevLevel);
					setTimeout(() => { _levelUpFrom = null; }, 3000);
				}

				// Check new achievements from addXp
				const newAchievements = addResult?.newAchievements as string[] | undefined;
				if (addResult && Array.isArray(newAchievements)) {
					for (const achId of newAchievements) {
						const def = getAchievement(achId as AchievementId);
						if (def) {
							_pendingAchievements = [..._pendingAchievements, def];
							setTimeout(() => {
								_pendingAchievements = _pendingAchievements.filter(a => a.id !== achId);
							}, 4000);
						}
					}
				}
			} else {
				_state = { ...cached, loading: false };
			}
		},

		/** Track an action — sends XP to dojo PDS, updates local state */
		async addXP(source: string) {
			if (!_actorDid) return;

			const prevLevel = levelFromXP(_state.totalXP);
			const amount = XP_VALUES[source as keyof typeof XP_VALUES] ?? 0;

			// Optimistic local update
			_state = {
				..._state,
				totalXP: _state.totalXP + amount,
				xp: _state.xp + amount,
				dailyXPEarned: _state.dailyXPEarned + amount,
			};
			saveCache(_state);

			// Send to dojo PDS
			const result = await dojoRpc('addXp', { did: _actorDid, source });
			if (result && !result.error) {
				// Reconcile with server response
				const totalXp = result.totalXp as number | undefined;
				if (typeof totalXp === 'number') {
					_state = { ..._state, totalXP: totalXp };
				}
				if (result.levelUp) {
					_levelUpFrom = Number(result.prevLevel ?? prevLevel);
					setTimeout(() => { _levelUpFrom = null; }, 3000);
				}
				const newAchievements = result.newAchievements as string[] | undefined;
				if (Array.isArray(newAchievements)) {
					for (const achId of newAchievements) {
						const def = getAchievement(achId as AchievementId);
						if (def) {
							if (!_state.achievements.includes(achId as AchievementId)) {
								_state = { ..._state, achievements: [..._state.achievements, achId as AchievementId] };
							}
							_pendingAchievements = [..._pendingAchievements, def];
							setTimeout(() => {
								_pendingAchievements = _pendingAchievements.filter(a => a.id !== achId);
							}, 4000);
						}
					}
				}
				saveCache(_state);
			}
		},

		trackPost() { return this.addXP('post'); },
		trackReply() { return this.addXP('reply'); },
		trackLikeGiven() { return this.addXP('likeGiven'); },
		trackFollowGiven() { return this.addXP('followGiven'); },
		trackDMSent() { return this.addXP('dmSent'); },
		trackDrillComplete(score: number) {
			return this.addXP(score >= 100 ? 'drillPerfect' : 'drillComplete');
		},
		trackAARSubmit() { return this.addXP('aarSubmit'); },

		addGems(amount: number) {
			if (!_actorDid) return;
			_state = { ..._state, gems: _state.gems + amount };
			saveCache(_state);
			void dojoRpc('addGems', { did: _actorDid, amount });
		},

		dismissAchievement(id: AchievementId) {
			_pendingAchievements = _pendingAchievements.filter(a => a.id !== id);
		},
	};
}
