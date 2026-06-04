import type { DetectConfig, LanguageCode } from './types.js';

/**
 * Default India language distribution (approximate speaker percentages).
 * Used when a Hindi-speaker visits to probabilistically select a regional language.
 */
export const INDIA_LANGUAGE_DISTRIBUTION: Record<LanguageCode, number> = {
	hi: 44.0,
	bn: 8.1,
	te: 7.2,
	ta: 6.3,
	mr: 7.0,
	gu: 4.8,
	kn: 3.7,
	ml: 3.2,
	pa: 2.8,
	en: 0.2,
};

/**
 * Select a language code using weighted random distribution.
 */
export function selectByDistribution(distribution: Record<LanguageCode, number>): LanguageCode {
	const random = Math.random() * 100;
	let cumulative = 0;
	for (const [lang, percentage] of Object.entries(distribution)) {
		cumulative += percentage;
		if (random <= cumulative) return lang;
	}
	// Fallback to first key
	return Object.keys(distribution)[0] ?? 'en';
}

/**
 * Detect the user's preferred language from `navigator.languages`.
 *
 * - Matches the primary language tag against the supported set
 * - For Hindi speakers, optionally uses India regional distribution
 * - Falls back to `config.defaultLang`
 */
export function detectLanguage(config: DetectConfig): LanguageCode {
	if (typeof globalThis.navigator === 'undefined') return config.defaultLang;

	const userLangs = navigator.languages || [navigator.language];
	const distribution = config.indiaDistribution ?? INDIA_LANGUAGE_DISTRIBUTION;

	const isHindiSpeaker = userLangs.some((l) => l.startsWith('hi'));
	if (isHindiSpeaker && distribution) {
		return selectByDistribution(distribution);
	}

	const primaryLang = userLangs[0]?.split('-')[0];
	if (primaryLang && config.supported.includes(primaryLang)) {
		return primaryLang;
	}

	return config.defaultLang;
}
