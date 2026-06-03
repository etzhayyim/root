import adapter from '@sveltejs/adapter-cloudflare';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

/** @type {import('@sveltejs/kit').Config} */
const config = {
	preprocess: vitePreprocess(),
	kit: {
		// fallback: 'spa' tells adapter-cloudflare to emit an index.html SPA
		// shell (with hashed module preloads) so the parent magatama-yoro
		// Worker's Assets binding can serve it as the `not_found_handling:
		// "single-page-application"` fallback.
		adapter: adapter({ fallback: 'spa' }),
		alias: {
			$lib: 'src/lib'
		}
	}
};

export default config;
