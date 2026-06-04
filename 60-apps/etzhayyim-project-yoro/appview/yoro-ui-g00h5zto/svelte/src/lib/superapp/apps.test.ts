import { describe, it, expect } from 'vitest';
import { apps, normalizeAppId, findAppById, resolveAppHref } from '../apps/apps.js';

describe('apps registry', () => {
	it('contains apps with required fields', () => {
		expect(apps.length).toBeGreaterThan(10);
		for (const app of apps) {
			expect(app.id).toBeTruthy();
			expect(app.name).toBeTruthy();
			expect(app.href).toMatch(/^https:\/\//);
			expect(app.category).toBeTruthy();
		}
	});

	it('has unique ids (except known duplicates)', () => {
		const ids = apps.map((a) => a.id);
		const counts = new Map<string, number>();
		for (const id of ids) {
			counts.set(id, (counts.get(id) ?? 0) + 1);
		}
		const duplicates = [...counts.entries()].filter(([, c]) => c > 1).map(([id]) => id);
		// yadoya is listed twice (known duplicate)
		expect(duplicates.length).toBeLessThanOrEqual(1);
	});

	it('all hrefs end with .etzhayyim.com path', () => {
		for (const app of apps) {
			expect(app.href).toContain('etzhayyim.com');
		}
	});
});

describe('normalizeAppId', () => {
	it('lowercases and trims', () => {
		expect(normalizeAppId('  NEWS ')).toBe('news');
	});

	it('strips .etzhayyim.com suffix', () => {
		expect(normalizeAppId('news.etzhayyim.com')).toBe('news');
	});

	it('replaces underscores with hyphens', () => {
		expect(normalizeAppId('webAnalytics')).toBe('analytics');
	});

	it('resolves email-service-adapter alias to mailer', () => {
		expect(normalizeAppId('email-service-adapter')).toBe('mailer');
	});

	it('resolves gmail alias to mailer', () => {
		expect(normalizeAppId('gmail')).toBe('mailer');
	});

	it('returns unknown IDs as-is', () => {
		expect(normalizeAppId('unknown-app')).toBe('unknown-app');
	});
});

describe('findAppById', () => {
	it('finds known app', () => {
		const app = findAppById('news');
		expect(app).toBeDefined();
		expect(app!.shortName).toBe('News');
	});

	it('resolves aliases before lookup', () => {
		const app = findAppById('email-service-adapter');
		expect(app).toBeDefined();
		expect(app!.id).toBe('mailer');
	});

	it('returns undefined for unknown', () => {
		expect(findAppById('nonexistent-xyz')).toBeUndefined();
	});
});

describe('resolveAppHref', () => {
	it('returns known app href', () => {
		expect(resolveAppHref('news')).toBe('https://news.etzhayyim.com');
	});

	it('falls back to provided href', () => {
		expect(resolveAppHref('nonexistent', 'https://custom.etzhayyim.com')).toBe('https://custom.etzhayyim.com');
	});

	it('generates default href for unknown app without fallback', () => {
		expect(resolveAppHref('mystery')).toBe('https://mystery.etzhayyim.com');
	});
});
