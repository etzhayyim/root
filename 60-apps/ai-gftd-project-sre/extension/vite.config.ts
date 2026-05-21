import { defineConfig } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';
import { resolve } from 'path';
import { copyFileSync, mkdirSync, cpSync } from 'fs';

export default defineConfig({
	resolve: {
		alias: {
			'@sre-shared': resolve(__dirname, '../shared/sre-toolbar-ui/src')
		}
	},
	plugins: [
		svelte({
			compilerOptions: {
				customElement: true
			}
		}),
		{
			name: 'copy-extension-files',
			writeBundle() {
				copyFileSync('manifest.json', 'dist/manifest.json');
				mkdirSync('dist/content', { recursive: true });
				mkdirSync('dist/icons', { recursive: true });
				cpSync('icons', 'dist/icons', { recursive: true });
			}
		}
	],
	build: {
		outDir: 'dist',
		rollupOptions: {
			input: {
				popup: resolve(__dirname, 'popup.html'),
				background: resolve(__dirname, 'src/background/main.ts'),
				toolbar: resolve(__dirname, 'src/content/toolbar.ts'),
				inject: resolve(__dirname, 'src/content/inject.ts')
			},
			output: {
				entryFileNames: (chunkInfo) => {
					if (chunkInfo.name === 'background') return 'background.js';
					if (chunkInfo.name === 'toolbar') return 'content/toolbar.js';
					if (chunkInfo.name === 'inject') return 'content/inject.js';
					return '[name].js';
				},
				chunkFileNames: 'chunks/[name]-[hash].js',
				assetFileNames: 'assets/[name]-[hash][extname]'
			}
		},
		emptyOutDir: true
	},
	define: {
		'process.env': '{}',
		global: 'globalThis'
	}
});
