import { svelte } from '@sveltejs/vite-plugin-svelte';
import { defineConfig } from 'vite';

export default defineConfig({
	plugins: [svelte()],
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
	server: {
		proxy: {
			'/translate.v1.TranslationService': {
				target: 'http://localhost:8080',
				changeOrigin: true
			},
			'/translate.v1.MCPService': {
				target: 'http://localhost:8080',
				changeOrigin: true
			}
		}
	}
});
