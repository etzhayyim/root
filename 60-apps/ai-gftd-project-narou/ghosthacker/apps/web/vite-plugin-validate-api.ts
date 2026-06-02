import type { Plugin } from 'vite';

/**
 * Vite plugin to validate API client usage and response types at build time
 */
export function validateApiClient(): Plugin {
	return {
		name: 'validate-api-client',
		enforce: 'pre',
		buildStart() {
			console.log('[validate-api-client] Starting API client validation...');
		},
		transform(code, id) {
			// Check for common API client issues
			if (id.includes('storyboard-client.ts') || id.includes('StoryboardEditor.svelte')) {
				// Validate that response handling is correct
				if (code.includes('response.episodes') && !code.includes('Array.isArray')) {
					console.warn(
						`[validate-api-client] Warning: ${id} accesses response.episodes without Array.isArray check`
					);
				}
				
				// Check for proper error handling
				if (code.includes('storyboardClient.') && !code.includes('catch')) {
					console.warn(
						`[validate-api-client] Warning: ${id} uses storyboardClient without error handling`
					);
				}
			}
			
			return null;
		},
		buildEnd() {
			console.log('[validate-api-client] API client validation complete');
		}
	};
}
