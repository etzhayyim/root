import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';
import { validateApiClient } from './vite-plugin-validate-api';

export default defineConfig({
	plugins: [
		sveltekit(),
		validateApiClient()
	],
	server: {
		port: 1421,
		strictPort: true,
		host: true,
		allowedHosts: true,
		watch: {
			usePolling: true
		},
		hmr: {
			clientPort: 1421
		}
	},
	ssr: {
		noExternal: [
			'@bufbuild/protobuf',
			'@connectrpc/connect',
			'@connectrpc/connect-web'
		]
	},
	envPrefix: ['VITE_'],
	build: {
		target: 'esnext',
		minify: 'esbuild',
		sourcemap: true,
		rollupOptions: {
			onwarn(warning, warn) {
				// Treat API client warnings as errors during build
				if (warning.message.includes('storyboardClient') || warning.message.includes('response.episodes')) {
					throw new Error(`Build error: ${warning.message}`);
				}
				warn(warning);
			}
		}
	}
});
