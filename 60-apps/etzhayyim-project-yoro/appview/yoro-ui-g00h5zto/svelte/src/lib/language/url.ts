import type { LanguageCode } from './types.js';

/**
 * Replace the language segment in a URL path.
 * Assumes the language code is the first path segment (e.g., `/ja/articles/123`).
 *
 * @param pathname - Current URL pathname
 * @param newLang - New language code
 * @returns Updated pathname with the language segment replaced
 */
export function replacePathLang(pathname: string, newLang: LanguageCode): string {
	const segments = pathname.split('/');
	segments[1] = newLang;
	return segments.join('/') || '/';
}

/**
 * Extract the language segment from a URL path.
 * Assumes the language code is the first path segment.
 *
 * @param pathname - URL pathname (e.g., `/ja/articles/123`)
 * @returns The language segment, or undefined if path is too short
 */
export function extractPathLang(pathname: string): string | undefined {
	const segments = pathname.split('/');
	return segments[1] || undefined;
}
