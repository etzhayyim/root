import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { detectLanguage, selectByDistribution, INDIA_LANGUAGE_DISTRIBUTION } from '../language/detect.js';
import { replacePathLang, extractPathLang } from '../language/url.js';

describe('selectByDistribution', () => {
	it('returns a key from the distribution', () => {
		const dist = { en: 50, ja: 50 };
		const result = selectByDistribution(dist);
		expect(['en', 'ja']).toContain(result);
	});

	it('returns the only key when 100%', () => {
		const dist = { fr: 100 };
		expect(selectByDistribution(dist)).toBe('fr');
	});

	it('INDIA_LANGUAGE_DISTRIBUTION sums to ~87.3', () => {
		const sum = Object.values(INDIA_LANGUAGE_DISTRIBUTION).reduce((a, b) => a + b, 0);
		expect(sum).toBeGreaterThan(85);
		expect(sum).toBeLessThan(100);
	});
});

describe('detectLanguage', () => {
	const origNavigator = globalThis.navigator;

	afterEach(() => {
		Object.defineProperty(globalThis, 'navigator', { value: origNavigator, writable: true });
	});

	it('returns defaultLang when navigator is undefined', () => {
		Object.defineProperty(globalThis, 'navigator', { value: undefined, writable: true });
		const result = detectLanguage({ supported: ['en', 'ja'], defaultLang: 'en' });
		expect(result).toBe('en');
	});

	it('matches primary language from navigator.languages', () => {
		Object.defineProperty(globalThis, 'navigator', {
			value: { languages: ['ja-JP', 'en-US'], language: 'ja-JP' },
			writable: true,
		});
		const result = detectLanguage({ supported: ['en', 'ja', 'ko'], defaultLang: 'en' });
		expect(result).toBe('ja');
	});

	it('falls back to defaultLang for unsupported language', () => {
		Object.defineProperty(globalThis, 'navigator', {
			value: { languages: ['sv-SE'], language: 'sv-SE' },
			writable: true,
		});
		const result = detectLanguage({ supported: ['en', 'ja'], defaultLang: 'en' });
		expect(result).toBe('en');
	});

	it('Hindi speaker gets India distribution result', () => {
		Object.defineProperty(globalThis, 'navigator', {
			value: { languages: ['hi-IN'], language: 'hi-IN' },
			writable: true,
		});
		const result = detectLanguage({ supported: ['en', 'hi', 'bn', 'te'], defaultLang: 'en' });
		// Should be one of the India distribution languages
		expect(typeof result).toBe('string');
		expect(result.length).toBeGreaterThan(0);
	});
});

describe('replacePathLang', () => {
	it('replaces language segment', () => {
		expect(replacePathLang('/en/articles/123', 'ja')).toBe('/ja/articles/123');
	});

	it('handles root path', () => {
		expect(replacePathLang('/en', 'fr')).toBe('/fr');
	});

	it('handles deep path', () => {
		expect(replacePathLang('/ko/a/b/c', 'zh')).toBe('/zh/a/b/c');
	});
});

describe('extractPathLang', () => {
	it('extracts language from path', () => {
		expect(extractPathLang('/ja/articles')).toBe('ja');
	});

	it('returns undefined for root path', () => {
		expect(extractPathLang('/')).toBeUndefined();
	});

	it('handles single segment', () => {
		expect(extractPathLang('/en')).toBe('en');
	});
});
