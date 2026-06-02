/**
 * Runtime validation utilities for API responses
 * These validations help catch type mismatches at runtime
 */

export function validateEpisodesResponse(response: unknown): asserts response is { episodes: Array<{ id: string; title: string; totalPages: number }> } {
	if (!response || typeof response !== 'object') {
		throw new Error(`Invalid response: expected object, got ${typeof response}`);
	}
	
	if (!('episodes' in response)) {
		throw new Error('Invalid response: missing episodes field');
	}
	
	if (!Array.isArray(response.episodes)) {
		throw new Error(`Invalid response: episodes is not an array, got ${typeof response.episodes}`);
	}
	
	for (const episode of response.episodes) {
		if (!episode || typeof episode !== 'object') {
			throw new Error(`Invalid episode: expected object, got ${typeof episode}`);
		}
		if (typeof episode.id !== 'string') {
			throw new Error(`Invalid episode.id: expected string, got ${typeof episode.id}`);
		}
		if (typeof episode.title !== 'string') {
			throw new Error(`Invalid episode.title: expected string, got ${typeof episode.title}`);
		}
		if (typeof episode.totalPages !== 'number') {
			throw new Error(`Invalid episode.totalPages: expected number, got ${typeof episode.totalPages}`);
		}
	}
}

export function validatePanelsResponse(response: unknown): asserts response is { panels: Array<unknown> } {
	if (!response || typeof response !== 'object') {
		throw new Error(`Invalid response: expected object, got ${typeof response}`);
	}
	
	if (!('panels' in response)) {
		throw new Error('Invalid response: missing panels field');
	}
	
	if (!Array.isArray(response.panels)) {
		throw new Error(`Invalid response: panels is not an array, got ${typeof response.panels}`);
	}
}
