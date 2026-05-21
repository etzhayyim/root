import { defineConfig } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';

export default defineConfig({
	plugins: [svelte({ compilerOptions: { css: 'injected' } })],
	build: {
		lib: {
			entry: './src/appview.svelte',
			formats: ['es'],
			fileName: 'appview'
		},
		outDir: 'dist-appview',
		emptyOutDir: true,
		rollupOptions: {
			external: [
				'svelte',
				'svelte/internal',
				'svelte/store',
				'svelte/transition',
				'svelte/motion',
				'svelte/animate',
				'svelte/easing'
			]
		}
	}
});
