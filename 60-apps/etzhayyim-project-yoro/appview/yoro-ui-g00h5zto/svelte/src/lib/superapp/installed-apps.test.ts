import { describe, it, expect } from 'vitest';
import {
	KNOWN_SCOPES,
	scopeLabel,
	scopeDescription,
	installedToAppLinks,
	type InstalledApp,
} from '../apps/installed-apps.js';

describe('KNOWN_SCOPES', () => {
	it('has at least 5 scopes', () => {
		expect(KNOWN_SCOPES.length).toBeGreaterThanOrEqual(5);
	});

	it('all scopes have id, label, description', () => {
		for (const s of KNOWN_SCOPES) {
			expect(s.id).toBeTruthy();
			expect(s.label).toBeTruthy();
			expect(s.description).toBeTruthy();
		}
	});

	it('scope ids are unique', () => {
		const ids = KNOWN_SCOPES.map((s) => s.id);
		expect(new Set(ids).size).toBe(ids.length);
	});
});

describe('scopeLabel', () => {
	it('returns label for known scope', () => {
		expect(scopeLabel('profile:read')).toBe('Profile');
	});

	it('returns id for unknown scope', () => {
		expect(scopeLabel('custom:xyz')).toBe('custom:xyz');
	});
});

describe('scopeDescription', () => {
	it('returns description for known scope', () => {
		expect(scopeDescription('profile:read')).toContain('name');
	});

	it('returns id for unknown scope', () => {
		expect(scopeDescription('custom:xyz')).toBe('custom:xyz');
	});
});

describe('installedToAppLinks', () => {
	it('converts installed apps to GfAppLink format', () => {
		const installed: InstalledApp[] = [
			{
				'installationId': 'inst1',
				'appId': 'news',
				'appName': 'News',
				'appIcon': '📰',
				'appHref': 'https://news.etzhayyim.com',
				version: '1.0.0',
				'grantedScopes': ['profile:read'],
				'installedAt': 1710700800,
			},
		];
		const links = installedToAppLinks(installed);
		expect(links).toHaveLength(1);
		expect(links[0].id).toBe('inst1');
		expect(links[0].name).toBe('News');
		expect(links[0].icon).toBe('📰');
		expect(links[0].href).toBe('https://news.etzhayyim.com');
	});

	it('falls back to first char of name for missing icon', () => {
		const installed: InstalledApp[] = [
			{
				'installationId': 'inst2',
				'appId': 'unknown-app-xyz',
				'appName': 'CustomApp',
				'appIcon': '',
				'appHref': '',
				version: '0.1.0',
				'grantedScopes': [],
				'installedAt': 0,
			},
		];
		const links = installedToAppLinks(installed);
		expect(links[0].icon).toBe('C');
	});

	it('returns empty array for empty input', () => {
		expect(installedToAppLinks([])).toEqual([]);
	});
});
