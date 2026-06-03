import adapter from '@sveltejs/adapter-static';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

export default {
  preprocess: vitePreprocess(),
  kit: {
    // Workers Assets serves svelte/build/. Static prerender + SPA fallback
    // so the Worker's Hono router can route un-prerendered paths to inline
    // HTML (e.g. /docs, /comparison) while /studio/** is fully client-side.
    adapter: adapter({
      pages: 'build',
      assets: 'build',
      fallback: 'index.html',
      precompress: false,
      strict: false,
    }),
    paths: {
      relative: false,
    },
  },
};
